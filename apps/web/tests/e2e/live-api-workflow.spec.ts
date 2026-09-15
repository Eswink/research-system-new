/**
 * 真实 FastAPI HTTP + 浏览器集成测试（PLAN-20260908-034 T30 + PLAN-20260910-037 WP-Z）。
 *
 * 前端经 vite dev（/api 代理到 8011）加载，后端为 tests/api/console_api_app
 * （Fake Ports：run 执行体受控、无真实凭据/付费 LLM）。覆盖：模板同源预检、
 * 草稿校验/保存/修订预检与启动、Run 启动与事件 replay、artifact 只读链、
 * 成本日序列、通知投影、human-gate 审批暂停与续跑、memory 门链 422，
 * 以及 PLAN-040 WP-D 控制面（health / custom role / clone / DELETE 链 /
 * run 审批历史 / 实验双支持）。
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

const CUSTOM_ROLE = (id: string): Record<string, unknown> => ({
  id,
  role_type: "analysis",
  category: "evaluation",
  default_model_profile: "research_strong",
  activation_default: "ON_DEMAND",
  requested_capabilities: ["analysis.read"],
  hard_model_capabilities: { all_of: ["function_calling"], any_of: [] },
  workspace_policy: "read_only",
});

function idem(prefix: string): Record<string, string> {
  return { "Idempotency-Key": `${prefix}-${String(Date.now())}-${String(Math.random())}` };
}

test("live: health 组成摘要（WP-A）", async ({ page }) => {
  const response = await page.request.get("/api/health");
  expect(response.ok()).toBeTruthy();
  const health = (await response.json()) as Record<string, unknown>;
  expect(health.status).toBe("ok");
  expect(health.composition).toBe("sqlite");
  expect(typeof health.pricing_degraded).toBe("boolean");
});

test("live: custom role → clone → agent 删除链（WP-B）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const roleId = `live_role_${String(Date.now())}`;
  const created = await page.request.post("/api/roles/custom", {
    headers: idem("live-role"),
    data: CUSTOM_ROLE(roleId),
  });
  expect(created.status()).toBe(201);
  const roleIds = ((await (await page.request.get("/api/roles")).json()) as {
    id: string;
  }[]).map((role) => role.id);
  expect(roleIds).toContain(roleId);
  const conflict = await page.request.post("/api/roles/custom", {
    headers: idem("live-role-2"),
    data: CUSTOM_ROLE(roleId),
  });
  expect(conflict.status()).toBe(409);

  const cloneId = `live_clone_${String(Date.now())}`;
  const clone = await page.request.post("/api/agents/director/clone", {
    headers: idem("live-clone"),
    data: { new_id: cloneId },
  });
  expect(clone.status()).toBe(201);
  const removed = await page.request.delete(`/api/agents/${cloneId}`, {
    headers: idem("live-del"),
  });
  expect(removed.status()).toBe(204);
  expect(
    (
      (await (await page.request.get("/api/projects/example-project/agents")).json()) as {
        id: string;
      }[]
    ).map((agent) => agent.id),
  ).not.toContain(cloneId);
});

test("live: 项目设置参考协议 + 实验双支持 + 审批历史 404 gate（WP-A/B/C）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const settings = (await (
    await page.request.get("/api/projects/example-project/settings")
  ).json()) as Record<string, unknown>;
  // 参考协议字段存在且为字符串（来源 project.yaml 的加载链由后端单测锁定；
  // 此处不硬编码具体值，避免与同进程内先前 PUT 的持久化顺序耦合）。
  expect(typeof settings.reference_protocol).toBe("string");

  const saved = await page.request.put("/api/projects/example-project/settings", {
    headers: idem("live-settings"),
    data: { ...settings, reference_protocol: "sort_analysis_v1.yaml" },
  });
  expect(saved.ok()).toBeTruthy();
  expect(((await saved.json()) as Record<string, unknown>).reference_protocol).toBe(
    "sort_analysis_v1.yaml",
  );
  // 恢复原值，避免同进程后续用例读到被本测试改写的持久设置。
  const restore = await page.request.put("/api/projects/example-project/settings", {
    headers: idem("live-settings-restore"),
    data: settings,
  });
  expect(restore.ok()).toBeTruthy();

  const plan = await page.request.post("/api/projects/example-project/experiments", {
    headers: idem("live-exp"),
    data: { name: "live pre-registration", hypothesis: "policy improves p50" },
  });
  expect(plan.status()).toBe(201);
  const planId = ((await plan.json()) as { id: string }).id;
  const archived = await page.request.post(`/api/experiments/${planId}/archive`, {
    headers: idem("live-exp-archive"),
    data: {},
  });
  expect(archived.ok()).toBeTruthy();

  const history = await page.request.get("/api/runs/no-such-run/approvals");
  expect(history.status()).toBe(404);
  const workers = (await (await page.request.get("/api/cluster/workers")).json()) as {
    workers: unknown[];
  };
  expect(Array.isArray(workers.workers)).toBe(true);
});

test("live: 项目注册表与归属（WP-C cycle 1）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const defaultList = (await (await page.request.get("/api/projects")).json()) as {
    id: string;
    name: string;
    status: string;
  }[];
  const primary = defaultList.find((item) => item.id === "example-project");
  expect(primary?.id).toBe("example-project");
  expect(primary?.name).toBe("Example ML Research");

  const created = await page.request.post("/api/projects", {
    headers: idem("live-project"),
    data: { name: "Live Registry Study" },
  });
  expect(created.status()).toBe(201);
  const projectId = ((await created.json()) as { id: string }).id;
  const listed = (await (await page.request.get("/api/projects")).json()) as { id: string }[];
  expect(listed.map((item) => item.id)).toContain(projectId);

  // 新注册项目自动带默认设置行（可编辑，不伪装未配置）。
  const settings = await page.request.get(`/api/projects/${projectId}/settings`);
  expect(settings.ok()).toBeTruthy();
  expect(((await settings.json()) as Record<string, unknown>).project_id).toBe(projectId);

  // 草稿按项目归属：新项目可见、其它项目不可见。
  const draft = await page.request.post(`/api/projects/${projectId}/protocol-drafts`, {
    headers: idem("live-project-draft"),
    data: { name: "scoped draft", yaml_text: VALID_DRAFT },
  });
  expect(draft.status()).toBe(201);
  const scoped = (await (
    await page.request.get(`/api/projects/${projectId}/protocol-drafts`)
  ).json()) as unknown[];
  expect(scoped.length).toBe(1);
  const other = (await (
    await page.request.get("/api/projects/example-project/protocol-drafts")
  ).json()) as { draft_id: string }[];
  expect(other.map((item) => item.draft_id)).not.toContain(
    ((await draft.json()) as { draft_id: string }).draft_id,
  );

  // 归档语义（无 DELETE）；幽灵项目仍 404。
  const archived = await page.request.patch(`/api/projects/${projectId}`, {
    headers: idem("live-project-archive"),
    data: { status: "ARCHIVED" },
  });
  expect(((await archived.json()) as { status: string }).status).toBe("ARCHIVED");
  expect((await page.request.get("/api/projects/ghost-project/settings")).status()).toBe(404);
});

test("live: reports/integrations/lineage 只读面（EC-02）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  // tool-providers: catalog 只读投影 + 三态健康（PLAN-060 起治理写面在注册表端点）。
  const providers = await page.request.get("/api/tool-providers");
  expect(providers.ok()).toBeTruthy();
  const catalog = (await providers.json()) as {
    providers: { id: string; kind: string; health: string }[];
    management_available: boolean;
  };
  expect(catalog.providers.length).toBeGreaterThan(0);
  expect(catalog.providers.some((item) => item.kind === "NATIVE")).toBe(true);
  expect(catalog.management_available).toBe(true);

  // Start a run so the run-scoped read-only endpoints have a real target.
  const templates = await page.request.get("/api/protocol-templates");
  const source = ((await templates.json()) as { source: string }[])[0]?.source ?? "";
  const start = await page.request.post("/api/projects/example-project/runs", {
    headers: idem("live-ec02"),
    data: { protocol_path: source.replace(/^examples\/protocols\//, "") },
  });
  expect(start.ok()).toBeTruthy();
  const runId = ((await start.json()) as { id: string }).id;

  // deliverable: 无产物时 available=false（诚实空态，不生成空报告）。
  const deliverable = await page.request.get(`/api/runs/${runId}/deliverable`);
  expect(deliverable.ok()).toBeTruthy();
  const report = (await deliverable.json()) as { available: boolean; deliverable: unknown };
  expect(typeof report.available).toBe("boolean");
  if (!report.available) expect(report.deliverable).toEqual({});

  // lineage: nodes/edges 为数组且全局血缘恒不可用（G9）。
  const lineage = await page.request.get(`/api/runs/${runId}/lineage`);
  expect(lineage.ok()).toBeTruthy();
  const graph = (await lineage.json()) as {
    nodes: unknown[];
    edges: unknown[];
    global_lineage_available: boolean;
  };
  expect(Array.isArray(graph.nodes)).toBe(true);
  expect(Array.isArray(graph.edges)).toBe(true);
  expect(graph.global_lineage_available).toBe(false);

  // 未知 run 的只读端点 404（不伪装空成功）。
  expect((await page.request.get("/api/runs/ghost-run/lineage")).status()).toBe(404);
  expect((await page.request.get("/api/runs/ghost-run/deliverable")).status()).toBe(404);
});

test("live: library 库目录创建/过滤/归档（EC-03 第一批）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const created = await page.request.post("/api/projects/example-project/library", {
    headers: idem("live-lib"),
    data: { kind: "prompt", name: "live prompt", description: "d", tags: ["x"] },
  });
  expect(created.status()).toBe(201);
  const resource = (await created.json()) as {
    id: string;
    kind: string;
    project_id: string;
    status: string;
  };
  expect(resource.kind).toBe("prompt");
  expect(resource.project_id).toBe("example-project");
  expect(resource.status).toBe("ACTIVE");

  // kind 过滤：prompt 列表含之，dataset 列表不含。
  const prompts = (await (
    await page.request.get("/api/projects/example-project/library?kind=prompt")
  ).json()) as { id: string }[];
  expect(prompts.map((item) => item.id)).toContain(resource.id);
  const datasets = (await (
    await page.request.get("/api/projects/example-project/library?kind=dataset")
  ).json()) as { id: string }[];
  expect(datasets.map((item) => item.id)).not.toContain(resource.id);

  // 归档幂等（归档非删除）；未知 id 404。
  const archived = await page.request.patch(`/api/library/${resource.id}`, {
    headers: idem("live-lib-archive"),
    data: { status: "ARCHIVED" },
  });
  expect(archived.status()).toBe(200);
  expect(((await archived.json()) as { status: string }).status).toBe("ARCHIVED");
  expect((await page.request.get("/api/library/ghost-resource")).status()).toBe(404);

  // 幽灵项目写入 404（不伪装归属）。
  const ghost = await page.request.post("/api/projects/ghost-project/library", {
    headers: idem("live-lib-ghost"),
    data: { kind: "prompt", name: "x" },
  });
  expect(ghost.status()).toBe(404);
});

test("live: ops 只读投影（EC-03 第二批）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  // schedules：进程内 4 个守护 scheduler 配置事实；管理面诚实锁定。
  const schedules = await page.request.get("/api/ops/schedules");
  expect(schedules.ok()).toBeTruthy();
  const scheduleView = (await schedules.json()) as {
    schedules: { name: string; interval_seconds: number }[];
    management_available: boolean;
  };
  const names = scheduleView.schedules.map((item) => item.name);
  expect(names).toContain("lease_recovery");
  expect(names).toContain("outbox_relay");
  expect(scheduleView.management_available).toBe(false);

  // alerts：派生收件箱 + 规则写面（PLAN-059 起 store 同侧装配 ⇒ 规则可用）。
  const alerts = await page.request.get("/api/projects/example-project/ops/alerts");
  expect(alerts.ok()).toBeTruthy();
  const alertView = (await alerts.json()) as { alerts: unknown[]; rules_available: boolean };
  expect(Array.isArray(alertView.alerts)).toBe(true);
  expect(alertView.rules_available).toBe(true);

  // incidents：已登记列表 + 失败 Run 候选；处置写面可用（细节见 live-ops-write.spec.ts）。
  const incidents = await page.request.get("/api/projects/example-project/ops/incidents");
  expect(incidents.ok()).toBeTruthy();
  const incidentView = (await incidents.json()) as {
    incidents: unknown[];
    candidates: unknown[];
    workflow_available: boolean;
  };
  expect(Array.isArray(incidentView.incidents)).toBe(true);
  expect(Array.isArray(incidentView.candidates)).toBe(true);
  expect(incidentView.workflow_available).toBe(true);

  // data-health：端点计数可见；聚合报告锁定。
  const health = await page.request.get("/api/projects/example-project/ops/data-health");
  expect(health.ok()).toBeTruthy();
  const healthView = (await health.json()) as {
    metrics: { metric: string }[];
    aggregate_available: boolean;
  };
  expect(healthView.metrics.map((item) => item.metric)).toContain("endpoints_total");
  expect(healthView.aggregate_available).toBe(false);

  // 未知项目 404（不伪装空成功）。
  expect((await page.request.get("/api/projects/ghost-project/ops/alerts")).status()).toBe(404);
});

test("live: 预算调整走账本 + 预留-消耗预测（EC-04 第一批）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const started = await page.request.post("/api/projects/example-project/runs", {
    headers: { "Idempotency-Key": `live-046-${String(Date.now())}` },
    data: { protocol_path: "m12_reference_research_v1.yaml" },
  });
  expect(started.ok()).toBeTruthy();
  const runId = ((await started.json()) as { id: string }).id;

  // preflight 预留经冻结 manifest 的 ref 归属到该 run（不是按作用域猜）。
  const before = await page.request.get(`/api/runs/${runId}/cost-forecast`);
  expect(before.ok()).toBeTruthy();
  const forecast = (await before.json()) as {
    lines: { reserved: number }[];
    attribution: string;
    forecast_scope: string;
    scope_note: string;
  };
  expect(forecast.lines.some((line) => line.reserved > 0)).toBe(true);
  expect(forecast.attribution).toBe("RESERVATION_REF");
  expect(forecast.forecast_scope).toBe("RESERVED_ONLY");
  expect(forecast.scope_note).toContain("not extrapolated");

  // 调整：release 既有预留 + reserve 新额度；预测随之更新。
  const adjusted = await page.request.post(`/api/runs/${runId}/interventions`, {
    headers: { "Idempotency-Key": `live-046-adjust-${String(Date.now())}` },
    data: {
      kind: "budget_adjust",
      adjustments: [{ resource_type: "MODEL_TOKENS", quantity: 5000, unit: "tokens" }],
    },
  });
  expect(adjusted.ok()).toBeTruthy();
  const outcome = (await adjusted.json()) as { released_ref: string | null };
  expect(outcome.released_ref).not.toBeNull();
  const after = (await (
    await page.request.get(`/api/runs/${runId}/cost-forecast`)
  ).json()) as { lines: { resource_type: string; reserved: number }[] };
  expect(after.lines.find((line) => line.resource_type === "MODEL_TOKENS")?.reserved).toBe(5000);
  expect((await page.request.get("/api/runs/ghost/cost-forecast")).status()).toBe(404);

  // 语义变更（换 Agent/协议）不在此处伪装：replace_agent 仍诚实 501。
  const semantic = await page.request.post(`/api/runs/${runId}/interventions`, {
    headers: { "Idempotency-Key": `live-046-semantic-${String(Date.now())}` },
    data: { kind: "replace_agent" },
  });
  expect(semantic.status()).toBe(501);
});

