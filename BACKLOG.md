# Engineering Backlog v0.4.0

## 当前工程状态

```text
Foundation / Executable Research Kernel（M0-M7 含 M5R）= completed
MVP 能力平面（M8-M11）= completed（2026-08-15）
M12 First Real Research Workflow = completed（R1 修复 + 2026-08-28 重判 PASS，RECHECK-20260828-023；DoD-3 live relay 凭据闭环）
M13 Research Console = completed（R1 修复 + 独立复审 PASS，2026-08-27）
M14 Durable Workflow + PostgreSQL = DONE（2026-08-28；WP-J2 重判 PASS，RECHECK-20260828-022）
```

M0-M11（含 M5R）全部完成（真实完成顺序：M0 → M1 → M3 → M2 → M4 → M5 →
M5R → M6 → M7 → M8 → M9 → M10 → M11 → M12 → M13）。完成矩阵见
`docs/roadmap/COMPLETION_MATRIX_M0_M11.md`（唯一权威），M7/M8/M9/M10/M11
集成里程碑见 `docs/roadmap/*_COMPLETION_RECORD.md`。M12/M13 完成事实与
R1 修复记录见 `docs/roadmap/M12_COMPLETION_RECORD.md` /
`M12_R1_COMPLETION_RECORD.md` / `M13_R1_COMPLETION_RECORD.md`；M12 原
PASS 判定经独立复审证伪并修复，2026-08-28 重新独立复审重判 **PASS**（RECHECK-20260828-023；DoD-3 live relay 凭据闭环后升 PASS）。本文件按三类组织：
**Completed**（已交付）、**Remaining Technical Debt**（已发现但不阻断）、
**Next Product Capability**（未来能力，非已实现事项）。

## Completed

### M0 — Repository Foundation Quality Gate（2026-08-11，commit `3cc6130`）

- [x] Python 3.12 + uv exact lockfile
- [x] ruff + mypy strict + import-linter + pytest
- [x] pnpm exact lockfile + ESLint + dependency-cruiser + TypeScript
- [x] `domain / application / adapter / entry` architecture positive/negative tests
- [x] offline quality/contract test entrypoints without real LLM/network/credentials
- [x] Windows + Linux CI deterministic gate definition
- [x] system-spec / Cursor governance validators wired into CI

### M1 / P0 — Validation & Domain（2026-08-11，commit `185a752`）

- [x] bootstrap validation script in CI
- [x] Domain entities/enums/invariants
- [x] JSON/YAML schema loaders
- [x] Run/Phase/Task state machines
- [x] RunManifest + Revision + digest
- [x] append-only Usage Ledger
- [x] Artifact digest/verification

### M3 / P0 — Model Relay（2026-08-11，commit `7bfcd3c`；先于 M2 完成）

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

### M2 / P0 — Protocol / Preflight（2026-08-12，commit `1035a64`；消费 M3 eligibility）

- [x] Protocol compiler
- [x] DAG validation
- [x] Role/model/tool/workspace resolution
- [x] BudgetReservation
- [x] Policy preflight
- [x] CompiledRunPlan / PreflightReport
- [x] dry-run projection

### M4 / P0 — Role / Team / Task（2026-08-12，commit `7c68e92`）

- [x] 26 Role fixtures
- [x] Lean/Standard/Rigorous templates
- [x] Role activation/collapsing
- [x] per-Agent model binding
- [x] heterogeneous reviewer constraints
- [x] TaskContract / AcceptanceCriteria
- [x] HandoffBundle

### M5 / P0 — Ports + Fakes（2026-08-12，commit `c75db51`）

- [x] Port 全集冻结于 `packages/application/ports/`（AgentRuntime / WorkflowEngine / ModelGateway / ToolProvider / WorkspaceBackend / ExecutionBackend / ArtifactStore / EventPublisher / PolicyEvaluator / CredentialResolver / MemoryStore / BudgetLedger + EndpointStore / ResourceCatalog）
- [x] 统一错误模型 / cancellation / idempotency 语义（ports/errors.py）
- [x] 12 个 Fake 实现（adapters/fakes/，deterministic + 错误注入 + call recording + close）
- [x] Contract suite（tests/contracts/，注册表驱动，Fake 与真实 adapter 共用）
- [x] PolicyEvaluator 注入式 preflight（无直接实例化）
- [x] fakes import-linter 契约 + provider 类型泄漏架构断言
- [x] PORTS.md 规格 + AGENT_RUNTIME sync 修正

### M5R / P0 — Upstream Source Intelligence & Runtime Qualification（2026-08-12/13，commits `717545d` + `5fc23d0`）

- [x] OpenHands SDK v1.42.0 源码级审计（Agent/Conversation/Events、LLM/Tools/MCP、Workspace/Context/Persistence/Security，file:path:symbol 级证据）
- [x] M5 14 Port 现实校验矩阵（5 个 adapter 承接 + 9 个 Research OS 自有；零结构性修正）
- [x] Executable spikes S1-S6（mock credential，全 PASS）+ SWE-ReX 对照
- [x] revision lock（机器可读）+ License Matrix 补充 + M6 三份文档（Design Notes / Risk Register / Readiness Report）
- [x] 裁决：M5R = PASS；M6 readiness = READY（无 BLOCK 级风险）

### M6 / P0 — OpenHands Adapter（2026-08-13，commit `f4b2168`）

- [x] relay mapping（`adapters/openhands/llm_factory.py`：三要素透传 + runtime model identifier 变换；S7 mock 端点实证）
- [x] Agent/Conversation lifecycle（`adapters/openhands/runtime_adapter.py`：create/run/pause/cancel/stream_events/fork 全通过）
- [x] event normalization（`adapters/openhands/event_mapping.py`：SDK 事件树 → RuntimeEvent 显式映射）
- [x] frozen Tool Set（`AgentSessionSpec.frozen_tool_set` → Tool spec 装配；tool_mapping 单测）
- [x] PolicyWrapped direct tool execution + agent loop 策略门禁（`policy_wrapper.py` DENY 阻断 + approval 事件；`policy_enforcing_agent.py` 在 SDK 工具执行点强制 PolicyEvaluator，复审 M6-6 修正）
- [x] DockerWorkspace（映射代码 `workspace_adapter.build_docker_workspace` + 探测式 smoke）
- [x] stuck mapping（`runtime_adapter.map_status_to_domain`：STUCK 收敛 FAILED，M6 无自动恢复路径）
- [x] resume Manifest check（M7 落实：`task_executor._assert_frozen_manifest` 按 AGENTS.md §5 强制，2026-08-14 勾选）
- [x] conversation fork mapping（`runtime_adapter.fork`：新 lineage 会话；ForkSpec override 重建 LLM/工具集，复审 M6-8 修正）
- [x] usage → BudgetLedger（run() 终态归一化写入，signal 语义，复审 M6-7 修正）
- [x] plugin pin/digest（M6 未引入插件；UPSTREAM_COMPONENTS controls 保持，引入时强制 digest 门禁）

### M7 / P0 — Reliable Mock Vertical Slice（2026-08-14，commit `782887d`）

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
- [x] resume Manifest check（`task_executor._assert_frozen_manifest` 按 AGENTS.md §5 强制）
- [x] RunManifestRevision.changes 结构不变量（非空 + str key，M7 复审技术债清偿）

### M7 收尾工程债（2026-08-14，PLAN-20260814-011）

- [x] ruff lint/format 闭环：`packages/application/run_orchestration/__init__.py`
      import 排序、`service.py` 2 个 unused imports、
      `tests/e2e/test_orchestration_convergence.py` import 排序 + 12 files
      `ruff format`；`ruff check packages adapters tests` 0 errors、
      `ruff format --check` 244 files 全过。
- [x] mypy strict 闭环（16 errors → 0，227 files Success）：
      `preflight.py` frozen_contracts 显式 `dict[str, object]`（RunManifest
      方差对齐）；`test_m2_policy_budget.py` Reserver 补齐 BudgetLedger
      protocol `release`；`test_run_rejections.py` capabilities 键改用
      `ModelCapability` 枚举；`test_fault_convergence.py` `_start` 返回
      `RunOutcome`；`test_cancel_resume.py` `_drift_parts` 用 TypedDict
      `DriftParts` + `RunManifest` 精确类型化。
- 验证：m0 profile 全绿（除 learning-evals 独立 P2 项）；pytest 989
      passed；validate_bundle + governance validate PASS。

### learning-evals fixture 污染修复（2026-08-14）

- [x] `run_cursor_learning_evals.py` `build()` 不再复制真实
      `.cursor/learning/` 资产，改为构造空 learning 骨架（REGISTRY +
      SKILL_RELATIONS + inbox/accepted/rejected/clusters 目录）：原实现
      复制真实 LEARN 提案后由 `install()` 覆盖 REGISTRY entries，导致
      fixture 测试中真实提案失去 registry 条目（"proposal missing
      registry entry"）且 target_paths 指向临时目录不存在的 rules
      （fixture 污染）。
- 验证：`run_cursor_learning_evals` PASS（4 模式）；
      `validate_cursor_learning` PASS（2 proposals, 9 relations）；
      engineering-lint（F/I）PASS；m0 profile 全绿恢复。

## Remaining Technical Debt

已发现、不阻断 M7 的事项；每项标注优先级（P 级）与目标归属。

| 项 | P 级 | 目标归属 | 说明 |
| --- | --- | --- | --- |
| PostgreSQL task queue | P1 | M14 | 同 Port 契约（`SqliteWorkflowEngine` 的 contract suite 为验收基线）；跨进程分布式调度属 M14（Durable Workflow + PostgreSQL）。**清偿（2026-08-28 修复轮）：** `adapters/postgres/workflow_engine.py` 等 + `test_workflow_engine_parity.py`（SQLite/PG parity）+ `test_cross_process_real.py`（真实 subprocess） |
| `recover_expired_leases` 定时自愈 | P2 | M14 | 当前为 start_run 懒触发，单进程安全；定时调度属 M14 范畴。**清偿（2026-08-28 修复轮）：** `services/api/scheduler.py` `LeaseRecoveryScheduler` 已在 `_lifespan` 启动（30s 周期）；`test_*` 验证自动恢复 |
| 历史 Run 快照运营迁移 | P2 | M14 | `manifest_semantic_digest=None` 的旧快照不可 resume：需重新冻结或 fork run；无自动迁移路径。**清偿（2026-08-28 债务收口轮）：** `packages/application/run_orchestration/snapshot_migration.py`（plan/apply use case：re-freeze 重算 digest 对写回 / fork 创建新 run 原 run 保持只读 / terminal 与未冻结 keep）+ `tools/snapshot_migrate.py` CLI（`--dry-run`/`--apply`，SQLite 或 PG RunStore）；默认行为不变（未迁移旧快照仍被 `convergence.assert_semantics_frozen` 安全拒绝） |
| ModelRelay + OpenHandsRuntimeAdapter usage 归账闭环到 BudgetLedger | P1 | M12 | 前提：真实 relay 链路 E2E（当前为 mock 端点）；M12 遗留。**清偿（2026-08-28 债务收口轮）：** `tests/e2e/test_m12_usage_real_relay.py`——离线 httpx.MockTransport 脚本化 relay 响应驱动 `OpenAIChatGateway.complete` → `UsageCollection/record_collected_usage` → BudgetLedger（默认 CI 可跑，证明真实代码路径完整）；`requires_live_llm` 手动 E2E（`RESEARCHOS_LIVE_E2E_ENDPOINT`/`RESEARCHOS_LIVE_E2E_KEY` 环境变量门控，真实凭据永不硬编码/落盘，非默认 CI） |
| retention 定时调度 | P2 | M14 | M9 交付显式触发 `apply_retention` 用例；定时扫描与 `recover_expired_leases` 同属 M14 定时调度范畴。**清偿（2026-08-28 收口轮）：** `packages/application/artifacts/retention.py` 并发健壮性（InvalidInputError → skipped）；`services/api/scheduler.py::RetentionScheduler`；`services/api/app.py::_lifespan` 接线（interval ≥ 1h）；`tests/application/artifacts/test_retention_schedule.py` 覆盖归档/删除/跳过/scheduler 冒烟 |
| Experiment 实体持久化 | P1 | M14 | M9 交付 Domain 实体与 use case；`ExperimentPlan/ExperimentRun/ReproducibilityAudit` 落 PostgreSQL Canonical State。**清偿（2026-08-28 收口轮）：** `packages/application/ports/experiment_store.py` Port；`adapters/postgres/migrations/003_experiment_state.sql`；`adapters/postgres/experiment_store.py`；`services/api/pg_composition.py` 接线；`tests/postgres/test_experiment_store_pg.py`（5 tests PASS） |
| EvidenceLedger 持久化 | P1 | M14 | M10 交付 `FakeEvidenceLedger`（进程内）；跨 run 持久化落 PostgreSQL Canonical State。**清偿（2026-08-28 修复轮）：** `adapters/postgres/evidence_ledger.py` + `002_domain_state.sql`（m12_* 表）+ `test_domain_stores_pg.py` |
| RetrievalIndex 持久化 / 真实 embedding | P2 | M12 前评估 | M10 交付 `InMemoryRetrievalIndex`（确定性 token 检索，可重建投影）；真实语义检索与 embedding provider 绑定属 future dependency，不实现（**保留**） |
| Memory/Evidence 内容级数据治理 | P2 | M19 | M10 gate 在 commit 前复用 `domain.redaction` 脱敏 secret 样式内容（Bearer/API key/URL 凭据）；完整 content policy、私有 CoT 识别与数据治理规则属 M19（**保留**） |
| Memory/Claim 并发写入控制 | P2 | M14 | M10 为单进程语义（Fake 内存实现 + 同 id 重复 commit 拒绝）；跨进程并发依赖 M14 PostgreSQL 事务语义。**清偿（2026-08-28 收口轮）：** `adapters/postgres/evidence_ledger.py` register_claim/source/evidence ON CONFLICT DO NOTHING + rowcount 校验 + update_claim rowcount 校验 + _require_verifiable 同事务 FOR SHARE；`adapters/postgres/migrations/004_memory_state.sql`；`adapters/postgres/memory_store.py::PostgresMemoryStore`（原子 commit ON CONFLICT DO NOTHING + rowcount；deactivate/delete 条件写 + rowcount）；`services/api/composition.py` ApiDeps.memory 槽位 + PG 装配注入；`tests/postgres/test_memory_claim_concurrency.py`（5 tests PASS：同提案竞争 commit 恰一赢；delete 0 行抛错；deactivate 幂等；claim 竞争检测；claim update unknown 拒绝）；`tests/contracts/registry.py` memory_store 加入 PG 实现 |

> M9 已清偿（2026-08-15，证据见 `docs/roadmap/M9_COMPLETION_RECORD.md`）：
> `DockerWorkspace 容器链路全量验证`（裁决 mapping-only + 真实链路由
> `adapters/execution/DockerExecutionBackend` 承担并 E2E 全量验证）、
> `ExecutionBackend 容器执行（Sandbox）`（Fake+Docker 双实现通过
> contract suite）。

## Next Product Capability

M7 后的产品能力建设方向。**M8-M15 已完成（见各 completion record）；
M16 及以后为未来设想，尚未实现**；立项时按 `AGENTS.md` 流程从 Plan Mode
开始。编号、名称、顺序、
依赖 DAG 与详细定义（Purpose / Scope / DoD / Entry Gate 等）以
`docs/roadmap/MILESTONES.md` 的 Post-M7 Roadmap 节为**唯一权威**；本表
只提供“能力 → Milestone”映射。

| 能力 | Milestone | 状态 |
| --- | --- | --- |
| Research Tool Plane：ToolCatalog/Resolver（P1 真实链）、Tool effect/risk classes、MCP Streamable HTTP + stdio、ToolPack manifest/install/update/revoke、Tool health/circuit breaker、Tool credential separation、large result artifact indirection | M8 Research Capability Plane | DONE（2026-08-14，`4c2c16d`） |
| Research Skill Registry：Skill 生命周期与 Registry、能力路由与复用 | M8 Research Capability Plane | DONE（2026-08-14） |
| Real Experiment Runtime：ExecutionBackend 真实实现、WorkspaceLease/worktree、ExperimentPlan/Run/Metric、内容寻址 Artifact Store 生产化、retention/export bundle、ReproducibilityAudit | M9 Real Experiment Runtime | DONE（2026-08-15，`4156238`/`b8560ee`） |
| Evidence / Memory Enhancement：SourceRecord、MemoryWriteProposal gate、Memory lifecycle/delete、derived vector index、Claim/Evidence relations、contradiction handling、negative result memory | M10 Evidence / Memory / Provenance | DONE（2026-08-15，`900c1b1`） |
| Evaluation Plane：Eval Harness modes、deterministic gates、reviewer panel、human calibration samples、canary/regression dashboard | M11 Evaluation Plane | DONE（2026-08-15，`0846765`/`0cc6361`） |
| First Real Research Workflow：真实 relay 链路 E2E + usage 归账闭环、工具 + 实验 + 证据全链、MVP 成立判定 | M12 First Real Research Workflow | DONE（2026-08-22；R1 修复完成 2026-08-23；重判 PASS 2026-08-28，RECHECK-20260828-023；DoD-3 live relay 凭据闭环） |
| Research Console：first-run relay wizard、models/probe page、team/agent model assignment、protocol/preflight dry run、task/run timeline、approvals/interventions、workspace diff、evidence/claim map、budget/usage、audit/export | M13 Research Console | DONE（R1 修复 + 独立复审 PASS，2026-08-27） |
| Durable Workflow：Temporal qualification + 采用/不采用决策（DEFERRED，ADR-0025）、PostgreSQL canonical state + task queue、跨进程分布式调度 | M14 Durable Workflow + PostgreSQL | DONE（2026-08-28；WP-J2 重判 PASS，RECHECK-20260828-022；Temporal DEFERRED，ADR-0025） |
| Observability / Cost / Evaluation Operations：OTel collector（隐私默认）、成本归集、eval 趋势运营 | M15 Observability / Cost / Eval Operations | DONE（2026-08-29） |
| Distributed Execution：多 worker、分区与调度、远程 sandbox/worker | M16 Distributed Execution + Remote Sandbox/Worker | PLANNED |
| GPU / HPC：远程/加固 sandbox、计算资源平面 | M17 GPU / HPC | PLANNED |
| Multi-user / Organization / RBAC：多租户数据模型、organization scope、RBAC | M18 Multi-user / Organization / RBAC | PLANNED |
| Production Security / Governance：OPA qualification 与决策、central Secret Manager、backup/restore、SLO | M19 Production Security / Governance + Backup/Recovery/SLO | PLANNED |

> M8-M11 完成事实与逐项证据见 `docs/roadmap/COMPLETION_MATRIX_M0_M11.md`
> 与各阶段 completion record；M12/M13 完成事实见各自 COMPLETION_RECORD
> 与 M12-R1/M13-R1 修复记录。M12 于 2026-08-28 重新独立复审重判 PASS
> （RECHECK-20260828-023，DoD-3 live relay 凭据闭环后升 PASS）；M13 于
> 2026-08-27 独立复审重判 PASS。M14 于 2026-08-28 WP-J2 重判 PASS
> （RECHECK-20260828-022），状态 DONE（Temporal DEFERRED 见 ADR-0025）。
> 本 BACKLOG 不自动开工任何未立项 Milestone。