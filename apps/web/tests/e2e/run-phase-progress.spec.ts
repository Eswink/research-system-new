/**
 * 十一相进度条（GOAL-20261101-103 EC-03）。
 *
 * **它封住的失败形态**：`RunDetailDto.phases` 有值、前端**不渲染** ⇒ 用户仍然只能看到
 * 「这条 run 是 RUNNING」。判据只认三条**可证伪**的事实：
 *
 * ① 十一相节点**全部**可见，且 `data-testid` 与相 id 逐字对应（少一个相就红）；
 * ② 每个节点带 `data-phase-state`，**四态各至少出现一次**，且四态的着色 class 互不相同
 *    （"有状态色"是可判的：色由 class 决定，不由截图决定）；
 * ③ 点击一个节点展开**该相自己的**制品列表（不展开就是红，展开成别相的也是红）。
 *
 * 另加一条边界：`phases === null`（没有冻结协议正文）⇒ 显示"读不到相结构"，
 * **不**渲染零个节点 —— 「读不到」与「没有相」必须分得开。
 */

import { expect, test } from "@playwright/test";

import { stubApi } from "./stub-api";

const PHASE_IDS = [
  "question",
  "retrieval",
  "novelty",
  "plan",
  "experiment",
  "review",
  "manuscript",
  "editorial",
  "revision",
  "submission",
  "report",
];

test("十一相节点全部可见且各带状态", async ({ page }) => {
  await stubApi(page);
  await page.goto("/#/run/timeline?run=eleven-phases");
  await expect(page.getByTestId("phase-progress")).toBeVisible({ timeout: 8_000 });

  for (const phaseId of PHASE_IDS) {
    const node = page.getByTestId(`phase-node-${phaseId}`);
    await expect(node, `相 ${phaseId} 必须有一个节点`).toBeVisible();
  }
  // 逐相**点名**核对：不是只数个数（少一相 + 多一相会互相掩盖）。
  const rendered = await page
    .locator('[data-testid^="phase-node-"]')
    .evaluateAll((nodes) => nodes.map((node) => node.getAttribute("data-testid")));
  expect(rendered).toEqual(PHASE_IDS.map((id) => `phase-node-${id}`));

  // 四态各至少一次（受控输入保证），且状态值落在闭集里。
  const states = await page
    .locator("[data-phase-state]")
    .evaluateAll((nodes) => nodes.map((node) => node.getAttribute("data-phase-state")));
  expect(new Set(states)).toEqual(new Set(["PENDING", "RUNNING", "SUCCEEDED", "FAILED"]));
});

test("四态的着色互不相同（状态色可判，不靠截图比色）", async ({ page }) => {
  await stubApi(page);
  await page.goto("/#/run/timeline?run=eleven-phases");
  await expect(page.getByTestId("phase-progress")).toBeVisible({ timeout: 8_000 });

  // 判**计算后的** `border-left-color`，不判 class 名：CSS module 会把类名哈希掉，
  // 按类名比对只会在构建细节上打转；而"有没有状态色"这件事的真身是渲染出来的颜色。
  const colours = await page.locator("[data-phase-state]").evaluateAll((nodes) =>
    nodes.map((node) => ({
      state: node.getAttribute("data-phase-state"),
      colour: getComputedStyle(node).borderLeftColor,
    })),
  );
  const byState = new Map<string, Set<string>>();
  for (const item of colours) {
    const set = byState.get(item.state ?? "") ?? new Set<string>();
    set.add(item.colour);
    byState.set(item.state ?? "", set);
  }
  // 每一态内部颜色一致（同类同色）……
  for (const [state, set] of byState) {
    expect([...set].length, `状态 ${state} 的节点应当同色`).toBe(1);
  }
  // ……而四态之间**两两不同**（否则"有状态色"就无从判断）。
  const distinct = [...byState.values()].map((set) => [...set][0]);
  expect(distinct.length, "受控输入必须让四态各出现至少一次").toBe(4);
  expect(new Set(distinct).size, "四态必须渲染成四种不同的颜色").toBe(4);
});

test("点击节点展开该相自己的制品列表", async ({ page }) => {
  await stubApi(page);
  await page.goto("/#/run/timeline?run=eleven-phases");
  await expect(page.getByTestId("phase-progress")).toBeVisible({ timeout: 8_000 });

  // 展开前：该相的制品列表不在场（否则"展开"这件事不可判）。
  await expect(page.getByTestId("phase-artifacts-question")).toHaveCount(0);
  await page.getByTestId("phase-node-question").getByRole("button").click();
  const list = page.getByTestId("phase-artifacts-question");
  await expect(list).toBeVisible();
  await expect(list).toContainText("task-q:research_question");

  // 切到另一相：只留一个展开（点击语义是"切换"，不是"多选"）。
  await page.getByTestId("phase-node-retrieval").getByRole("button").click();
  await expect(page.getByTestId("phase-artifacts-retrieval")).toBeVisible();
  await expect(page.getByTestId("phase-artifacts-question")).toHaveCount(0);

  // 没有产出的相：展开后给明确空态（不是一条空 ul）。
  await page.getByTestId("phase-node-revision").getByRole("button").click();
  await expect(page.getByTestId("phase-artifacts-empty-revision")).toBeVisible();
});

test("没有冻结协议正文的 run 说「读不到相结构」，不渲染零个节点", async ({ page }) => {
  await stubApi(page);
  await page.goto("/#/run/timeline?run=no-frozen-body");
  await expect(page.getByTestId("phase-progress")).toBeVisible({ timeout: 8_000 });

  await expect(page.getByTestId("phase-progress-unavailable")).toBeVisible();
  await expect(page.locator('[data-testid^="phase-node-"]')).toHaveCount(0);
});
