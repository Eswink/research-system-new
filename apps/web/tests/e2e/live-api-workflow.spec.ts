/**
 * 真实 FastAPI HTTP + 浏览器集成测试（PLAN-20260908-034 T30 + PLAN-20260910-037 WP-Z）。
 *
 * 前端经 vite dev（/api 代理到 8011）加载，后端为 tests/api/console_api_app
 * （Fake Ports：run 执行体受控、无真实凭据/付费 LLM）。覆盖：模板同源预检、
 * 草稿校验/保存/修订预检与启动、Run 启动与事件 replay、artifact 只读链、
 * 成本日序列、通知投影、human-gate 审批暂停与续跑、memory 门链 422。
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

test("live: 草稿修订预检与启动（WP-B 主链）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const create = await page.request.post("/api/projects/example-project/protocol-drafts", {
    headers: { "Idempotency-Key": `live-wpb-${String(Date.now())}` },
    data: { name: "wpb draft", yaml_text: VALID_DRAFT },
  });
  expect(create.status()).toBe(201);
  const draft = (await create.json()) as { draft_id: string; revision: number };
  const ref = { draft_id: draft.draft_id, draft_revision: draft.revision };
  const compiled = await page.request.post("/api/protocols/validate", { data: ref });
  expect(compiled.ok()).toBeTruthy();
  const compile = await page.request.post("/api/projects/example-project/compile", {
    data: ref,
  });
  expect(compile.ok()).toBeTruthy();
  const started = await page.request.post("/api/projects/example-project/runs", {
    headers: { "Idempotency-Key": `live-wpb-run-${String(Date.now())}` },
    data: ref,
  });
  expect(started.ok()).toBeTruthy();
  const run = (await started.json()) as { id: string; state: string };
  expect(run.state).not.toBe("WAITING_FOR_APPROVAL");
});

test("live: artifact 列表与日序列/通知投影（WP-C/D/G 只读链）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const daily = await page.request.get("/api/cost/daily");
  expect(daily.ok()).toBeTruthy();
  const series = (await daily.json()) as { days: unknown[]; truncated: boolean };
  expect(Array.isArray(series.days)).toBe(true);
  // m12 参考协议在受控 pin/health 下 freeze 成功（manifest.frozen 事件可投影）
  const started = await page.request.post("/api/projects/example-project/runs", {
    headers: { "Idempotency-Key": `live-z-run-${String(Date.now())}` },
    data: { protocol_path: "m12_reference_research_v1.yaml" },
  });
  expect(started.ok()).toBeTruthy();
  const notifications = await page.request.get("/api/notifications");
  expect(notifications.ok()).toBeTruthy();
  const noteView = (await notifications.json()) as {
    notifications: { type: string; run_id: string | null }[];
    note: string;
  };
  expect(noteView.notifications.some((item) => item.type === "manifest.frozen")).toBe(true);
  const runId = ((await started.json()) as { id: string }).id;
  const artifacts = await page.request.get(`/api/runs/${runId}/artifacts`);
  expect(artifacts.ok()).toBeTruthy();
  const ghost = await page.request.get("/api/runs/ghost/artifacts");
  expect(ghost.status()).toBe(404);
});

test("live: human-gate 审批暂停与续跑（WP-H 主链）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const start = await page.request.post("/api/projects/example-project/runs", {
    headers: { "Idempotency-Key": `live-wph-${String(Date.now())}` },
    data: { protocol_path: "human_gate_demo_v1.yaml" },
  });
  expect(start.ok()).toBeTruthy();
  const run = (await start.json()) as { id: string; state: string };
  expect(run.state).toBe("WAITING_FOR_APPROVAL");
  const approvals = (await (
    await page.request.get("/api/approvals")
  ).json()) as { id: string; run_id: string; status: string; version: string }[];
  const mine = approvals.find((item) => item.run_id === run.id);
  expect(mine?.status).toBe("PENDING");
  const approvalId = mine?.id ?? "missing-approval";
  const decided = await page.request.post(`/api/approvals/${approvalId}/decide`, {
    headers: {
      "If-Match": mine?.version ?? "",
      "Idempotency-Key": `live-wph-d-${String(Date.now())}`,
    },
    data: { decision: "approve" },
  });
  expect(decided.ok()).toBeTruthy();
  const after = (await (await page.request.get(`/api/runs/${run.id}`)).json()) as {
    state: string;
  };
  expect(["SUCCEEDED", "FAILED"]).toContain(after.state);
});

test("live: memory 门链——未知 provenance 422 且不入账（WP-F）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const listed = await page.request.get("/api/projects/example-project/memory");
  expect(listed.ok()).toBeTruthy();
  const rejected = await page.request.post("/api/memory/proposals", {
    headers: { "Idempotency-Key": `live-wpf-${String(Date.now())}` },
    data: {
      tier: "SESSION",
      kind: "FACT",
      content: "unproven claim",
      provenance: "paper://not-registered",
      confidence: 0.9,
      curator_approved: false,
    },
  });
  expect(rejected.status()).toBe(422);
  const after = (await (
    await page.request.get("/api/projects/example-project/memory")
  ).json()) as { records: unknown[] };
  expect(after.records.length).toBe(0);
});
