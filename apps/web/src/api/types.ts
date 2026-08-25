/**
 * Control Plane API DTO 类型（与 schemas/openapi.m13.json 单一 schema truth 对应）。
 *
 * 前端只消费本文件类型（API DTO boundary）：禁止 import packages/domain
 * Python 概念。本文件由 openapi.m13.json 维护，契约测试
 * tests/contracts/test_openapi_snapshot.py 防止后端 schema 漂移；
 * 若 API DTO 变更，先更新后端再同步本文件（单一 schema truth 原则）。
 */

/** 资源版本（ETag 值；If-Match 用） */
export type Version = string;

export interface ProblemDto {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
}

export type CredentialState = "configured" | "missing";

export interface DiscoveryConfigDto {
  enabled: boolean;
  allow_models: string[];
}

export interface LlmEndpointCreateDto {
  name: string;
  base_url: string;
  protocol: "OPENAI_COMPATIBLE";
  api_style: "chat_completions" | "responses";
  api_key?: string;
  enabled?: boolean;
  request_timeout_seconds?: number;
  max_retries?: number;
  concurrency_limit?: number;
  discovery?: DiscoveryConfigDto;
}

export interface LlmEndpointUpdateDto {
  name?: string;
  base_url?: string;
  api_style?: "chat_completions" | "responses";
  api_key?: string;
  enabled?: boolean;
  request_timeout_seconds?: number;
  max_retries?: number;
  concurrency_limit?: number;
}

export interface LlmEndpointReadDto {
  id: string;
  name: string;
  protocol: string;
  base_url: string;
  api_style: string;
  enabled: boolean;
  /** 安全状态视图：configured / missing，永不包含明文 Key */
  credential: CredentialState;
  request_timeout_seconds: number;
  max_retries: number;
  concurrency_limit: number;
  version: Version;
}

export interface EndpointTestRequestDto {
  model_id: string;
}

export interface EndpointTestResultDto {
  ok: boolean;
  returned_model_name: string | null;
  system_fingerprint: string | null;
  error_category: string | null;
  error_message_redacted: string | null;
  probed_at: string | null;
}

export interface DiscoverModelsResultDto {
  model_ids: string[];
}

export interface EndpointHealthDto {
  ok: boolean;
  error_category: string | null;
  error_message_redacted: string | null;
  checked_at: string;
}

export interface CapabilityAssertionDto {
  status: string;
  confidence: number;
  source: string;
  probe_version: string | null;
}

export interface CapabilityFailureDto {
  capability: string;
  error_category: string | null;
  error_message_redacted: string | null;
}

export interface ModelRuntimeFingerprintDto {
  endpoint_config_digest: string;
  probe_suite_digest: string | null;
  returned_model_identifier: string | null;
  system_fingerprint: string | null;
  observed_capabilities: string[];
}

export interface ModelCreateDto {
  endpoint_id: string;
  model_name: string;
  display_name?: string;
  enabled?: boolean;
  capabilities?: Record<string, CapabilityAssertionDto>;
}

export interface ModelUpdateDto {
  display_name?: string;
  enabled?: boolean;
  capabilities?: Record<string, CapabilityAssertionDto>;
}

export interface ModelReadDto {
  id: string;
  endpoint_id: string;
  model_name: string;
  display_name: string | null;
  enabled: boolean;
  capabilities: Record<string, CapabilityAssertionDto>;
  version: Version;
}

export interface ProbeResultDto {
  model_id: string;
  ok: boolean;
  observed_capabilities: string[];
  returned_model_name: string | null;
  system_fingerprint: string | null;
  /**
   * system_fingerprint 是否可用。false 时 UI 必须渲染
   * "Configuration reproducible / provider fingerprint unavailable"，
   * 禁止渲染 "Fully reproducible model"（M12 诚实建模，不得美化）。
   */
  provider_fingerprint_available: boolean;
  error_category: string | null;
  error_message_redacted: string | null;
  capability_failures: CapabilityFailureDto[];
  probed_at: string | null;
  fingerprint: ModelRuntimeFingerprintDto | null;
}

export interface CompatibilityViewDto {
  model: ModelReadDto;
  endpoint_id: string;
  endpoint_healthy_hint: boolean | null;
  hard_capability_requirements: string[];
}

export interface RoleDefinitionDto {
  id: string;
  role_type: string;
  category: string;
  activation_default: string;
  requested_capabilities: string[];
  hard_model_capabilities: { all_of: string[]; any_of: string[] };
  default_model_profile: string | null;
  workspace_policy: string;
  default_skills: string[];
  review_panel_role: string;
}

export interface TeamTemplateDto {
  id: string;
  display_name: string;
  extends: string | null;
  roles: Record<string, { min_instances: number; max_instances: number }>;
}

export interface AgentSpecDto {
  id: string;
  role: string;
  model_binding: { mode: string; value: string | null };
  workspace_policy: string | null;
  skill_refs: string[];
  capability_refs: string[];
  max_context_tokens: number | null;
  max_iterations: number | null;
  runtime_kind: string | null;
  budget_policy_ref: string | null;
}

export interface ProjectSettingsDto {
  project_id: string;
  team_template_id: string;
  default_model_profile_id: string | null;
  budget_policy_id: string;
  workspace_backend: string;
  compute_profile: string | null;
  policy_id: string;
}

export interface ProtocolSourceDto {
  path: string;
}

export interface CompileResultDto {
  plan_id: string | null;
  protocol_digest: string | null;
  findings: { code: string; severity: string; message: string }[];
  successful: boolean;
}

export interface PreflightReportDto {
  status: "PASS" | "WARN" | "FAIL";
  findings: {
    code: string;
    severity: string;
    message: string;
    subject_ref: string | null;
  }[];
  estimated_cost: number | null;
  reserved_budget_ref: string | null;
  unresolved_risks: string[];
}

export interface DryRunProjectionDto {
  role_counts: Record<string, number>;
  agent_models: Record<string, string>;
  tools: Record<string, string[]>;
  workspaces: Record<string, string>;
  compute_profiles: Record<string, string | null>;
  budget_reservations: {
    id: string;
    scope: string;
    resource_type: string;
    quantity: number;
    unit: string;
  }[];
  estimated_cost_minor: number | null;
  approval_actions: string[];
}

export interface RunDetailDto {
  id: string;
  project_id: string;
  protocol_id: string;
  state: string;
  manifest_digest: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskDto {
  task_id: string;
  contract_id: string;
  agent_id: string | null;
  status: string;
  attempt: number;
}

export interface RunEventDto {
  event_id: string;
  type: string;
  schema_version: string;
  occurred_at: string;
  actor: string;
  scope: string;
  run_id: string | null;
  task_id: string | null;
  trace_id: string | null;
  payload: Record<string, unknown>;
}

export interface ApprovalDto {
  id: string;
  run_id: string;
  action: string;
  risk: string;
  context: string;
  policy_source: string;
  status: string;
  version: string;
}

export interface ApprovalDecideDto {
  decision: "approve" | "deny";
}

export interface EvidenceDto {
  id: string;
  source_ref: string;
  content_digest: string;
  run_id: string | null;
  experiment_run_id: string | null;
  artifact_id: string | null;
  image_digest: string | null;
  environment_digest: string | null;
  model_refs: string[];
  manifest_digest: string | null;
}

export interface RelationDto {
  claim_id: string;
  evidence_id: string;
  relation: string;
  strength: number;
}

export interface ClaimDto {
  id: string;
  statement: string;
  status: string;
  author: string | null;
  relations: RelationDto[];
}

export interface ClaimMapDto {
  claims: ClaimDto[];
  unsupported_claims: string[];
  contradictory_claims: string[];
}

export interface UsageEntryDto {
  entry_id: string;
  resource_type: string;
  quantity: number;
  unit: string;
  cost_status: string;
  estimated_cost_minor: number | null;
  actual_cost_minor: number | null;
  model_id: string | null;
  task_id: string | null;
}

export interface BudgetViewDto {
  entries: UsageEntryDto[];
  total_estimated_cost_minor: number;
  unknown_cost_entries: number;
  reservations: {
    id: string;
    scope: string;
    resource_type: string;
    quantity: number;
    unit: string;
  }[];
}

export interface ExportBundleDto {
  run_id: string;
  run_state: string;
  manifest_digest: string | null;
  evidence: EvidenceDto[];
  claims: ClaimDto[];
  usage: BudgetViewDto;
  exported_from: string;
}