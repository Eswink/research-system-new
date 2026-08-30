/**
 * Control Plane API client 单元测试（node:test + 全局 fetch mock）。
 *
 * 验证（M13 DoD）：
 * - mutating 请求带 Idempotency-Key（重复提交/重试安全）；
 * - 错误映射为 ApiError（ProblemDto 契约）；
 * - 带 ETag 的资源返回 version（If-Match 语义基础）。
 * 不依赖真实后端；fetch 注入 mock。
 */

import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

import { ApiError, api } from "../../src/api/client";

type FetchCall = {
  url: string;
  init: RequestInit;
};

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

function jsonResponse(body: unknown, status = 200, headers: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...headers },
  });
}

test("createEndpoint 发送 Idempotency-Key 与 JSON body", async () => {
  responses.push(
    jsonResponse(
      {
        id: "ep-1",
        name: "relay-a",
        protocol: "OPENAI_COMPATIBLE",
        base_url: "https://relay.example.com/v1",
        api_style: "chat_completions",
        enabled: true,
        credential: "configured",
        request_timeout_seconds: 60,
        max_retries: 3,
        concurrency_limit: 4,
        version: "sha256:abc",
      },
      201,
      { etag: "sha256:abc" },
    ),
  );
  const result = await api.createEndpoint({
    name: "relay-a",
    base_url: "https://relay.example.com/v1",
    protocol: "OPENAI_COMPATIBLE",
    api_style: "chat_completions",
    api_key: "sk-secret",
  });
  assert.equal(calls.length, 1);
  const headers = new Headers(calls[0]?.init.headers);
  assert.ok(headers.get("Idempotency-Key"), "mutating 请求必须带 Idempotency-Key");
  assert.equal(headers.get("Content-Type"), "application/json");
  const body = JSON.parse(String(calls[0]?.init.body));
  assert.equal(body.api_key, "sk-secret");
  assert.equal(result.etag, "sha256:abc");
  assert.equal(result.dto.credential, "configured");
});

test("重复提交使用不同幂等 key（每个调用独立）", async () => {
  responses.push(jsonResponse({ id: "ep-1" }, 201), jsonResponse({ id: "ep-2" }, 201));
  await api.createEndpoint({
    name: "a",
    base_url: "https://x.example/v1",
    protocol: "OPENAI_COMPATIBLE",
    api_style: "chat_completions",
  });
  await api.createEndpoint({
    name: "b",
    base_url: "https://x.example/v1",
    protocol: "OPENAI_COMPATIBLE",
    api_style: "chat_completions",
  });
  const keys = calls.map((call) => new Headers(call.init.headers).get("Idempotency-Key"));
  assert.equal(keys[0] !== keys[1], true, "每次 mutating 调用必须使用新 Idempotency-Key");
});

test("updateEndpoint 发送 If-Match（资源版本）", async () => {
  responses.push(jsonResponse({ id: "ep-1", version: "sha256:v2" }, 200));
  await api.updateEndpoint("ep-1", { name: "renamed" }, "sha256:v1");
  const headers = new Headers(calls[0]?.init.headers);
  assert.equal(headers.get("If-Match"), "sha256:v1");
});

test("412 映射为 ApiError（stale version）", async () => {
  responses.push(
    jsonResponse(
      {
        type: "about:blank",
        title: "Precondition Failed",
        status: 412,
        detail: "mismatch",
        instance: "/models/x",
      },
      412,
    ),
  );
  await assert.rejects(
    () => api.updateModel("x", { display_name: "n" }, "sha256:stale"),
    (err: unknown) => {
      assert.ok(err instanceof ApiError);
      assert.equal(err.status, 412);
      assert.equal(err.problem.title, "Precondition Failed");
      return true;
    },
  );
});

test("probe 结果透传 provider_fingerprint_available", async () => {
  responses.push(
    jsonResponse({
      model_id: "m-1",
      ok: true,
      observed_capabilities: ["CHAT"],
      returned_model_name: "model-alpha",
      system_fingerprint: null,
      provider_fingerprint_available: false,
      error_category: null,
      error_message_redacted: null,
      capability_failures: [],
      probed_at: null,
      fingerprint: null,
    }),
  );
  const result = await api.probeModel("m-1");
  assert.equal(result.provider_fingerprint_available, false);
  assert.equal(result.system_fingerprint, null);
});

test("evaluationsTrend 传递 dataset、expected digests 与 limit", async () => {
  responses.push(jsonResponse({ dataset_id: "ds-1", truncated: true }));
  await api.evaluationsTrend("ds-1", ["sha256:a", "sha256:b"], 25);
  const expected =
    "/api/evaluations/trend?dataset_id=ds-1" +
    "&expected_digests=sha256%3Aa&expected_digests=sha256%3Ab&limit=25";
  assert.equal(calls[0]?.url, expected);
});
