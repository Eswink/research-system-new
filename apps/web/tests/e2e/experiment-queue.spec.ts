/**
 * Console e2e（PLAN-20260915-052 WP-D / G14）：实验队列与调度。
 *
 * 验证 experiments 页队列面板渲染控制面队列视图（含已派发条目的 run 链接、
 * 排队条目的排期与草稿来源），以及取消动作真的发往 DELETE 端点并刷新视图
 * （用受控覆盖观察状态变化，不依赖替身默认值）。
 */

import { expect, test } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

const QUEUED = {
  id: "queue-entry-2",
  project_id: "example-project",
  plan_id: "plan-stub-1",
  plan_name: "sort-benchmark",
  protocol_path: null,
  draft_id: "draft-7",
  draft_revision: 3,
  state: "QUEUED",
  not_before: "2026-09-16T09:00:00+00:00",
  claimed_at: null,
  run_id: null,
  failure_reason: null,
  created_at: "2026-09-15T10:03:00+00:00",
  updated_at: "2026-09-15T10:03:00+00:00",
};

const CANCELLED = { ...QUEUED, state: "CANCELLED", updated_at: "2026-09-15T10:04:00+00:00" };

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test.afterEach(() => {
  assertNoUnmatched();
});

test("队列面板呈现派发结果与排期条目", async ({ page }) => {
  await page.goto("/#/portfolio/experiments");
  const panel = page.getByTestId("experiment-queue-panel");
  await expect(panel).toBeVisible();
  const dispatched = panel.getByTestId("queue-row-queue-entry-1");
  await expect(dispatched).toContainText("DISPATCHED");
  await expect(dispatched).toContainText("m12_reference_research_v1.yaml");
  await expect(dispatched.getByRole("link", { name: "run-stub-1" })).toBeVisible();
  const queued = panel.getByTestId("queue-row-queue-entry-2");
  await expect(queued).toContainText("QUEUED");
  await expect(queued).toContainText("draft-7@r3");
  await expect(queued).toContainText("2026-09-16T09:00:00+00:00");
  await expect(panel).toContainText("at-least-once");
});

test("取消排队条目（DELETE 端点返回 CANCELLED）", async ({ page }) => {
  let cancelled = false;
  await page.route("**/api/experiment-queue/queue-entry-2", (route) => {
    if (route.request().method() === "DELETE") cancelled = true;
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(CANCELLED),
    });
  });
  await page.route("**/api/projects/example-project/experiment-queue", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        entries: [cancelled ? CANCELLED : QUEUED],
        dispatch_note: "stub",
      }),
    }),
  );
  await page.goto("/#/portfolio/experiments");
  const row = page.getByTestId("queue-row-queue-entry-2");
  await expect(row).toContainText("QUEUED");
  await row.getByRole("button", { name: "取消" }).click();
  await expect(page.getByTestId("queue-row-queue-entry-2")).toContainText("CANCELLED");
  expect(cancelled).toBe(true);
});

test("入队表单提交协议路径到 queue 端点", async ({ page }) => {
  let body: unknown = null;
  await page.route("**/api/projects/example-project/experiments/plan-stub-1/queue", (route) => {
    body = route.request().postDataJSON();
    return route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify(CANCELLED),
    });
  });
  await page.goto("/#/portfolio/experiments");
  const form = page.getByTestId("enqueue-form");
  await form.getByLabel("计划").selectOption("plan-stub-1");
  await form.getByLabel("协议路径").fill("m12_reference_research_v1.yaml");
  await form.getByRole("button", { name: "入队" }).click();
  await expect.poll(() => body).not.toBeNull();
  expect(body).toEqual({ protocol_path: "m12_reference_research_v1.yaml", not_before: null });
});
