/**
 * 真实 API live 链（GOAL-013 EC-02 第 1 条）：`#/plan/overview` 在**真实读面**下渲染。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）。判据形态是
 * **「页面 == 读面」**：先经 HTTP 取该页消费的四条读面（`GET /runs/{id}`、
 * `/runs/{id}/tasks`、`/runs/{id}/claims`、`/runs/{id}/usage`），再与 DOM 逐值比对——
 * 指标卡里的数必须是**读面返回的那个数**，不是前端常量。
 *
 * **成对反证**：两条受控 run 走同一页面、同一组件，差别只在数据——
 * `RICH_RUN_ID` 的论断读面有 1 条，`EMPTY_RUN_ID` 的论断读面是空的 ⇒ 同一张论断卡
 * 必须分别显示 `1` 与 `0`（读面自己的零，不是伪造的占位）。凡读面为空的段落
 * （本夹具里 tasks 两条都是空）页面必须显示**诚实空态**。
 *
 * **诚实边界**：本用例判的是「读面 → DTO → 页面」这一段；夹具的 run 不是真实
 * LLM/容器跑出来的（真实全链在 pytest 层，见 GOAL-012 EC-02/EC-03 的 pytest 判据），
 * 因此本用例**不**声称「页面上那次运行真的在容器里跑过」。
 *
 * 读面快照落 `scratch/`（**不进仓库、不上传外部服务**），目录用
 * `EC13_SNAPSHOT_DIR` 指定，缺省 `scratch/goal013-c1/`。
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { expect, test, type Locator, type Page } from "@playwright/test";

// 受控 run（tests/api/console_api_app.py 声明；两棵树都不存在的 run 会 404）。
const RICH_RUN_ID = "55555555-5555-4555-8555-555555555555";
const EMPTY_RUN_ID = "44444444-4444-4444-8444-444444444444";

const SNAPSHOT_DIR = process.env.EC13_SNAPSHOT_DIR ?? "scratch/goal013-c1";

interface RunDetailView {
  id: string;
  project_id: string;
  protocol_id: string;
  state: string;
  manifest_digest: string | null;
}

interface ClaimMapView {
  claims: unknown[];
  unsupported_claims: unknown[];
  contradictory_claims: unknown[];
  degraded: boolean;
}

interface UsageView {
  entries: unknown[];
  total_estimated_cost_minor: number | null;
  total_currency: string | null;
  unknown_cost_entries: number;
}

interface TaskView {
  status: string;
}

interface ReadFace {
  run: RunDetailView;
  tasks: TaskView[];
  claims: ClaimMapView;
  usage: UsageView;
}

/** 指标卡按**标签文字**定位（label 随语言变：两种都接受，别把文案钉成语言常量）。 */
function metricCard(page: Page, labels: readonly string[]): Locator {
  const alternation = labels.map((label) => label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|");
  return page.locator("div.panel", { has: page.getByText(new RegExp(`^(${alternation})$`)) });
}

/** 读面值行：指标卡里紧跟标签的那段文字。 */
function metricValue(page: Page, labels: readonly string[]): Locator {
  return metricCard(page, labels).locator("div").nth(1);
}

async function fetchJson<T>(page: Page, path: string): Promise<T> {
  const response = await page.request.get(path);
  expect(response.ok(), `read face ${path} must be OK`).toBeTruthy();
  return (await response.json()) as T;
}

async function readFace(page: Page, runId: string): Promise<ReadFace> {
  return {
    run: await fetchJson<RunDetailView>(page, `/api/runs/${runId}`),
    tasks: await fetchJson<TaskView[]>(page, `/api/runs/${runId}/tasks`),
    claims: await fetchJson<ClaimMapView>(page, `/api/runs/${runId}/claims`),
    usage: await fetchJson<UsageView>(page, `/api/runs/${runId}/usage`),
  };
}

function writeSnapshot(name: string, payload: unknown): void {
  mkdirSync(SNAPSHOT_DIR, { recursive: true });
  writeFileSync(join(SNAPSHOT_DIR, name), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

async function openOverview(page: Page, runId: string): Promise<void> {
  await page.goto(`/#/plan/overview?run=${encodeURIComponent(runId)}`, {
    waitUntil: "domcontentloaded",
  });
  await expect(page.getByTestId("overview-page")).toBeVisible();
}

test("live: 概览页的四张指标卡 == 读面（页面 == 读面）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const view = await readFace(page, RICH_RUN_ID);
  writeSnapshot("plan-overview-read-face.json", view);
  expect(view.claims.claims.length).toBeGreaterThan(0);

  await openOverview(page, RICH_RUN_ID);

  // 任务卡：读面自己的 done/total（空数组 ⇒ 0 / 0，不是「—」）。
  const done = view.tasks.filter((task) => task.status === "SUCCEEDED").length;
  await expect(metricValue(page, ["任务", "Tasks"])).toHaveText(
    `${String(done)} / ${String(view.tasks.length)}`,
  );

  // 论断卡：读面 claims 的长度，逐值比对。
  await expect(metricValue(page, ["论断", "Claims"])).toHaveText(
    String(view.claims.claims.length),
  );

  // 成本卡：读面 total 为 null ⇒ 必须走「金额未知」通道，而不是 0。
  const total = view.usage.total_estimated_cost_minor;
  const costCard = metricCard(page, ["成本", "Cost"]);
  if (total === null) {
    await expect(costCard.getByText(/金额未知|amount unknown/)).toBeVisible();
  } else {
    await expect(metricValue(page, ["成本", "Cost"])).toHaveText(String(total));
  }

  // 运行状态卡与冻结身份：读面的 state 与 manifest_digest 决定 DOM 文本。
  await expect(metricValue(page, ["运行状态", "Run state"])).toHaveText(view.run.state);
  const chip = view.run.manifest_digest === null ? "NOT FROZEN" : "FROZEN";
  await expect(page.getByText(chip, { exact: true })).toBeVisible();
});

test("live: 读面为空时页面显示诚实空态（成对反证，不伪造数据）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const rich = await readFace(page, RICH_RUN_ID);
  const bare = await readFace(page, EMPTY_RUN_ID);
  writeSnapshot("plan-overview-bare-read-face.json", bare);

  // 反证前提：两条 run 的论断读面**确实**不同（否则下面两条断言同义，是空断言）。
  expect(bare.claims.claims.length).toBe(0);
  expect(rich.claims.claims.length).toBeGreaterThan(bare.claims.claims.length);

  await openOverview(page, EMPTY_RUN_ID);
  await expect(metricValue(page, ["论断", "Claims"])).toHaveText("0");

  // 空任务读面 ⇒ 段落显示空态文案（同一个组件在富读面下显示的是任务卡列表）。
  // 锚定匹配：不加 `^…$` 时前缀扩展文案也会绿（GOAL-013 cycle 2 的按压实测撞到过）。
  await expect(
    page.getByText(/^(没有已读取的执行任务|No loaded execution tasks)$/),
  ).toBeVisible();
  await expect(page.getByText(EMPTY_RUN_ID, { exact: false }).first()).toBeVisible();
});
