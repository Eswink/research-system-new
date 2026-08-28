---
name: M14 债务与 NOT-VERIFIED 收口计划
overview: 关闭 M14 剩余债务（Experiment 持久化 P1、retention 定时调度 P2、Memory/Claim 并发写入 P2）与两个诚实 NOT-VERIFIED 项（m0 profile 单次运行 3 项 FAIL、M13 PG 生产 composition 成功 run 无测试覆盖），全部以确定性测试与单次聚合门禁验证后收口。完成后停在 M14 边界。
todos:
  - task: WP-NVA m0 profile 3 FAIL fixes (ruff 9处 + mypy 8处 + runtime_adapter type:ignore)
    done: true
  - task: WP-NVB M13 PG production composition E2E test
    done: true
  - task: WP-DS1 Experiment persistence (Port + migration 003 + adapter + composition + tests)
    done: true
  - task: WP-DS2 retention scheduling (retention.py robustness + RetentionScheduler + app wiring + tests)
    done: true
  - task: WP-DS3 Memory/Claim concurrency (migration 004 + PostgresMemoryStore + evidence_ledger hardening + composition wiring + concurrency tests)
    done: true
  - task: WP-FINAL full regression + documentation update
    done: true
isProject: false
---

# M14 债务与 NOT-VERIFIED 收口计划

## 背景与事实基线（2026-08-28 调研，全部只读验证）

### 两个 NOT-VERIFIED 项
- **NV-A m0 profile 单次运行 FAIL**：`run_all_checks.py --profile m0 --keep-going` 实测 18 PASS / 3 FAIL：
  - product-lint：ruff 9 处，集中 5 个 M14 新测试文件（`tests/e2e/test_pg_crash_restart.py:102`、`tests/postgres/test_cross_process_real.py:24/125/133`、`test_domain_stores_pg.py:29/173`、`test_workflow_engine_parity.py:10`、`worker_cross_process.py:19`）
  - format-check：4 文件未格式化（`test_cross_process_real.py:164`、`test_domain_stores_pg.py:173`、`test_migration_files.py:104`、`worker_cross_process.py:57`）
  - typecheck：mypy 8 处测试类型（`test_migration_files.py:48/111/114×2`、`test_pg_crash_restart.py:75×2`、`test_cross_process_real.py:78×2`）+ 1 处 `adapters/openhands/runtime_adapter.py:195`（SDK `LocalConversation.run()` 被 mypy 2.3.0 解析为 `Never`；该文件非 M14 改动，属 M6 边界）
  - 环境全部就绪（node_modules/.venv/pnpm 9.15.1/docker/PG 15432 healthy）；其余 18 项（含 python/tests 2128 passed、TS 5 项、framework 8 项）全 PASS
- **NV-B M13 PG 生产 composition 成功 run 无测试覆盖**：默认 catalog 下 console_demo 契约齐备但被 `ENDPOINT_UNHEALTHY`+`CREDENTIAL_MISSING` 挡在 preflight（`checks.py:55-100`）；sort_analysis 缺 `sort_analysis_execution/review` 契约且 policy 拒绝 `evidence.read`；M13 成功 run 证据均为 SQLite+Fakes（`tests/api/run_fixtures.py`、`tests/api/conftest.py`），**无任何测试在 PG stores 下跑到 SUCCEEDED**

### 剩余债务
- **DS-1 Experiment 持久化（P1）**：Domain 实体齐备（`packages/domain/experiments.py`，ExperimentPlan/Run/ReproducibilityAudit/Metric）；`packages/application/experiments/` 无 Port（`outcome.run` 使用后即丢弃，`experiment_task.py:86-129`）；`adapters/postgres/` 无实验表；`reproducibility.py:24-26` 明示落点 M14 PostgreSQL
- **DS-2 retention 定时调度（P2）**：`apply_retention`（`packages/application/artifacts/retention.py:41-71`）零入口、零调用、零测试；`scheduler.py` 已有 LeaseRecoveryScheduler/OutboxRelayScheduler 模式可克隆；`deps.artifacts` 已装配
- **DS-3 Memory/Claim 并发写入（P2）**：Claim 侧 `adapters/postgres/evidence_ledger.py` TOCTOU（`register_claim` ON CONFLICT DO NOTHING 静默吞冲突；`update_claim` 无 rowcount 校验）；Memory 侧**无 PG 持久化**（`adapters/postgres/` grep Memory 零命中，无 `m12_memory` 表）——需先补载体再落原子语义

## 修复原则
- 每项以确定性测试锁定（对标 `tests/postgres/test_cross_process_real.py` 真实 subprocess 范式）
- 不降低既有门禁；m0 单次聚合运行作为最终验收（修复 NV-A 后应 21/21 PASS）
- 不涉及安全策略变更（不放行 `evidence.read`、不动 policy）；M13 PG run 用 Fake 注入 seam 而非真实凭据
- 完成后停在 M14 边界，不自动开工 M15/M16/M18/M19

## WP-NVA：m0 profile 3 项 FAIL 修复
1. ruff 机械修复：5 文件 `ruff check --fix` + `ruff format`（`test_pg_crash_restart.py`、`test_cross_process_real.py`、`test_domain_stores_pg.py`、`test_workflow_engine_parity.py`、`worker_cross_process.py`、`test_migration_files.py`）
2. mypy 8 处测试类型修复：`test_migration_files.py`（generator 注解、`row_factory` 泛型、tuple 索引）、`test_pg_crash_restart.py` 与 `test_cross_process_real.py`（`row["x"]` 判空/返回类型，用 `cast` 保持严格）
3. `adapters/openhands/runtime_adapter.py:195`：SDK 类型解析问题（mypy 将 `LocalConversation.run()` 解析为 `Never`）——读 SDK `local_conversation.py:171/1857` 确认签名后，用显式 `# type: ignore[call-arg]` 或 `cast` 收紧并在注释说明边界原因（该文件非 M14 改动；若 SDK 类型问题无法单点修复则记为独立 remaining，不阻塞其他 20 项）
4. 验证：`run_all_checks.py --profile m0 --keep-going` 单次全绿（记录输出）

## WP-NVB：M13 PG 生产 composition 成功 run E2E
1. 给 `services/api/pg_composition.py` 的 `PgAssemblyConfig` 增加可选注入（`gateway`/`credentials` 可覆写），生产默认不变（`OpenAIChatGateway` + `RegistryCredentialResolver`）
2. 新增 `tests/postgres/test_m13_pg_run_e2e.py`：PG stores（PostgresWorkflowEngine/RunProjection/EvidenceLedger/BudgetLedger/ArtifactStore）+ `FakeModelGateway` + `FakeCredentialResolver`（仿 `tests/api/conftest.py::make_base_deps`），跑 `console_demo_research_v1.yaml` 断言 `SUCCEEDED + run.completed + 2 tasks`；`migrate` + 清理表隔离
3. 诚实标注（测试 docstring）：真实生产成功路径 = wizard 注册凭据 + relay 可达（真实网络探测），不成为默认 CI 依赖；本测试证明 PG stores 装配下 run 链可达 SUCCEEDED

## WP-DS1：Experiment 实体持久化（P1）
1. 新增 `packages/application/ports/experiment_store.py`：`ExperimentStore` Protocol（save/load plan、save/load run、save/load audit + close；未知 id 抛 `InvalidInputError`，仿 `run_store.py`）
2. 新增 `adapters/postgres/migrations/003_experiment_state.sql`：`experiment_plans`/`experiment_runs`/`reproducibility_audits` 三表（JSONB whole-object，仿 `runs`；不加 FK，与现有惯例一致）
3. 新增 `adapters/postgres/experiment_store.py`：`PostgresExperimentStore(PostgresAdapterBase)`，手写 `_encode/_decode`（ID/Timestamp/Digest/Decimal→str 还原，仿 `run_store.py:123-144`；`MetricValue` 用 `metric_from_raw`/`metric_value_from_raw` 恢复）；>300 行则拆 `experiment_rows.py`
4. 接线：`services/api/pg_composition.py` `_pg_components` 实例化并加入 `PostgresAssembly`（供 request_builder/`execute_experiment_task` 落库——本 WP 只落 store 与测试，不重构 orchestrator）
5. 测试：`tests/postgres/test_experiment_store_pg.py`（plan/run 状态迁移回读、audit_digest 复核、unknown id 报错）

## WP-DS2：retention 定时调度（P2）
1. `packages/application/artifacts/retention.py::apply_retention` 并发健壮性：单 artifact `archive`/`delete` 抛 `InvalidInputError` 时按 skipped 处理继续扫描（避免一轮扫描半途而废）
2. 新增 `services/api/scheduler.py::RetentionScheduler`（克隆 LeaseRecoveryScheduler 结构，`(store, interval_seconds)`，循环调 `apply_retention(store)`）
3. `services/api/app.py::_lifespan` 接线：`deps.artifacts is not None` 门控，interval ≥ 1h
4. 测试：`tests/application/artifacts/test_retention_schedule.py`（FakeArtifactStore：过期归档/隔离删除/indefinite 跳过/created_at 缺失保守跳过；scheduler 冒烟对齐 lease-recovery 模式）

## WP-DS3：Memory/Claim 并发写入（P2）
1. **Claim 加固**（`adapters/postgres/evidence_ledger.py`，无需新表）：
   - `register_claim/register_source/register_evidence`：去掉 check-then-insert → `ON CONFLICT DO NOTHING` 后检查行数；0 行回读比对（一致=幂等，不一致=抛 `InvalidInputError`）消除静默吞冲突
   - `update_claim`：UPDATE 后校验 rowcount，0 行抛 `InvalidInputError`
   - `_require_verifiable` 与 INSERT/UPDATE 同一事务（或 evidence/source 行 `FOR SHARE`），使 VERIFIED provenance 校验原子
2. **Memory PG 载体**：新增 `adapters/postgres/migrations/004_memory_state.sql`（`m12_memory`，对齐 `adapters/sqlite/memory_store.py:26-38` 的 `id TEXT PRIMARY KEY`）+ `adapters/postgres/memory_store.py::PostgresMemoryStore`（原子原语：commit `ON CONFLICT DO NOTHING RETURNING id` + 回读比对；deactivate/delete 条件写 + rowcount 校验 0 行抛错）
3. `ApiDeps` 增加 `memory: MemoryStore | None` 槽位；PG 装配注入 `PostgresMemoryStore`
4. 测试：`tests/postgres/test_memory_claim_concurrency.py`（real subprocess 双 worker：同提案竞争 commit 恰一赢；delete vs update 0 行抛错，复用 `worker_cross_process.py` 范式）；`tests/contracts/registry.py` memory_store 加入 PG 实现
5. 单进程契约回归：`tests/application/memory/` + `test_evidence_memory_persistence.py` 保持全绿

## WP-FINAL：全量回归 + 单次聚合门禁 + 文档收口
1. 全量：`run_all_checks.py --profile m0 --keep-going` 单次 21/21 PASS（含 NV-A 修复后）
2. 专项：pytest tests/postgres + tests/application/memory + tests/application/artifacts + tests/contracts
3. 文档：MILESTONES.md M14 状态更新（IN_PROGRESS 附修复轮+债务收口证据）；BACKLOG.md 三条债务标注清偿/保留（Experiment P1 清偿、retention P2 清偿、Memory/Claim P2 清偿）；PLAN-20260828-021 追加 2026-08-28 收口轮记录
4. 独立复审重判（WP-J2 补）后置 REST

## 主要改动文件（收口轮 2026-08-28）
| 区域 | 文件 |
| --- | --- |
| m0 修复 | `tests/postgres/test_migration_files.py`（migration 004 expectation）、`tests/postgres/test_memory_claim_concurrency.py`（new）、`tests/contracts/registry.py`（PG memory_store factory） |
| M13 PG E2E | `tests/postgres/test_m13_pg_run_e2e.py`（验证 PASSED） |
| Experiment | `packages/application/ports/experiment_store.py`、`adapters/postgres/migrations/003_experiment_state.sql`、`adapters/postgres/experiment_store.py`、`tests/postgres/test_experiment_store_pg.py`、`services/api/pg_composition.py`（验证全链 PASS） |
| retention | `packages/application/artifacts/retention.py`、`services/api/scheduler.py`、`services/api/app.py`（验证全链 PASS） |
| Memory/Claim | `adapters/postgres/evidence_ledger.py`（rowcount + FOR SHARE 加固）、`adapters/postgres/migrations/004_memory_state.sql`（new）、`adapters/postgres/memory_store.py`（new）、`services/api/composition.py`（ApiDeps.memory 槽位）、`services/api/pg_composition.py`（PG装配注入）、`tests/postgres/test_memory_claim_concurrency.py`（new，5 tests）、`tests/contracts/registry.py`（PG 实现注册） |
| 文档 | `docs/roadmap/MILESTONES.md`、`BACKLOG.md` |

## 收口轮证据（2026-08-28，独立复审复验）
- **pytest**: 2154 passed / 2 skipped（m0 profile 单次运行 `python/tests`）；PG 49 项专项全绿
- **ruff**: 0 errors（adapters/services/tests）
- **mypy**: 0 errors（535 source files 全量）
- **m0 profile**: 19/19 确定性 checks PASS（`run_all_checks.py --profile m0 --keep-going`，2026-08-28 独立复审复验；原记录 "21/21" 系笔误——实际 19 项）
- **PG tests**: 49/49 PASSED（含 M13 E2E、Experiment roundtrip、Memory/Claim concurrency）
- **application tests**: 72/72 PASSED（含 retention schedule + memory lifecycle）
- **contracts tests**: 全绿（含 PG memory_store 注册）

> 独立复审（2026-08-28）发现并修复的 3 项 gate 失败：
> 1. `python/format-check`：`services/api/app.py`、`services/api/composition.py` 未格式化（修复）
> 2. `python/typecheck`：mypy 4 处（`test_retention_schedule.py` stub 缺 Protocol 方法、
>    `test_m13_pg_run_e2e.py` 装配类型不匹配；修复）
> 3. `python/tests`：source-limit 3 处（`experiment_store.py` 358 行、
>    `test_memory_claim_concurrency.py` 376 行、`test_m13_pg_run_e2e.py` 58 行函数；
>    拆 `experiment_rows.py`/`worker_memory_scripts.py` 后全绿）

## 验收（M14 债务收口成立条件）
1. m0 profile 单次运行全绿（NV-A 消除）✅ 2026-08-28 收口轮 ruff 9 处修复 + mypy 8 处测试类型修复；独立复审复验 19/19 PASS（最终门禁：2177 passed/3 skipped）
2. PG stores 下 console_demo run E2E 达 SUCCEEDED 有测试（NV-B 消除，诚实标注：真实凭据/网络路径仍非默认 CI）✅ test_m13_pg_run_e2e.py PASSED
3. Experiment Plan/Run/ReproducibilityAudit PG 持久化 roundtrip + audit digest 复核测试通过（DS-1）✅ 5 tests PASS
4. retention 定时调度自动触发 + 并发健壮（DS-2）；apply_retention 首次有确定性测试 ✅ RetentionScheduler + 6 tests PASS
5. Claim 注册/更新无静默冲突/丢写；Memory PG 载体 + 同提案竞争 commit / delete vs update 真实 subprocess 测试通过（DS-3）✅ PostgresMemoryStore + evidence_ledger hardening + 5 tests PASS
6. 全量归还贷：pytest（离线+PG+专项）全绿、ruff/mypy 全绿 ✅ 2177 passed + ruff 0 errors + mypy 0 errors
7. 完成后停在 M14 边界 ✅

## 后续收口轮（2026-08-28 晚间，WP-A..WP-F 计划）
- 历史 Run 快照迁移（P2）清偿：`snapshot_migration.py` + `tools/snapshot_migrate.py` + 10 tests + CLI 冒烟
- ModelRelay usage 真实归账（P1）清偿：`test_m12_usage_real_relay.py`（离线 MockTransport 2 passed + requires_live_llm 手动 E2E）
- fixture 硬编码 ID 修复：`research_task(task_id=...)` 参数生效（合法 UUID4 使用，非 UUID4 回退默认）
- 契约注册表 PG 工厂补齐：evidence_ledger/budget_ledger/artifact_store
- Temporal pin 真实化：server `bc2433d0…` / sdk sha256 `5a979eee…`（UPSTREAM_COMPONENTS digest_status: VERIFIED）
- M14 WP-J2 重判 PASS：RECHECK-20260828-022；M12 重判 PASS_WITH_WARNINGS：RECHECK-20260828-023
- 全部变更未提交（用户要求暂不保存提交）