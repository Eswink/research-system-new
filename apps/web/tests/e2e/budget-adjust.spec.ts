/**
 * Console e2e（PLAN-20260914-046 WP-C）：预算页预测渲染 + 调整真实生效。
 *
 * 确定性 API 替身：验证预算调整走 BudgetLedger 后，预留-消耗预测跟随更新，
 * 且不可计量（UNKNOWN）条目不被渲染成 0。
 */

import { expect, test } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

const RUN_ID = "run-stub-1";

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test.afterEach(() => {
  assertNoUnmatched();
});

async function openBudget(page: Parameters<typeof stubApi>[0]): Promise<void> {
  await page.goto(`/#/govern/budget?run=${RUN_ID}`);
  await expect(page.getByTestId("budget-page")).toBeVisible();
}

test("预算页渲染预留-消耗预测，UNKNOWN 不显示为 0", async ({ page }) => {
  await openBudget(page);
  const forecast = page.getByRole("table", { name: "预留-消耗预测" });
  await expect(forecast).toBeVisible();
  // 已预留/已消耗/剩余：MODEL_TOKENS 1000 − 400 = 600
  const tokens = forecast.getByRole("row", { name: /MODEL_TOKENS/ });
  await expect(tokens).toContainText("1000");
  await expect(tokens).toContainText("400");
  await expect(tokens).toContainText("600");
  // GPU_TIME 计量不可用：剩余不是 0，而是显式不可计量
  const gpu = forecast.getByRole("row", { name: /GPU_TIME/ });
  await expect(gpu).toContainText("UNKNOWN");
  await expect(gpu).not.toContainText("60 seconds");
  await expect(page.getByText("RESERVED_ONLY")).toBeVisible();
});

test("预算调整写入账本后预测跟随更新", async ({ page }) => {
  await openBudget(page);
  await page.getByRole("button", { name: "调整预算" }).click();
  const quota = page.getByLabel("新额度");
  await quota.fill("2500");
  await page.getByRole("button", { name: "提交调整" }).click();
  const tokens = page.getByRole("table", { name: "预留-消耗预测" }).getByRole("row", {
    name: /MODEL_TOKENS/,
  });
  await expect(tokens).toContainText("2500");
  await expect(tokens).toContainText("2100");
});
