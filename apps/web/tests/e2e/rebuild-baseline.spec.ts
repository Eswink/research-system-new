/**
 * e2e 失败基线（PLAN-20260908-034 T03/T10）。
 *
 * 期望行为：严格 API 替身下，未注册的 /api 请求必须使页面请求失败
 * （测试可观测），而不是静默返回空数组兜底。
 * 基线（重建前）：当前 stub-api.ts 对未匹配请求统一 fulfillJson([]) → 本用例失败。
 * T10 重建严格替身后：本用例通过。
 */

import { expect, test } from "@playwright/test";

import { stubApi } from "./stub-api";

test("baseline: unmatched API request must not silently succeed (T10)", async ({ page }) => {
  await stubApi(page);
  await page.goto("/");
  const response = await page.evaluate(async () => {
    const res = await fetch("/api/definitely-not-a-real-endpoint");
    return { status: res.status, body: await res.text() };
  });
  // 严格替身：未匹配请求应返回 500/404 标记（非 200 空数组）
  expect(response.status).toBeGreaterThanOrEqual(400);
});
