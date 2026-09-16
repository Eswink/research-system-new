/**
 * ops 读/写替身路由（G7 / PLAN-20260915-059；从 stub-routes.ts 拆出以守 450 行硬上限）。
 *
 * 写面用**模块级可变状态**：e2e 要验证"写了之后读面真的变了"（规则静音、
 * 事故登记后候选减一），静态响应无法表达这个因果，因此这里按需可变。
 * 每个用例开始前由 resetOpsStub() 复位。
 */

import type { StubRoute } from "./stub-routes";

interface StubRule {
  id: string;
  project_id: string;
  name: string;
  kind: string | null;
  max_severity: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

interface StubIncident {
  id: string;
  title: string;
  severity: string;
  status: string;
  run_id: string | null;
  assignee: string | null;
  resolution: string | null;
  opened_at: string;
  updated_at: string;
  closed_at: string | null;
}

const NOW = "2026-09-16T00:00:00Z";

let rules: StubRule[] = [];
let incidents: StubIncident[] = [];
let seq = 0;

/** 每个用例前复位（stub 状态跨用例会串味）。 */
export function resetOpsStub(): void {
  rules = [
    {
      id: "rule-1",
      project_id: "example-project",
      name: "known worker churn",
      kind: "WORKER_OFFLINE",
      max_severity: "WARNING",
      enabled: true,
      created_at: NOW,
      updated_at: NOW,
    },
  ];
  incidents = [];
  // 种子规则已占用 rule-1：新建从 rule-2 起，避免 id 撞车（撞车会静默改到种子上）。
  seq = 1;
}

function nextId(prefix: string): string {
  seq += 1;
  return `${prefix}-${String(seq)}`;
}

function severityRank(severity: string): number {
  return { CRITICAL: 0, WARNING: 1, INFO: 2 }[severity] ?? 3;
}

/** 规则命中只打静音标记：kind / max_severity 为空即"不限"。 */
function mutedBy(kind: string, severity: string): string | null {
  for (const rule of rules) {
    if (!rule.enabled) continue;
    if (rule.kind !== null && rule.kind !== kind) continue;
    if (rule.max_severity !== null && severityRank(severity) > severityRank(rule.max_severity)) {
      continue;
    }
    return rule.id;
  }
  return null;
}

const ALERTS = [
  {
    kind: "RUN_FAILED",
    severity: "CRITICAL",
    subject: "run-stub-failed",
    detail: "run run-stub-failed is FAILED",
  },
  {
    kind: "WORKER_OFFLINE",
    severity: "WARNING",
    subject: "worker-2",
    detail: "worker worker-2 is OFFLINE",
  },
];

function alertsBody() {
  const alerts = ALERTS.map((alert) => {
    const muted = mutedBy(alert.kind, alert.severity);
    const incident = incidents.find(
      (item) => item.run_id === alert.subject && item.status !== "CLOSED",
    );
    return { ...alert, muted: muted !== null, muted_by: muted, incident_id: incident?.id ?? null };
  });
  return {
    alerts,
    rules_available: true,
    rules_reason: null,
    rules_applied: rules.length,
    muted_count: alerts.filter((alert) => alert.muted).length,
  };
}

function incidentsBody() {
  const registered = new Set(incidents.map((item) => item.run_id));
  const candidates = [
    {
      run_id: "run-stub-failed",
      protocol_id: "proto-stub",
      state: "FAILED",
      updated_at: NOW,
    },
  ].filter((row) => !registered.has(row.run_id));
  return {
    incidents,
    candidates,
    workflow_available: true,
    workflow_reason: null,
  };
}

const ruleRow = (raw: Record<string, unknown>, id: string): StubRule => ({
  id,
  project_id: "example-project",
  name: String(raw.name ?? ""),
  kind: (raw.kind as string | null) ?? null,
  max_severity: (raw.max_severity as string | null) ?? null,
  enabled: raw.enabled !== false,
  created_at: NOW,
  updated_at: NOW,
});

const incidentRow = (raw: Record<string, unknown>, id: string): StubIncident => ({
  id,
  title: String(raw.title ?? ""),
  severity: String(raw.severity ?? "WARNING"),
  status: "OPEN",
  run_id: (raw.run_id as string | null) ?? null,
  assignee: null,
  resolution: null,
  opened_at: NOW,
  updated_at: NOW,
  closed_at: null,
});

function patchRule(id: string, raw: Record<string, unknown>): StubRule | null {
  const current = rules.find((item) => item.id === id);
  if (current === undefined) return null;
  const patched: StubRule = {
    ...current,
    name: raw.name === undefined ? current.name : String(raw.name),
    kind: raw.clear_kind === true ? null : ((raw.kind as string | null) ?? current.kind),
    max_severity:
      raw.clear_max_severity === true
        ? null
        : ((raw.max_severity as string | null) ?? current.max_severity),
    enabled: raw.enabled === undefined ? current.enabled : raw.enabled === true,
    updated_at: NOW,
  };
  rules = rules.map((item) => (item.id === id ? patched : item));
  return patched;
}

function transition(
  id: string,
  apply: (incident: StubIncident) => StubIncident,
): { status: number; body: unknown } {
  const current = incidents.find((item) => item.id === id);
  if (current === undefined) return { status: 404, body: { title: "Incident Not Found" } };
  if (current.status === "CLOSED") return { status: 409, body: { title: "Incident Closed" } };
  const next = apply(current);
  incidents = incidents.map((item) => (item.id === id ? next : item));
  return { status: 200, body: next };
}

export const OPS_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/projects\/[^/]+\/ops\/alerts$/,
    handler: () => ({ status: 200, body: alertsBody() }),
  },
  {
    method: "GET",
    pattern: /^\/projects\/[^/]+\/ops\/incidents$/,
    handler: () => ({ status: 200, body: incidentsBody() }),
  },
  {
    method: "POST",
    pattern: /^\/projects\/[^/]+\/ops\/incidents$/,
    handler: (_url, body) => {
      const incident = incidentRow((body ?? {}) as Record<string, unknown>, nextId("inc"));
      incidents = [...incidents, incident];
      return { status: 201, body: incident };
    },
  },
  {
    method: "POST",
    pattern: /^\/ops\/incidents\/[^/]+\/assign$/,
    handler: (url, body) => {
      const id = url.pathname.split("/").at(-2) ?? "";
      const assignee = String(((body ?? {}) as Record<string, unknown>).assignee ?? "");
      return transition(id, (incident) => ({
        ...incident,
        status: "ASSIGNED",
        assignee,
        updated_at: NOW,
      }));
    },
  },
  {
    method: "POST",
    pattern: /^\/ops\/incidents\/[^/]+\/close$/,
    handler: (url, body) => {
      const id = url.pathname.split("/").at(-2) ?? "";
      const resolution = String(((body ?? {}) as Record<string, unknown>).resolution ?? "");
      return transition(id, (incident) => ({
        ...incident,
        status: "CLOSED",
        resolution,
        closed_at: NOW,
        updated_at: NOW,
      }));
    },
  },
  {
    method: "GET",
    pattern: /^\/projects\/[^/]+\/ops\/alert-rules$/,
    handler: () => ({
      status: 200,
      body: { rules, rules_available: true, rules_reason: null },
    }),
  },
  {
    method: "POST",
    pattern: /^\/projects\/[^/]+\/ops\/alert-rules$/,
    handler: (_url, body) => {
      if (rules.some((item) => item.name === String((body as Record<string, unknown>).name))) {
        return { status: 409, body: { title: "Duplicate Rule" } };
      }
      const rule = ruleRow((body ?? {}) as Record<string, unknown>, nextId("rule"));
      rules = [...rules, rule];
      return { status: 201, body: rule };
    },
  },
  {
    method: "PATCH",
    pattern: /^\/ops\/alert-rules\/[^/]+$/,
    handler: (url, body) => {
      const id = url.pathname.split("/").at(-1) ?? "";
      const patched = patchRule(id, (body ?? {}) as Record<string, unknown>);
      return patched === null
        ? { status: 404, body: { title: "Alert Rule Not Found" } }
        : { status: 200, body: patched };
    },
  },
  {
    method: "DELETE",
    pattern: /^\/ops\/alert-rules\/[^/]+$/,
    handler: (url) => {
      const id = url.pathname.split("/").at(-1) ?? "";
      if (!rules.some((item) => item.id === id)) {
        return { status: 404, body: { title: "Alert Rule Not Found" } };
      }
      rules = rules.filter((item) => item.id !== id);
      return { status: 204, body: null };
    },
  },
  {
    method: "GET",
    pattern: /^\/projects\/[^/]+\/ops\/data-health$/,
    handler: () => ({
      status: 200,
      body: {
        metrics: [{ metric: "endpoints_total", value: "0", status: "INFO" }],
        aggregate_available: false,
        aggregate_reason: "no aggregate report API",
      },
    }),
  },
];
