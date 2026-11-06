/**
 * 一条路由的结构签名重录（GOAL-20261107-107 EC-03）。
 *
 * **它存在的理由**：`UPDATE_OUTLINES=1` 会把**所有观测到的**签名写回基线，而
 * `design-outline-guard.spec.ts` 里还有四条**反证臂**（注入改动 → 应当判红）。
 * 整组重录会把注入后的形状写进基线 ⇒ 反证臂永远绿（实测：4 failed / 2 passed，
 * 失败的正是那四条）。
 *
 * **单跑一次、只改一条**：`pnpm --dir apps/web exec playwright test outline-regen.spec.ts`
 * 然后立刻用普通模式跑 `design-outline-guard.spec.ts` 复核 —— 重录本身不是通过。
 */

import { expect, test } from "@playwright/test";

import { stubApi } from "./stub-api";
import { buildOutline, saveOutlineFor } from "./design-outline";

/** 本轮动了 UI 的路由（程序页在 `portfolio-projects` 上）。 */
const ROUTE = "portfolio-projects";
const HASH = "#/portfolio/projects";

test("regenerate the portfolio-projects outline", async ({ page }) => {
  await stubApi(page);
  await page.goto(`/${HASH}`);
  await expect(page.getByTestId("projects-page")).toBeVisible();
  // 页面稳定的定义 = 加载态消失（GOAL-105 `W-5` 的教训：骨架先于数据可见）。
  await expect(page.getByTestId("loading-state")).toHaveCount(0);
  saveOutlineFor(ROUTE, await buildOutline(page));
});
