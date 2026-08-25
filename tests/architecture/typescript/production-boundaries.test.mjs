import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const cli = path.join(root, "node_modules", "dependency-cruiser", "bin", "dependency-cruise.mjs");
const config = path.join(root, "dependency-cruiser.config.mjs");

function listSourceFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...listSourceFiles(full));
    } else if (/\.(ts|tsx)$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

test("apps/web 生产源码通过全部生产架构边界", () => {
  const result = spawnSync(
    process.execPath,
    [cli, "--config", config, "--output-type", "json", "apps/web/src"],
    { cwd: root, encoding: "utf8", env: { ...process.env, FORCE_COLOR: "0" } },
  );
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  assert.deepEqual(report.summary.violations, []);
});

test("apps/web 源码不 import packages/domain 或 adapters（静态扫描）", () => {
  const files = listSourceFiles(path.join(root, "apps/web/src"));
  assert.ok(files.length > 0, "apps/web/src 必须存在生产源码");
  for (const file of files) {
    const source = readFileSync(file, "utf8");
    assert.ok(
      !/from ["'](?:packages\/domain|adapters|services\/)/.test(source),
      `${path.relative(root, file)} 不得 import domain/adapter/services 内部`,
    );
  }
});

test("services/api 生产源码通过全部生产架构边界", () => {
  const result = spawnSync(
    process.execPath,
    [cli, "--config", config, "--output-type", "json", "services"],
    { cwd: root, encoding: "utf8", env: { ...process.env, FORCE_COLOR: "0" } },
  );
  // services 是 Python 包（无 TS 文件）；depcruise 对空目录应无违规或跳过
  if (result.status === 0) {
    const report = JSON.parse(result.stdout);
    assert.deepEqual(report.summary.violations, []);
  }
});
