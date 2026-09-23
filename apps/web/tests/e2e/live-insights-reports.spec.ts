/**
 * 真实 API live 链（GOAL-013 EC-02 第 5 条）：`#/insights/reports` 在**真实读面**下渲染。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）。判据形态是
 * **「页面 == 读面」**：先经 HTTP 取 `GET /runs/{id}/deliverable`，再与 DOM **逐值**比对
 * —— 页面渲染的研究目标 / 产物指纹就是读面返回的值，**不是**前端常量。
 *
 * **成对反证**：两条 run 走同一页面、同一组件，差别只在数据 ——
 * `LIVE_DELIVERABLE_RUN_ID` 的读面 `available: true`（有 `deliverable.objective` 与
 * `artifact_id`）⇒ 页面渲染报告正文与来源区块；另一条 run 的读面 `available: false`
 * ⇒ 页面必须显示读面 `reason` **逐字**，且**不**渲染来源区块（不伪造报告）。
 *
 * **诚实边界**：`1111…1111` 的交付物是**受控夹具**（见 `console_api_app` 的 D-4 注记），
 * 不是一次真实 M12 参考链的产出。本用例只判「读面 → DTO → 页面」，**不声称**
 * 「页面上是真实研究运行产出的报告」。
 *
 * 读面快照落 `scratch/`（**不进仓库、不上传外部服务**），目录用 `EC13_SNAPSHOT_DIR` 指定。
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SNAPSHOT_DIR = process.env.EC13_SNAPSHOT_DIR ?? "scratch/goal013-c3";

// 受控 run（tests/api/console_api_app.py 声明；实测读面分别 available=true / false）。
const RUN_WITH_DELIVERABLE = "11111111-1111-4111-8111-111111111111";
const RUN_WITHOUT_DELIVERABLE = "44444444-4444-4444-8444-444444444444";

interface DeliverableView {
  run_id: string;
  available: boolean;
  reason?: string | null;
  artifact_id?: string | null;
  deliverable: Record<string, unknown>;
}

function writeSnapshot(name: string, payload: unknown): void {
  mkdirSync(SNAPSHOT_DIR, { recursive: true });
  writeFileSync(join(SNAPSHOT_DIR, name), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

async function readDeliverable(page: Page, runId: string): Promise<DeliverableView> {
  const response = await page.request.get(`/api/runs/${runId}/deliverable`);
  expect(response.ok(), `deliverable read face must be OK for ${runId}`).toBeTruthy();
  return (await response.json()) as DeliverableView;
}

async function openReports(page: Page, runId: string): Promise<void> {
  await page.goto(`/#/insights/reports?run=${encodeURIComponent(runId)}`, {
    waitUntil: "domcontentloaded",
  });
  await expect(page.getByTestId("reports-page")).toBeVisible();
}

test("live: 交付物读面非空时，报告页渲染的是读面的值（页面 == 读面）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const view = await readDeliverable(page, RUN_WITH_DELIVERABLE);
  writeSnapshot("insights-reports-read-face.json", view);
  // 反证前提：这条读面**确实**非空且带 objective，否则下面的比对退化成「空 == 空」。
  expect(view.available).toBeTruthy();
  const objective = view.deliverable.objective;
  expect(typeof objective).toBe("string");

  await openReports(page, RUN_WITH_DELIVERABLE);
  const pageBody = page.getByTestId("reports-page");
  // 目标段落逐字来自读面（`deliverable.objective`）。
  await expect(pageBody.getByText(String(objective))).toBeVisible();
  // 来源区块：`artifact_id` 由**端点**从持久化产物导出，页面必须显示同一个值。
  await expect(pageBody.getByText("artifact_id")).toBeVisible();
  await expect(pageBody.getByText(String(view.artifact_id))).toBeVisible();
});

test("live: 无交付物的 run 显示读面给出的原因，且不渲染来源区块（成对反证）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const rich = await readDeliverable(page, RUN_WITH_DELIVERABLE);
  const bare = await readDeliverable(page, RUN_WITHOUT_DELIVERABLE);
  writeSnapshot("insights-reports-bare-read-face.json", bare);

  // 反证前提：两条读面**确实**不同（否则两条断言同义，是空断言）。
  expect(bare.available).toBe(false);
  expect(rich.available).toBe(true);
  expect(typeof bare.reason).toBe("string");

  await openReports(page, RUN_WITHOUT_DELIVERABLE);
  const pageBody = page.getByTestId("reports-page");
  // 空态文案**逐字**来自读面 `reason`（不是前端自造的一句话）。
  await expect(pageBody.getByText(String(bare.reason))).toBeVisible();
  // 反证：未产出交付物时**不得**渲染来源区块（否则就是在伪造来源）。
  await expect(pageBody.getByText("artifact_id")).toHaveCount(0);
  await expect(pageBody.getByText("artifact_digest")).toHaveCount(0);
});
