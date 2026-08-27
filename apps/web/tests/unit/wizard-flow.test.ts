/**
 * Wizard 流程逻辑单元测试（node:test + fetch mock，WP-B2）。
 *
 * 覆盖（M13-R1 WP-B2）：
 * - discovery 成功 / 503 降级 / 空列表三态；
 * - probe 无模型 → no-models（进入 Models 步而非静默成功）；
 * - probe ok=false → result 返回给调用方分支（DoneStep 渲染失败态，
 *   不伪装成功外观）；
 * - 手动 Model ID 路径（api.createModel 直接可达，客户端契约断言）。
 */

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import { api } from "../../src/api/client";
import { discoverOrFallback, probeFirstModel } from "../../src/features/setup/wizardApi";

let responses: Response[] = [];
let calls: { url: string; init: RequestInit }[] = [];

beforeEach(() => {
  responses = [];
  calls = [];
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

test("discoverOrFallback: discovery 成功返回模型 id 列表", async () => {
  responses.push(jsonResponse({ model_ids: ["m-a", "m-b"] }));
  const outcome = await discoverOrFallback("ep-1");
  assert.deepEqual(outcome, { ids: ["m-a", "m-b"], error: null });
});

test("discoverOrFallback: discovery 503 降级为手动输入提示（不抛异常）", async () => {
  responses.push(
    jsonResponse(
      {
        type: "about:blank",
        title: "Relay Unavailable",
        status: 503,
        detail: "relay down",
        instance: "/x",
      },
      503,
    ),
  );
  const outcome = await discoverOrFallback("ep-1");
  assert.deepEqual(outcome.ids, []);
  assert.ok(outcome.error?.startsWith("discovery unavailable"), outcome.error ?? "");
});

test("discoverOrFallback: 空列表提示手动输入", async () => {
  responses.push(jsonResponse({ model_ids: [] }));
  const outcome = await discoverOrFallback("ep-1");
  assert.deepEqual(outcome.ids, []);
  assert.ok(outcome.error?.includes("enter a model id manually"), outcome.error ?? "");
});

test("probeFirstModel: 无模型 → no-models（进入 Models 步而非静默成功）", async () => {
  responses.push(jsonResponse([]));
  const outcome = await probeFirstModel("ep-1");
  assert.equal(outcome.kind, "no-models");
});

test("probeFirstModel: probe ok=false 仍返回 result（调用方分支渲染失败态）", async () => {
  responses.push(jsonResponse([{ id: "m-1", model_name: "m", endpoint_id: "ep-1" }]));
  responses.push(
    jsonResponse({
      model_id: "m-1",
      ok: false,
      observed_capabilities: [],
      returned_model_name: null,
      system_fingerprint: null,
      provider_fingerprint_available: false,
      error_category: "MODEL_AUTH",
      error_message_redacted: "401 ***REDACTED***",
      capability_failures: [],
      probed_at: "2026-08-26T00:00:00Z",
      fingerprint: null,
    }),
  );
  const outcome = await probeFirstModel("ep-1");
  if (outcome.kind !== "result") {
    assert.fail("expected result outcome");
  }
  assert.equal(outcome.result.ok, false);
  assert.equal(outcome.result.error_category, "MODEL_AUTH");
});

test("probeFirstModel: probe ok=true 返回成功结果", async () => {
  responses.push(jsonResponse([{ id: "m-1", model_name: "m", endpoint_id: "ep-1" }]));
  responses.push(
    jsonResponse({
      model_id: "m-1",
      ok: true,
      observed_capabilities: ["CHAT"],
      returned_model_name: "m",
      system_fingerprint: "fp-1",
      provider_fingerprint_available: true,
      error_category: null,
      error_message_redacted: null,
      capability_failures: [],
      probed_at: "2026-08-26T00:00:00Z",
      fingerprint: null,
    }),
  );
  const outcome = await probeFirstModel("ep-1");
  if (outcome.kind !== "result") {
    assert.fail("expected result outcome");
  }
  assert.equal(outcome.result.ok, true);
  assert.equal(outcome.result.provider_fingerprint_available, true);
});

test("手动 Model ID 路径：api.createModel 携带 Idempotency-Key", async () => {
  responses.push(jsonResponse({ id: "m-9", model_name: "gpt-4o-mini", endpoint_id: "ep-1" }));
  const created = await api.createModel({
    endpoint_id: "ep-1",
    model_name: "gpt-4o-mini",
    enabled: true,
  });
  assert.equal(created.id, "m-9");
  const headers = new Headers(calls[0]?.init.headers);
  assert.ok(headers.get("Idempotency-Key"), "createModel 必须带 Idempotency-Key");
  assert.ok(calls[0]?.url.includes("/models"));
});
