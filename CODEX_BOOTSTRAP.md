# CODEX_BOOTSTRAP.md — v0.2.2 Engineering Bootstrap

## 目标

先实现可验证的软件内核，而不是完整 Autonomous Research。

MVP 必须保持：

```text
User LLM Relay
+ Per-Agent Model Binding
+ OpenHands Native Runtime
+ Existing Tool/MCP/Workspace Wheels
```

## M0 — Repository Foundation

```text
apps/web
services/api
services/orchestrator
services/evaluator
services/tool_gateway

packages/domain
packages/protocols
packages/tasks
packages/roles
packages/models
packages/tools
packages/workspace
packages/policies
packages/memory
packages/provenance
packages/events
packages/budget
packages/observability

adapters/openhands
adapters/local_workflow
adapters/postgres
adapters/object_store

tests/contracts
scripts
infra
```

Python：

- 3.12+
- uv
- Pydantic v2
- SQLAlchemy 2
- Alembic
- pytest
- ruff
- mypy

Web：

- pnpm
- Next.js
- TypeScript

## M1 — Domain Kernel

优先实体：

```text
Project
ResearchRun
RunManifest
RunManifestRevision
ProtocolDefinition
ProtocolVersion
CompiledRunPlan
PreflightReport
PhaseRun

RoleDefinition
TeamTemplate
RoleActivationPolicy
AgentSpec
AgentRun
AgentSession

ResearchTask
TaskContract
AcceptanceCriterion
HandoffBundle
TaskLease
FailureRecord

LLMEndpoint
EndpointHealth
ModelDefinition
ModelCapability
ModelCompatibilityProfile
ModelProbeResult
ModelProfile
ModelBinding
ModelRuntimeFingerprint

SkillSpec
Capability
CapabilityGrant
ToolSpec
ToolProviderSpec
ToolPackManifest
ToolInstallation
ToolCallRecord
ToolResultRecord

Workspace
WorkspaceLease
WorkspaceSnapshot
ExecutionSpec

ContextSnapshot
MemoryRecord
MemoryWriteProposal
MemorySnapshot

Claim
Evidence
EvidenceRelation
SourceRecord
ExperimentPlan
ExperimentRun
Artifact
ArtifactRetentionPolicy
Decision
ReviewFinding

BudgetPolicy
BudgetReservation
UsageLedgerEntry
QuotaPolicy
ApprovalRequest
Intervention
```

要求：

- 无 upstream 类型
- stable enum
- UUID
- UTC
- Decimal/最小货币单位
- JSON round-trip
- deterministic digest
- invariant tests

## M2 — Protocol Compiler + Preflight

实现：

```text
ProtocolDefinition
→ validate
→ resolve Roles/Agents
→ resolve Models
→ resolve Tools
→ resolve Workspace/Compute
→ reserve Budget
→ evaluate Policy
→ CompiledRunPlan
→ PreflightReport
```

Preflight 失败必须给出机器可读 finding。

## M3 — Model Relay Compatibility

实现：

- OpenAI-compatible Endpoint
- manual Model ID
- optional `/models`
- connectivity/auth/model probe
- tool calling/structured output probe
- ModelEligibilityPolicy
- endpoint health/circuit breaker
- runtime fingerprint
- secret redaction

## M4 — Role/Team/Task

实现：

- 26 个 Role fixtures
- Lean / Standard / Rigorous TeamTemplate
- RolePool
- same-role multi-model Agent
- TaskContract
- HandoffBundle
- AcceptanceCriteria
- structured output validation

## M5 — Ports + Fakes

```text
WorkflowEngine
AgentRuntime
ModelGateway
ToolProvider
WorkspaceBackend
ExecutionBackend
ArtifactStore
EventPublisher
PolicyEvaluator
CredentialResolver
MemoryStore
BudgetLedger
```

提供 Fake 实现和 contract suite。

## M6 — OpenHands Spike

验证：

```text
User Relay
→ ModelDefinition
→ OpenHands LLM
→ Agent
→ Conversation
→ frozen tool set
→ safe workspace
→ normalized events
```

额外验证：

- direct tool execution 必须经过 Policy Wrapper
- resume 时 Manifest compatibility
- tool-set drift 拒绝或 fork
- plugin refs pin
- secrets 不进入 Domain/log

## M7 — Reliable Mock Vertical Slice

```text
Project
→ TeamTemplate
→ Protocol Compile
→ Preflight
→ Freeze Manifest
→ Create Task
→ Acquire Lease
→ Agent Session
→ Tool Call
→ Handoff
→ Artifact
→ Evidence
→ Claim
→ Evaluation
→ Complete
```

注入故障：

- transient model failure
- duplicate task delivery
- tool timeout
- worker crash
- budget exhaustion
- user pause/cancel

## Definition of Done

- `scripts/validate_bundle.py` 通过
- Domain tests 通过
- Role/Model/Protocol references 完整
- Preflight 能拒绝不兼容模型
- duplicate task 不产生重复副作用
- Run resume 不允许静默模型漂移
- tool credentials 与 LLM credential 隔离
- Reviewer read-only
- Writer 不能升级 Claim truth
- OpenHands adapter contract 通过
