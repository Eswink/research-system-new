# Domain Model v0.2.2

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
policy version
context template hashes
workspace/execution backend
environment
input artifact digests
budget reservation
```

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
RoleActivationPolicy
RolePool
AgentSpec
AgentRun
AgentSession
```

Role 不绑定具体 ModelDefinition。

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
input_schema
output_schema
required_artifacts
acceptance_criteria
capabilities
budget
timeout
retry_policy
failure_policy
```

### HandoffBundle

```text
task_id
producer
summary
structured_output
artifact_refs
claim/evidence refs
open_questions
known_failures
recommended_next_actions
digest
```

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
Evidence
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
