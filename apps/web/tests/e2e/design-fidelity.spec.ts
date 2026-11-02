/**
 * 视觉对照截图门禁（PLAN-20260908-034 T31；四组合于 GOAL-20261103-104 EC-02 落地）。
 *
 * 35 条基线条目（33 条规范路由 + 2 条携带选中 run 的时间线变体）× **四组合**
 * （dark/normal/zh、dark/compact/en、light/normal/en、light/compact/zh）。
 *
 * 文件头此前声称「双主题×双密度×中英文」，而实现只跑 `dark/normal/zh` —— 三轴里两轴
 * 从未被像素门覆盖（GOAL-20261103-104 EC-02 实测并补齐）。四组合取**对角**而非全笛卡尔积
 * （2×2×2 = 8）：每个主题、每种密度、每种语言各出现两次，任一条轴漂移都会撞上至少一条基线；
 * 8 组合的收益只是多一倍维护面，不是多一倍覆盖。
 *
 * 截图前断言页面身份（testid）与关键控件存在，避免把缺页/错误态录为正常基准。
 * 首跑 `pnpm exec playwright test design-fidelity --update-snapshots` 生成回归基线
 * （基线须在设计对照通过后批准）。**平台后缀由 Playwright 自动加**：`-win32.png` /
 * `-linux.png` 两份都要有 —— CI 只跑 ubuntu，只产 win32 会让整条门禁在 CI 上恒红
 * （`W-7` 刚证明过「CI 上跑不起来」的形态）。
 */

import { expect, test, type Page } from "@playwright/test";

import { assertOutlines, buildOutline } from "./design-outline";
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
  // GOAL-007 cycle 4 = EC-04：**选中 run** 的运行页。既有 `run-timeline` 基线不选 run
  // （`runs-empty`），而执行体披露行只在选中 run 时渲染 ⇒ 只留那一条基线的话，新分支在
  // 像素/结构门上是**不可见**的（本轮实测：加行后结构签名不变）。这条基线让披露行真的被门覆盖。
  {
    name: "run-timeline-substrate",
    hash: "#/run/timeline?run=substrate-openhands",
    testid: "run-panel",
  },
  // GOAL-20261103-104 EC-02：**十一相进度条**的填充态。
  // `run-timeline` 不选 run、`run-timeline-substrate` 的 run 没有冻结协议正文 ⇒ 两条都只
  // 渲染 `phase-progress-unavailable` 空态。此前 `design-outlines.json` 里 `phase-node`
  // **零命中**：十一相的着色 / 换行 / 展开在像素门与结构门上都从未被覆盖。
  // `eleven-phases` fixture 的 11 个 id 与 `direction_to_manuscript_v1.yaml` 逐字一致，
  // 四种状态各至少出现一次。
  {
    name: "run-timeline-phases",
    hash: "#/run/timeline?run=eleven-phases",
    testid: "run-panel",
  },
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
  { name: "ops-alerts", hash: "#/ops/alerts", testid: "alerts-page" },
  { name: "ops-incidents", hash: "#/ops/incidents", testid: "incidents-page" },
  { name: "ops-schedules", hash: "#/ops/schedules", testid: "schedules-page" },
  { name: "ops-integrations", hash: "#/ops/integrations", testid: "integrations-page" },
  { name: "ops-data-health", hash: "#/ops/data-health", testid: "data-health-page" },
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

/**
 * 四组合（GOAL-20261103-104 EC-02）：2 主题 × 2 密度 × 2 语言取**对角**。
 * 每轴各出现两次；任一轴漂移必然撞上至少一条基线。
 */
const COMBINATIONS: readonly Prefs[] = [
  { theme: "dark", density: "normal", lang: "zh" },
  { theme: "dark", density: "compact", lang: "en" },
  { theme: "light", density: "normal", lang: "en" },
  { theme: "light", density: "compact", lang: "zh" },
];

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

test("35 路由主截图（四组合：双主题 × 双密度 × 中英文）", async ({ page }) => {
  test.setTimeout(600_000);
  await stubApi(page);
  // 四组合取对角：每个主题 / 密度 / 语言各出现两次（见文件头）。
  for (const prefs of COMBINATIONS) {
    const suffix = `${prefs.theme}-${prefs.density}-${prefs.lang}`;
    for (const route of ALL_ROUTES) {
      await seedPrefs(page, prefs);
      await page.goto(`/${route.hash}`);
      await expect(page.getByTestId(route.testid).first()).toBeVisible({ timeout: 8_000 });
      await page.waitForTimeout(120);
      await expect(page).toHaveScreenshot(`${route.name}-${suffix}.png`, {
        maxDiffPixelRatio: 0.02,
      });
    }
  }
});

/**
 * 结构签名门禁（GOAL-20260915-003 EC-01）：像素比率对"整块新增"不敏感
 * （实测 0.48%~1.73% < 2%），结构签名必须对节点增删敏感——多一行、多一个面板
 * 都会变更签名，从而强制"重生成基线 + 目检"这一步真的发生。
 */
test("35 路由结构签名（DOM outline，整块新增必红）", async ({ page }) => {
  test.setTimeout(180_000);
  await stubApi(page);
  const observed: Record<string, string> = {};
  for (const route of ALL_ROUTES) {
    await seedPrefs(page, { theme: "dark", density: "normal", lang: "zh" });
    await page.goto(`/${route.hash}`);
    await expect(page.getByTestId(route.testid).first()).toBeVisible({ timeout: 8_000 });
    await page.waitForTimeout(120);
    observed[route.name] = await buildOutline(page);
  }
  assertOutlines(observed);
});

/**
 * **十一相进度条的元素级像素门禁**（GOAL-20261103-104 EC-02 的判据 (iii)）。
 *
 * 为什么整页截图不够：`run-timeline-phases` 的 1280×720 视口里，相进度条在**折叠线以下**
 * ——整页基线把它录进了文件，却把它**录在不可见的区域**。实测反证：把 `.succeeded` 的
 * 左边框从 `--success` 改成 `--danger`（DOM 一字未动），整页像素判据与结构签名判据
 * **都仍然绿**。那意味着「十一相着色」此前在两道门上都只是**名义覆盖**。
 *
 * 元素级截图把判据钉在**进度条自己**身上 ⇒ 任何一个相节点的颜色变化都必然落到像素上。
 * 同时它仍是四组合（与主截图同轴），不是只测一种主题。
 */
const PHASE_ROUTE = { name: "run-timeline-phases", hash: "#/run/timeline?run=eleven-phases" };

test("十一相进度条元素级像素（四组合，颜色变化必红）", async ({ page }) => {
  test.setTimeout(180_000);
  await stubApi(page);
  for (const prefs of COMBINATIONS) {
    const suffix = `${prefs.theme}-${prefs.density}-${prefs.lang}`;
    await seedPrefs(page, prefs);
    await page.goto(`/${PHASE_ROUTE.hash}`);
    const track = page.getByTestId("phase-track");
    await expect(track).toBeVisible({ timeout: 8_000 });
    await expect(page.getByTestId("phase-node-report")).toBeVisible({ timeout: 8_000 });
    await page.waitForTimeout(120);
    await expect(track).toHaveScreenshot(`phase-track-${suffix}.png`, {
      maxDiffPixels: 0,
      animations: "disabled",
      scale: "css",
    });
  }
});
