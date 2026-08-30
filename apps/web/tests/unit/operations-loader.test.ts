/**
 * Operations loaders 单元测试（node:test + 全局 fetch mock）。
 *
 * 覆盖 M15 operations 视图的读取编排（useOperations 的非 React 部分）：
 * - fetchOperationsRun 同时命中 telemetry 与 cost 两个端点；
 * - 任一端点失败时错误向外传播（hook 端转为 error 态，不吞成空态）；
 * - fetchOperationsTrend 透传 dataset / expected digests / limit；
 * - operationsErrorMessage 区分 Error 与未知异常。
 */

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import { ApiError } from "../../src/api/client";
import {
  fetchOperationsRun,
  fetchOperationsTrend,
  operationsErrorMessage,
} from "../../src/features/operations/useOperations";

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
      return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
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

test("fetchOperationsRun 同时读取 telemetry 与 cost 并组装快照", async () => {
  responses.push(
    jsonResponse({
      run_id: "run-9",
      generated_at: "2026-08-30T00:00:00Z",
      tasks: { total: 2, succeeded: 2, failed: 0, cancelled: 0, queued: 0, leased: 0, other: 0 },
      outbox: { pending: 0, status: "KNOWN", unavailable_reason: null },
      sink: { enabled: true, dropped: 0, unlinked: 0, last_error: null },
    }),
  );
  responses.push(
    jsonResponse({
      run_id: "run-9",
      pricing_version: "v1",
      pricing_digest: "sha256:pricing",
      pricing_frozen: true,
      pricing_degraded_reason: null,
      dimensions: [],
      total: {
        status: "ESTIMATED",
        minor_units: 250,
        currency: "JPY",
        effective_from: "2026-08-30",
        calculation_method: "unit_price_minor_per_unit",
      },
    }),
  );
  const snapshot = await fetchOperationsRun("run-9");
  assert.deepEqual(
    calls.map((call) => call.url),
    ["/api/runs/run-9/telemetry", "/api/runs/run-9/cost"],
  );
  assert.equal(snapshot.telemetry.run_id, "run-9");
  assert.equal(snapshot.cost.total.minor_units, 250);
  assert.equal(snapshot.cost.total.currency, "JPY");
});

test("fetchOperationsRun 在端点失败时向外传播 ApiError", async () => {
  responses.push(jsonResponse({ detail: "not found" }, 404));
  await assert.rejects(
    () => fetchOperationsRun("missing-run"),
    (error: unknown) => error instanceof ApiError && error.status === 404,
  );
  assert.equal(calls.length, 2);
});

test("fetchOperationsTrend 透传 dataset、expected digests 与 limit", async () => {
  responses.push(
    jsonResponse({
      dataset_id: "ds-1",
      truncated: false,
      segments: [],
      divergences: [],
      missing: [],
    }),
  );
  const trend = await fetchOperationsTrend("ds-1", ["sha256:a"], 25);
  const [trendCall] = calls;
  assert.ok(trendCall, "expected one recorded fetch");
  assert.match(trendCall.url, /dataset_id=ds-1/);
  assert.match(trendCall.url, /expected_digests=sha256%3Aa/);
  assert.match(trendCall.url, /limit=25/);
  assert.equal(trend.dataset_id, "ds-1");
});

test("operationsErrorMessage 归一化异常消息", () => {
  assert.equal(operationsErrorMessage(new Error("boom")), "boom");
  assert.equal(operationsErrorMessage("not-an-error"), "operations failed");
});
