/**
 * 真实链路 live 链（GOAL-007 cycle 4 = EC-04）：执行体披露读面经真实 HTTP 到页面。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）：
 *
 * - 夹具声明行（`LIVE_SUBSTRATE_RUN_ID`）：冻结事件声明执行体 = `openhands`；
 * - 真启动的 run：app 的选择面是默认解析结果 ⇒ 冻结出 `fake`。
 *
 * 页面必须渲染**读面返回的那个值**（不是前端常量）：每处都从 HTTP 面取值再与 DOM
 * 比对，并断言两种执行体在页面上**互不相同**（这就是本 EC 的靶子）。
 */

import { expect, test, type Page } from "@playwright/test";

// 夹具声明为真实执行体的那条 run（tests/api/console_api_app.py 的 `LIVE_SUBSTRATE_RUN_ID`）。
// 该 UUID 不能与别处当作「不存在的 run」的取值相同，否则那边的 404 断言会变成 200。
const DECLARED_RUN_ID = "44444444-4444-4444-8444-444444444444";
const FROZEN_PROTOCOL = "m12_reference_research_v1.yaml";

interface RunDetail {
  id: string;
  execution: {
    execution_backend: string | null;
    runtime_fingerprint: { status: string; substrate: string | null; reason: string | null } | null;
  } | null;
}

async function runDetail(page: Page, runId: string): Promise<RunDetail> {
  const response = await page.request.get(`/api/runs/${encodeURIComponent(runId)}`);
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as RunDetail;
}

test("live: 两种执行体在页面上可区分，且都与读面同值", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const declared = await runDetail(page, DECLARED_RUN_ID);
  expect(declared.execution?.execution_backend).toBe("openhands");
  // 指纹只报状态：夹具声明的是未验证 + 原因，不是一个指纹值。
  expect(declared.execution?.runtime_fingerprint?.status).toBe("NOT_VERIFIED");

  const started = await page.request.post("/api/projects/example-project/runs", {
    headers: { "Idempotency-Key": `live-substrate-${String(Date.now())}` },
    data: { protocol_path: FROZEN_PROTOCOL },
  });
  expect(started.ok()).toBeTruthy();
  const run = (await started.json()) as { id: string };
  const startedDetail = await runDetail(page, run.id);
  expect(startedDetail.execution?.execution_backend).toBe("fake");
  expect(startedDetail.execution?.execution_backend).not.toBe(
    declared.execution?.execution_backend,
  );

  await page.goto(`/#/run/timeline?run=${encodeURIComponent(DECLARED_RUN_ID)}`);
  await expect(page.getByTestId("run-execution-backend")).toHaveText("openhands");
  await expect(page.getByTestId("run-runtime-fingerprint")).toContainText("NOT_VERIFIED");

  await page.goto(`/#/run/timeline?run=${encodeURIComponent(run.id)}`);
  await expect(page.getByTestId("run-execution-backend")).toHaveText("fake");
});
