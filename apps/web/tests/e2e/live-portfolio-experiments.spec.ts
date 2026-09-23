/**
 * 真实 API live 链（GOAL-013 EC-02 第 4 条）：`#/portfolio/experiments` 在**真实读面**下渲染。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）。判据形态是
 * **「页面 == 读面」**：先经 HTTP 取**该 run** 的 `GET /runs/{id}/experiments`（该页按
 * `?run=` 选中运行后消费的就是这条读面），再与 DOM **逐行逐值**比对 ——
 * 行数、制品数、**指标键数**都由读面导出，**不是**前端常量。
 *
 * **成对反证**：两条 run 走同一页面、同一组件，差别只在数据 ——
 * `LIVE_EXPERIMENT_RUN_ID` 的读面有指标（2 个键）⇒ 指标列渲染 2；
 * `LIVE_EXPERIMENT_BARE_RUN_ID` 的读面 `metrics` 是**空对象** ⇒ 指标列必须渲染 **0**，
 * **不得**补一个占位指标（不伪造数据）。
 *
 * **诚实边界**：本用例判的是「读面 → DTO → 页面」这一段；实验是**受控夹具**、
 * 不是真容器跑出来的，不声称「页面上的实验来自一次真实执行」。
 *
 * 读面快照落 `scratch/`（**不进仓库、不上传外部服务**），目录用 `EC13_SNAPSHOT_DIR` 指定。
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SNAPSHOT_DIR = process.env.EC13_SNAPSHOT_DIR ?? "scratch/goal013-c3";

// 受控 run（tests/api/console_api_app.py 声明；实测读面分别有指标 / 无指标）。
const RUN_WITH_METRICS = "55555555-5555-4555-8555-555555555555";
const RUN_WITHOUT_METRICS = "66666666-6666-4666-8666-666666666666";

// 列序见 `experimentColumns`：id(0) / artifacts(1) / image(2) / metrics(3) / reproduction(4)。
const ARTIFACTS_COLUMN = 1;
const METRICS_COLUMN = 3;

interface ExperimentRunView {
  experiment_run_id: string;
  artifact_ids: string[];
  metrics: Record<string, number>;
}

interface ExperimentsView {
  experiments: ExperimentRunView[];
  reproduction_note: string;
}

function writeSnapshot(name: string, payload: unknown): void {
  mkdirSync(SNAPSHOT_DIR, { recursive: true });
  writeFileSync(join(SNAPSHOT_DIR, name), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

async function readExperiments(page: Page, runId: string): Promise<ExperimentsView> {
  const response = await page.request.get(`/api/runs/${runId}/experiments`);
  expect(response.ok(), `experiments read face must be OK for ${runId}`).toBeTruthy();
  return (await response.json()) as ExperimentsView;
}

async function openExperiments(page: Page, runId: string): Promise<void> {
  await page.goto(`/#/portfolio/experiments?run=${encodeURIComponent(runId)}`, {
    waitUntil: "domcontentloaded",
  });
  await expect(page.getByTestId("experiments-page")).toBeVisible();
}

/** 表格行（多语言 `aria-label` ⇒ 必须写成**选择器列表**，CSS 属性选择器不做候选）。 */
function experimentRows(page: Page) {
  return page
    .locator(
      ["实验列表", "Experiments"]
        .map((label) => `table[aria-label="${label}"]`)
        .join(", "),
    )
    .first()
    .locator("tbody tr");
}

function metricKeyCount(item: ExperimentRunView): number {
  return Object.keys(item.metrics).length;
}

test("live: 实验表的逐行计数 == 读面（页面 == 读面）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const view = await readExperiments(page, RUN_WITH_METRICS);
  writeSnapshot("portfolio-experiments-read-face.json", view);
  // 反证前提：这条读面**确实**有实验且有指标，否则下面的逐行比对退化。
  expect(view.experiments.length).toBeGreaterThan(0);
  expect(view.experiments.every((item) => metricKeyCount(item) > 0)).toBeTruthy();

  await openExperiments(page, RUN_WITH_METRICS);
  const rows = experimentRows(page);
  await expect(rows).toHaveCount(view.experiments.length);

  // 逐行逐值：行内文本必须含读面的 `experiment_run_id`，制品数与指标键数由读面导出。
  for (const item of view.experiments) {
    const row = rows.filter({ hasText: item.experiment_run_id });
    await expect(row, `one row per experiment: ${item.experiment_run_id}`).toHaveCount(1);
    await expect(row.locator("td").nth(ARTIFACTS_COLUMN)).toHaveText(
      String(item.artifact_ids.length),
    );
    await expect(row.locator("td").nth(METRICS_COLUMN)).toHaveText(String(metricKeyCount(item)));
  }
});

test("live: 指标为空的实验渲染 0，不补占位指标（成对反证）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const rich = await readExperiments(page, RUN_WITH_METRICS);
  const bare = await readExperiments(page, RUN_WITHOUT_METRICS);
  writeSnapshot("portfolio-experiments-bare-read-face.json", bare);

  // 反证前提：两条读面**确实**不同（否则这条与正向同义，是空断言）。
  expect(bare.experiments.length).toBeGreaterThan(0);
  expect(bare.experiments.every((item) => metricKeyCount(item) === 0)).toBeTruthy();
  expect(rich.experiments.some((item) => metricKeyCount(item) > 0)).toBeTruthy();

  await openExperiments(page, RUN_WITHOUT_METRICS);
  const rows = experimentRows(page);
  await expect(rows).toHaveCount(bare.experiments.length);

  for (const item of bare.experiments) {
    // 读面里该条**没有**指标 ⇒ 页面必须渲染 0，不得补占位。
    await expect(
      rows.filter({ hasText: item.experiment_run_id }).locator("td").nth(METRICS_COLUMN),
      `${item.experiment_run_id} has no metrics in the read face ⇒ the cell must read 0`,
    ).toHaveText("0");
  }
  // 正向对照：同一条 run 的读面若换成有指标的实验，指标列**不是** 0
  // （证明上面的 0 来自数据，而不是「这一列恒为 0」）。
  await openExperiments(page, RUN_WITH_METRICS);
  for (const item of rich.experiments) {
    await expect(
      experimentRows(page).filter({ hasText: item.experiment_run_id }).locator("td").nth(3),
    ).not.toHaveText("0");
  }
});
