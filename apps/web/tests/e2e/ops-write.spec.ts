/**
 * Console e2e（PLAN-20260915-059 WP-D）：ops 写面（告警规则 CRUD + 事故处置）。
 *
 * 验证"写了之后读面真的变了"：规则新建/停用/删除会改变 alerts 的静音标记，
 * 候选登记为事故后该 run 从候选列表消失，关闭后行内不再有处置动作。
 */

import { expect, test, type Page } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";
import { resetOpsStub } from "./stub-routes-ops";

test.beforeEach(() => {
  resetOpsStub();
});

test.afterEach(() => {
  assertNoUnmatched();
});

async function openAlerts(page: Page): Promise<void> {
  await stubApi(page);
  await page.goto("/#/ops/alerts");
  await expect(page.getByTestId("alerts-page")).toBeVisible();
  await expect(page.getByTestId("alert-rules-panel")).toBeVisible();
}

async function openIncidents(page: Page): Promise<void> {
  await stubApi(page);
  await page.goto("/#/ops/incidents");
  await expect(page.getByTestId("incidents-page")).toBeVisible();
  await expect(page.getByTestId("incident-board")).toBeVisible();
}

test("规则命中只加静音标记，告警仍在列表里", async ({ page }) => {
  await openAlerts(page);
  await expect(page.getByTestId("alert-muted")).toHaveCount(1);
  // 两条告警都还在（静音不是隐藏）。
  const table = page.getByRole("table", { name: "告警", exact: true });
  await expect(table).toContainText("run-stub-failed");
  await expect(table).toContainText("worker-2");
});

test("新建规则后静音计数变化，停用后恢复", async ({ page }) => {
  await openAlerts(page);
  await page.getByPlaceholder("规则名").fill("mute everything");
  await page.getByRole("button", { name: "新建规则" }).click();
  await expect(page.getByText("mute everything")).toBeVisible();
  await expect(page.getByTestId("alert-muted")).toHaveCount(2);

  const row = page.getByRole("row").filter({ hasText: "mute everything" });
  await row.getByRole("button", { name: "停用" }).click();
  await expect(row.getByRole("button", { name: "启用" })).toBeVisible();
  await expect(page.getByTestId("alert-muted")).toHaveCount(1);
});

test("删除规则后其静音效果消失", async ({ page }) => {
  await openAlerts(page);
  const row = page.getByRole("row").filter({ hasText: "known worker churn" });
  await row.getByRole("button", { name: "删除" }).click();
  await expect(page.getByRole("row").filter({ hasText: "known worker churn" })).toHaveCount(0);
  await expect(page.getByTestId("alert-muted")).toHaveCount(0);
});

test("登记候选为事故后该 run 移出候选列表", async ({ page }) => {
  await openIncidents(page);
  await expect(page.getByText("run-stub-failed")).toBeVisible();
  await page.getByTestId("declare-candidate").click();
  await expect(page.getByTestId("incident-actions")).toBeVisible();
  await expect(page.getByText("无候选")).toBeVisible();
});

test("指派与关闭：关闭后显示结论且不再有处置动作", async ({ page }) => {
  await openIncidents(page);
  await page.getByTestId("declare-candidate").click();
  const actions = page.getByTestId("incident-actions");
  await actions.getByPlaceholder("处理人").fill("ops-1");
  await actions.getByRole("button", { name: "指派" }).click();
  await expect(page.getByRole("row").filter({ hasText: "ops-1" })).toBeVisible();

  const reopened = page.getByTestId("incident-actions");
  await reopened.getByPlaceholder("处理结论").fill("网络分区已恢复");
  await reopened.getByRole("button", { name: "关闭" }).click();
  await expect(page.getByTestId("incident-closed")).toContainText("网络分区已恢复");
  await expect(page.getByTestId("incident-actions")).toHaveCount(0);
});
