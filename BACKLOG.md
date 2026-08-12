# Engineering Backlog v0.4.0

## M5R / P0 — Upstream Source Intelligence & Runtime Qualification

- [x] OpenHands SDK v1.42.0 源码级审计（Agent/Conversation/Events、LLM/Tools/MCP、Workspace/Context/Persistence/Security，file:path:symbol 级证据）
- [x] M5 14 Port 现实校验矩阵（5 个 adapter 承接 + 9 个 Research OS 自有；零结构性修正）
- [x] Executable spikes S1-S6（mock credential，全 PASS）+ SWE-ReX 对照
- [x] revision lock（机器可读）+ License Matrix 补充 + M6 三份文档（Design Notes / Risk Register / Readiness Report）
- [x] 裁决：M5R = PASS；M6 readiness = READY（无 BLOCK 级风险）

## M0 — Repository Foundation Quality Gate

- [x] Python 3.12 + uv exact lockfile
- [x] ruff + mypy strict + import-linter + pytest
- [x] pnpm exact lockfile + ESLint + dependency-cruiser + TypeScript
- [x] `domain / application / adapter / entry` architecture positive/negative tests
- [x] offline quality/contract test entrypoints without real LLM/network/credentials
- [x] Windows + Linux CI deterministic gate definition
- [x] system-spec / Cursor governance validators wired into CI

## M1 / P0 — Validation & Domain

- [x] bootstrap validation script in CI
- [x] Domain entities/enums/invariants
- [x] JSON/YAML schema loaders
- [x] Run/Phase/Task state machines
- [x] RunManifest + Revision + digest
- [x] append-only Usage Ledger
- [x] Artifact digest/verification

## M3 / P0 — Model Relay

- [x] LLMEndpoint CRUD + encrypted credential ref
- [x] manual ModelDefinition
- [x] endpoint test
- [x] optional model discovery
- [x] capability probe
- [x] ModelEligibilityPolicy
- [x] endpoint health/circuit breaker
- [x] ModelRuntimeFingerprint
- [x] fallback audit
- [x] secret redaction

## M4 / P0 — Role / Team / Task

- [x] 26 Role fixtures
- [x] Lean/Standard/Rigorous templates
- [x] Role activation/collapsing
- [x] per-Agent model binding
- [x] heterogeneous reviewer constraints
- [x] TaskContract / AcceptanceCriteria
- [x] HandoffBundle

## M2 / P0 — Protocol / Preflight

- [x] Protocol compiler
- [x] DAG validation
- [x] Role/model/tool/workspace resolution
- [x] BudgetReservation
- [x] Policy preflight
- [x] CompiledRunPlan / PreflightReport
- [x] dry-run projection

## M5 / P0 — Ports + Fakes

- [x] Port 全集冻结于 `packages/application/ports/`（AgentRuntime / WorkflowEngine / ModelGateway / ToolProvider / WorkspaceBackend / ExecutionBackend / ArtifactStore / EventPublisher / PolicyEvaluator / CredentialResolver / MemoryStore / BudgetLedger + EndpointStore / ResourceCatalog）
- [x] 统一错误模型 / cancellation / idempotency 语义（ports/errors.py）
- [x] 12 个 Fake 实现（adapters/fakes/，deterministic + 错误注入 + call recording + close）
- [x] Contract suite（tests/contracts/，注册表驱动，Fake 与真实 adapter 共用）
- [x] PolicyEvaluator 注入式 preflight（无直接实例化）
- [x] fakes import-linter 契约 + provider 类型泄漏架构断言
- [x] PORTS.md 规格 + AGENT_RUNTIME sync 修正

## M7 / P0 — Reliable Runtime

- [ ] PostgreSQL task queue
- [ ] TaskLease/heartbeat
- [ ] IdempotencyRecord
- [ ] Transactional Outbox
- [ ] retry/backoff/circuit breaker
- [ ] cancellation/compensation
- [ ] duplicate delivery tests
- [x] WorkflowEngine port + Fake（M5 完成语义冻结；M7 以 contract suite 验收持久化实现）

## M6 / P0 — OpenHands Adapter

- [ ] relay mapping
- [ ] Agent/Conversation lifecycle
- [ ] event normalization
- [ ] frozen Tool Set
- [ ] PolicyWrapped direct tool execution
- [ ] DockerWorkspace
- [ ] stuck mapping
- [ ] resume Manifest check
- [ ] conversation fork mapping
- [ ] plugin pin/digest

## P1 — Tool Plane

- [ ] ToolCatalog/Resolver
- [ ] Tool effect/risk classes
- [ ] MCP Streamable HTTP + stdio
- [ ] ToolPack manifest/install/update/revoke
- [ ] Tool health/circuit breaker
- [ ] Tool credential separation
- [ ] large result artifact indirection

## P1 — Memory / Evidence

- [ ] SourceRecord
- [ ] MemoryWriteProposal gate
- [ ] Memory lifecycle/delete
- [ ] derived vector index
- [ ] Claim/Evidence relations
- [ ] contradiction handling
- [ ] negative result memory

## P1 — Experiment / Artifact

- [ ] ExecutionBackend port
- [ ] WorkspaceLease/worktree
- [ ] ExperimentPlan/Run/Metric
- [ ] content-addressed Artifact Store
- [ ] retention/export bundle
- [ ] ReproducibilityAudit

## P1 — Evaluation

- [ ] Eval Harness modes
- [ ] deterministic gates
- [ ] reviewer panel
- [ ] human calibration samples
- [ ] canary/regression dashboard

## P2 — Product UI

- [ ] first-run relay wizard
- [ ] models/probe page
- [ ] team/agent model assignment
- [ ] protocol/preflight dry run
- [ ] task/run timeline
- [ ] approvals/interventions
- [ ] workspace diff
- [ ] evidence/claim map
- [ ] budget/usage
- [ ] audit/export

## P2 — Production

- [ ] Temporal adapter
- [ ] OPA adapter
- [ ] central Secret Manager
- [ ] remote/hardened sandbox
- [ ] OTel collector/dashboards
- [ ] backup/restore
- [ ] RBAC/organization scope
