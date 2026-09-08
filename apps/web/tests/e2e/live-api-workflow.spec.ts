/**
 * 真实 FastAPI HTTP + 浏览器集成测试（PLAN-20260908-034 T30）。
 *
 * 前端经 vite dev（/api 代理到 8011）加载，后端为 tests/api/console_api_app
 * （Fake Ports：run 执行体受控、无真实凭据/付费 LLM）。覆盖：模板同源预检、
 * 草稿校验/保存、Run 启动与事件 replay。
 */

import { expect, test } from "@playwright/test";

const VALID_DRAFT = [
  "id: live_research_v1_0_0",
  "version: 1.0.0",
  "phases:",
  "  - id: execution",
  "    strategy: single_agent",
  "    required_roles:",
  "      - {role: experiment_engineer, min_instances: 1, max_instances: 1}",
  "    task_contract: live_execution",
  "    timeout_seconds: 120",
].join("\n");

test("live: 模板目录与受控模板同源预检", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const templates = await page.request.get("/api/protocol-templates");
  expect(templates.ok()).toBeTruthy();
  const body = (await templates.json()) as { source: string }[];
  expect(body.length).toBeGreaterThan(0);
  // compile/preflight 接受相对 protocols 目录的文件名（模板 source 去前缀）
  const source = (body[0]?.source ?? "").replace(/^examples\/protocols\//, "");
  const preflight = await page.request.post("/api/projects/example-project/compile", {
    data: { path: source },
  });
  expect(preflight.ok()).toBeTruthy();
  const report = (await preflight.json()) as { status: string };
  expect(["PASS", "WARN", "FAIL"]).toContain(report.status);
});

test("live: 草稿校验零副作用 + 保存产生修订", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const validate = await page.request.post("/api/protocol-drafts/validate", {
    data: { yaml_text: VALID_DRAFT },
  });
  expect(validate.ok()).toBeTruthy();
  const result = (await validate.json()) as { ok: boolean; phase_count: number };
  expect(result.ok).toBe(true);
  expect(result.phase_count).toBe(1);

  const create = await page.request.post("/api/projects/example-project/protocol-drafts", {
    headers: { "Idempotency-Key": "live-create-1" },
    data: { name: "live draft", yaml_text: VALID_DRAFT },
  });
  expect(create.status()).toBe(201);
  const draft = (await create.json()) as { draft_id: string; revision: number };
  expect(draft.revision).toBe(1);
});

test("live: 启动运行并读取事件 replay", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const templates = await page.request.get("/api/protocol-templates");
  const source = ((await templates.json()) as { source: string }[])[0]?.source ?? "";
  const start = await page.request.post("/api/projects/example-project/runs", {
    headers: { "Idempotency-Key": "live-run-1" },
    data: { protocol_path: source.replace(/^examples\/protocols\//, "") },
  });
  expect(start.ok()).toBeTruthy();
  const run = (await start.json()) as { id: string; state: string };
  expect(run.id).toBeTruthy();

  const events = await page.request.get(`/api/runs/${run.id}/events`);
  expect(events.ok()).toBeTruthy();
  const frames = (await events.json()) as { type: string }[];
  expect(Array.isArray(frames)).toBe(true);
});
