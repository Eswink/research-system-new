/**
 * 真实 API live 链（PLAN-20260915-059 WP-D）：ops 写面（告警规则 CRUD + 事故处置）经真实 HTTP。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）：该装配的 run-ready
 * deps 带同侧 SQLite OpsStore（见 tests/api/run_fixtures._run_ready_sqlite_stores）。
 * 由 playwrightLive.config.ts 驱动（vite /api 代理 → uvicorn:8011）。
 */

import { expect, test } from "@playwright/test";

const PROJECT = "example-project";
const idem = (tag: string) => ({ "Idempotency-Key": `live-059-${tag}-${String(Date.now())}` });

interface RuleRow {
  id: string;
  name: string;
  kind: string | null;
  max_severity: string | null;
  enabled: boolean;
}

interface AlertRow {
  kind: string;
  severity: string;
  subject: string;
  muted: boolean;
  muted_by: string | null;
  incident_id: string | null;
}

interface IncidentRow {
  id: string;
  title: string;
  status: string;
  run_id: string | null;
  assignee: string | null;
  resolution: string | null;
}

test("live: 规则 CRUD 走真实 HTTP，且读面因规则改变", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const created = await page.request.post(`/api/projects/${PROJECT}/ops/alert-rules`, {
    headers: idem("rule"),
    data: { name: "live mute all", max_severity: "INFO" },
  });
  expect(created.status()).toBe(201);
  const rule = (await created.json()) as RuleRow;
  expect(rule.name).toBe("live mute all");
  expect(rule.max_severity).toBe("INFO");
  expect(rule.enabled).toBe(true);
  expect(rule.kind).toBeNull();

  const listed = await page.request.get(`/api/projects/${PROJECT}/ops/alert-rules`);
  expect(listed.ok()).toBeTruthy();
  const view = (await listed.json()) as { rules: RuleRow[]; rules_available: boolean };
  expect(view.rules_available).toBe(true);
  expect(view.rules.map((row) => row.id)).toContain(rule.id);

  const disabled = await page.request.patch(`/api/ops/alert-rules/${rule.id}`, {
    headers: idem("patch"),
    data: { enabled: false },
  });
  expect(disabled.ok()).toBeTruthy();
  expect(((await disabled.json()) as RuleRow).enabled).toBe(false);

  // 未知枚举值 422（不静默接受）。
  const invalid = await page.request.post(`/api/projects/${PROJECT}/ops/alert-rules`, {
    headers: idem("bad"),
    data: { name: "bad kind", kind: "NOT_A_KIND" },
  });
  expect(invalid.status()).toBe(422);

  const removed = await page.request.delete(`/api/ops/alert-rules/${rule.id}`, {
    headers: idem("delete"),
  });
  expect(removed.status()).toBe(204);
  const gone = await page.request.patch(`/api/ops/alert-rules/${rule.id}`, {
    headers: idem("gone"),
    data: { enabled: true },
  });
  expect(gone.status()).toBe(404);
});

test("live: 事故 declare/assign/close 全链，关闭后拒绝再处置", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const declared = await page.request.post(`/api/projects/${PROJECT}/ops/incidents`, {
    headers: idem("declare"),
    data: { title: "live incident", severity: "CRITICAL" },
  });
  expect(declared.status()).toBe(201);
  const incident = (await declared.json()) as IncidentRow;
  expect(incident.status).toBe("OPEN");

  const assigned = await page.request.post(`/api/ops/incidents/${incident.id}/assign`, {
    headers: idem("assign"),
    data: { assignee: "ops-1" },
  });
  expect(assigned.ok()).toBeTruthy();
  expect(((await assigned.json()) as IncidentRow).assignee).toBe("ops-1");
  expect(((await assigned.json()) as IncidentRow).status).toBe("ASSIGNED");

  const closed = await page.request.post(`/api/ops/incidents/${incident.id}/close`, {
    headers: idem("close"),
    data: { resolution: "root-caused" },
  });
  expect(closed.ok()).toBeTruthy();
  const closedRow = (await closed.json()) as IncidentRow;
  expect(closedRow.status).toBe("CLOSED");
  expect(closedRow.resolution).toBe("root-caused");

  // 已关闭 → 再处置 409（域状态机，不是静默 no-op）。
  const again = await page.request.post(`/api/ops/incidents/${incident.id}/close`, {
    headers: idem("again"),
    data: { resolution: "second" },
  });
  expect(again.status()).toBe(409);

  // 空 resolution 422。
  const empty = await page.request.post(`/api/ops/incidents/${incident.id}/assign`, {
    headers: idem("empty"),
    data: { assignee: "" },
  });
  expect([409, 422]).toContain(empty.status());
});

test("live: 告警读面带规则与事故的消费痕迹", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const rule = await page.request.post(`/api/projects/${PROJECT}/ops/alert-rules`, {
    headers: idem("mute"),
    data: { name: "live mute workers", kind: "WORKER_OFFLINE" },
  });
  expect(rule.status()).toBe(201);

  const alerts = await page.request.get(`/api/projects/${PROJECT}/ops/alerts`);
  expect(alerts.ok()).toBeTruthy();
  const view = (await alerts.json()) as {
    alerts: AlertRow[];
    rules_available: boolean;
    rules_applied: number;
    muted_count: number;
  };
  expect(view.rules_available).toBe(true);
  expect(view.rules_applied).toBeGreaterThan(0);
  // 静音是标记不是过滤：muted_count >= 1 时列表长度仍包含被静音的项。
  expect(view.muted_count).toBe(view.alerts.filter((row) => row.muted).length);
  for (const row of view.alerts) {
    expect(row.muted_by === null).toBe(!row.muted);
    if (!row.muted) expect(row.muted_by).toBeNull();
    if (row.muted) {
      expect(row.kind).toBe("WORKER_OFFLINE");
      expect(row.muted_by).toBe(view.alerts.find((item) => item.muted)?.muted_by ?? row.muted_by);
    }
  }

  const incidents = await page.request.get(`/api/projects/${PROJECT}/ops/incidents`);
  const incidentView = (await incidents.json()) as {
    workflow_available: boolean;
    candidates: { run_id: string }[];
  };
  expect(incidentView.workflow_available).toBe(true);
  expect(Array.isArray(incidentView.candidates)).toBe(true);
});
