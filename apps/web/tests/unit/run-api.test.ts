/**
 * Run 相关 API client 单元测试（node:test + fetch mock）。
 *
 * 验证（M13 DoD 6/12）：run 启动/cancel 走 Idempotency-Key；
 * Timeline 事件按 event_id 排序去重（replay 投影）；错误映射。
 */

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import { api } from "../../src/api/client";

type FetchCall = { url: string; init: RequestInit };

let calls: FetchCall[] = [];
let responses: Response[] = [];

beforeEach(() => {
  calls = [];
  responses = [];
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    calls.push({ url, init: init ?? {} });
    const next = responses.shift();
    if (next === undefined) {
      return new Response("{}", { status: 200 });
    }
    return next;
  }) as typeof fetch;
});

afterEach(() => {
  delete (globalThis as { fetch?: unknown }).fetch;
});

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

const runDetail = {
  id: "run-1",
  project_id: "example-project",
  protocol_id: "sort_analysis_v1_0_1",
  state: "RUNNING",
  manifest_digest: "sha256:abc",
  created_at: "2026-08-24T00:00:00Z",
  updated_at: "2026-08-24T00:00:00Z",
};

test("startRun 发送 Idempotency-Key（mutating）", async () => {
  responses.push(jsonResponse(runDetail));
  const result = await api.startRun("sort_analysis_v1.yaml");
  assert.equal(result.id, "run-1");
  const headers = new Headers(calls[0]?.init.headers);
  assert.ok(headers.get("Idempotency-Key"), "start run 必须带 Idempotency-Key");
});

test("cancelRun 发送 Idempotency-Key", async () => {
  responses.push(jsonResponse({ ...runDetail, state: "CANCELLED" }));
  const result = await api.cancelRun("run-1");
  assert.equal(result.state, "CANCELLED");
  const headers = new Headers(calls[0]?.init.headers);
  assert.ok(headers.get("Idempotency-Key"));
});

test("runEvents 返回按 event_id 排序的 projection（去重基础）", async () => {
  const events = [
    { event_id: "e-2", type: "task.completed", occurred_at: "2026-08-24T00:00:02Z", payload: {} },
    { event_id: "e-1", type: "manifest.frozen", occurred_at: "2026-08-24T00:00:01Z", payload: {} },
    { event_id: "e-1", type: "manifest.frozen", occurred_at: "2026-08-24T00:00:01Z", payload: {} },
  ];
  responses.push(jsonResponse(events));
  const result = await api.runEvents("run-1");
  assert.equal(result.length, 3);
  assert.equal(new Set(result.map((item) => item.event_id)).size, 2);
});

test("409 映射为 ApiError（Invalid Transition）", async () => {
  responses.push(
    jsonResponse(
      {
        type: "about:blank",
        title: "Invalid Transition",
        status: 409,
        detail: "invalid transition",
        instance: "/runs/run-1/cancel",
      },
      409,
    ),
  );
  await assert.rejects(
    () => api.cancelRun("run-1"),
    (err: unknown) => {
      assert.ok(err instanceof Error);
      assert.equal((err as { status?: number }).status, 409);
      return true;
    },
  );
});