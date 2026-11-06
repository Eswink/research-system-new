/**
 * 改稿并排差异（GOAL-20261107-107 EC-01）。
 *
 * **它封住的失败形态**：改稿链的两份正文此前各渲染成一个 `<pre>`、上下堆叠 —— 看得见
 * 两份，但「改了哪几行」要人眼逐字比。后端 `GET /artifacts/{left}/diff/{right}` 与
 * `ArtifactDiffPanel` 的行渲染**早已存在**（`workspace-diff.spec.ts` 就在用），缺的只是
 * 把 `supersedes` 当左 id 接上去。
 *
 * **判据口径**（两向）：① 含 v1+v2 的 run ⇒ `revision-diff` 在场，且「新增行」与
 * 「删除行」**分别**以不同的样式类渲染（按 class 核对，因为行文本本身不带 `ADDED` 前缀
 * —— 那正是 `DiffLineRow` 的既有形态）；② 只有 v1 的 run ⇒ `revision-diff` **不渲染**
 * （不伪造一个空的并排面板）。
 */

import { expect, test } from "@playwright/test";

import { stubApi } from "./stub-api";

/** 与 `DiffLineRow` 的三个 class 对应（CSS Modules 会加哈希前缀 ⇒ 用子串属性选择器）。 */
const ADDED = 'span[class*="diffAdded"]';
const REMOVED = 'span[class*="diffRemoved"]';

test("改稿链把 v1 → v2 的增删行分别渲染出来", async ({ page }) => {
  await stubApi(page);
  await page.goto("/#/insights/reports?run=manuscript-run");

  const diff = page.getByTestId("revision-diff");
  await expect(diff).toHaveCount(1, { timeout: 8_000 });
  // 增与删**分别**有行：夹具的 v2 与 v1 有差异，逐行集合差会产生这两类。
  await expect(diff.locator(ADDED)).not.toHaveCount(0);
  await expect(diff.locator(REMOVED)).not.toHaveCount(0);
  // 统计芯片也在：增删条数不是靠人眼数。
  await expect(diff).toContainText("context");
});

test("只有 v1 的 run 不渲染并排面板", async ({ page }) => {
  await stubApi(page);
  // 该 run 的制品列表只有一份 `manuscript.md`（没有 `manuscript_v2.md`）⇒ 改稿面板缺席。
  await page.goto("/#/insights/reports?run=single-manuscript-run");
  await expect(page.getByTestId("manuscript-body")).toHaveCount(1, { timeout: 8_000 });
  await expect(page.getByTestId("revision-diff")).toHaveCount(0);
});
