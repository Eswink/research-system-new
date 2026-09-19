# Domain Model v0.4.0

## 1. Project / Run

### Project

```text
id
owner_scope
name
objective
target_profile
default_team_template_id
default_model_profile_id
data_classification
status
```

### ResearchRun

```text
id
project_id
protocol_version_id
compiled_plan_id
manifest_id
autonomy_level
status
started_at
completed_at
```

### RunManifest

不可变语义快照：

```text
protocol/compiled plan hash
source commit
role definitions
agent specs
resolved models
model runtime fingerprints
effective tools/tool pack digests
task contracts          # 引用契约的冻结快照（M7 补充，防契约漂移）
policy version
context template hashes
workspace/execution backend
environment
input artifact digests
budget reservation
```

`digest()` 覆盖全部声明字段；`semantic_digest()` 排除 `frozen_at`
（冻结时刻元数据不参与语义比对），用于 resume 时校验 plan/catalog/契约
未漂移（WORKFLOW_RELIABILITY.md §8）。**部分字段已有来源**：`execution_backend` 由
组合根的选择面写入、`model_runtime_fingerprints` 由该选择面给出**状态**记录
（GOAL-007 EC-01/EC-04，见 AGENT_RUNTIME.md §3.1 与 §3.3）；其余 M7 期无法从
compile/preflight 上下文获取的字段（source_commit、context_template_hashes、
environment、input_artifact_digests）保持 None/空，**不伪填充**——「有来源」与
「没来源」必须分开说（见 packages/domain/manifest.py 的 M7 边界声明）。

### RunManifestRevision

运行中改变模型、Tool Set、Policy、重要 Context Template 时，不允许原地修改 Manifest。

只能：

```text
fork run
or
explicit revision + approval + audit
```

## 2. Compile / Preflight

### CompiledRunPlan

解析完成的：

```text
phase DAG
task templates
role pools
agent candidates
model eligibility
tool requirements
workspace/compute requirements
budgets
gates
stop conditions
role activations   # Role 激活/折叠投影（RoleActivationRecord）
phase assignments  # phase → role → agent 稳定绑定（PhaseAssignment）
```

### PreflightReport

包含：

```text
PASS / FAIL / WARN
findings[]
estimated cost
reserved budget
unresolved risks
```

## 3. Role / Team / Agent

```text
RoleDefinition
TeamTemplate
ActivationPolicy / RoleActivationDecision（packages/domain/activation.py）
RolePool
AgentSpec（model_binding + skill_refs + capability_refs + workspace/context/runtime/budget）
AgentRun
AgentSession
```

Role 不绑定具体 ModelDefinition（ADR-0011）；Role 通过 `default_skills` 声明可折叠
等价 Skill，通过 `forbidden_capabilities` 声明权限边界（Reviewer 只读 / Writer 不
得改 Claim truth / ExperimentEngineer 不得外部发布）。Agent 配置面见
`schemas/agent-spec.schema.json`；激活/折叠与 phase 绑定投影进入
CompiledRunPlan（role_activations / phase_assignments）。

## 4. Task / Handoff

### ResearchTask

```text
id
run_id
phase_run_id
contract_id
assigned_agent_id?
status
priority
attempt
idempotency_key
lease_id?
```

### TaskContract

```text
id
version
purpose
input_schema
output_schema
required_capabilities
required_artifacts
acceptance_criteria
budget
timeout_seconds
retry_policy
failure_policy
idempotency_scope
```

实现：`packages/domain/tasks.py`；结构化验收参数（artifact/minimum_sources/metric/
operator/threshold/evaluator）与求值器见 `packages/domain/acceptance.py`。

### HandoffBundle

```text
task_id
producer
producer_agent_id?
producer_role_id?
summary
created_at
structured_output
artifact_refs
claim/evidence refs
decision_refs
open_questions
known_failures
recommended_next_actions
digest
```

实现：`packages/domain/tasks.py`；加载器 `adapters/contracts/tasks_loaders.py::load_handoff_bundles`。

## 5. Model

```text
LLMEndpoint
EndpointHealth
ModelDefinition
ModelCapability
ModelCompatibilityProfile
ModelProbeResult
ModelProfile
ModelBinding
ModelRuntimeFingerprint
```

### ModelRuntimeFingerprint

尽可能记录：

```text
endpoint config digest
requested model ID
returned model identifier
system fingerprint
selected response metadata
probe suite/hash
observed capabilities
timestamp
```

## 6. Tool / Plugin

```text
SkillSpec
Capability
CapabilityGrant
ToolSpec
ToolProviderSpec
ToolPackManifest
ToolInstallation
ToolHealth
ToolCallRecord
ToolResultRecord
```

## 7. Workspace / Execution

```text
Workspace
WorkspaceLease
WorkspaceSnapshot
ExecutionSpec
ExecutionRun
ComputeReservation
```

## 8. Memory / Context

```text
ContextSnapshot
MemoryRecord
MemoryWriteProposal
MemorySnapshot
MemoryIndexProjection
```

`MemoryIndexProjection` 可重建，不是 canonical。

## 9. Budget / Quota

```text
BudgetPolicy
BudgetReservation
UsageLedgerEntry
QuotaPolicy
```

成本未知时，使用 token/request/compute 上限作为硬边界。

## 10. Approval / Intervention

```text
ApprovalRequest
ApprovalDecision
Intervention
```

例如：

- 增加预算；
- 新网络域；
- 安装依赖；
- 修改 Tool Set；
- 替换模型；
- 发布 Deliverable。

## 11. Evidence / Sources / Experiments

```text
SourceRecord
Claim
Evidence              # artifact_id 强引用生产 Artifact（M7 补充，弱 source_ref 之外的第二锚点）
EvidenceRelation
ExperimentPlan
ExperimentRun
Metric
Artifact
Decision
ReviewFinding
Deliverable
```

## 12. Reliability

```text
TaskLease
RetryAttempt
FailureRecord
CompensationAction
OutboxEvent
IdempotencyRecord
```
