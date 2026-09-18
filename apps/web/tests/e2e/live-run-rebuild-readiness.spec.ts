/**
 * 真实 API live 链（GOAL-20260918-006 cycle 3 = EC-03）：重建就绪读面经真实 HTTP
 * 到页面。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）：
 *
 * - 真启动一条 run（受控 pin + Fake runtime 终态）⇒ canonical 行上有冻结正文与两个
 *   digest，读面判"记录自足"；
 * - 夹具历史行（`LIVE_SNAPSHOT_RUN_ID`，无任何装配输入）⇒ 读面拒绝并按行字段名
 *   逐个点名缺失事实。
 *
 * 页面必须渲染**读面返回的那个值**（不是前端常量）：两处都从 HTTP 面取值再与
 * DOM 比对；文案不越界（拒绝 ≠ 不可回填）。
 */

import { expect, test, type Page } from "@playwright/test";

const LEGACY_RUN_ID = "11111111-1111-4111-8111-111111111111";
// 受控 pin + Fake runtime 下会真的 freeze manifest 与正文的参考协议（执行是否成功
// 与"记录够不够重建"无关：读面只回答输入齐不齐）。
const FROZEN_PROTOCOL = "m12_reference_research_v1.yaml";

interface RunDetail {
  id: string;
  rebuild: { status: string; missing: string[] };
}

async function runDetail(page: Page, runId: string): Promise<RunDetail> {
  const response = await page.request.get(`/api/runs/${encodeURIComponent(runId)}`);
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as RunDetail;
}

test("live: 真启动的 run 记录自足，页面与读面同值", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const started = await page.request.post("/api/projects/example-project/runs", {
    headers: { "Idempotency-Key": `live-rebuild-${String(Date.now())}` },
    data: { protocol_path: FROZEN_PROTOCOL },
  });
  expect(started.ok()).toBeTruthy();
  const run = (await started.json()) as { id: string };

  const detail = await runDetail(page, run.id);
  expect(detail.rebuild.status).toBe("SELF_CONTAINED");
  expect(detail.rebuild.missing).toEqual([]);

  await page.goto(`/#/run/timeline?run=${encodeURIComponent(run.id)}`);
  await expect(page.getByTestId("run-rebuild-status")).toHaveText(detail.rebuild.status);
  await expect(page.getByTestId("run-rebuild")).toContainText("记录自足");
  // 分类器不变量：missing 非空 ⇔ REFUSED 非空 ⇒ 自足态不列缺失事实。
  await expect(page.getByTestId("run-rebuild-missing")).toHaveCount(0);
});

test("live: 历史行被读面拒绝并按字段名点名，页面照实呈现", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const detail = await runDetail(page, LEGACY_RUN_ID);
  expect(detail.rebuild.status).toBe("REFUSED");
  expect(detail.rebuild.missing.length).toBeGreaterThan(0);

  await page.goto(`/#/run/timeline?run=${LEGACY_RUN_ID}`);
  await expect(page.getByTestId("run-rebuild-status")).toHaveText(detail.rebuild.status);
  const missing = page.getByTestId("run-rebuild-missing");
  await expect(missing).toBeVisible();
  for (const name of detail.rebuild.missing) {
    await expect(missing).toContainText(name);
  }
  // 拒绝的是"这个读面给不了结论"，不是"回填不可能"。
  await expect(page.getByTestId("run-rebuild")).toContainText("这不是「不可回填」的判定");
  await expect(page.getByTestId("run-rebuild-note")).toContainText("不预告重建结果");
});
