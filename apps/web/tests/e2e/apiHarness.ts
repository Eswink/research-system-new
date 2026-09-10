import type { Page, Request } from "@playwright/test";
import type {
  AgentSpecDto, ApprovalDto, ProtocolDraftViewDto, RunDetailDto,
} from "../../src/api/types";
import {
  AGENT, APPROVAL, CLUSTER, COST, DRAFT, ENDPOINT, EXPERIMENTS, MODEL, PREFLIGHT,
  PROBE, PROJECTION, ROLE, RUN, SETTINGS, TASKS, TREND, VALID_YAML,
  claimsView, eventFrame, evidenceRecord, usageView,
} from "./apiFixtures";

interface Call {
  method: string; path: string; body: Record<string, unknown>; headers: Record<string, string>;
}
interface Reply { status: number; body: unknown }

export interface ApiHarness {
  calls: Call[];
  unmatched: string[];
  failures: Map<string, number>;
  runs: RunDetailDto[];
  approvals: ApprovalDto[];
  agents: AgentSpecDto[];
  settings: Record<string, unknown>;
  draft: ProtocolDraftViewDto;
}

/** Strict transport test double: absent routes fail, mutation preconditions are observable. */
export async function installApiHarness(page: Page): Promise<ApiHarness> {
  const state: ApiHarness = {
    calls: [], unmatched: [], failures: new Map(),
    runs: [structuredClone(RUN), { ...RUN, id: "run-two", state: "SUCCEEDED" }],
    approvals: [structuredClone(APPROVAL)], agents: [structuredClone(AGENT)],
    settings: { ...SETTINGS },
    draft: structuredClone(DRAFT),
  };
  await page.route("**/api/**", async (route) => {
    const call = readCall(route.request());
    state.calls.push(call);
    const failure = state.failures.get(`${call.method} ${call.path}`);
    if (failure !== undefined) {
      await route.fulfill(jsonReply(problem(failure, "Injected API failure")));
      return;
    }
    if (call.headers.accept?.startsWith("text/event-stream") === true) {
      const frame = JSON.stringify(eventFrame);
      await route.fulfill({ contentType: "text/event-stream",
        body: `id: ${eventFrame.event_id}\nevent: ${eventFrame.type}\ndata: ${frame}\n\n` });
      return;
    }
    const reply = call.method === "GET" ? readReply(call, state) : writeReply(call, state);
    if (reply === null) state.unmatched.push(`${call.method} ${call.path}`);
    await route.fulfill(jsonReply(reply ?? problem(500, `Unstubbed ${call.method} ${call.path}`)));
  });
  return state;
}

function readCall(request: Request): Call {
  let body: unknown = null;
  try { body = request.postDataJSON(); } catch { body = null; }
  return {
    method: request.method(), path: new URL(request.url()).pathname.replace(/^\/api/, ""),
    headers: request.headers(), body: record(body),
  };
}

function record(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? value as Record<string, unknown> : {};
}

function jsonReply(reply: Reply) {
  return { status: reply.status, contentType: "application/json",
    body: JSON.stringify(reply.body) };
}

function problem(status: number, detail: string): Reply {
  return { status, body: { type: "about:blank", title: "Test transport error", status,
    detail, instance: "/api/test" } };
}

function readReply(call: Call, state: ApiHarness): Reply | null {
  const collection: Record<string, unknown> = {
    "/llm-endpoints": [ENDPOINT], "/models": [MODEL], "/roles": [ROLE],
    "/team-templates": [], "/projects/example-project/agents": state.agents,
    "/projects/example-project/settings": state.settings,
    "/projects/example-project/runs": state.runs,
    "/approvals": state.approvals, "/cluster/workers": CLUSTER, "/evaluations/trend": TREND,
    "/protocol-templates": [template()], "/protocol-templates/sort-analysis": template(),
    "/projects/example-project/protocol-drafts": [state.draft],
  };
  if (Object.hasOwn(collection, call.path)) return { status: 200, body: collection[call.path] };
  const segments = pathSegments(call.path);
  if (isSingle(segments, "llm-endpoints", ENDPOINT.id)) return { status: 200, body: ENDPOINT };
  if (isSingle(segments, "models", MODEL.id)) return { status: 200, body: MODEL };
  if (segments[0] === "models" && segments[1] === MODEL.id && segments[2] === "compatibility") {
    return {
      status: 200,
      body: { model: MODEL, endpoint_id: ENDPOINT.id, endpoint_healthy_hint: null,
        hard_capability_requirements: [] },
    };
  }
  if (segments[0] === "protocol-drafts" && segments[2] === "revisions") {
    return revisionReply(state, segments);
  }
  if (call.path.startsWith("/protocol-drafts/")) return { status: 200, body: state.draft };
  if (segments[0] !== "runs") return null;
  const run = state.runs.find((item) => item.id === segments[1]);
  if (run === undefined) return problem(404, "Run not found");
  return runReply(run, segments.slice(2).join(slash()));
}

function slash(): string {
  return decodeURIComponent("%2F");
}

function pathSegments(path: string): string[] {
  return path.split(slash()).filter((part) => part.length > 0);
}

function isSingle(segments: string[], first: string, second: string): boolean {
  return segments.length === 2 && segments[0] === first && segments[1] === second;
}

function revisionReply(state: ApiHarness, segments: string[]): Reply {
  const revision = {
    draft_id: state.draft.draft_id,
    revision: state.draft.revision,
    yaml_text: state.draft.yaml_text,
    source_digest: state.draft.source_digest,
    created_at: state.draft.created_at,
  };
  if (segments.length === 3) return { status: 200, body: [revision] };
  return Number(segments[3]) === revision.revision
    ? { status: 200, body: revision }
    : problem(404, "Revision not found");
}

function template() {
  return { template_id: "sort-analysis", display_name: "Controlled test protocol",
    description: "Deterministic fixture", yaml_text: VALID_YAML,
    source: "examples/protocols/sort_analysis_v1.yaml" };
}

function runReply(run: RunDetailDto, resource: string): Reply | null {
  const resources: Record<string, unknown> = {
    "": run, tasks: TASKS, events: [{ ...eventFrame, run_id: run.id }],
    "claim-map": claimsView, evidence: [evidenceRecord], usage: usageView,
    experiments: EXPERIMENTS, telemetry: { ...TELEMETRY_BASE(), run_id: run.id },
    cost: { ...COST, run_id: run.id },
    placement: { run_id: run.id, placements: CLUSTER.workers, execution_tasks: [] },
    export: { run_id: run.id, run_state: run.state, manifest_digest: run.manifest_digest,
      evidence: [evidenceRecord], claims: claimsView.claims, usage: usageView,
      exported_from: "http-test-fixture" },
  };
  return Object.hasOwn(resources, resource) ? { status: 200, body: resources[resource] } : null;
}

function TELEMETRY_BASE() {
  return { manifest_digest: RUN.manifest_digest, exporter_config_digest: "sha256:exporter",
    generated_at: RUN.updated_at,
    tasks: { total: 1, succeeded: 0, failed: 0, cancelled: 0, queued: 0, leased: 1, other: 0 },
    outbox: { pending: null, status: "UNKNOWN", unavailable_reason: "read model unavailable" },
    sink: { enabled: false, dropped: 0, unlinked: 0, last_error: null } };
}

function writeReply(call: Call, state: ApiHarness): Reply | null {
  const analysis = analysisReply(call);
  if (analysis !== null) return analysis;
  if (!call.headers["idempotency-key"]) return problem(400, "Missing Idempotency-Key");
  return mutationReply(call, state);
}

/** 分析类动作（后端豁免 Idempotency-Key）：validate/compile/preflight/dry-run/test。 */
function analysisReply(call: Call): Reply | null {
  if (call.path === "/protocol-drafts/validate") {
    return { status: 200, body: { ok: true, issues: [], protocol_id: "test",
      protocol_digest: "sha256:test", phase_count: 1 } };
  }
  if (call.path === "/protocols/validate") {
    return { status: 200, body: { plan_id: "harness-plan", protocol_digest: "sha256:harness",
      findings: [], successful: true } };
  }
  if (call.path.endsWith("/compile") || call.path.endsWith("/preflight")) {
    return { status: 200, body: PREFLIGHT };
  }
  if (call.path === "/models/model-one/probe") return { status: 200, body: PROBE };
  if (call.path.endsWith("/dry-run")) return { status: 200, body: PROJECTION };
  if (call.path.endsWith("/test")) {
    return { status: 200, body: { ok: false, returned_model_name: null, system_fingerprint: null,
      error_category: "MODEL_UNAVAILABLE", error_message_redacted: null,
      probed_at: "2026-09-10T00:00:00Z" } };
  }
  return null;
}

function mutationReply(call: Call, state: ApiHarness): Reply | null {
  if (isSingle(pathSegments(call.path), "llm-endpoints", ENDPOINT.id)) {
    if (call.headers["if-match"] !== ENDPOINT.version) {
      return problem(412, "Stale endpoint version");
    }
    return { status: 200, body: { ...ENDPOINT, ...safePatch(call.body), version: "endpoint-v2" } };
  }
  if (call.path === "/approvals/approval-one/decide") return decide(call, state);
  if (call.path === "/agents/agent-one") return saveAgent(call, state);
  if (call.path === "/projects/example-project/settings") {
    state.settings = { ...state.settings, ...call.body };
    return { status: 200, body: state.settings };
  }
  if (call.method === "POST" && call.path === "/projects/example-project/agents") {
    const created = { ...AGENT, id: "agent-created", ...call.body };
    state.agents = [...state.agents, created as AgentSpecDto];
    return { status: 201, body: created };
  }
  if (call.path === "/projects/example-project/protocol-drafts") {
    state.draft = { ...state.draft, yaml_text: String(call.body.yaml_text), revision: 1 };
    return { status: 201, body: state.draft };
  }
  if (call.path === "/projects/example-project/runs") {
    const run = { ...RUN, id: "started-run" }; state.runs.push(run);
    return { status: 201, body: run };
  }
  if (call.path.endsWith("/cancel")) {
    const run = state.runs.find((item) => call.path === `/runs/${item.id}/cancel`);
    if (run === undefined) return problem(404, "Run not found");
    run.state = "CANCELLED"; return { status: 200, body: run };
  }
  if (/pause|resume$/.test(call.path)) return transitionReply(call, state);
  return null;
}

/** 凭据字段永不回显：api_key 从 PATCH 合并中剔除。 */
function safePatch(body: Record<string, unknown>): Record<string, unknown> {
  const copy = { ...body };
  delete copy.api_key;
  return copy;
}

function transitionReply(call: Call, state: ApiHarness): Reply | null {
  const segments = pathSegments(call.path);
  const run = state.runs.find((item) => item.id === segments[1]);
  if (run === undefined) return problem(404, "Run not found");
  const pausing = segments[segments.length - 1] === "pause";
  if (pausing !== (run.state === "RUNNING")) return problem(409, "Invalid Transition");
  run.state = pausing ? "PAUSED" : "RUNNING";
  return { status: 200, body: run };
}

function decide(call: Call, state: ApiHarness): Reply {
  const approval = state.approvals[0];
  if (approval === undefined) return problem(409, "Already decided");
  if (call.headers["if-match"] !== approval.version) return problem(412, "Stale approval version");
  state.approvals = [];
  return { status: 200, body: { ...approval, status: call.body.decision === "approve"
    ? "APPROVED" : "DENIED" } };
}

function saveAgent(call: Call, state: ApiHarness): Reply {
  const agent = state.agents[0];
  if (agent === undefined || call.headers["if-match"] !== agent.version) {
    return problem(412, "Stale agent version");
  }
  const binding = record(call.body.model_binding);
  if (binding.mode === "INHERIT" && binding.value === null) {
    agent.model_binding = { mode: "INHERIT", value: null };
  } else if (binding.mode === "EXPLICIT_MODEL" && typeof binding.value === "string") {
    agent.model_binding = { mode: "EXPLICIT_MODEL", value: binding.value };
  } else return problem(422, "Invalid binding");
  agent.version = "agent-v2";
  return { status: 200, body: agent };
}
