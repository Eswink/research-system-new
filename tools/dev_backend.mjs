#!/usr/bin/env node
// Dev backend launcher: Postgres (compose) + Control Plane API + Worker Gateway
// in one terminal, auto-loading the repo-root .env (same operator env as
// docs/operations/PERSONAL_DEPLOYMENT.md §5).
//
// Usage:
//   pnpm dev:backend                 # start api + gateway (default)
//   pnpm dev:backend:postgres-only   # only ensure Postgres (API/Gateway manual)
//   pnpm dev:backend -- stop         # stop api + gateway
//   pnpm dev:backend -- status       # show process / port / log state
//   pnpm dev:backend -- tail [name]  # tail logs (default: tail all)
//
// Logs: scratch/dev-backend/logs/{postgres,api,gateway}.log
// PIDs: scratch/dev-backend/pids/{api,gateway}.pid
// .env keys set on the host are passed through unchanged; this tool only
// ensures the Postgres service is up and starts the two uv/python processes.

import { spawn, spawnSync } from "node:child_process";
import { closeSync, existsSync, mkdirSync, openSync, readFileSync, writeFileSync } from "node:fs";
import net from "node:net";
import process from "node:process";
import { setTimeout } from "node:timers/promises";
import { fileURLToPath } from "node:url";

import { gatewayBind, parseDsnEndpoint, parseDotEnv } from "./dev-backend/lib.mjs";

const repoRoot = fileURLToPath(new URL("..", import.meta.url));
const composeFile = "infra/compose/personal-production.yaml";
const logDir = "scratch/dev-backend/logs";
const pidDir = "scratch/dev-backend/pids";
const logNames = ["postgres", "api", "gateway"];
const isWin = process.platform === "win32";
// Opened log fds are kept so Windows `shell: true` spawns can reuse them;
// closed when the launcher exits.
const heldFds = new Set();

function fail(message) {
  console.error(`[dev:backend] ${message}`);
  process.exit(1);
}

function sh(args) {
  const res = spawnSync(args[0], args.slice(1), {
    cwd: repoRoot,
    stdio: "inherit",
    shell: isWin,
  });
  if (res.status !== 0) throw new Error(`command failed (${res.status}): ${args.join(" ")}`);
}

function composeUp() {
  sh(["docker", "compose", "--project-directory", ".", "-f", composeFile, "up", "-d", "--build"]);
}

function composeDown() {
  sh(["docker", "compose", "--project-directory", ".", "-f", composeFile, "down"]);
}

function isPortOpen(port, host = "127.0.0.1") {
  return new Promise((resolve) => {
    const socket = net.createConnection({ port, host, timeout: 500 });
    const done = (ok) => {
      socket.destroy();
      resolve(ok);
    };
    socket.once("connect", () => done(true));
    socket.once("error", () => done(false));
    socket.once("timeout", () => done(false));
  });
}

async function ensurePostgres() {
  const endpoint = parseDsnEndpoint(process.env.RESEARCHOS_POSTGRES_DSN);
  if (!endpoint) {
    return fail("RESEARCHOS_POSTGRES_DSN 缺少 user@host[:port]，无法定位端口（.env 是否缺失？）");
  }
  const { host, port } = endpoint;
  const reachable = () =>
    isPortOpen(port, host).then((ok) => (ok ? true : isPortOpen(port, "127.0.0.1")));
  if (await reachable()) {
    console.log(`[dev:backend] Postgres already reachable at ${host}:${port}`);
    return;
  }
  console.log("[dev:backend] Postgres not running, starting compose service...");
  composeUp();
  for (let i = 0; i < 45; i += 1) {
    if (await reachable()) {
      console.log(`[dev:backend] Postgres up at ${host}:${port}`);
      return;
    }
    await setTimeout(2000);
  }
  fail(
    `Postgres did not open ${host}:${port} within 90s（compose 日志：docker compose -f ${composeFile} logs）`,
  );
}

function spawnTracked(name, command, args) {
  mkdirSync(`${repoRoot}/${logDir}`, { recursive: true });
  const logPath = `${repoRoot}/${logDir}/${name}.log`;
  // Windows `shell: true` spawn requires numeric stdio fds, not stream objects.
  // The fd stays open while the launcher lives (kept via a Set, closed on exit).
  const fd = openSync(logPath, "a");
  heldFds.add(fd);
  const child = spawn(command, args, {
    cwd: repoRoot,
    stdio: ["ignore", fd, fd],
    shell: isWin,
  });
  writeFileSync(`${repoRoot}/${pidDir}/${name}.pid`, String(child.pid), "utf-8");
  child.on("exit", (code) => {
    console.log(`[dev:backend] ${name} exited (code=${code}); log: ${logPath}`);
  });
  return child;
}

function readPid(name) {
  const file = `${repoRoot}/${pidDir}/${name}.pid`;
  if (!existsSync(file)) return null;
  const pid = Number(readFileSync(file, "utf-8").trim());
  return Number.isInteger(pid) && pid > 0 ? pid : null;
}

function killTree(pid) {
  if (pid === null) return;
  try {
    process.kill(pid, 0);
  } catch {
    return; // already gone
  }
  if (isWin) {
    spawnSync("taskkill", ["/F", "/T", "/PID", String(pid)], { stdio: "inherit", shell: false });
  } else {
    try {
      process.kill(-pid, "SIGTERM");
    } catch {
      process.kill(pid, "SIGTERM");
    }
  }
}

function closeHeldFds() {
  for (const fd of heldFds) closeSync(fd);
  heldFds.clear();
}

function stopApiAndGateway() {
  for (const name of ["gateway", "api"]) {
    const pid = readPid(name);
    if (pid) {
      console.log(`[dev:backend] stopping ${name} (pid ${pid})`);
      killTree(pid);
    } else {
      console.log(`[dev:backend] ${name}: no recorded pid`);
    }
  }
}

async function status() {
  const endpoint = parseDsnEndpoint(process.env.RESEARCHOS_POSTGRES_DSN);
  const rows = [
    [
      "postgres",
      endpoint
        ? (await isPortOpen(endpoint.port, endpoint.host)) ||
          (await isPortOpen(endpoint.port, "127.0.0.1"))
          ? "UP"
          : "DOWN"
        : "DOWN",
      endpoint ? `dsn ${endpoint.host}:${endpoint.port} (compose ${composeFile})` : "no dsn",
    ],
  ];
  for (const name of ["api", "gateway"]) {
    const pid = readPid(name);
    let alive = false;
    if (pid) {
      try {
        process.kill(pid, 0);
        alive = true;
      } catch {
        alive = false;
      }
    }
    rows.push([name, alive ? `UP (pid ${pid})` : "DOWN", `log ${logDir}/${name}.log`]);
  }
  for (const [svc, state, note] of rows) {
    console.log(`[dev:backend] ${svc.padEnd(8)} ${state.padEnd(16)} ${note}`);
  }
}

function tail(name) {
  if (!logNames.includes(name)) fail(`未知 log 名：${name}（可选：${logNames.join(" / ")}）`);
  const path = `${repoRoot}/${logDir}/${name}.log`;
  if (!existsSync(path)) fail(`${logDir}/${name}.log 不存在（先启动？）`);
  const args = isWin
    ? ["-NoProfile", "-Command", `Get-Content -Wait -Path '${path}'`]
    : ["-f", path];
  const child = spawn(isWin ? "powershell" : "tail", args, { stdio: "inherit" });
  child.on("exit", () => {
    closeHeldFds();
    process.exit(0);
  });
}

function tailAll() {
  const children = [];
  for (const name of logNames) {
    const path = `${repoRoot}/${logDir}/${name}.log`;
    if (!existsSync(path)) continue;
    const args = isWin
      ? [
          "-NoProfile",
          "-Command",
          `Get-Content -Wait -Path '${path}' | ForEach-Object { Write-Host '[${name}] ' $_ }`,
        ]
      : ["-f", path];
    children.push(
      spawn(isWin ? "powershell" : "tail", args, {
        stdio: isWin ? "inherit" : ["ignore", "pipe", "inherit"],
      }),
    );
  }
  if (children.length === 0) fail(`${logDir}/ 下没有日志可 tail（先启动？）`);
  for (const child of children) {
    if (!isWin) child.stdout?.pipe(process.stdout);
    child.on("error", () => {});
  }
  const onSig = () => {
    for (const child of children) child.kill();
    process.exit(0);
  };
  process.on("SIGINT", onSig);
  process.on("SIGTERM", onSig);
}

function start() {
  void (async () => {
    await ensurePostgres();
    for (const name of ["api", "gateway"]) {
      const pid = readPid(name);
      if (pid) killTree(pid); // replace stale process, keep its log file
    }
    const apiPort = process.env.RESEARCHOS_API_PORT ?? "8000";
    const bind = gatewayBind(process.env);
    spawnTracked("api", "uv", [
      "run",
      "--frozen",
      "--no-sync",
      "uvicorn",
      "--factory",
      "services.api.app:create_app",
      "--host",
      "127.0.0.1",
      "--port",
      apiPort,
    ]);
    spawnTracked("gateway", "uv", [
      "run",
      "--frozen",
      "--no-sync",
      "python",
      "-B",
      "-m",
      "services.api.worker_gateway",
    ]);
    console.log("[dev:backend] started:");
    console.log(`  api     -> http://127.0.0.1:${apiPort}   (log ${logDir}/api.log)`);
    console.log(`  gateway -> http://${bind.host}:${bind.port}   (log ${logDir}/gateway.log)`);
    console.log(
      "[dev:backend] stop: pnpm dev:backend -- stop | status: pnpm dev:backend -- status | logs: pnpm dev:backend -- tail",
    );
    const onSig = () => {
      console.log("\n[dev:backend] signal received, stopping api + gateway...");
      stopApiAndGateway();
      closeHeldFds();
      process.exit(0);
    };
    process.on("SIGINT", onSig);
    process.on("SIGTERM", onSig);
  })();
}

function mergeDotEnvIntoProcess() {
  const path = `${repoRoot}/.env`;
  if (!existsSync(path)) return fail("仓库根缺少 .env（Postgres 密码与 Worker 凭据来源）");
  const values = parseDotEnv(readFileSync(path, "utf-8"));
  for (const [key, value] of Object.entries(values)) {
    if (process.env[key] === undefined) process.env[key] = value;
  }
}

function main(argv) {
  mergeDotEnvIntoProcess();
  const flags = new Set(argv.filter((a) => a.startsWith("--")));
  const action = argv.find((a) => !a.startsWith("--")) ?? "start";
  mkdirSync(pidDir, { recursive: true });
  switch (action) {
    case "start":
      if (flags.has("postgres-only")) {
        void ensurePostgres().then(() =>
          console.log("[dev:backend] postgres ensured (api/gateway not started)"),
        );
        return;
      }
      start();
      return;
    case "stop":
      stopApiAndGateway();
      if (flags.has("with-postgres")) {
        console.log("[dev:backend] stopping compose postgres (volumes preserved)...");
        composeDown();
      }
      closeHeldFds();
      return;
    case "status":
      void status();
      return;
    case "tail": {
      const target = argv.find((a) => a !== "tail" && !a.startsWith("--"));
      if (target) tail(target);
      else tailAll();
      return;
    }
    default:
      fail(`未知动作：${action}（可选：start / stop / status / tail）`);
  }
}

main(process.argv.slice(2));
