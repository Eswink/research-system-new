# CODEX_BOOTSTRAP.md — Research OS Cursor Engineering Bootstrap v0.4.0

## Current Engineering State（2026-08-14）

```text
Foundation / Executable Research Kernel = completed（M0-M7 含 M5R）
```

M0-M7 核心基础设施阶段**已完成**，真实完成顺序：
`M0 → M1 → M3 → M2 → M4 → M5 → M5R → M6 → M7`（M3 先于 M2：M2 Preflight
消费 M3 Model Relay 产物）。完成矩阵见
[docs/roadmap/COMPLETION_MATRIX_M0_M7.md](docs/roadmap/COMPLETION_MATRIX_M0_M7.md)，
M7 集成里程碑记录见
[docs/roadmap/M7_COMPLETION_RECORD.md](docs/roadmap/M7_COMPLETION_RECORD.md)。

### 新 Agent 开始工作时首先检查

1. 根 `VERSION`（= 0.4.0，唯一版本源）与 `AGENTS.md`（工程契约）。
2. `docs/INDEX.md` 与 `BACKLOG.md`（完成事项 / 技术债 / 下一能力）。
3. `docs/roadmap/COMPLETION_MATRIX_M0_M7.md`（各阶段证据入口）。
4. `docs/architecture/PORTS.md` 与 `DOMAIN_MODEL.md`（当前契约现状）。

### 已冻结（稳定 Contract，M7 后不再日常变更）

- Domain 实体/值对象/枚举/状态机（`packages/domain/`）与 JSON Schema
  （`schemas/`）交叉引用校验（`validate_bundle.py`）。
- Protocol Compiler → Preflight → Manifest Freeze 链与机器可读
  CompiledRunPlan/PreflightReport。
- 14 个 inward-owned Ports（`packages/application/ports/`）+ 统一错误模型
  + contract suite（`tests/contracts/`，注册表驱动）。
- 可靠性语义：at-least-once + idempotency + Transactional Outbox；
  TaskLease/heartbeat/recover_expired_leases。
- OpenHands adapter 边界：openhands-sdk **v1.42.0@391fbb8d**（revision
  lock + sdist digest，见 `docs/references/upstream/OPENHANDS_REVISION_LOCK.yaml`）。
- M0 工程门禁（m0 profile 全量回归）作为每阶段/每次变更的确定性验收。

### 可继续演进（不视为冻结）

- `adapters/sqlite/` → PostgreSQL（同 Port 契约；技术债，BACKLOG）。
- ExecutionBackend 容器实现 / DockerWorkspace 全量验证（技术债）。
- Tool Plane、Skill Registry、Evidence/Memory、Evaluation Plane、
  Research Console、Durable Workflow（BACKLOG Next Product Capability）。
- 规格目标（PostgreSQL Canonical State，ADR-0002）与当前实现的差异
  显式记录，不以文档覆盖实现。

---

## 历史说明（Bootstrap 定义，已完成里程碑）

> 以下章节是 M0-M7 开发期的里程碑定义（canonical milestone details），
> 保留工程价值；各阶段现状与证据以
> `docs/roadmap/COMPLETION_MATRIX_M0_M7.md` 为准。

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

## M6 — OpenHands Spike（已完成 2026-08-13，commit `f4b2168`；定义保留）

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

## M7 — Reliable Mock Vertical Slice（已完成 2026-08-14，commit `782887d`；定义保留）

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
