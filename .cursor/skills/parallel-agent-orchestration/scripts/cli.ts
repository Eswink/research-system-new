#!/usr/bin/env node
/**
 * Deterministic parallel agent orchestration CLI.
 *
 * Explicitly invoked (see SKILL.md); requires CURSOR_API_KEY in the
 * environment. Never accepts the API key as an argument, never reads .env
 * files, and prints only redacted run summaries on stdout.
 */
import { readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

import { SdkAgentFactory, SdkModelCatalog } from "./sdk-adapter.ts";
import { verifyModel } from "./model-preflight.ts";
import { runWaves } from "./runner.ts";
import type { WaveHooks } from "./runner.ts";
import { validateTasks, formatIssues } from "./waves.ts";
import type { AgentRunSummary, ParallelTask, RunHandle } from "./types.ts";

const MAX_TASKS_BYTES = 64 * 1024;

export interface ParsedArgs {
  readonly modelId: string;
  readonly tasksPath: string;
  readonly cwd: string;
}

export function parseCliArgs(argv: readonly string[]): ParsedArgs {
  const values = new Map<string, string>();
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (flag === undefined || value === undefined || !flag.startsWith("--")) {
      throw new Error(`usage: agents:parallel --model-id <id> --tasks <file> [--cwd <dir>]`);
    }
    values.set(flag, value);
  }
  const modelId = values.get("--model-id");
  const tasksPath = values.get("--tasks");
  const cwd = values.get("--cwd") ?? process.cwd();
  if (modelId === undefined || tasksPath === undefined) {
    throw new Error(`missing required flags; got: ${[...values.keys()].join(",") || "none"}`);
  }
  return { modelId, tasksPath, cwd };
}

export function loadTasksFile(tasksPath: string): ParallelTask[] {
  const raw = readFileSync(tasksPath, "utf8");
  if (Buffer.byteLength(raw, "utf8") > MAX_TASKS_BYTES) {
    throw new Error(`tasks file exceeds ${String(MAX_TASKS_BYTES)} bytes`);
  }
  const parsed: unknown = JSON.parse(raw);
  if (!Array.isArray(parsed)) {
    throw new Error("tasks file must be a JSON array");
  }
  const issues = validateTasks(parsed);
  if (issues.length > 0) {
    throw new Error(`invalid tasks: ${formatIssues(issues)}`);
  }
  return parsed as ParallelTask[];
}

/** Fail closed when the key is absent; never log or echo its value. */
export function requireApiKey(env: NodeJS.ProcessEnv): string {
  const apiKey = env.CURSOR_API_KEY;
  if (typeof apiKey !== "string" || apiKey.trim().length === 0) {
    throw new Error("CURSOR_API_KEY is not set; refusing to start");
  }
  return apiKey;
}

export function exitCodeFor(summaries: readonly AgentRunSummary[]): number {
  const hasStartup = summaries.some(
    (s) => s.failureClass === "startup" || s.failureClass === "preflight",
  );
  if (hasStartup) {
    return 1;
  }
  return summaries.every((s) => s.status === "finished") ? 0 : 2;
}

export function serializeSummaries(summaries: readonly AgentRunSummary[]): string {
  return `${JSON.stringify(summaries, null, 2)}\n`;
}

export function printSummaries(summaries: readonly AgentRunSummary[]): void {
  process.stdout.write(serializeSummaries(summaries));
}

/** Registers active run handles; Ctrl+C aborts further waves and cancels them. */
function startCancellation(hooksRef: { hooks: WaveHooks }, controller: AbortController): void {
  const active = new Set<RunHandle>();
  hooksRef.hooks = {
    onRunStart: (_task, run) => {
      active.add(run);
      run.wait().then(
        () => active.delete(run),
        () => active.delete(run),
      );
    },
  };
  const abort = async (): Promise<void> => {
    controller.abort();
    await Promise.allSettled([...active].map((run) => run.cancel()));
  };
  process.once("SIGINT", () => {
    void abort();
  });
}

async function main(): Promise<number> {
  const args = parseCliArgs(process.argv.slice(2));
  const apiKey = requireApiKey(process.env);
  const cwd = resolve(args.cwd);
  statSync(cwd);
  const tasks = loadTasksFile(resolve(args.tasksPath));
  const preflight = await verifyModel(new SdkModelCatalog(apiKey), args.modelId);
  if (!preflight.ok) {
    process.stderr.write(`model preflight failed: ${preflight.reason}\n`);
    return 1;
  }
  const hooksRef: { hooks: WaveHooks } = { hooks: {} };
  const controller = new AbortController();
  startCancellation(hooksRef, controller);
  const summaries = await runWaves(new SdkAgentFactory(), tasks, {
    options: { cwd, modelId: preflight.modelId, apiKey, signal: controller.signal },
    hooks: hooksRef.hooks,
  });
  printSummaries(summaries);
  return exitCodeFor(summaries);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  main()
    .then((code) => {
      process.exitCode = code;
    })
    .catch((error: unknown) => {
      process.stderr.write(`${error instanceof Error ? error.message : "startup failed"}\n`);
      process.exitCode = 1;
    });
}
