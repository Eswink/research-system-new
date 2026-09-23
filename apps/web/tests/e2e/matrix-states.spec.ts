/**
 * EC-04（GOAL-20260923-013）页面判据：`ops/matrix` 是**界面状态说明页（非实时运维状态）**。
 *
 * 这是 (ii) 一等事实的**页面可见面**证据（离线、零出网；stub 替身）：
 * ① `?source=live#/ops/matrix` 渲染说明面，页面上**看得见**该性质的两处文案
 *    （`pageSupport.reason` 横幅 + 页面文案 `matrix.hint`）；
 * ② 默认（`auto`）落在示例面并**标示例身份** —— 证明本页不冒充实时运维状态。
 *
 * 判据性质披露：本判据读的是**静态文案**（产品不消费任何读面），因此它的敏感面是
 * **页面那一段**（改文案 / 改身份渲染即红），**不是**「改数据」——本页没有数据面。
 */

import { expect, test } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

/** 与 `pageSupport.ts` 的 `reason` 逐字一致（改它会同时改设计基线，故这里按契约钉住）。 */
const REASON = "界面状态说明页（非实时运维状态）";

/** 页面文案（zh）：与 `apps/web/src/i18n/zh.ts` 的 `matrix.hint` 逐字一致。 */
const HINT = "本页为界面状态说明：呈现加载/空/错误/权限/未知等组件状态，非实时运维状态。";

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test.afterEach(() => {
  assertNoUnmatched();
});

test("live 来源下 ops/matrix 显示界面状态说明（非实时运维状态）", async ({ page }) => {
  await page.goto("/?source=live#/ops/matrix");
  const page_ = page.getByTestId("gap-page-ops-matrix");
  await expect(page_).toBeVisible();
  await expect(page.getByTestId("data-source-badge")).toHaveAttribute("data-source", "live");
  // 两处可见文案：reason 横幅 + 详情栏的页面文案。
  await expect(page_.getByText(REASON, { exact: true })).toBeVisible();
  await expect(page_.getByText(HINT, { exact: true })).toBeVisible();
});

test("默认来源下 ops/matrix 落在示例面并标示例身份（不冒充实时运维状态）", async ({ page }) => {
  await page.goto("/#/ops/matrix");
  await expect(page.getByTestId("example-page-ops-matrix")).toBeVisible();
  await expect(page.getByTestId("data-source-badge")).toHaveAttribute("data-source", "example");
  // 反证方向：默认面**不**渲染说明面（说明面只在显式 live 下出现）。
  await expect(page.getByTestId("gap-page-ops-matrix")).toHaveCount(0);
});
