/**
 * 重建就绪读面（`RunDetailDto.rebuild`）在运行页的接线
 * （GOAL-20260918-006 cycle 3 = EC-03）。
 *
 * 读面只回答"记录够不够重建"，不预告重建结果。三条受控 fixture 正好是分类器的
 * 三态（`packages/application/run_orchestration/rebuild_readiness.py`）：本 spec 断言
 * 三态在页面上可区分、`missing` 按**行字段名**点名、结论文案不越界
 * （REFUSED 不写成「不可回填」的判定、SELF_CONTAINED 不写成「重建必过」）。
 */

import { expect, test } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

const CASES = [
  { id: "rebuild-self-contained", status: "SELF_CONTAINED", missing: [] },
  { id: "rebuild-source-dependent", status: "SOURCE_DEPENDENT", missing: [] },
  {
    id: "rebuild-refused",
    status: "REFUSED",
    missing: ["manifest_digest", "manifest_semantic_digest", "protocol_body", "protocol_source"],
  },
] as const;

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test.afterEach(() => {
  assertNoUnmatched();
});

test("读面三态在页面上可区分，missing 按行字段名点名", async ({ page }) => {
  const seen: string[] = [];
  for (const item of CASES) {
    await page.goto(`/#/run/timeline?run=${item.id}`);
    await expect(page.getByText("重建就绪（读面）")).toBeVisible();
    const status = page.getByTestId("run-rebuild-status");
    await expect(status).toHaveText(item.status);
    seen.push((await status.textContent()) ?? "");
    const missing = page.getByTestId("run-rebuild-missing");
    if (item.missing.length === 0) {
      // 分类器不变量：missing 非空 ⇔ REFUSED；其余两态不列缺失事实。
      await expect(missing).toHaveCount(0);
      continue;
    }
    await expect(missing).toBeVisible();
    for (const name of item.missing) {
      await expect(missing).toContainText(name);
    }
  }
  // 三态互不相同（页面不是把同一个值渲染三遍）。
  expect(new Set(seen).size).toBe(CASES.length);
});

test("结论文案不越界：不预告重建结果", async ({ page }) => {
  await page.goto("/#/run/timeline?run=rebuild-self-contained");
  const selfContained = page.getByTestId("run-rebuild");
  await expect(selfContained).toContainText("记录自足：重建所需输入都在库内");
  await expect(selfContained).not.toContainText("必过");
  await expect(page.getByTestId("run-rebuild-note")).toContainText("不预告重建结果");

  await page.goto("/#/run/timeline?run=rebuild-refused");
  const refused = page.getByTestId("run-rebuild");
  // 拒绝的是"这个读面给不了结论"，不是"回填不可能"。
  await expect(refused).toContainText("读面拒绝给出结论");
  await expect(refused).toContainText("这不是「不可回填」的判定");

  await page.goto("/#/run/timeline?run=rebuild-source-dependent");
  await expect(page.getByTestId("run-rebuild")).toContainText("依赖来源");
});
