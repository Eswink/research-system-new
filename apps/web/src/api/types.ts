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

export type ThinkingIntensity = "MINIMAL" | "LOW" | "MEDIUM" | "HIGH" | "MAX";

export interface ModelCreateDto {
  endpoint_id: string;
  model_name: string;
  display_name?: string;
  enabled?: boolean;
  capabilities?: Record<string, CapabilityAssertionDto>;
  /** 声明的上下文窗口（tokens，>=1）。声明值：当前不发送给 provider。 */
  context_window_tokens?: number;
  /** 声明的思考强度（厂商中立相对词）。声明值：映射未实现时不代表已生效。 */
  thinking_intensity?: ThinkingIntensity;
}

export interface ModelUpdateDto {
  /** 后端语义：显式 null 清除显示名（str | None） */
  display_name?: string | null;
  enabled?: boolean;
  capabilities?: Record<string, CapabilityAssertionDto>;
  context_window_tokens?: number;
  thinking_intensity?: ThinkingIntensity;
}

export interface ModelReadDto {
  id: string;
  endpoint_id: string;
  model_name: string;
  display_name: string | null;
  enabled: boolean;
  capabilities: Record<string, CapabilityAssertionDto>;
  /** 未声明时为 null —— null 表示「没有声明」，不是某个默认值。 */
  context_window_tokens: number | null;
  thinking_intensity: ThinkingIntensity | null;
  version: Version;
}

/**
 * 漂移三态（GOAL-008 EC-05）。`UNKNOWN` = **未探到**，不得当成「无漂移」渲染。
 */
export type ModelDriftState = "MATCH" | "DRIFT" | "UNKNOWN";

export interface ModelDriftDto {
  state: ModelDriftState;
  declared_model_name: string;
  returned_model_name: string | null;
  /** 由域层给出的人读说明（只含两个模型标识，无凭据、无原始响应体）。 */
  detail: string;
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
  /** 登记声明值与 provider 返回标识的三态对比（EC-05）。 */
  drift: ModelDriftDto;
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

export interface PausedDispatchDto {
  // GOAL-004 cycle 2：PAUSED 的派发语义。RETRY_SCHEDULED = 守护线程到期会自己续跑
  // （due_now=true 表示现在就已到期）；USER_PAUSED = 只有人工 resume 会动它；
  // UNKNOWN = 没有 workflow 读面，不猜。
  kind: string;
  next_retry_at: string | null;
  due_now: boolean;
}

export interface DispatchRetryDto {
  // GOAL-004 cycle 6：重排读面（与 paused_dispatch 同一次读出的数字）。
  scheduled: number;
  due: number;
  next_retry_at: string | null;
}

export interface LeaseHolderDto {
  // 一个活着的租约持有者；worker_id 为 null = 控制面自己持有（agent session 投递）。
  task_id: string;
  worker_id: string | null;
  fence: number;
  expires_at: string | null;
}

export interface DispatchOwnershipDto {
  // GOAL-004 cycle 6：统一派发读面（任何状态都给）。WORKER_CLAIM = 有活租约持有者；
  // RETRY_DISPATCH = 任务面有重排（等时钟或已到期）；BOTH = 两件事实同时存在；
  // NONE = 都没有；UNKNOWN = 读面读不到，不猜。
  kind: string;
  retry: DispatchRetryDto;
  holders: LeaseHolderDto[];
}

/** 重建能力读面：这份**记录**够不够重建、缺哪条事实（`missing` 是 canonical 行字段名）。 */
export interface RebuildReadinessDto {
  status: string;
  missing: string[];
}

// GOAL-010 EC-04：指纹四要素落读面。status 只有两态（REPEATABLE_CONFIGURATION /
// NOT_VERIFIED）；source 说明这份事实从哪来：FROZEN_PLACEHOLDER = 冻结快照里的状态
// 记录（这次 run 没有实测记录，四要素全为空且 missing_fields 点名全部四项），
// RUN_OBSERVATION = 调用后落下的实测记录。returned_model_identifier 取自**本次 run 的
// usage 度量**（不是响应头、也不是请求里写的那个 id）；观测到多个不同值时留 null，
// 多值本身在 observed_model_identifiers 里。
export interface RuntimeFingerprintDto {
  status: string;
  substrate: string | null;
  reason: string | null;
  source: string;
  endpoint_config_digest: string | null;
  returned_model_identifier: string | null;
  probe_suite_digest: string | null;
  system_fingerprint: string | null;
  observed_model_identifiers: string[];
  missing_fields: string[];
}

// GOAL-007 cycle 4 = EC-04：执行体读面。外层的 null 与 execution_backend 的
// null 是两件事：外层 null = 这条 run 尚未冻结；execution_backend === null =
// 冻结时未声明。两者都不代表某个具体执行体。
export interface RunExecutionDto {
  execution_backend: string | null;
  runtime_fingerprint: RuntimeFingerprintDto | null;
}

export interface RunDetailDto {
  id: string;
  project_id: string;
  protocol_id: string;
  state: string;
  manifest_digest: string | null;
  // GOAL-004 cycle 4：冻结的语义 digest（排除冻结时刻；null = 未冻结，
  // 或 manifest.frozen 事件早于本轮）。失败收敛的 run 同样带它。
  manifest_semantic_digest: string | null;
  // GOAL-004 cycle 1：冻结协议正文的 digest（null = 旧 run 没有冻结正文，
  // 重启续跑仍依赖外部来源可解析）。
  protocol_body_digest: string | null;
  // GOAL-004 cycle 2：仅 state === "PAUSED" 时非 null。
  paused_dispatch: PausedDispatchDto | null;
  // GOAL-004 cycle 6：统一派发读面（任何状态都给；与 paused_dispatch 同一次读）。
  dispatch: DispatchOwnershipDto | null;
  // GOAL-005 cycle 6 = EC-06：重建能力读面（任何状态都给；历史行点名缺失事实）。
  rebuild: RebuildReadinessDto;
  // GOAL-007 cycle 4 = EC-04：执行体读面（仅详情路径给；列表路径为 null）。
  execution: RunExecutionDto | null;
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
  /** 来源记录的可读面（GOAL-010 EC-02）：取不到来源时为 null。 */
  source_origin: string | null;
  source_trust_label: string | null;
  source_access_time: string | null;
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

/** 项目日序列的一天：未进投影样本时给出排除原因（G12）。 */
export interface ProjectCostDayDto {
  date: string;
  amount: CostAmountDto;
  mixed_pricing: boolean;
  included_in_projection: boolean;
  exclusion_reason: string | null;
}

/**
 * 已计价日均外推（method=MEAN_OF_VALUED_DAYS）。
 *
 * `unavailable_reason` 非空时不给金额：样本为空（NO_VALUED_DAYS）或跨币种
 * （CURRENCY_CONFLICT，绝不隐式换算）。
 */
export interface ProjectCostProjectionDto {
  method: string;
  horizon_days: number;
  valued_days: number;
  excluded_days: number;
  observed_minor: number | null;
  observed_status: string;
  currency: string | null;
  pricing_version: string | null;
  daily_mean_minor: number | null;
  projected_minor: number | null;
  unavailable_reason: string | null;
  note: string;
}

/** 项目级成本预测：日序列 + 外推 + 排除项 + 归属注记（G12）。 */
export interface ProjectCostForecastDto {
  project_id: string;
  from_date: string | null;
  to_date: string | null;
  truncated: boolean;
  days: ProjectCostDayDto[];
  projection: ProjectCostProjectionDto;
  unattributed_entries: number;
  attribution_note: string | null;
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

/** 制品内容 diff 的一行（PLAN-047；CONTEXT/ADDED/REMOVED/HUNK_HEADER）。 */
export interface ArtifactDiffLineDto {
  kind: "CONTEXT" | "ADDED" | "REMOVED" | "HUNK_HEADER";
  text: string;
}

export interface ArtifactDiffStatsDto {
  added: number;
  removed: number;
  context: number;
}

/** 两制品内容 diff：available=false 时 reason 在场且 lines 为空（≠ 无差异）。 */
export interface ArtifactDiffDto {
  left_digest: string;
  right_digest: string;
  comparison: string;
  available: boolean;
  identical: boolean;
  reason: string | null;
  lines: ArtifactDiffLineDto[];
  stats: ArtifactDiffStatsDto;
  truncated: boolean;
  note: string;
}

/** 工作区快照读取能力：未配置快照根时 configured=false + note（不伪装计数）。 */
export interface WorkspaceSnapshotCapabilityDto {
  configured: boolean;
  retained_snapshots: number;
  max_files_per_snapshot: number;
  note: string;
}

export interface WorkspaceSnapshotFileDto {
  path: string;
  size_bytes: number;
  sha256: string;
}

export interface WorkspaceSnapshotTreeDto {
  digest: string;
  files: WorkspaceSnapshotFileDto[];
  file_count: number;
  total_bytes: number;
  truncated: boolean;
}

export interface WorkspaceSnapshotChangeDto {
  path: string;
  kind: string;
  left_sha256: string | null;
  right_sha256: string | null;
  left_size_bytes: number | null;
  right_size_bytes: number | null;
}

/** 两个快照的文件级 diff（只比路径/大小/sha256；内容行级 diff 在制品侧）。 */
export interface WorkspaceSnapshotDiffDto {
  left_digest: string;
  right_digest: string;
  comparison: string;
  identical: boolean;
  added: number;
  removed: number;
  changed: number;
  unchanged: number;
  changes: WorkspaceSnapshotChangeDto[];
  truncated: boolean;
  note: string;
}

export interface RunWorkspaceSnapshotDto {
  digest: string;
  recorded_as: string[];
  retained: boolean;
}

export interface RunWorkspaceSnapshotsDto {
  run_id: string;
  snapshots: RunWorkspaceSnapshotDto[];
  note: string;
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

/** 注册请求（G15 / PLAN-060）：pinned_revision 必须是 sha256:<hex> 内容寻址 pin。 */
export interface ToolProviderRegisterDto {
  id: string;
  kind: string;
  capabilities: string[];
  pinned_revision: string;
  effect_class?: string;
  transport?: string | null;
  protocol_version?: string | null;
  network_domains?: string[];
  health_check?: boolean;
  /** 端点来源**声明**：环境变量名，其值是端点 URL（只存变量名，值不进读面）。 */
  endpoint_env?: string | null;
  /** **必需**凭据的引用名（声明即必需；只存引用名，凭据值不进读面）。 */
  credential_ref?: string | null;
}

export interface ToolProviderUpdateDto {
  capabilities?: string[];
  pinned_revision?: string;
  effect_class?: string;
  transport?: string | null;
  protocol_version?: string | null;
  network_domains?: string[];
  health_check?: boolean;
  endpoint_env?: string | null;
  credential_ref?: string | null;
}

/**
 * `endpoint_env` 的解析结果（PLAN-072）：只有状态 / 变量名 / 指纹。
 * BOUND = 环境变量已设置（此时才有 fingerprint）；ENV_UNSET = 声明了但没设置；
 * NOT_DECLARED = 没声明过。端点明文不进读面。
 */
export interface ToolProviderEndpointBindingDto {
  state: string;
  env_name: string | null;
  endpoint_digest: string | null;
}

/**
 * `credential_ref` 的**存在性**判定结果（PLAN-074）：状态 / 引用名 / 是否在场。
 * PRESENT = 声明的必需凭据当前可解析；ABSENT = 声明了但解析不到（provider 不可用）；
 * NOT_DECLARED = 没声明过；UNCHECKED = 存在性检查本身不可用（不猜）。凭据值不进读面。
 */
export interface ToolProviderCredentialBindingDto {
  state: string;
  credential_ref: string | null;
  present: boolean;
}

export interface ToolProviderRegistrationDto {
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
  registered_at: string | null;
  updated_at: string | null;
  approved_at: string | null;
  revoked_at: string | null;
  revoked_reason: string | null;
  last_health: string | null;
  health_detail: string | null;
  health_checked_at: string | null;
  /** 最近一次复核观测到的 schema 指纹；null = 至今没观测到（≠ 没有漂移）。 */
  last_schema_digest: string | null;
  /** 比对基线（首次观测值，或被批准接受的值）。 */
  schema_baseline_digest: string | null;
  /** 当前观测是否已偏离基线（状态语义，不是"上次 vs 这次"）。 */
  schema_drift: boolean;
  schema_drift_since: string | null;
  /** 端点绑定三态（现算：取决于进程环境此刻的样子，不是注册时写下的声明）。 */
  endpoint_binding: ToolProviderEndpointBindingDto;
  /** 凭据绑定（现算：只查存在性，凭据值不进读面）。 */
  credential_binding: ToolProviderCredentialBindingDto;
  catalog_active: boolean;
}

export interface ToolProviderRegistrationListDto {
  registrations: ToolProviderRegistrationDto[];
  management_available: boolean;
  management_reason: string | null;
  note: string;
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

export interface ProjectLineageNodeDto {
  id: string;
  kind: string;
  label: string;
  run_ids: string[];
  shared: boolean;
}

export interface ProjectLineageResourceDto {
  id: string;
  kind: ResourceKind;
  name: string;
  status: ResourceStatus;
}

export interface ProjectLineageDto {
  project_id: string;
  run_count: number;
  nodes: ProjectLineageNodeDto[];
  edges: LineageEdgeDto[];
  library_resources: ProjectLineageResourceDto[];
  reference_recording: string;
  reference_recording_reason: string | null;
  degraded: boolean;
  degraded_reason: string | null;
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
  /** 规则只做静音标记，不隐藏告警（看不见的问题更难修）。 */
  muted: boolean;
  muted_by: string | null;
  /** 来源 run 已有未关闭事故时带回事故 id（写面被读面消费）。 */
  incident_id: string | null;
}

export interface AlertsViewDto {
  alerts: AlertItemDto[];
  rules_available: boolean;
  rules_reason: string | null;
  rules_applied: number;
  muted_count: number;
}

export interface AlertRuleDto {
  id: string;
  project_id: string;
  name: string;
  kind: string | null;
  max_severity: string | null;
  enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface AlertRulesViewDto {
  rules: AlertRuleDto[];
  rules_available: boolean;
  rules_reason: string | null;
}

export interface AlertRuleWriteDto {
  name: string;
  kind?: string | null;
  max_severity?: string | null;
  enabled?: boolean;
}

export interface AlertRulePatchDto {
  name?: string;
  kind?: string | null;
  max_severity?: string | null;
  enabled?: boolean;
  clear_kind?: boolean;
  clear_max_severity?: boolean;
}

/** 已登记事故（declare/assign/close 的真实状态）。 */
export interface IncidentItemDto {
  id: string;
  title: string;
  severity: string;
  status: string;
  run_id: string | null;
  assignee: string | null;
  resolution: string | null;
  opened_at: string | null;
  updated_at: string | null;
  closed_at: string | null;
}

/** 派生候选（FAILED run）；失败 Run 不自动登记为事故。 */
export interface IncidentCandidateDto {
  run_id: string;
  protocol_id: string;
  state: string;
  updated_at: string;
}

export interface IncidentsViewDto {
  incidents: IncidentItemDto[];
  candidates: IncidentCandidateDto[];
  workflow_available: boolean;
  workflow_reason: string | null;
}

export interface IncidentDeclareDto {
  title: string;
  severity?: string;
  run_id?: string | null;
}

export interface IncidentAssignDto {
  assignee: string;
}

export interface IncidentCloseDto {
  resolution: string;
}

export interface ScheduleJobDto {
  job: string;
  purpose: string;
}

export interface ScheduleEntryDto {
  name: string;
  job: string;
  interval_seconds: number;
  purpose: string;
  enabled: boolean;
  builtin: boolean;
  note: string;
  executor_attached: boolean;
  run_count: number;
  last_run_at: string | null;
  last_outcome: string | null;
  last_error: string | null;
  next_due_at: string | null;
}

export interface SchedulesViewDto {
  schedules: ScheduleEntryDto[];
  jobs: ScheduleJobDto[];
  note: string;
  management_available: boolean;
  management_reason: string | null;
}

export interface ScheduleCreateDto {
  name: string;
  job: string;
  interval_seconds: number;
  enabled: boolean;
  note?: string;
}

export interface ScheduleUpdateDto {
  enabled?: boolean | null;
  interval_seconds?: number | null;
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

/** G14 实验队列 DTO（状态来自域状态机；不发明进度字段）。 */
export interface ExperimentQueueEnqueueDto {
  protocol_path?: string | null;
  draft_id?: string | null;
  draft_revision?: number | null;
  not_before?: string | null;
}

export interface ExperimentQueueEntryDto {
  id: string;
  project_id: string;
  plan_id: string;
  plan_name: string | null;
  protocol_path: string | null;
  draft_id: string | null;
  draft_revision: number | null;
  state: string;
  not_before: string | null;
  claimed_at: string | null;
  run_id: string | null;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExperimentQueueViewDto {
  entries: ExperimentQueueEntryDto[];
  dispatch_note: string;
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

/** WP-C（PLAN-049）策略面只读快照：声明规则 + 门链能力的逐 scope 有效判决。 */
export interface PolicyRuleViewDto {
  effect: string;
  capability: string | null;
  action: string | null;
  scope: string | null;
  constraints: Record<string, unknown>;
}

export interface GateCapabilityViewDto {
  capability: string;
  scopes: string[];
  effects: Record<string, string>;
  reasons: Record<string, string>;
}

export interface PolicyCapabilitiesDto {
  policy_id: string;
  version: string;
  default_effect: string;
  source: string;
  rules: PolicyRuleViewDto[];
  gate_capabilities: GateCapabilityViewDto[];
  note: string;
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

export interface ToolPackPermissionDiffDto {
  added_capabilities: string[];
  added_network_domains: string[];
  added_credentials: string[];
}

/** 待批准的更新：未生效。`digest` 是**候选**版本，表里显示的是生效版本。 */
export interface ToolPackPendingDto {
  digest: string;
  version: string;
  capabilities: string[];
  diff: ToolPackPermissionDiffDto;
  note: string;
}

export interface ToolPackDto {
  id: string;
  state: string;
  digest: string;
  version: string;
  source: string;
  resolved_revision: string;
  license: string;
  capabilities: string[];
  network_domains: string[];
  credential_names: string[];
  tool_ids: string[];
  installed_at: string | null;
  revoked_reason: string | null;
  pending: ToolPackPendingDto | null;
  catalog_digest_active: boolean;
}

export interface ToolPackListDto {
  packs: ToolPackDto[];
  note: string;
  unavailable_reason: string | null;
}

export interface ToolPackSubmitResultDto {
  status: string;
  pack: ToolPackDto;
  diff: ToolPackPermissionDiffDto | null;
  note: string;
}
