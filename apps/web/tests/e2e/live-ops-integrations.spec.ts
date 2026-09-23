/**
 * 真实 API live 链（GOAL-013 EC-02 第 6 条）：`#/ops/integrations` 在**真实读面**下渲染。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）。判据形态是
 * **「页面 == 读面」**：先经 HTTP 取 `GET /tool-providers`，再与 DOM **逐行逐值**比对
 * —— 目录行数、每行的 provider id 与**健康态**都来自读面，**不是**前端常量。
 *
 * **成对反证**：读面里 3 个 provider 的健康态是 `HEALTHY` / **`UNKNOWN`** / `HEALTHY`
 * （`UNKNOWN` 那条是 `ncbi_eutils`，声明了 `health_check` 但当前无法判定）。
 * ⇒ 反证方向：`UNKNOWN` 必须**如实**显示为 `UNKNOWN`，页面**不得**把它渲染成健康
 * ——「无法判定」不等于「健康」，不伪造健康。
 *
 * **诚实边界**：本用例判的是「读面 → DTO → 页面」这一段；健康态来自受控夹具与既有探测结果，
 * 不声称「页面上是此刻的真实外部联通性」。
 *
 * 读面快照落 `scratch/`（**不进仓库、不上传外部服务**），目录用 `EC13_SNAPSHOT_DIR` 指定。
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { expect, test, type Page } from "@playwright/test";

const SNAPSHOT_DIR = process.env.EC13_SNAPSHOT_DIR ?? "scratch/goal013-c3";

interface ProviderView {
  id: string;
  kind: string;
  trust_level: string;
  health: string;
}

interface ProvidersView {
  providers: ProviderView[];
  management_available: boolean;
}

function writeSnapshot(name: string, payload: unknown): void {
  mkdirSync(SNAPSHOT_DIR, { recursive: true });
  writeFileSync(join(SNAPSHOT_DIR, name), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

async function readProviders(page: Page): Promise<ProvidersView> {
  const response = await page.request.get("/api/tool-providers");
  expect(response.ok(), "tool providers read face must be OK").toBeTruthy();
  return (await response.json()) as ProvidersView;
}

/** 目录表（多语言 `aria-label` ⇒ 选择器列表；CSS 属性选择器不做候选）。 */
function providerRows(page: Page) {
  return page
    .locator(
      ["Tool Provider 目录", "Tool provider catalog"]
        .map((label) => `table[aria-label="${label}"]`)
        .join(", "),
    )
    .first()
    .locator("tbody tr");
}

test("live: provider 目录逐行逐值 == 读面（页面 == 读面）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const view = await readProviders(page);
  writeSnapshot("ops-integrations-read-face.json", view);
  // 反证前提：读面**确实**同时含健康态与无法判定态，否则下面的逐行比对退化。
  expect(view.providers.length).toBeGreaterThan(0);
  expect(view.providers.some((item) => item.health === "UNKNOWN")).toBeTruthy();
  expect(view.providers.some((item) => item.health !== "UNKNOWN")).toBeTruthy();

  await page.goto("/#/ops/integrations", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("integrations-page")).toBeVisible();
  const rows = providerRows(page);
  await expect(rows).toHaveCount(view.providers.length);

  // 逐行逐值：每行的 id 与健康态都由读面导出（顺序无关，按 id 定位）。
  for (const item of view.providers) {
    const row = rows.filter({ hasText: item.id });
    await expect(row, `one row per provider: ${item.id}`).toHaveCount(1);
    await expect(row.getByText(item.health, { exact: true })).toBeVisible();
  }
});

test("live: 无法判定的 provider 如实显示 UNKNOWN，不伪装健康（成对反证）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const view = await readProviders(page);
  const unknown = view.providers.filter((item) => item.health === "UNKNOWN");
  const healthy = view.providers.filter((item) => item.health === "HEALTHY");
  // 反证前提：两侧**都非空**且真的不同（否则这条与正向同义，是空断言）。
  expect(unknown.length).toBeGreaterThan(0);
  expect(healthy.length).toBeGreaterThan(0);

  await page.goto("/#/ops/integrations", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("integrations-page")).toBeVisible();
  const rows = providerRows(page);

  for (const item of unknown) {
    const row = rows.filter({ hasText: item.id });
    // 读面说「无法判定」⇒ 页面必须显示 UNKNOWN，且**不得**显示成健康。
    await expect(row.getByText("UNKNOWN", { exact: true })).toBeVisible();
    await expect(
      row.getByText("HEALTHY", { exact: true }),
      `${item.id} reads UNKNOWN in the read face ⇒ the page must not claim it is healthy`,
    ).toHaveCount(0);
  }
  // 正向对照：读面说健康的那些**确实**显示为健康（证明上面的 0 不是「所有行都不显示健康」）。
  for (const item of healthy) {
    const row = rows.filter({ hasText: item.id });
    await expect(row.getByText("HEALTHY", { exact: true })).toBeVisible();
  }
});
