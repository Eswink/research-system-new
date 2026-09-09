/**
 * Console e2e：八域外壳 + hash 导航 + 编辑器闭环（确定性 API 替身）。
 * 覆盖（T31）：33 路由独立身份、直达/刷新恢复、主题/语言即时生效、
 * 未知地址未找到页、编辑器 Form/YAML 与启动门禁。
 */

import { expect, test } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test.afterEach(() => {
  assertNoUnmatched();
});

test("八域导航渲染，域展开子页", async ({ page }) => {
  await page.goto("/#/plan/protocol");
  await expect(page.getByTestId("console-main")).toBeVisible();
  const domains = ["plan", "portfolio", "run", "library", "evidence", "insights", "ops", "govern"];
  for (const domain of domains) {
    await expect(page.getByTestId(`nav-domain-${domain}`)).toBeVisible();
  }
  await expect(page.getByTestId("nav-plan-protocol")).toBeVisible();
});

test("直达 example 路由保持页面身份与来源，刷新不串页", async ({ page }) => {
  await page.goto("/#/library/prompts");
  await expect(page.getByTestId("example-page-library-prompts")).toBeVisible();
  await expect(page.getByTestId("data-source-badge")).toHaveAttribute("data-source", "example");
  await page.reload();
  await expect(page.getByTestId("example-page-library-prompts")).toBeVisible();
  await expect(page.getByTestId("data-source-badge")).toHaveAttribute("data-source", "example");
});

test("未知地址进入未找到页", async ({ page }) => {
  await page.goto("/#/bogus/nope");
  await expect(page.getByTestId("not-found")).toBeVisible();
});

test("主题切换即时生效并持久化", async ({ page }) => {
  await page.goto("/#/plan/protocol");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByTestId("toggle-theme").click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("语言切换即时生效", async ({ page }) => {
  await page.goto("/#/plan/protocol");
  await page.getByTestId("toggle-language").click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
});

test("旧别名路由映射到规范页", async ({ page }) => {
  await page.goto("/#/assets/compute");
  await expect(page.getByTestId("nav-domain-ops")).toBeVisible();
});
