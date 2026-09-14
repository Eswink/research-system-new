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

export type CostAmountStatus =
  | "ACTUAL"
  | "ESTIMATED"
  | "MONETARY_UNAVAILABLE"
  | "USAGE_UNKNOWN"
  | "ZERO"
  | "NO_DATA"
  | "CURRENCY_CONFLICT"
  | "PARTIALLY_METERED";
export type PriceDimension = "model" | "tool" | "experiment" | "evaluation";
export type ResourceType =
  | "MODEL_TOKENS"
  | "MODEL_REQUESTS"
  | "MODEL_COST"
  | "EVALUATION_SCORER"
  | "TOOL_REQUESTS"
  | "TOOL_COST"
  | "CPU_TIME"
  | "GPU_TIME"
  | "MEMORY"
  | "STORAGE"
  | "NETWORK"
  | "WALL_CLOCK"
  | "AGENT_TURNS"
  | "PARALLELISM";
export type LedgerCostStatus = "KNOWN" | "UNKNOWN";
export type LedgerQuantityStatus = "KNOWN" | "UNKNOWN";
export type OutboxPendingStatus = "KNOWN" | "UNKNOWN";
export type TrendPointVerdict =
  "PASS" | "PASS_WITH_WARNINGS" | "REVISE" | "BLOCK" | "INDETERMINATE" | "MISSING_EVALUATION";
export type RegressionVerdict =
  "PASS" | "PASS_WITH_WARNINGS" | "REVISE" | "BLOCK" | "INDETERMINATE";
export type ComparabilityVerdict =
  | "COMPARABLE"
  | "CASE_SET_CHANGED"
  | "RUBRIC_CHANGED"
  | "DATASET_CHANGED"
  | "GATE_CONFIG_CHANGED"
  | "SCORER_CHANGED"
  | "EVALUATOR_CHANGED"
  | "SYSTEM_VERSION_CHANGED"
  | "SEGMENTED"
  | "INCOMPATIBLE_GENERATION";

export interface ProblemDto {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
}

/** Artifact 只读视图（WP-C；内容级 verified 仅单资源查询返回）。 */
export interface ArtifactDto {
  id: string;
  digest: string;
  size_bytes: number;
  media_type: string;
  state: string;
  created_by: string | null;
  source_refs: string[];
  classification: string | null;
  retention_policy: string | null;
  created_at: string | null;
  verified: boolean | null;
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
  /** 后端语义：显式 null 清除显示名（str | None） */
  display_name?: string | null;
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
  /** resource version（ETag 值，If-Match 用） */
  version: string;
}

export interface AgentCreateDto {
  role: string;
  model_binding?: { mode: string; value: string | null };
  workspace_policy?: string | null;
  max_context_tokens?: number | null;
  max_iterations?: number | null;
}

export interface AgentUpdatePayload {
  model_binding?: { mode: string; value: string | null };
  workspace_policy?: string | null;
  max_context_tokens?: number | null;
  max_iterations?: number | null;
}

export interface ProjectDto {
  id: string;
  name: string;
  status: "ACTIVE" | "ARCHIVED";
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateDto {
  name: string;
}

export interface ProjectUpdateDto {
  name?: string | null;
  status?: "ACTIVE" | "ARCHIVED" | null;
}

export interface ProjectSettingsDto {
  project_id: string;
  team_template_id: string;
  default_model_profile_id: string | null;
  budget_policy_id: string;
  workspace_backend: string;
  compute_profile: string | null;
  policy_id: string;
  /** WP-C：项目参考协议（Team 页预检使用；null = 未配置，诚实空态）。 */
  reference_protocol: string | null;
}

export interface ProtocolSourceDto {
  /** 受控模板路径与草稿修订引用二选一（WP-B；loader 统一裁决 422）。 */
  path?: string;
  draft_id?: string;
  draft_revision?: number;
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
  estimated_cost_currency: string | null;
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
    resource_type: ResourceType;
    quantity: number;
    unit: string;
  }[];
  estimated_cost_minor: number | null;
  estimated_cost_currency: string | null;
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
  /** ledger 行损坏时整图降级标记（WP-P4，未知行不整体失败） */
  degraded: boolean;
}

export interface UsageEntryDto {
  entry_id: string;
  resource_type: ResourceType;
  quantity: number;
  unit: string;
  cost_status: LedgerCostStatus;
  estimated_cost_minor: number | null;
  actual_cost_minor: number | null;
  currency: string;
  quantity_status: LedgerQuantityStatus;
  unavailable_reason: string | null;
  attempt: number;
  run_id: string | null;
  model_id: string | null;
  task_id: string | null;
}

export interface BudgetViewDto {
  entries: UsageEntryDto[];
  total_estimated_cost_minor: number | null;
  total_currency: string | null;
  known_cost_subtotal_minor: number | null;
  unknown_cost_entries: number;
  reservations: {
    id: string;
    scope: string;
    resource_type: ResourceType;
    quantity: number;
    unit: string;
  }[];
}

/** 单组 (resource_type, unit) 的预留/消耗/剩余；null = 不可计量或尚无消耗记录。 */
export interface ForecastLineDto {
  resource_type: ResourceType;
  unit: string;
  reserved: number;
  consumed: number | null;
  remaining: number | null;
  data_status: "KNOWN" | "UNKNOWN" | "NO_DATA";
  entry_count: number;
  unknown_entry_count: number;
}

/** 成本预测投影：只覆盖已预留部分（forecast_scope=RESERVED_ONLY）。 */
export interface CostForecastDto {
  run_id: string;
  lines: ForecastLineDto[];
  consumed_cost_minor: number | null;
  currency: string | null;
  cost_status: string;
  unknown_cost_entries: number;
  /** 预留归属：RESERVATION_REF（权威引用）/ RUN_SCOPE（退化匹配）/ NONE。 */
  attribution: "RESERVATION_REF" | "RUN_SCOPE" | "NONE";
  /** 账本中存在但无权威引用可归到本 run 的预留条数（>0 表示预留总量不完整）。 */
  unattributed_reserved: number;
  forecast_scope: string;
  scope_note: string;
}

/** 预算调整结果（append-only 账本上的动作摘要；不修改历史条目）。 */
export interface BudgetAdjustOutcomeDto {
  run_id: string;
  released_ref: string | null;
  reservation_ref: string;
  reservations: {
    id: string;
    scope: string;
    resource_type: ResourceType;
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

export interface DeliverableDto {
  run_id: string;
  available: boolean;
  reason: string | null;
  artifact_id: string | null;
  artifact_digest: string | null;
  deliverable: Record<string, unknown>;
}

export interface ToolProviderDto {
  id: string;
  kind: string;
  trust_level: string;
  effect_class: string;
  capabilities: string[];
  transport: string | null;
  protocol_version: string | null;
  network_domains: string[];
  health_check: boolean;
  health: string;
}

export interface ToolProviderListDto {
  providers: ToolProviderDto[];
  management_available: boolean;
  management_reason: string | null;
}

export interface LineageNodeDto {
  id: string;
  kind: string;
  label: string;
  run_id: string | null;
}

export interface LineageEdgeDto {
  source: string;
  target: string;
  relation: string;
}

export interface LineageDto {
  run_id: string;
  nodes: LineageNodeDto[];
  edges: LineageEdgeDto[];
  global_lineage_available: boolean;
  global_lineage_reason: string | null;
  degraded: boolean;
}

export type ResourceKind = "prompt" | "dataset" | "notebook";
export type ResourceStatus = "ACTIVE" | "ARCHIVED";

export interface LibraryResourceDto {
  id: string;
  project_id: string;
  kind: ResourceKind;
  name: string;
  description: string;
  content_ref: string | null;
  tags: string[];
  status: ResourceStatus;
  created_at: string;
  updated_at: string;
}

export interface AlertItemDto {
  kind: string;
  severity: string;
  subject: string;
  detail: string;
}

export interface AlertsViewDto {
  alerts: AlertItemDto[];
  rules_available: boolean;
  rules_reason: string | null;
}

export interface IncidentItemDto {
  run_id: string;
  protocol_id: string;
  state: string;
  updated_at: string;
}

export interface IncidentsViewDto {
  incidents: IncidentItemDto[];
  workflow_available: boolean;
  workflow_reason: string | null;
}

export interface ScheduleEntryDto {
  name: string;
  interval_seconds: number;
  purpose: string;
  enabled: boolean;
}

export interface SchedulesViewDto {
  schedules: ScheduleEntryDto[];
  management_available: boolean;
  management_reason: string | null;
}

export interface DataHealthMetricDto {
  metric: string;
  value: string;
  status: string;
}

export interface DataHealthViewDto {
  metrics: DataHealthMetricDto[];
  aggregate_available: boolean;
  aggregate_reason: string | null;
}

export interface ExperimentRunDto {
  experiment_run_id: string;
  artifact_ids: string[];
  image_digest: string | null;
  environment_digest: string | null;
  metrics: Record<string, unknown>;
  reproduction_available: boolean;
}

export interface ExperimentViewDto {
  experiments: ExperimentRunDto[];
  reproduction_note: string;
}
export interface TelemetryTaskCountsDto {
  total: number;
  succeeded: number;
  failed: number;
  cancelled: number;
  queued: number;
  leased: number;
  other: number;
}

export interface TelemetryOutboxDto {
  pending: number | null;
  status: OutboxPendingStatus;
  unavailable_reason: string | null;
}

export interface TelemetrySinkDto {
  enabled: boolean;
  dropped: number;
  unlinked: number;
  last_error: string | null;
}

export interface RunTelemetryDto {
  run_id: string;
  manifest_digest: string | null;
  exporter_config_digest: string | null;
  generated_at: string;
  tasks: TelemetryTaskCountsDto;
  outbox: TelemetryOutboxDto;
  sink: TelemetrySinkDto;
}

export interface CostAmountDto {
  status: CostAmountStatus;
  minor_units: number | null;
  currency: string;
  effective_from: string | null;
  calculation_method: string | null;
}

export interface CostDimensionDto {
  dimension: PriceDimension;
  resource_key: string;
  amount: CostAmountDto;
  entry_count: number;
}

export interface CostViewDto {
  run_id: string;
  pricing_version: string;
  pricing_digest: string;
  pricing_frozen: boolean;
  pricing_degraded_reason: string | null;
  dimensions: CostDimensionDto[];
  total: CostAmountDto;
}

/** 定价表分组（同 (version,digest) 的 entries 小计；WP-D）。 */
export interface PricingGroupDto {
  pricing_version: string;
  pricing_digest: string;
  pricing_frozen: boolean;
  amount: CostAmountDto;
  entry_count: number;
}

export interface CostDayPointDto {
  date: string;
  total: CostAmountDto;
  mixed_pricing: boolean;
  groups: PricingGroupDto[];
}

/** 跨 run 成本日序列（WP-D；只含有数据的日期，无预测无插值）。 */
export interface CostDailyViewDto {
  truncated: boolean;
  days: CostDayPointDto[];
  attribution_note: string | null;
}

/** WP-E 实验平面 DTO。 */
export interface ExperimentRunRowDto extends ExperimentRunDto {
  run_id: string;
}

export interface ProjectExperimentsViewDto {
  experiments: ExperimentRunRowDto[];
  reproduction_note: string;
}

export interface ExperimentPlanCreateDto {
  name: string;
  hypothesis?: string | null;
  task_contract_ref?: string | null;
}

export interface ExperimentPlanDto {
  id: string;
  name: string;
  hypothesis: string | null;
  task_contract_ref: string | null;
  input_spec_digest: string | null;
  state: string;
  created_at: string;
  updated_at: string;
}

/** WP-F 产品 Memory DTO（committed records；无 pending 状态）。 */
export interface MemoryRecordDto {
  id: string;
  tier: string;
  kind: string;
  content: string;
  provenance: string;
  confidence: number;
  valid_from: string | null;
  review_after: string | null;
  expires_at: string | null;
  supersedes: string[];
  active: boolean;
}

export interface MemoryViewDto {
  records: MemoryRecordDto[];
  scope_note: string;
}

export interface MemoryProposalCreateDto {
  tier: string;
  kind: string;
  content: string;
  provenance: string;
  confidence: number;
  supersedes?: string[];
  proposed_by?: string | null;
  curator_approved: boolean;
}

export interface MemoryCommittedDto {
  record: MemoryRecordDto;
  decision: string;
}

/** WP-G 通知投影（outbox 事件白名单；不含 payload 内容）。 */
export interface NotificationDto {
  id: string;
  type: string;
  run_id: string | null;
  task_id: string | null;
  occurred_at: string;
  read: boolean;
}

export interface NotificationsViewDto {
  notifications: NotificationDto[];
  note: string;
}

export interface TrendPointDto {
  report_digest: string;
  recorded_at: string | null;
  verdict: TrendPointVerdict;
  dataset_id: string | null;
  dataset_version: string | null;
  dataset_digest: string | null;
  gate_config_id: string | null;
  gate_config_version: string | null;
  gate_config_digest: string | null;
  system_version: string | null;
  comparison_digest: string | null;
  run_id: string | null;
  pass_count: number;
  fail_count: number;
  infra_error_count: number;
  reviewer_failure_count: number;
  missing: boolean;
  integrity_error: string | null;
}

export interface RegressionMarkerDto {
  baseline_digest: string;
  candidate_digest: string;
  verdict: RegressionVerdict;
  newly_regressed: string[];
  newly_fixed: string[];
}

export interface TrendSegmentDto {
  points: TrendPointDto[];
  comparisons: RegressionMarkerDto[];
}

export interface TrendDivergenceDto {
  verdict: ComparabilityVerdict;
  reason: string;
}

export interface TrendViewDto {
  dataset_id: string | null;
  truncated: boolean;
  segments: TrendSegmentDto[];
  divergences: TrendDivergenceDto[];
  missing: TrendPointDto[];
}

export interface ClusterWorkerDto {
  worker_ref: string;
  state: string;
  protocol_version: string;
  runtime_version: string;
  platform: string;
  registration_generation: number;
  max_concurrency: number;
  drain_requested: boolean;
  last_heartbeat: string | null;
}

export interface ProtocolDraftIssueDto {
  path: string;
  code: string;
  message: string;
  severity: string;
}

export interface ProtocolDraftValidateResultDto {
  ok: boolean;
  issues: ProtocolDraftIssueDto[];
  protocol_id: string | null;
  protocol_digest: string | null;
  phase_count: number;
}

export interface ProtocolDraftTemplateDto {
  template_id: string;
  display_name: string;
  description: string;
  yaml_text: string;
  source: string;
}

export interface ProtocolDraftViewDto {
  draft_id: string;
  project_id: string;
  name: string;
  revision: number;
  yaml_text: string;
  source_digest: string;
  created_at: string;
  updated_at: string;
}

export interface ProtocolDraftSummaryDto {
  draft_id: string;
  project_id: string;
  name: string;
  revision: number;
  source_digest: string;
  created_at: string;
  updated_at: string;
}

export interface ProtocolDraftRevisionDto {
  draft_id: string;
  revision: number;
  yaml_text: string;
  source_digest: string;
  created_at: string;
}

export interface RunStartPayloadDto {
  /** 旧路径引用（examples/protocols/ 内）与新草稿修订引用二选一 */
  protocol_path?: string;
  draft_id?: string;
  draft_revision?: number;
  trace_id?: string;
}

export interface ClusterViewDto {
  workers: ClusterWorkerDto[];
}

export interface RunPlacementDto {
  run_id: string;
  placements: ClusterWorkerDto[];
  execution_tasks: string[];
}
