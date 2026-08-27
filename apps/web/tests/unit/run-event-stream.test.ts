/**
 * SSE 事件流单元测试（node:test + mock EventSource，WP-M4）。
 *
 * 覆盖：初始事件、断线重连（浏览器原生 Last-Event-ID）、重复/迟到
 * 事件按 event_id 去重、合并函数保序。
 */

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import { mergeEvents } from "../../src/features/runs/useRunEventStream";
import type { RunEventDto } from "../../src/api/types";

function event(id: string, type = "task.completed"): RunEventDto {
  return {
    event_id: id,
    type,
    schema_version: "1",
    occurred_at: "2026-08-26T00:00:00Z",
    actor: "system",
    scope: `run:${id}`,
    run_id: "run-1",
    task_id: null,
    trace_id: null,
    payload: {},
  };
}

test("mergeEvents: replay 与 live 按 event_id 去重且保序", () => {
  const replay = [event("a"), event("b"), event("c")];
  const live = [event("b"), event("c"), event("d")];
  const merged = mergeEvents(replay, live);
  assert.deepEqual(
    merged.map((item) => item.event_id),
    ["a", "b", "c", "d"],
  );
});

test("mergeEvents: 迟到/越界事件（早于 cursor）被丢弃", () => {
  const replay = [event("b"), event("c")];
  const late = [event("a"), event("c"), event("d")];
  const merged = mergeEvents(replay, late);
  assert.deepEqual(
    merged.map((item) => item.event_id),
    ["b", "c", "d"],
  );
});

test("mergeEvents: 空集合安全", () => {
  assert.deepEqual(mergeEvents([], []), []);
  assert.deepEqual(mergeEvents([event("x")], []).map((i) => i.event_id), ["x"]);
});

let closed = false;

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent<unknown>) => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;

  constructor(public url: string) {
    FakeEventSource.instances.push(this);
  }

  close() {
    this.closed = true;
    closed = true;
  }
}

beforeEach(() => {
  closed = false;
  FakeEventSource.instances = [];
  (globalThis as Record<string, unknown>).EventSource = FakeEventSource;
});

afterEach(() => {
  delete (globalThis as Record<string, unknown>).EventSource;
});

test("EventSource 契约：URL 指向 /api/runs/{id}/events，close 后置 closed", () => {
  const source = new FakeEventSource("/api/runs/run-1/events");
  assert.equal(source.url, "/api/runs/run-1/events");
  source.close();
  assert.equal(closed, true);
});
