/** Deterministic browser test transport fixtures; never imported by product code. */
import type {
  AgentSpecDto, ApprovalDto, ClusterViewDto, CostViewDto, DryRunProjectionDto,
  ExperimentViewDto, ModelReadDto, PreflightReportDto, ProbeResultDto,
  ProjectSettingsDto, RoleDefinitionDto, RunDetailDto, RunTelemetryDto, TaskDto, TrendViewDto,
} from "../../src/api/types";
import { claimsView, eventFrame, evidenceRecord, usageView } from "../unit/consoleFixtures";
import { DRAFT, ENDPOINT, VALID_YAML } from "./stub-api";

export { claimsView, eventFrame, evidenceRecord, usageView, DRAFT, ENDPOINT, VALID_YAML };

export const RUN: RunDetailDto = {
  id: "run-one", project_id: "example-project", protocol_id: "controlled-protocol",
  state: "RUNNING", manifest_digest: "sha256:manifest",
  created_at: "2026-09-09T00:00:00Z", updated_at: "2026-09-09T00:00:00Z",
};

export const MODEL: ModelReadDto = {
  id: "model-one", endpoint_id: ENDPOINT.id, model_name: "test-model", display_name: "Test model",
  enabled: true, capabilities: {}, version: "model-v1",
};

export const AGENT: AgentSpecDto = {
  id: "agent-one", role: "experiment_engineer", model_binding: { mode: "INHERIT", value: null },
  workspace_policy: null, skill_refs: [], capability_refs: [], max_context_tokens: null,
  max_iterations: null, runtime_kind: null, budget_policy_ref: null, version: "agent-v1",
};

export const ROLE: RoleDefinitionDto = {
  id: "experiment_engineer", role_type: "experiment_engineer", category: "experiment",
  activation_default: "REQUIRED_BY_PROTOCOL", requested_capabilities: [],
  hard_model_capabilities: { all_of: [], any_of: [] }, default_model_profile: null,
  workspace_policy: "read_only", default_skills: [], review_panel_role: "NONE",
};

export const APPROVAL: ApprovalDto = {
  id: "approval-one", run_id: RUN.id, action: "Publish deliverable", risk: "HIGH",
  context: "External publication requires approval", policy_source: "policy:publication",
  status: "PENDING", version: "approval-v1",
};

export const SETTINGS: ProjectSettingsDto = {
  project_id: "example-project", team_template_id: "standard", default_model_profile_id: null,
  budget_policy_id: "low_cost", workspace_backend: "openhands_docker",
  compute_profile: null, policy_id: "default-deny", reference_protocol: "ai_ml_research_v0_4_0.yaml",
};

export const PREFLIGHT: PreflightReportDto = {
  status: "WARN", findings: [{ code: "PROVIDER_FINGERPRINT_UNAVAILABLE", severity: "WARNING",
    message: "The provider fingerprint is unavailable", subject_ref: MODEL.id }],
  estimated_cost: null, estimated_cost_currency: null, reserved_budget_ref: null,
  unresolved_risks: ["Provider fingerprint unavailable"],
};

export const PROJECTION: DryRunProjectionDto = {
  role_counts: { experiment_engineer: 1 }, agent_models: { "agent-one": "model-one" },
  tools: {}, workspaces: {}, compute_profiles: {}, budget_reservations: [],
  estimated_cost_minor: null, estimated_cost_currency: null, approval_actions: [],
};

export const TELEMETRY: RunTelemetryDto = {
  run_id: RUN.id, manifest_digest: RUN.manifest_digest, exporter_config_digest: "sha256:exporter",
  generated_at: RUN.updated_at,
  tasks: { total: 1, succeeded: 0, failed: 0, cancelled: 0, queued: 0, leased: 1, other: 0 },
  outbox: { pending: null, status: "UNKNOWN", unavailable_reason: "read model unavailable" },
  sink: { enabled: false, dropped: 0, unlinked: 0, last_error: null },
};

export const COST: CostViewDto = {
  run_id: RUN.id, pricing_version: "fixture-v1", pricing_digest: "sha256:pricing",
  pricing_frozen: true, pricing_degraded_reason: "Provider usage missing",
  total: { status: "USAGE_UNKNOWN", minor_units: null, currency: "JPY",
    effective_from: null, calculation_method: null }, dimensions: [],
};

export const EXPERIMENTS: ExperimentViewDto = {
  experiments: [{ experiment_run_id: "experiment-one", artifact_ids: ["artifact-one"],
    image_digest: "sha256:image", environment_digest: "sha256:environment",
    metrics: { accuracy: 0.85 }, reproduction_available: false }],
  reproduction_note: "Persisted references only; reproduction is unavailable",
};

export const CLUSTER: ClusterViewDto = { workers: [{
  worker_ref: "worker-one", state: "READY", protocol_version: "1", runtime_version: "1",
  platform: "linux", registration_generation: 1, max_concurrency: 1,
  drain_requested: false, last_heartbeat: RUN.updated_at,
}] };

export const TASKS: TaskDto[] = [{ task_id: "task-one", contract_id: "contract-one",
  agent_id: AGENT.id, status: "LEASED", attempt: 1 }];

export const TREND: TrendViewDto = { dataset_id: null, truncated: false, segments: [],
  divergences: [], missing: [] };

export const PROBE: ProbeResultDto = {
  model_id: MODEL.id, ok: false, observed_capabilities: [], returned_model_name: null,
  system_fingerprint: null, provider_fingerprint_available: false, error_category: "TIMEOUT",
  error_message_redacted: "Fixture timeout", capability_failures: [], probed_at: RUN.updated_at,
  fingerprint: null,
};
