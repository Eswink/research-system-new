/**
 * 链上制品标签 + 手稿视图（GOAL-20261101-103 EC-04）。
 *
 * **它封住的失败形态**（同一个病，两个面）：GOAL-099/100/102 做出来的手稿 / 编辑决定 /
 * 投稿包在 UI 上**与一条 `tool-result:...` 没有区别** —— 制品浏览器只显示裸 id，报告页
 * 只渲染 M12 的 `deliverable.json`。
 *
 * 四条判据（每条都可证伪）：
 * ① `manuscript.md` 显示为「手稿」，且**不再只是一串裸 id**；
 * ② **未命中闭集**的制品（`tool-result:xyz`）**没有**标签 —— 未命中不伪造；
 * ③ 报告页渲染手稿的 **Markdown 正文**（按内容核对，不是"有个面板"）；
 * ④ 编辑决定按四值闭集解析出来，且投稿包五件各有下载链接。
 */

import { expect, test } from "@playwright/test";

import { stubApi } from "./stub-api";

test("制品浏览器把 manuscript.md 显示为「手稿」，未命中者不伪造标签", async ({ page }) => {
  await stubApi(page);
  await page.goto("/#/run/workspace?run=manuscript-run");
  await expect(page.getByTestId("artifact-rows")).toBeVisible({ timeout: 8_000 });

  // ① 命中闭集的制品有标签（中文界面）。
  await expect(page.getByTestId("artifact-label-manuscript.md")).toHaveText("手稿");
  await expect(page.getByTestId("artifact-label-manuscript_v2.md")).toHaveText("修改稿");
  await expect(page.getByTestId("artifact-label-editorial_decision")).toHaveText("编辑决定");
  await expect(page.getByTestId("artifact-label-cover_letter.md")).toHaveText("Cover Letter");

  // ② 未命中闭集的制品**没有**标签（`tool-result:xyz`）。
  await expect(page.locator('[data-testid^="artifact-label-tool-result"]')).toHaveCount(0);
  // 而它仍然在列表里（标签缺席 ≠ 制品缺席）。
  await expect(page.getByTestId("artifact-rows")).toContainText("tool-result:xyz");
});

test("报告页渲染手稿的 Markdown 正文与编辑决定与投稿包链接", async ({ page }) => {
  await stubApi(page);
  await page.goto("/#/insights/reports?run=manuscript-run");
  // 改稿链 ⇒ **两段**正文（手稿 + 修改稿）。两份都在场正是"能对照"这条结构事实。
  const bodies = page.getByTestId("manuscript-body");
  await expect(bodies).toHaveCount(2, { timeout: 8_000 });

  // ③ 正文是**内容**，不是 id：按 Markdown 里真实存在的句子核对。
  await expect(bodies.first()).toContainText("A study of sorting");
  await expect(bodies.first()).toContainText("## Abstract");
  await expect(bodies.first()).not.toContainText("## Limitations");

  // 改稿链：修改稿替代手稿这件事在页面上读得到（第二段是 v2 的正文）。
  await expect(bodies.nth(1)).toContainText("## Limitations");
  // 且 v2 的父指针真的显示出来（EC-02 的读面字段在 UI 上被用到）。
  await expect(page.getByText("task-m:manuscript.md", { exact: false }).first()).toBeVisible();

  // ④ 编辑决定解析出四值之一 + 理由 + 要求的改动。
  const decision = page.getByTestId("editorial-decision-block");
  await expect(decision).toBeVisible();
  await expect(decision).toContainText("major_revision");
  await expect(decision).toContainText("stronger comparison baseline");
  await expect(page.getByTestId("editorial-required-changes")).toContainText("add a baseline");

  // ⑤ 投稿包五件各有链接（按 href 里的真实制品 id 核对）。
  const links = page.getByTestId("submission-package-links").getByRole("link");
  await expect(links).toHaveCount(5);
  const hrefs = await links.evaluateAll((nodes) => nodes.map((node) => node.getAttribute("href")));
  for (const name of [
    "cover_letter.md",
    "author_contributions.md",
    "conflicts_of_interest.md",
    "data_availability.md",
    "supplementary.md",
  ]) {
    expect(hrefs.some((href) => href?.includes(name) === true), `${name} 必须有下载链接`).toBe(true);
  }
});

test("没有手稿的 run 不渲染手稿面板（空面板会把「没产出」读成「产出为空」）", async ({ page }) => {
  await stubApi(page);
  await page.goto("/#/insights/reports?run=substrate-openhands");
  // 该 run 的制品读面走既有 503 兜底 ⇒ 面板不出现，但页面本身仍在。
  await expect(page.getByTestId("reports-page")).toBeVisible({ timeout: 8_000 });
  await expect(page.getByTestId("manuscript-body")).toHaveCount(0);
});
