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

## M7 / P0 — Reliable Runtime（M7 完成，2026-08-13）

- [x] ResearchRun 实体 + Run 状态机真实迁移（`packages/domain/run.py`）
- [x] RunOrchestrationService 端到端编排（Compile → Preflight → Freeze → TeamResolve → Execute → Evidence/Claim → Gate → Complete，`packages/application/run_orchestration/`）
- [x] SQLite 持久化三件套：`SqliteWorkflowEngine`（tasks/leases/idempotency_records/outbox_events）+ `SqliteArtifactStore`（内容寻址 blob）+ `SqliteOutboxEventPublisher`（Transactional Outbox）
- [x] TaskLease/heartbeat + 重启恢复（`recover_expired_leases`，进程重启模拟测试）
- [x] IdempotencyRecord（submit 幂等去重 + request_digest）
- [x] Transactional Outbox（业务写入与事件同事务，EVENT_MODEL.md §3）
- [x] retry/backoff（TransientPortError + retryable_categories 门控，F-01/F-02）
- [x] cancellation/compensation（协作式 cancel + lease 释放 + CANCELLED 事件，幂等）
- [x] duplicate delivery tests（F-07 + idempotency 套件）
- [x] Reference Scenario `examples/protocols/sort_analysis_v1.yaml`（2-phase，2 roles）
- [x] E2E 故障注入矩阵 F-01..F-12（tests/e2e/）
- [x] Pause/Resume（frozen manifest 语义 + digest mismatch 拒绝）
- [x] WorkflowEngine port + Fake（M5 完成语义冻结；M7 以 contract suite 验收持久化实现）
- [x] resume Manifest check（M6 遗留项完成：`task_executor._assert_frozen_manifest` 按 AGENTS.md §5 强制）
- [x] RunManifestRevision.changes 结构不变量（非空 + str key，M7 复审技术债清偿）
- [ ] PostgreSQL task queue（生产升级路径，同 Port 契约；跨进程分布式调度属 Temporal 阶段）
- [ ] recover_expired_leases 定时自愈（当前为 start_run 懒触发，单进程安全；定时调度属 Temporal/P2-Production 范畴）
- [ ] ModelRelay + OpenHandsRuntimeAdapter usage 归账闭环到 BudgetLedger（M8 接入，前提：真实 relay 链路 E2E）
- [ ] 历史 Run 快照运营迁移（`manifest_semantic_digest=None` 的旧快照不可 resume：需重新冻结或 fork run；无自动迁移路径）

## M6 / P0 — OpenHands Adapter（M6 完成，2026-08-13）

- [x] relay mapping（`adapters/openhands/llm_factory.py`：三要素透传 + runtime model identifier 变换；S7 mock 端点实证）
- [x] Agent/Conversation lifecycle（`adapters/openhands/runtime_adapter.py`：create/run/pause/cancel/stream_events/fork 全通过）
- [x] event normalization（`adapters/openhands/event_mapping.py`：SDK 事件树 → RuntimeEvent 显式映射）
- [x] frozen Tool Set（`AgentSessionSpec.frozen_tool_set` → Tool spec 装配；tool_mapping 单测）
- [x] PolicyWrapped direct tool execution + agent loop 策略门禁（`policy_wrapper.py` DENY 阻断 + approval 事件；`policy_enforcing_agent.py` 在 SDK 工具执行点强制 PolicyEvaluator，复审 M6-6 修正）
- [x] DockerWorkspace（映射代码 `workspace_adapter.build_docker_workspace` + 探测式 smoke；容器链路验证延后 M7）
- [x] stuck mapping（`runtime_adapter.map_status_to_domain`：STUCK 收敛 FAILED，M6 无自动恢复路径）
- [ ] resume Manifest check（Manifest compatibility 检查在 M6 范围外：M6 会话无 resume 入口，Fork 直接新会话；M7 接入时按 AGENTS.md §5 强制）→ M7 完成（task_executor._assert_frozen_manifest）
- [x] conversation fork mapping（`runtime_adapter.fork`：新 lineage 会话；ForkSpec override 重建 LLM/工具集，复审 M6-8 修正）
- [x] usage → BudgetLedger（run() 终态归一化写入，signal 语义，复审 M6-7 修正）
- [ ] plugin pin/digest（M6 未引入插件；UPSTREAM_COMPONENTS controls 保持，引入时强制 digest 门禁）

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
