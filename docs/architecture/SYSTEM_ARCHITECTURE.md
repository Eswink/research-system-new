# System Architecture v0.4.0

## 1. Control / Execution / Data 三平面

```text
┌──────────────────────── Control Plane ────────────────────────┐
│ Next.js Console                                               │
│ FastAPI API                                                   │
│ Protocol Compiler / Preflight                                 │
│ WorkflowEngine / Scheduler                                    │
│ Role/Model/Tool Resolver                                      │
│ Policy / Budget / Approval                                    │
└────────────────────────────┬───────────────────────────────────┘
                             │ Compiled Tasks
┌──────────────────────── Execution Plane ───────────────────────┐
│ AgentRuntime Port                                             │
│   └ OpenHandsRuntimeAdapter                                   │
│ Model Gateway → User Relay                                    │
│ Tool Runtime → Native / MCP / REST                            │
│ Workspace / Execution → Local / Docker / Remote / HPC         │
│ Workers / Leases / Heartbeats                                 │
└────────────────────────────┬───────────────────────────────────┘
                             │ Events / Artifacts
┌────────────────────────── Data Plane ──────────────────────────┐
│ PostgreSQL canonical entities                                 │
│ Transactional Outbox / Audit Events                           │
│ S3/MinIO content-addressed artifacts                          │
│ Secret Store                                                  │
│ Derived search/vector indexes                                 │
│ OTel/MLflow telemetry                                         │
└────────────────────────────────────────────────────────────────┘
```

## 2. 主链

```text
Project Draft
→ ProtocolDefinition
→ ProtocolCompiler
→ CompiledRunPlan
→ PreflightReport
→ RunManifest
→ WorkflowEngine
→ ResearchTask
→ AgentSession
→ HandoffBundle
→ Evidence / Experiment / Review
→ Quality Gates
→ Deliverable
```

## 3. 代码所有权与依赖方向

```text
apps/web
└─ UI entry adapter；只消费 API DTO，不持有后端 Canonical State

services/*
├─ inbound entry adapter
└─ composition root；装配 use case、Port 与具体 adapter

packages/application
├─ use cases / orchestration
├─ inward-owned Ports
└─ API DTO ↔ Domain 显式映射

packages/domain
├─ 纯实体、值对象、决策、事件与状态机
└─ protocols/tasks/roles/models/tools/... 作为内部领域模块

adapters/*
└─ 实现 application Ports；承接外部 I/O 与副作用
```

M0 在 `tests/architecture/` 中用双语言正反向夹具固化这些边界；M1-M7 已
按此边界落地真实实现：`packages/domain/`（29 模块）、
`packages/application/`（protocol_compile / preflight / model_relay /
policy / ports / run_orchestration）、`adapters/`（contracts / fakes /
relay / openhands / sqlite）。新生产模块进入时，必须同时声明语言/包归属、
公开入口和相应测试。

编译期依赖只允许：

```text
apps / services / adapters → packages/application → packages/domain
```

`packages/application` 不 import 具体 adapter；`packages/domain` 不知道 Web、ORM、LLM、OpenHands、Workflow 或 provider SDK。具体实现只由 `services/*` composition root 注入。

运行时控制流与源码依赖方向分开表达：

```text
Inbound:
entry adapter → application use case → domain

Outbound:
application use case → inward-owned Port → injected adapter
```

## 4. 关键端口

```text
WorkflowEngine
AgentRuntime
ModelGateway
ToolProvider
WorkspaceBackend
ExecutionBackend
ArtifactStore
PolicyEvaluator
CredentialResolver
BudgetLedger
MemoryStore
EventPublisher
Evaluator
```

Domain 不依赖具体实现。

## 5. Model Runtime

```text
AgentSpec
→ ModelBinding
→ ModelResolver
→ ModelEligibility
→ ModelDefinition
→ LLMEndpoint
→ OpenHands LLM config
→ User Relay
```

## 6. Tool Runtime

```text
Requested Capabilities
∩ Policy
∩ Workspace Lease
∩ Provider Health
→ Effective Tool Set
→ freeze in AgentSession
```

## 7. Durable Boundary

### Domain State
业务真相。

### Workflow State
调度/重试/等待。

### Agent Runtime State
对话/工具循环。

### Telemetry
诊断信息。

四者关联，不互相替代。

### 当前实现状态（M7，2026-08-14）

- Canonical State 的规格目标是 PostgreSQL Domain Entity（ADR-0002）；
  M7 垂直切片经同一 WorkflowEngine / ArtifactStore / EventPublisher
  Port 使用 `adapters/sqlite/` 实现（SqliteWorkflowEngine /
  SqliteArtifactStore / SqliteOutboxEventPublisher）。SQLite 是可替换
  实现，contract suite（`tests/contracts/`）是 PostgreSQL 生产实现的
  验收基线；PostgreSQL 属于 Remaining Technical Debt（`BACKLOG.md`）。
- 内容寻址 Artifact 由 `SqliteArtifactStore`（本地 blob）提供；S3/MinIO
  对象存储为生产部署演进目标，同 ArtifactStore Port。
- Next.js Console / FastAPI API / Secret Store / OTel 为部署演进目标
  （归属 M13 / M15 / M19，见 `docs/roadmap/MILESTONES.md` Post-M7
  Roadmap），当前以离线质量门禁与 `tests/e2e/` 验证内核行为。

## 8. 数据一致性

Domain 写入与 Event 发布采用 Transactional Outbox。

Worker 执行按 at-least-once 设计，业务副作用通过 idempotency/lease/dedupe 控制。

## 9. 部署演进

```text
Local Developer
→ Self-hosted Team
→ Distributed/Hardened
```

不要求第一版一次性上线 Temporal、OPA、Kubernetes 或微虚拟机，但所有边界预留 adapter。
