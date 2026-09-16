/**
 * Tool Provider 注册面替身（G15 / PLAN-20260915-060 EC-05）。
 *
 * 与真后端同一因果：目录（GET /tool-providers）只含 examples 契约 + **已批准**
 * 注册；PENDING 与 REVOKED 不出现。静态替身无法表达"批准后才进目录"，因此
 * 这里用模块级可变状态，`resetRegistryStub()` 在每个用例前复位。
 */

import type { StubRoute } from "./stub-routes";

interface StubRegistration {
  id: string;
  kind: string;
  state: string;
  trust_level: string;
  capabilities: string[];
  effect_class: string;
  pinned_revision: string;
  transport: string | null;
  protocol_version: string | null;
  network_domains: string[];
  health_check: boolean;
  registered_at: string;
  updated_at: string;
  approved_at: string | null;
  revoked_at: string | null;
  revoked_reason: string | null;
  last_health: string | null;
  health_detail: string | null;
  health_checked_at: string | null;
  last_schema_digest: string | null;
  schema_baseline_digest: string | null;
  schema_drift: boolean;
  schema_drift_since: string | null;
  /** 端点绑定三态（PLAN-072）：替身只回事实，判定在服务端。 */
  endpoint_binding: {
    state: string;
    env_name: string | null;
    endpoint_digest: string | null;
  };
  /** 凭据存在性判定（PLAN-074）：替身只回事实，判定在服务端；凭据值不进读面。 */
  credential_binding: {
    state: string;
    credential_ref: string | null;
    present: boolean;
  };
  catalog_active: boolean;
}

/** 下一次 health-check 要回的 schema 事实（用例可编排"有漂移/无漂移"两种形态）。
 *
 * 替身**不重新实现**漂移判定（那是域的口径，由 tests/api 覆盖）：它只负责把用例
 * 指定的 DTO 事实回给前端，用来证明 console **渲染**了这些字段。
 */
export interface HealthScript {
  status: string;
  detail: string;
  lastSchemaDigest: string | null;
  baselineDigest: string | null;
  drift: boolean;
}

let healthScript: HealthScript | null = null;

/** 编排下一次健康复核的返回形态；不调用则回默认的诚实 UNKNOWN（无 digest）。 */
export function scriptHealthCheck(script: HealthScript): void {
  healthScript = script;
}

/** 有漂移的那次复核（用例最常用的一种编排）。 */
export function scriptSchemaDrift(baseline: string, current: string): void {
  scriptHealthCheck({
    status: "HEALTHY",
    detail: "scripted probe",
    lastSchemaDigest: current,
    baselineDigest: baseline,
    drift: true,
  });
}

/** 无漂移的那次复核（对照组）。 */
export function scriptSchemaStable(digest: string): void {
  scriptHealthCheck({
    status: "HEALTHY",
    detail: "scripted probe",
    lastSchemaDigest: digest,
    baselineDigest: digest,
    drift: false,
  });
}

const NOW = "2026-09-16T00:00:00Z";

const BASE_PROVIDERS = [
  {
    id: "openhands_workspace",
    kind: "NATIVE",
    trust_level: "BUILT_IN",
    effect_class: "EXECUTE",
    capabilities: ["workspace.read", "workspace.write.notes"],
    transport: null,
    protocol_version: null,
    network_domains: [],
    health_check: false,
    health: "HEALTHY",
  },
];

let registrations: StubRegistration[] = [];

/** 每个用例前复位（注册状态跨用例会串味）。 */
export function resetRegistryStub(): void {
  registrations = [];
  healthScript = null;
}

const TRUST: Record<string, string> = {
  PENDING: "UNTRUSTED",
  ACTIVE: "USER_APPROVED",
  REVOKED: "REVOKED",
};

function catalogBody() {
  const approved = registrations
    .filter((item) => item.state === "ACTIVE")
    .map((item) => ({
      id: item.id,
      kind: item.kind,
      trust_level: item.trust_level,
      effect_class: item.effect_class,
      capabilities: item.capabilities,
      transport: item.transport,
      protocol_version: item.protocol_version,
      network_domains: item.network_domains,
      health_check: item.health_check,
      health: item.last_health ?? "UNKNOWN",
    }));
  return {
    providers: [...BASE_PROVIDERS, ...approved],
    management_available: true,
    management_reason: null,
  };
}

function registration(
  raw: Record<string, unknown>,
  id: string,
): StubRegistration {
  return {
    id,
    kind: String(raw.kind ?? "REST"),
    state: "PENDING",
    trust_level: TRUST.PENDING ?? "UNTRUSTED",
    capabilities: (raw.capabilities as string[] | undefined) ?? [],
    effect_class: String(raw.effect_class ?? "READ_ONLY"),
    pinned_revision: String(raw.pinned_revision ?? ""),
    transport: (raw.transport as string | null) ?? null,
    protocol_version: (raw.protocol_version as string | null) ?? null,
    network_domains: (raw.network_domains as string[] | undefined) ?? [],
    health_check: raw.health_check === true,
    registered_at: NOW,
    updated_at: NOW,
    approved_at: null,
    revoked_at: null,
    revoked_reason: null,
    last_health: null,
    health_detail: null,
    health_checked_at: null,
    last_schema_digest: null,
    schema_baseline_digest: null,
    schema_drift: false,
    schema_drift_since: null,
    endpoint_binding: { state: "NOT_DECLARED", env_name: null, endpoint_digest: null },
    credential_binding: { state: "NOT_DECLARED", credential_ref: null, present: false },
    catalog_active: false,
  };
}

function withState(current: StubRegistration, state: string): StubRegistration {
  const revoked = state === "REVOKED";
  return {
    ...current,
    state,
    trust_level: TRUST[state] ?? "UNTRUSTED",
    catalog_active: state === "ACTIVE",
    approved_at: state === "ACTIVE" ? NOW : current.approved_at,
    revoked_at: revoked ? NOW : current.revoked_at,
    updated_at: NOW,
  };
}

function replace(next: StubRegistration): StubRegistration {
  registrations = registrations.map((item) => (item.id === next.id ? next : item));
  return next;
}

/** 动作路由公共体：找不到 404，终态 409（与后端语义一致）。 */
function act(
  url: URL,
  apply: (current: StubRegistration) => StubRegistration,
): { status: number; body: unknown } {
  const id = url.pathname.split("/").at(-2) ?? "";
  const current = registrations.find((item) => item.id === id);
  if (current === undefined) return { status: 404, body: { title: "Registration Not Found" } };
  if (current.state === "REVOKED") return { status: 409, body: { title: "Provider Revoked" } };
  return { status: 200, body: replace(apply(current)) };
}

export const REGISTRY_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/tool-providers$/,
    handler: () => ({ status: 200, body: catalogBody() }),
  },
  {
    method: "GET",
    pattern: /^\/tool-provider-registrations$/,
    handler: () => ({
      status: 200,
      body: {
        registrations,
        management_available: true,
        management_reason: null,
        note: "PENDING 不入目录；APPROVE 后以 USER_APPROVED 进入；REVOKE 为终态。",
      },
    }),
  },
  {
    method: "POST",
    pattern: /^\/tool-provider-registrations$/,
    handler: (_url, body) => {
      const raw = (body ?? {}) as Record<string, unknown>;
      const id = String(raw.id ?? "");
      if (registrations.some((item) => item.id === id)) {
        return { status: 409, body: { title: "Provider Already Registered" } };
      }
      if (BASE_PROVIDERS.some((item) => item.id === id)) {
        return { status: 409, body: { title: "Provider Id Reserved" } };
      }
      const created = registration(raw, id);
      registrations = [...registrations, created];
      return { status: 201, body: created };
    },
  },
  {
    method: "POST",
    pattern: /^\/tool-provider-registrations\/[^/]+\/approve$/,
    handler: (url) => {
      const id = url.pathname.split("/").at(-2) ?? "";
      const current = registrations.find((item) => item.id === id);
      if (current === undefined) return { status: 404, body: { title: "Registration Not Found" } };
      if (current.state !== "PENDING") {
        return { status: 409, body: { title: "Provider Not Pending" } };
      }
      return { status: 200, body: replace(withState(current, "ACTIVE")) };
    },
  },
  {
    method: "POST",
    pattern: /^\/tool-provider-registrations\/[^/]+\/revoke$/,
    handler: (url, body) => {
      const reason = String(((body ?? {}) as Record<string, unknown>).reason ?? "");
      return act(url, (current) => ({ ...withState(current, "REVOKED"), revoked_reason: reason }));
    },
  },
  {
    method: "POST",
    pattern: /^\/tool-provider-registrations\/[^/]+\/health-check$/,
    handler: (url) =>
      act(url, (current) => ({
        ...current,
        last_health: healthScript?.status ?? "UNKNOWN",
        health_detail: healthScript?.detail ?? "控制面未注册可探测的 provider 实例",
        health_checked_at: NOW,
        updated_at: NOW,
        // 编排过就照编排回；没编排则保持原状（不凭空造 digest，也不清除已有事实）
        last_schema_digest: healthScript?.lastSchemaDigest ?? current.last_schema_digest,
        schema_baseline_digest: healthScript?.baselineDigest ?? current.schema_baseline_digest,
        schema_drift: healthScript?.drift ?? current.schema_drift,
        schema_drift_since:
          healthScript === null
            ? current.schema_drift_since
            : healthScript.drift
              ? NOW
              : null,
      })),
  },
];
