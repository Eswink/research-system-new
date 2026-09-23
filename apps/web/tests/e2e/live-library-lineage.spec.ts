/**
 * 真实 API live 链（GOAL-013 EC-02 第 2 条）：`#/library/lineage` 在**真实读面**下渲染。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）。判据形态是
 * **「页面 == 读面」**：先经 HTTP 取 `GET /projects/{id}/lineage`，再与 DOM **逐值**比对——
 * 合并摘要里的三个数就是读面的 `run_count` / `nodes.length` / `edges.length`，
 * 两张表的行数就是读面的数组长度，**不是**前端常量。
 *
 * **成对反证（同一读面内）**：该读面实测 `library_resources` 为 **0** ⇒ 库资源面板必须显示
 * **诚实空态文案**且**不渲染空表**（同一个组件在非空时渲染表、在空时渲染文案）。
 * 这条不需要第二个 run：非空表（节点 / 边）与空态（库资源）在同一次响应里同时成立。
 *
 * **诚实边界**：本用例判的是「读面 → DTO → 页面」这一段，读面由夹具装配（Fake Ports），
 * 不是真实 LLM/容器跑出来的；不声称「页面上的血缘来自一次真实研究运行」。
 *
 * 读面快照落 `scratch/`（**不进仓库、不上传外部服务**），目录用 `EC13_SNAPSHOT_DIR` 指定。
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SNAPSHOT_DIR = process.env.EC13_SNAPSHOT_DIR ?? "scratch/goal013-c2";

interface ProjectLineageView {
  project_id: string;
  run_count: number;
  nodes: { id: string; kind: string; shared: boolean }[];
  edges: unknown[];
  library_resources: { id: string; kind: string; name: string }[];
  reference_recording: string;
  reference_recording_reason: string;
  degraded: boolean;
}

function writeSnapshot(name: string, payload: unknown): void {
  mkdirSync(SNAPSHOT_DIR, { recursive: true });
  writeFileSync(join(SNAPSHOT_DIR, name), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

/** 表按 aria-label 定位（label 随语言变：两种都接受，别把文案钉成语言常量）。 */
function tableRows(page: Page, labels: readonly string[]) {
  // CSS 属性选择器**不做**候选：必须写成选择器列表（`a, b`），否则 `a|b` 会被当字面量。
  return page
    .locator(labels.map((label) => `table[aria-label="${label}"]`).join(", "))
    .first()
    .locator("tbody tr");
}

async function readFace(page: Page, projectId: string): Promise<ProjectLineageView> {
  const response = await page.request.get(`/api/projects/${projectId}/lineage`);
  expect(response.ok(), "project lineage read face must be OK").toBeTruthy();
  return (await response.json()) as ProjectLineageView;
}

test("live: 血缘页的三张表与合并摘要 == 读面（页面 == 读面）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const view = await readFace(page, "example-project");
  writeSnapshot("library-lineage-read-face.json", view);
  // 反证前提：读面**确实**有内容，否则下面的逐值断言会退化成「0 == 0」。
  expect(view.nodes.length).toBeGreaterThan(0);

  await page.goto("/#/library/lineage", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("lineage-page")).toBeVisible();

  // 合并摘要：三个数逐值来自读面。
  const counts = [view.run_count, view.nodes.length, view.edges.length].map(String);
  await expect(page.getByText(counts.join(" / "), { exact: false }).first()).toBeVisible();

  // 两张非空表的行数 == 读面数组长度。
  await expect(tableRows(page, ["项目血缘节点", "Project lineage nodes"])).toHaveCount(
    view.nodes.length,
  );
  await expect(tableRows(page, ["项目血缘边", "Project lineage edges"])).toHaveCount(
    view.edges.length,
  );
});

test("live: 库资源读面为空时显示诚实空态，且不渲染空表（成对反证）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const view = await readFace(page, "example-project");

  await page.goto("/#/library/lineage", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("lineage-page")).toBeVisible();

  if (view.library_resources.length === 0) {
    // 空 ⇒ 文案在场、表缺席（同一个组件在非空时渲染表）。
    // 判据**必须锚定**：不加 `^…$` 时 `项目内无库资源占位` 这类前缀扩展也会绿
    // （按压实测撞到过），那样等于没锁住「诚实空态」这句话本身。
    await expect(
      page.getByText(/^(项目内无库资源|No library resources in this project)$/),
    ).toBeVisible();
    const resourceTables = page.locator(
      'table[aria-label="未连边库资源"], table[aria-label="Unlinked library resources"]',
    );
    await expect(resourceTables).toHaveCount(0);
  } else {
    // 非空 ⇒ 行数必须等于读面长度（本夹具当前为空，此分支备而不用）。
    await expect(tableRows(page, ["未连边库资源", "Unlinked library resources"])).toHaveCount(
      view.library_resources.length,
    );
  }
  // 引用面无记录：后端如实标注，页面原样呈现（不画猜测的边）。
  if (view.reference_recording !== "RECORDED") {
    const noticed = page.getByText(view.reference_recording_reason, { exact: false });
    await expect(noticed.first()).toBeVisible();
  }
});
