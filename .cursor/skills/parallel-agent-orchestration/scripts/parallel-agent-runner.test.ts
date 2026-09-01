import assert from "node:assert/strict";
import { test } from "node:test";

import { runWaves } from "./runner.ts";
import type { WaveConfig } from "./runner.ts";
import { splitWaves, validateTasks } from "./waves.ts";
import { verifyModel } from "./model-preflight.ts";
import { MAX_PARALLEL_PER_WAVE } from "./types.ts";
import type { ModelCatalog, ParallelTask, RunHandle, RunOutcome, RuntimeOptions } from "./types.ts";
import { Barrier, FakeFactory, FakeRun, finished, optionsFor, tasksOf } from "./fakes.ts";
import type { FakeRunWindow } from "./fakes.ts";

function configFor(options = optionsFor(), hooks = {}): WaveConfig {
  return { options, hooks };
}

/** Explicit runtime lookup; avoids relying on find()/index narrowing. */
function summaryOf<T extends { taskId: string }>(summaries: readonly T[], taskId: string): T {
  for (const summary of summaries) {
    if (summary.taskId === taskId) {
      return summary;
    }
  }
  throw new Error(`missing summary for ${taskId}`);
}

function failureReasonOf(model: { readonly ok: boolean; readonly reason?: string }): string {
  if (model.ok) {
    throw new Error(`expected model preflight failure, got ok for ${model.reason ?? "?"}`);
  }
  return model.reason ?? "no reason";
}

test("三个任务在同一波内并发进入（区间重叠）", async () => {
  const barrier = new Barrier();
  const factory = new FakeFactory(barrier, new Map());
  const pending = runWaves(factory, tasksOf(3), configFor());
  await new Promise((resolve) => setTimeout(resolve, 10));
  barrier.release();
  const summaries = await pending;
  assert.equal(summaries.length, 3);
  assert.ok(summaries.every((summary) => summary.status === "finished"));
});

test("第四个任务在下一波启动，且没有累计任务上限", async () => {
  const barrier = new Barrier();
  const factory = new FakeFactory(barrier, new Map());
  const windows = new Map<string, FakeRunWindow>();
  const hooks = {
    onRunStart: (task: ParallelTask, run: RunHandle) => {
      windows.set(task.id, (run as FakeRun).window);
    },
  };
  const pending = runWaves(factory, tasksOf(4), configFor(optionsFor(), hooks));
  await new Promise((resolve) => setTimeout(resolve, 10));
  const waveOneIds = ["task-1", "task-2", "task-3"];
  const started = waveOneIds.map((id) => summaryOfWindow(windows, id).start);
  assert.ok(started.every((value) => value !== undefined));
  assert.equal(windows.get("task-4"), undefined);
  barrier.release();
  const summaries = await pending;
  assert.equal(summaries.length, 4);
  const waveOneEnd = Math.max(...waveOneIds.map((id) => summaryOfWindow(windows, id).end ?? 0));
  const lateStart = summaryOfWindow(windows, "task-4").start;
  assert.ok(lateStart !== undefined);
  assert.ok(lateStart >= waveOneEnd);
  assert.equal(factory.created, 4);
});

function summaryOfWindow(windows: ReadonlyMap<string, FakeRunWindow>, id: string): FakeRunWindow {
  const hit = windows.get(id);
  if (hit === undefined) {
    throw new Error(`missing run window for ${id}`);
  }
  return hit;
}

test("单个任务启动失败不影响其他任务", async () => {
  const barrier = new Barrier();
  const outcomes = new Map<string, RunOutcome | { code: string }>([
    ["task-2", { code: "auth_error" }],
  ]);
  const factory = new FakeFactory(barrier, outcomes);
  barrier.release();
  const summaries = await runWaves(factory, tasksOf(3), configFor());
  const failed = summaryOf(summaries, "task-2");
  assert.equal(failed.status, "startup_failed");
  assert.equal(failed.failureClass, "startup");
  assert.equal(failed.reason, "auth_error");
  assert.ok(summaries.filter((summary) => summary.status === "finished").length === 2);
});

test("运行失败与取消分别保留，且 dispose 全路径执行", async () => {
  const barrier = new Barrier();
  const outcomes = new Map<string, ReturnType<typeof finished> | { code: string }>([
    [
      "task-1",
      {
        status: "error",
        result: undefined,
        errorCode: "timeout",
        requestId: "req-1",
        resolvedModelId: undefined,
        durationMs: undefined,
      },
    ],
    [
      "task-2",
      {
        status: "cancelled",
        result: undefined,
        errorCode: undefined,
        requestId: undefined,
        resolvedModelId: undefined,
        durationMs: undefined,
      },
    ],
    ["task-3", finished()],
  ]);
  const factory = new FakeFactory(barrier, outcomes);
  barrier.release();
  const summaries = await runWaves(factory, tasksOf(3), configFor());
  assert.equal(summaryOf(summaries, "task-1").status, "run_failed");
  assert.equal(summaryOf(summaries, "task-2").status, "cancelled");
  assert.equal(summaryOf(summaries, "task-3").status, "finished");
  assert.ok(factory.agents.every((agent) => agent.disposed));
});

test("解析模型与请求模型不一致时按 model_drift 失败", async () => {
  const barrier = new Barrier();
  const outcomes = new Map<string, ReturnType<typeof finished> | { code: string }>([
    ["task-1", finished("ok", "fallback-model")],
  ]);
  const factory = new FakeFactory(barrier, outcomes);
  barrier.release();
  const summaries = await runWaves(factory, tasksOf(1), configFor());
  const summary = summaryOf(summaries, "task-1");
  assert.equal(summary.status, "run_failed");
  assert.equal(summary.failureClass, "model_drift");
  assert.equal(summary.resolvedModel, "fallback-model");
});

test("abort 信号把未启动任务记为取消", async () => {
  const controller = new AbortController();
  const options: RuntimeOptions = { ...optionsFor(), signal: controller.signal };
  const barrier = new Barrier();
  const factory = new FakeFactory(barrier, new Map());
  const pending = runWaves(factory, tasksOf(4), configFor(options));
  await new Promise((resolve) => setTimeout(resolve, 10));
  controller.abort();
  barrier.release();
  const summaries = await pending;
  const late = summaryOf(summaries, "task-4");
  assert.equal(late.status, "cancelled");
  assert.equal(late.reason, "cancelled_before_start");
});

test("splitWaves 限制波大小并拒绝越界", () => {
  assert.equal(MAX_PARALLEL_PER_WAVE, 3);
  const waves = splitWaves(tasksOf(7), 3);
  assert.deepEqual(
    waves.map((wave) => wave.length),
    [3, 3, 1],
  );
  assert.throws(() => splitWaves(tasksOf(1), 4), RangeError);
  assert.throws(() => splitWaves(tasksOf(1), 0), RangeError);
});

test("任务校验拒绝重复 id、空 prompt 与非只读 mutation", () => {
  const issues = validateTasks([
    { id: "a", prompt: "p1", mutation: "read_only" },
    { id: "a", prompt: "p2", mutation: "read_only" },
    { id: "b", prompt: "  ", mutation: "read_only" },
    { id: "c", prompt: "p3", mutation: "write" },
    { id: "d", prompt: "p4" },
  ]);
  assert.deepEqual(
    issues.map((issue) => `${issue.taskId}:${issue.reason.split(" ")[0] ?? ""}`),
    ["a:duplicate", "b:prompt", "c:only", "d:task"],
  );
});

test("模型目录 preflight：命中、缺失与目录不可用均按契约处理", async () => {
  const catalog: ModelCatalog = {
    list: () =>
      Promise.resolve([
        { id: "model-a", displayName: "Model A" },
        { id: "model-b", displayName: "Model B" },
      ]),
  };
  const hit = await verifyModel(catalog, "model-a");
  assert.equal(hit.ok, true);
  const missing = await verifyModel(catalog, "model-z");
  assert.equal(missing.ok, false);
  const broken: ModelCatalog = {
    list: () => Promise.reject(new Error("down")),
  };
  const unavailable = await verifyModel(broken, "model-a");
  assert.equal(unavailable.ok, false);
  assert.equal(failureReasonOf(unavailable), "model_catalog_unavailable");
});
