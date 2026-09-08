/**
 * 截图基准（PLAN-20260908-033 AC-06 / CONSOLE_REBUILD §6.6）。
 *
 * 11 条路由 × 4 组合（dark/light × normal/compact × zh/en）= 44 张基准。
 * 全部基于确定性 API 替身（stubApi），页面数据固定，无时间戳/随机内容；
 * 首跑用 `pnpm exec playwright test screenshots --update-snapshots` 生成基准。
 */

import { expect, test, type Page } from "@playwright/test";

import { stubApi } from "./stub-api";

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

const ROUTES: readonly { name: string; hash: string; ready: string }[] = [
  { name: "plan-protocol", hash: "#/plan/protocol", ready: "protocol-editor" },
  { name: "plan-team", hash: "#/plan/team", ready: "team-page" },
  { name: "run-runs", hash: "#/run/runs", ready: "run-panel" },
  { name: "run-workspace", hash: "#/run/workspace", ready: "console-main" },
  { name: "evidence-inspection", hash: "#/evidence/inspection", ready: "inspection-panel" },
  { name: "assets-endpoints", hash: "#/assets/endpoints", ready: "endpoints-home" },
  { name: "assets-models", hash: "#/assets/models", ready: "console-main" },
  { name: "assets-compute", hash: "#/assets/compute", ready: "console-main" },
  { name: "govern-approvals", hash: "#/govern/approvals", ready: "console-main" },
  { name: "govern-operations", hash: "#/govern/operations", ready: "operations-panel" },
  { name: "setup-wizard", hash: "#/setup", ready: "" },
];

const COMBOS: readonly {
  tag: string;
  theme: string;
  density: string;
  lang: string;
}[] = [
  { tag: "dark-normal-zh", theme: "dark", density: "normal", lang: "zh" },
  { tag: "light-normal-zh", theme: "light", density: "normal", lang: "zh" },
  { tag: "dark-compact-zh", theme: "dark", density: "compact", lang: "zh" },
  { tag: "dark-normal-en", theme: "dark", density: "normal", lang: "en" },
];

async function waitReady(page: Page, route: { name: string; ready: string }): Promise<void> {
  if (route.name === "setup-wizard") {
    // setup 向导为全屏接管，无外壳
    await page.getByText("API Key").waitFor({ state: "visible" });
    return;
  }
  if (route.ready === "console-main") {
    await page.getByTestId("console-main").waitFor({ state: "visible" });
    return;
  }
  await page.getByTestId(route.ready).waitFor({ state: "visible" });
}

async function openWithPreferences(
  page: Page,
  combo: { theme: string; density: string; lang: string },
  hash: string,
): Promise<void> {
  await page.goto("/");
  const selects = page.locator("select");
  await selects.nth(0).waitFor({ state: "visible" });
  await selects.nth(0).selectOption(combo.theme);
  await selects.nth(1).selectOption(combo.density);
  await selects.nth(2).selectOption(combo.lang);
  await expect(page.locator("html")).toHaveAttribute("data-theme", combo.theme);
  await page.goto(`/${hash}`);
}

for (const combo of COMBOS) {
  for (const route of ROUTES) {
    test(`截图基准 ${route.name} × ${combo.tag}`, async ({ page }) => {
      await openWithPreferences(page, combo, route.hash);
      await waitReady(page, route);
      await page.waitForTimeout(150);
      await expect(page).toHaveScreenshot(`${route.name}-${combo.tag}.png`, {
        maxDiffPixelRatio: 0.02,
      });
    });
  }
}
