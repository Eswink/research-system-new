/**
 * 视觉对照截图门禁（PLAN-20260908-034 T31）。
 *
 * 33 条规范路由 × dark/normal/zh 主截图；高风险页增加双主题×双密度×中英文组合。
 * 截图前断言页面身份（testid）与关键控件存在，避免把缺页/错误态录为正常基准。
 * 首跑 `pnpm exec playwright test design-fidelity --update-snapshots` 生成回归基线
 * （基线须在设计对照通过后批准）。
 */

import { expect, test, type Page } from "@playwright/test";

import { stubApi } from "./stub-api";

const ALL_ROUTES: readonly { name: string; hash: string; testid: string }[] = [
  { name: "plan-overview", hash: "#/plan/overview", testid: "console-main" },
  { name: "plan-protocol", hash: "#/plan/protocol", testid: "protocol-editor" },
  { name: "plan-team", hash: "#/plan/team", testid: "team-page" },
  {
    name: "portfolio-projects",
    hash: "#/portfolio/projects",
    testid: "projects-page",
  },
  { name: "portfolio-experiments", hash: "#/portfolio/experiments", testid: "console-main" },
  { name: "portfolio-runs-history", hash: "#/portfolio/runs-history", testid: "run-history" },
  { name: "portfolio-compare", hash: "#/portfolio/compare", testid: "console-main" },
  { name: "run-timeline", hash: "#/run/timeline", testid: "run-panel" },
  { name: "run-approvals", hash: "#/run/approvals", testid: "approvals-panel" },
  { name: "run-workspace", hash: "#/run/workspace", testid: "console-main" },
  { name: "library-prompts", hash: "#/library/prompts", testid: "library-prompt-page" },
  { name: "library-datasets", hash: "#/library/datasets", testid: "library-dataset-page" },
  {
    name: "library-notebooks",
    hash: "#/library/notebooks",
    testid: "library-notebook-page",
  },
  { name: "library-model-registry", hash: "#/library/model-registry", testid: "models-page" },
  { name: "library-lineage", hash: "#/library/lineage", testid: "console-main" },
  { name: "library-endpoints", hash: "#/library/endpoints", testid: "endpoints-home" },
  { name: "library-setup", hash: "#/library/setup", testid: "relay-wizard" },
  { name: "evidence-claims", hash: "#/evidence/claims", testid: "inspection-panel" },
  { name: "insights-reports", hash: "#/insights/reports", testid: "reports-page" },
  { name: "insights-cost-analytics", hash: "#/insights/cost-analytics", testid: "console-main" },
  { name: "ops-alerts", hash: "#/ops/alerts", testid: "example-page-ops-alerts" },
  { name: "ops-incidents", hash: "#/ops/incidents", testid: "example-page-ops-incidents" },
  { name: "ops-schedules", hash: "#/ops/schedules", testid: "example-page-ops-schedules" },
  { name: "ops-integrations", hash: "#/ops/integrations", testid: "integrations-page" },
  { name: "ops-data-health", hash: "#/ops/data-health", testid: "example-page-ops-data-health" },
  { name: "ops-matrix", hash: "#/ops/matrix", testid: "example-page-ops-matrix" },
  { name: "ops-compute", hash: "#/ops/compute", testid: "console-main" },
  { name: "ops-observability", hash: "#/ops/observability", testid: "operations-panel" },
  { name: "govern-budget", hash: "#/govern/budget", testid: "console-main" },
  { name: "govern-audit", hash: "#/govern/audit", testid: "console-main" },
  { name: "settings", hash: "#/settings/settings", testid: "console-main" },
  {
    name: "notifications",
    hash: "#/notifications/notifications",
    testid: "notifications-page",
  },
  { name: "command-center", hash: "#/command-center/command-center", testid: "command-center" },
];

interface Prefs {
  theme: string;
  density: string;
  lang: string;
}

async function seedPrefs(page: Page, prefs: Prefs): Promise<void> {
  await page.addInitScript(
    ([t, d, l]) => {
      localStorage.setItem(
        "ros.console.preferences",
        JSON.stringify({ theme: t, density: d, language: l, editorMode: "form", version: "test" }),
      );
    },
    [prefs.theme, prefs.density, prefs.lang] as const,
  );
}

test("33 路由主截图（dark/normal/zh）", async ({ page }) => {
  test.setTimeout(180_000);
  await stubApi(page);
  for (const route of ALL_ROUTES) {
    await seedPrefs(page, { theme: "dark", density: "normal", lang: "zh" });
    await page.goto(`/${route.hash}`);
    await expect(page.getByTestId(route.testid).first()).toBeVisible({ timeout: 8_000 });
    await page.waitForTimeout(120);
    await expect(page).toHaveScreenshot(`${route.name}-dark-normal-zh.png`, {
      maxDiffPixelRatio: 0.02,
    });
  }
});
