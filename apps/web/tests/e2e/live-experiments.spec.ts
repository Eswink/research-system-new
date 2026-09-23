/**
 * 真实 API live 链（GOAL-012 EC-05）：实验读面在浏览器里用**真实数据**渲染产物与指标。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）。两条受控 run 的
 * 实验记录走**产品自己的准入路径**（`register_experiment_evidence`，run 链同一个函数）写进
 * canonical；指标由**内容寻址制品**的 JSON 承载（读面 `_metrics_for` 就这么取）。
 *
 * 判据形态是 **「页面 == 读面」**：先经 HTTP 取 `GET /runs/{id}/experiments`，再与 DOM
 * 逐值比对（制品引用数、镜像指纹、指标字段数、抽屉里的指标原始投影）——页面渲染的必须是
 * 读面返回的那个值，而不是前端常量。
 *
 * **成对反证**：第二条 run 的实验只有一件**非 JSON** 制品 ⇒ 读面 `metrics` 为空 ⇒ 同一个
 * 组件必须显示空态。两条 run 走同一页面、同一组件，差别只在数据。
 *
 * **诚实边界**：夹具的**执行**不是真容器跑出来的——真实容器的实验全链在 pytest 层
 * （`tests/e2e/test_ec02_experiment_chain_offline.py`、`test_ec03_experiment_evidence_chain.py`）。
 * 本用例判的是「读面 → DTO → 页面」这一段，不声称「页面上那次实验真的在容器里跑过」。
 *
 * 读面快照与截图落 `scratch/`（**不进仓库、不上传外部服务**），目录用
 * `EC05_SNAPSHOT_DIR` 指定，缺省 `scratch/goal012-c5/`。
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

// 受控 run（tests/api/console_api_app.py 声明；两棵树都不存在的 run 会 404）。
const RUN_ID = "55555555-5555-4555-8555-555555555555";
const BARE_RUN_ID = "66666666-6666-4666-8666-666666666666";

const SNAPSHOT_DIR =
  process.env.EC05_SNAPSHOT_DIR ?? join(process.cwd(), "..", "..", "scratch", "goal012-c5");

interface ExperimentRun {
  experiment_run_id: string;
  artifact_ids: string[];
  image_digest: string | null;
  environment_digest: string | null;
  metrics: Record<string, unknown>;
  reproduction_available: boolean;
}

interface ExperimentView {
  experiments: ExperimentRun[];
  reproduction_note: string;
}

async function readFace(page: Page, runId: string): Promise<ExperimentView> {
  const response = await page.request.get(`/api/runs/${encodeURIComponent(runId)}/experiments`);
  expect(response.ok(), await response.text()).toBeTruthy();
  return (await response.json()) as ExperimentView;
}

function writeSnapshot(name: string, payload: unknown): void {
  mkdirSync(SNAPSHOT_DIR, { recursive: true });
  writeFileSync(join(SNAPSHOT_DIR, name), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

/** 实验目录表（aria-label 随语言变：两种都接受，别把文案钉死成语言常量）。 */
function catalogTable(page: Page) {
  return page.locator('table[aria-label="实验列表"], table[aria-label="Experiments"]');
}

async function openCatalog(page: Page, runId: string) {
  await page.goto(`/#/portfolio/experiments?run=${encodeURIComponent(runId)}`, {
    waitUntil: "domcontentloaded",
  });
  await expect(catalogTable(page)).toBeVisible();
}

test("live: 实验页渲染读面的真实指标与制品（页面 == 读面）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const view = await readFace(page, RUN_ID);
  expect(view.experiments.length).toBe(1);
  const experiment = view.experiments[0];
  expect(experiment).toBeDefined();
  if (experiment === undefined) return;
  expect(experiment.artifact_ids.length).toBeGreaterThan(0);
  expect(Object.keys(experiment.metrics).length).toBeGreaterThan(0);
  writeSnapshot("read-face.json", view);

  await openCatalog(page, RUN_ID);
  const rows = catalogTable(page).locator("tbody tr");
  const row = rows.filter({ hasText: experiment.experiment_run_id });
  await expect(row).toHaveCount(1);
  const cells = row.locator("td");
  await expect(cells.nth(0)).toHaveText(experiment.experiment_run_id);
  await expect(cells.nth(1)).toHaveText(String(experiment.artifact_ids.length));
  await expect(cells.nth(2)).toHaveText((experiment.image_digest ?? "UNKNOWN").slice(0, 20));
  await expect(cells.nth(3)).toHaveText(String(Object.keys(experiment.metrics).length));

  // 抽屉（同一组件的第二处渲染面）：元数据 + 指标**原始投影**
  await row.click();
  const drawer = page.getByRole("dialog");
  await expect(drawer).toBeVisible();
  await expect(drawer).toContainText(experiment.experiment_run_id);
  await expect(drawer).toContainText(experiment.image_digest ?? "—");
  await expect(drawer).toContainText(String(experiment.reproduction_available));
  for (const artifactId of experiment.artifact_ids) {
    await expect(drawer).toContainText(artifactId);
  }
  await expect(drawer.locator("pre")).toHaveText(
    JSON.stringify(experiment.metrics, null, 2),
  );

  writeSnapshot("page-values.json", {
    run_id: RUN_ID,
    artifact_cells: await cells.nth(1).textContent(),
    metric_field_cells: await cells.nth(3).textContent(),
    image_cell: await cells.nth(2).textContent(),
    metrics_projection: await drawer.locator("pre").textContent(),
  });
  await page.screenshot({ path: join(SNAPSHOT_DIR, "experiments-page.png"), fullPage: true });
});

test("live: 无指标实验照实显示空态（成对反证）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const view = await readFace(page, BARE_RUN_ID);
  expect(view.experiments.length).toBe(1);
  const experiment = view.experiments[0];
  expect(experiment).toBeDefined();
  if (experiment === undefined) return;
  // 反证的前提：读面这一侧**本来就**没有指标、且只有一件制品
  expect(Object.keys(experiment.metrics)).toEqual([]);
  expect(experiment.artifact_ids.length).toBe(1);
  writeSnapshot("read-face-bare.json", view);

  await openCatalog(page, BARE_RUN_ID);
  const rows = catalogTable(page).locator("tbody tr");
  const row = rows.filter({ hasText: experiment.experiment_run_id });
  await expect(row).toHaveCount(1);
  const cells = row.locator("td");
  await expect(cells.nth(1)).toHaveText("1");
  await expect(cells.nth(3)).toHaveText("0");

  await row.click();
  const drawer = page.getByRole("dialog");
  await expect(drawer).toBeVisible();
  // 同一组件：指标面照实空态（不是把上一条 run 的值留在页面上）
  await expect(drawer.locator("pre")).toHaveCount(0);
  await expect(drawer).toContainText(/没有已记录指标|No recorded metrics/);
  await page.screenshot({ path: join(SNAPSHOT_DIR, "experiments-page-bare.png"), fullPage: true });
});
