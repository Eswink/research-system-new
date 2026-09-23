/**
 * 真实 API live 链（GOAL-013 EC-02 第 3 条）：`#/govern/audit` 在**真实读面**下渲染。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）。判据形态是
 * **「页面 == 读面」**：先经 HTTP 取 `GET /runs/{id}/events`，再与 DOM **逐值**比对——
 * 事件时间线里的行数就是读面返回的事件条数，**不是**前端常量。
 *
 * **成对反证**：两条受控 run 走同一页面、同一组件，差别只在数据——
 * `SUBSTRATE_RUN_ID` 的事件读面有 **1** 条，`BARE_EVENT_RUN_ID` 的读面是 **0** 条
 * ⇒ 前者渲染事件列表（`ol > li` 计数 == 读面长度），后者必须渲染**诚实空态文案**
 * 且**不渲染任何事件行**。
 *
 * **诚实边界**：本用例判的是「读面 → DTO → 页面」这一段；夹具事件不是真实 LLM/容器跑出来的，
 * 不声称「页面上的事件来自一次真实研究运行」。
 *
 * 读面快照落 `scratch/`（**不进仓库、不上传外部服务**），目录用 `EC13_SNAPSHOT_DIR` 指定。
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SNAPSHOT_DIR = process.env.EC13_SNAPSHOT_DIR ?? "scratch/goal013-c2";

// 受控 run（tests/api/console_api_app.py 声明；实测事件读面分别为 1 条与 0 条）。
const RUN_WITH_EVENTS = "44444444-4444-4444-8444-444444444444";
const RUN_WITHOUT_EVENTS = "55555555-5555-4555-8555-555555555555";

interface RunEventView {
  event_id: string;
  type: string;
}

function writeSnapshot(name: string, payload: unknown): void {
  mkdirSync(SNAPSHOT_DIR, { recursive: true });
  writeFileSync(join(SNAPSHOT_DIR, name), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

async function readEvents(page: Page, runId: string): Promise<RunEventView[]> {
  const response = await page.request.get(`/api/runs/${runId}/events`);
  expect(response.ok(), `events read face must be OK for ${runId}`).toBeTruthy();
  return (await response.json()) as RunEventView[];
}

async function openAudit(page: Page, runId: string): Promise<void> {
  await page.goto(`/#/govern/audit?run=${encodeURIComponent(runId)}`, {
    waitUntil: "domcontentloaded",
  });
  await expect(page.getByTestId("governance-page")).toBeVisible();
  await expect(page.getByTestId("run-timeline")).toBeVisible();
}

/** 事件行（时间线是一段有序列表，每行一个按钮）。 */
function eventRows(page: Page) {
  return page.getByTestId("run-timeline").locator("ol > li");
}

test("live: 审计页的事件行数 == 读面（页面 == 读面）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const events = await readEvents(page, RUN_WITH_EVENTS);
  writeSnapshot("govern-audit-read-face.json", events);
  // 反证前提：这条读面**确实**非空，否则下面的等式退化成「0 == 0」。
  expect(events.length).toBeGreaterThan(0);

  await openAudit(page, RUN_WITH_EVENTS);
  await expect(eventRows(page)).toHaveCount(events.length);
  // 行数与读面同值还不够：至少有一条事件的类型出现在页面上（值也是读面的）。
  const first = events[0];
  if (first !== undefined) {
    await expect(page.getByTestId("run-timeline").getByText(first.type).first()).toBeVisible();
  }
});

test("live: 事件读面为空时显示诚实空态，且不渲染事件行（成对反证）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const rich = await readEvents(page, RUN_WITH_EVENTS);
  const bare = await readEvents(page, RUN_WITHOUT_EVENTS);
  writeSnapshot("govern-audit-bare-read-face.json", bare);

  // 反证前提：两条读面**确实**不同（否则两条断言同义，是空断言）。
  expect(bare.length).toBe(0);
  expect(rich.length).toBeGreaterThan(bare.length);

  await openAudit(page, RUN_WITHOUT_EVENTS);
  // 判据**必须锚定**：不加 `^…$` 时前缀扩展文案（如「没有匹配的正式事件占位」）也会绿。
  await expect(
    page.getByText(/^(没有匹配的正式事件|No matching persisted events)$/),
  ).toBeVisible();
  await expect(eventRows(page)).toHaveCount(0);
});
