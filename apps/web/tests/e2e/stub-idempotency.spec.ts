/**
 * EC-05：替身 harness 必须自己守住 mutating 契约（PLAN-20260915-068）。
 *
 * 用 `page.evaluate(fetch(...))` 发原始请求——`page.request` 不经过 `page.route`，
 * 只有页面内的 fetch 才真的走替身。（客户端漏发 key 的场景就是键在这里被证伪的：
 * 缺头拿到 422，任何"操作成功"的断言都会失败。）
 */

import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

interface ApiResult {
  status: number;
  body: Record<string, unknown>;
}

interface CallOptions {
  method: string;
  path: string;
  body?: unknown;
  key?: string;
}

async function call(page: Page, options: CallOptions): Promise<ApiResult> {
  const { method, path, body, key } = options;
  const payload = body === undefined ? "" : JSON.stringify(body);
  const args: [string, string, string, string] = [method, path, payload, key ?? ""];
  return page.evaluate(
    async ([m, p, rawBody, header]) => {
      const headers: Record<string, string> = { "content-type": "application/json" };
      if (header !== "") {
        headers["Idempotency-Key"] = header;
      }
      const init: RequestInit = { method: m, headers };
      if (rawBody !== "") {
        init.body = rawBody;
      }
      const response = await fetch(p, init);
      const text = await response.text();
      return { status: response.status, body: JSON.parse(text) as Record<string, unknown> };
    },
    args,
  );
}

test.beforeEach(async ({ page }) => {
  await stubApi(page);
  await page.goto("/", { waitUntil: "domcontentloaded" });
});

test("缺 Idempotency-Key 的 mutating 请求被拒（与真中间件同形状）", async ({ page }) => {
  const created = await call(page, { method: "POST", path: "/api/projects", body: { name: "p" } });
  expect(created.status).toBe(422);
  expect(created.body).toEqual({
    type: "about:blank",
    title: "Idempotency-Key Required",
    status: 422,
    detail: "mutating requests require Idempotency-Key",
    instance: "",
  });

  const deleted = await call(page, { method: "DELETE", path: "/api/projects/proj-stub-1" });
  expect(deleted.status).toBe(422);
  expect(deleted.body.title).toBe("Idempotency-Key Required");

  // PATCH 与 DELETE 一样是 mutating（词表由 parity 守卫钉住，这里给一条真实请求作背书）
  const patched = await call(page, {
    method: "PATCH",
    path: "/api/projects/proj-stub-1",
    body: { name: "x" },
  });
  expect(patched.status).toBe(422);
  expect(patched.body.title).toBe("Idempotency-Key Required");
  assertNoUnmatched();
});

test("分析类 POST 免 key（test/validate/probe 等没有业务写入）", async ({ page }) => {
  const probed = await call(page, {
    method: "POST",
    path: "/api/llm-endpoints/endpoint-stub-1/test",
    body: {},
  });
  expect(probed.status).not.toBe(422);
  expect(probed.body.title).not.toBe("Idempotency-Key Required");
  assertNoUnmatched();
});

test("同 key 不同请求体 → 422 Reused", async ({ page }) => {
  const key = "key-reused-in-stub";
  const first = await call(page, {
    method: "POST",
    path: "/api/projects",
    body: { name: "proj-alpha" },
    key,
  });
  expect(first.status).not.toBe(422);

  const second = await call(page, {
    method: "POST",
    path: "/api/projects",
    body: { name: "proj-beta" },
    key,
  });
  expect(second.status).toBe(422);
  expect(second.body.title).toBe("Idempotency-Key Reused");
  assertNoUnmatched();
});

test("同 key 同请求体 → 重放首次响应（不会二次改状态）", async ({ page }) => {
  const key = "key-replay-in-stub";
  const body = { name: "sched_replay_stub", job: "lease_recovery", interval_seconds: 60 };
  const first = await call(page, { method: "POST", path: "/api/ops/schedules", body, key });
  expect(first.status).toBe(201);

  // 若替身没有重放语义，第二次会真的再建一遍 ⇒ 命中重名 409。
  const replay = await call(page, { method: "POST", path: "/api/ops/schedules", body, key });
  expect(replay.status).toBe(201);
  expect(replay.body).toEqual(first.body);
  assertNoUnmatched();
});
