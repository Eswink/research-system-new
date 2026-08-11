# CODEX_BOOTSTRAP.md — Research OS Cursor Engineering Bootstrap v0.4.0

## 目标

先实现可验证的软件内核，而不是完整 Autonomous Research。

MVP 必须保持：

```text
User LLM Relay
+ Per-Agent Model Binding
+ OpenHands Native Runtime
+ Existing Tool/MCP/Workspace Wheels
```

## M0 — Repository Foundation Quality Gate

M0 固化的目标模块边界如下；本阶段不创建只有占位文件的生产目录：

```text
apps/web

services/*

packages/domain
packages/application

adapters/*

tests/architecture
infra
```

当前通过 `tests/architecture/python` 与 `tests/architecture/typescript` 的正反向夹具证明依赖规则能够放行正确图并拒绝错误图。上述生产目录只在首个真实职责模块及其测试同时进入时创建，避免用空包制造假门禁。

职责边界：

```text
apps/web
→ UI entry adapter，只消费 API DTO，不复制 Canonical State

services/*
→ entry adapter + composition root，负责装配 use case 与具体 adapter

packages/application
→ use cases + inward-owned Ports + DTO/Domain 映射

packages/domain
→ 纯实体、值对象、决策、事件和状态机
  protocols/tasks/roles/models/tools/... 是内部领域模块，不提前拆成互相依赖的顶层包

adapters/*
→ 实现 application Ports，承接 OpenHands、数据库、对象存储和工作流副作用
```

编译期依赖：

```text
apps / services / adapters → packages/application → packages/domain
```

运行时出站调用：

```text
application use case → inward-owned Port → injected adapter
```

Python：

- 3.12+
- uv + exact lockfile
- pytest
- ruff
- mypy strict
- import-linter

Web：

- pnpm + exact lockfile
- TypeScript
- ESLint
- dependency-cruiser

M0 完成条件：

- Windows/Linux 可从 lockfile 确定性安装；
- lint、strict typecheck、dependency boundary、unit/contract test 均有命令入口；
- CI 执行上述门禁及 system-spec / Cursor governance validators；
- composition root 是具体 adapter 的唯一装配位置；
- 不引入真实 LLM、OpenHands、数据库或 UI 业务行为。

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

- `.cursor/skills/system-spec-check/scripts/validate_bundle.py` 通过
- Domain tests 通过
- Role/Model/Protocol references 完整
- Preflight 能拒绝不兼容模型
- duplicate task 不产生重复副作用
- Run resume 不允许静默模型漂移
- tool credentials 与 LLM credential 隔离
- Reviewer read-only
- Writer 不能升级 Claim truth
- OpenHands adapter contract 通过
