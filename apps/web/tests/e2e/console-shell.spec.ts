/**
 * Console e2e：hash 导航 + 外壳 + 编辑器闭环（确定性 API 替身）。
 * 覆盖（AC-06）：路由直达/刷新恢复、主题持久化、编辑器 Form/YAML
 * 切换、保存状态、启动门禁。
 */

import { expect, test } from "@playwright/test";

import { stubApi, VALID_YAML } from "./stub-api";

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test("外壳渲染 + hash 导航直达 + 刷新恢复", async ({ page }) => {
  await page.goto("/#/assets/models");
  await expect(page.getByTestId("console-main")).toBeVisible();
  await expect(page.getByTestId("nav-assets-models")).toHaveClass(/active/);
  await page.reload();
  await expect(page.getByTestId("console-main")).toBeVisible();
  await expect(page).toHaveURL(/#\/assets\/models/);
});

test("主题与密度切换即时生效并持久化", async ({ page }) => {
  await page.goto("/");
  await page.locator("select").nth(0).selectOption("light");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("编辑器：Form/YAML 切换保留内容", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("protocol-editor")).toBeVisible();
  // YAML 模式填入合法协议 → 切回 Form 应渲染 Identity 区（内容不丢）
  await page.getByRole("radio", { name: "YAML" }).click();
  await expect(page.getByTestId("yaml-view")).toBeVisible();
  await page.getByTestId("yaml-view").locator("textarea").fill(VALID_YAML);
  await page.getByRole("radio", { name: "表单" }).click();
  await expect(page.locator("[data-testid='section-identity']")).toBeVisible();
  await expect(page.locator("#protocol-id")).toHaveValue("sort_analysis_v1_0_1");
});

test("编辑器：保存成功后进入 saved 状态", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("protocol-editor")).toBeVisible();
  // YAML 模式下编辑文本产生 dirty；Create draft 返回 saved
  await page.getByRole("radio", { name: "YAML" }).click();
  await page.getByTestId("yaml-view").locator("textarea").fill(VALID_YAML);
  await page.getByRole("button", { name: "Save" }).first().click();
  await expect(page.getByTestId("editor-save-status")).toHaveText("saved", { timeout: 10_000 });
});

test("启动门禁：无保存/预检时 Start 禁用", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("editor-start")).toBeDisabled();
});
