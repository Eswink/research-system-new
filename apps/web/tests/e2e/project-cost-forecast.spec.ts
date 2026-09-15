/**
 * Console e2e（PLAN-20260915-057 WP-B / G12）：项目级成本预测面板。
 *
 * 断言页面把后端口径原样呈现：方法是 `MEAN_OF_VALUED_DAYS`、样本/排除计数来自响应、
 * 已计价日均 × 视野 = 外推额；被排除的那天显示**原因**（USAGE_UNKNOWN），
 * 而不是把它当成 0 画进曲线。
 */

import { expect, test } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test.afterEach(() => {
  assertNoUnmatched();
});

test("项目级成本预测呈现外推口径与排除原因", async ({ page }) => {
  await page.goto("/#/insights/cost-analytics");
  const panel = page.getByTestId("project-cost-forecast");
  await expect(panel).toBeVisible();

  // 口径行：方法 + 视野 + 样本天数 + 排除天数（全部来自响应）。
  await expect(panel).toContainText("MEAN_OF_VALUED_DAYS");
  await expect(panel).toContainText("视野 7 天");
  await expect(panel).toContainText("样本天数 1");
  await expect(panel).toContainText("排除 1");

  // 金额行：已计价合计（ACTUAL）→ 外推（1200 × 7 = 8400）。
  await expect(page.getByTestId("project-cost-forecast-amount")).toContainText("1200");
  await expect(page.getByTestId("project-cost-forecast-amount")).toContainText("8400");

  // 日表：进样本的一天与"被排除 + 原因"的一天都在场。
  const days = panel.getByRole("table", { name: "项目成本日序列" });
  await expect(days.getByRole("row").filter({ hasText: "2026-09-13" })).toContainText("1200");
  const excluded = days.getByRole("row").filter({ hasText: "2026-09-14" });
  await expect(excluded).toContainText("USAGE_UNKNOWN");
  await expect(excluded).toContainText("—");
});
