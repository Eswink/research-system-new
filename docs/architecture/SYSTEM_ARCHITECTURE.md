# System Architecture v0.2.2

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

## 3. 关键端口

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

## 4. Model Runtime

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

## 5. Tool Runtime

```text
Requested Capabilities
∩ Policy
∩ Workspace Lease
∩ Provider Health
→ Effective Tool Set
→ freeze in AgentSession
```

## 6. Durable Boundary

### Domain State
业务真相。

### Workflow State
调度/重试/等待。

### Agent Runtime State
对话/工具循环。

### Telemetry
诊断信息。

四者关联，不互相替代。

## 7. 数据一致性

Domain 写入与 Event 发布采用 Transactional Outbox。

Worker 执行按 at-least-once 设计，业务副作用通过 idempotency/lease/dedupe 控制。

## 8. 部署演进

```text
Local Developer
→ Self-hosted Team
→ Distributed/Hardened
```

不要求第一版一次性上线 Temporal、OPA、Kubernetes 或微虚拟机，但所有边界预留 adapter。
