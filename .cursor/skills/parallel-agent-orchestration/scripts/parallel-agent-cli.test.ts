import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, test } from "node:test";

import {
  exitCodeFor,
  loadTasksFile,
  parseCliArgs,
  requireApiKey,
  serializeSummaries,
} from "./cli.ts";
import type { AgentRunSummary } from "./types.ts";

const dir = mkdtempSync(join(tmpdir(), "agents-parallel-cli-"));
after(() => {
  rmSync(dir, { recursive: true, force: true });
});

function write(name: string, content: string): string {
  const path = join(dir, name);
  writeFileSync(path, content, "utf8");
  return path;
}

test("parseCliArgs 接受显式参数并拒绝缺失/非法输入", () => {
  const parsed = parseCliArgs([
    "--model-id",
    "gpt-5.6-sol",
    "--tasks",
    "t.json",
    "--cwd",
    "D:/repo",
  ]);
  assert.equal(parsed.modelId, "gpt-5.6-sol");
  assert.equal(parsed.tasksPath, "t.json");
  assert.equal(parsed.cwd, "D:/repo");
  assert.throws(() => parseCliArgs(["--tasks", "t.json"]));
  assert.throws(() => parseCliArgs(["model-id"]));
  assert.throws(() => parseCliArgs([]));
});

test("loadTasksFile 校验结构、重复 id 与 mutation", () => {
  const good = write(
    "good.json",
    JSON.stringify([{ id: "a", prompt: "p", mutation: "read_only" }]),
  );
  assert.equal(loadTasksFile(good).length, 1);
  const notArray = write("not-array.json", JSON.stringify({ id: "a" }));
  assert.throws(() => loadTasksFile(notArray), /JSON array/);
  const duplicate = write(
    "duplicate.json",
    JSON.stringify([
      { id: "a", prompt: "p", mutation: "read_only" },
      { id: "a", prompt: "q", mutation: "read_only" },
    ]),
  );
  assert.throws(() => loadTasksFile(duplicate), /invalid tasks/);
  const mutation = write(
    "mutation.json",
    JSON.stringify([{ id: "a", prompt: "p", mutation: "write" }]),
  );
  assert.throws(() => loadTasksFile(mutation), /invalid tasks/);
});

test("loadTasksFile 拒绝超过大小上限的任务文件", () => {
  const huge = write(
    "huge.json",
    JSON.stringify([{ id: "a", prompt: "x".repeat(70 * 1024), mutation: "read_only" }]),
  );
  assert.throws(() => loadTasksFile(huge), /exceeds/);
});

test("requireApiKey 只从环境读取且拒绝空值", () => {
  assert.throws(() => requireApiKey({}), /CURSOR_API_KEY/);
  assert.throws(() => requireApiKey({ CURSOR_API_KEY: "   " }), /CURSOR_API_KEY/);
  assert.equal(requireApiKey({ CURSOR_API_KEY: "env-only-key" }), "env-only-key");
});

function summary(overrides: Partial<AgentRunSummary>): AgentRunSummary {
  return {
    taskId: "task-1",
    agentId: "agent-1",
    runId: "run-1",
    requestId: "req-1",
    requestedModel: "model-a",
    resolvedModel: "model-a",
    status: "finished",
    durationMs: 10,
    failureClass: undefined,
    resultDigest: "a".repeat(64),
    resultSize: 2,
    reason: undefined,
    ...overrides,
  };
}

test("exitCodeFor 区分 0/1/2", () => {
  assert.equal(exitCodeFor([summary({})]), 0);
  assert.equal(
    exitCodeFor([
      summary({}),
      summary({ taskId: "t2", status: "run_failed", failureClass: "run" }),
    ]),
    2,
  );
  assert.equal(exitCodeFor([summary({ status: "cancelled", failureClass: "cancelled" })]), 2);
  assert.equal(exitCodeFor([summary({ status: "startup_failed", failureClass: "startup" })]), 1);
});

test("serializeSummaries 不包含 prompt、凭据或额外字段", () => {
  const serialized = serializeSummaries([
    summary({}),
    summary({
      taskId: "t2",
      status: "startup_failed",
      failureClass: "startup",
      reason: "auth_error",
    }),
  ]);
  assert.ok(!serialized.includes("prompt"));
  assert.ok(!serialized.includes("apiKey"));
  assert.ok(!serialized.includes("test-key"));
  const allowed = new Set([
    "taskId",
    "agentId",
    "runId",
    "requestId",
    "requestedModel",
    "resolvedModel",
    "status",
    "durationMs",
    "failureClass",
    "resultDigest",
    "resultSize",
    "reason",
  ]);
  for (const parsed of JSON.parse(serialized) as AgentRunSummary[]) {
    for (const key of Object.keys(parsed)) {
      assert.ok(allowed.has(key), `unexpected key: ${key}`);
    }
  }
});
