---
id: RECHECK-20260828-022
plan_id: PLAN-20260828-021
attempt: 2
status: COMPLETED
result: PASS
created_at: 2026-08-28
completed_at: 2026-08-28
reviewer: root-agent-independent-pass
baseline_ref: M14 首轮独立复审（3 BLOCKER + 2 MAJOR + MINOR，2026-08-28 上午）
checked_head: 本会话第二轮对抗性复审 + 修复轮（migrate 事务修复 + m0 gate 修复 + 契约注册表 PG 补齐）
---

# RECHECK-20260828-022 — M14 Durable Workflow + PostgreSQL 独立复审重判（WP-J2）

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260828-021-m14-durable-workflow-postgresql.md`（AC-01..AC-07）
- 复审基线：首轮独立复审 FAIL（BLOCKER-1 隐式事务写丢失 / BLOCKER-2 并发 claim 双 owner / BLOCKER-3 fencing 失效 / MAJOR-1 CANCELLED 可被恢复 / MAJOR-2 PG outbox 无 relay），修复轮（WP-A..WP-K）完成
- 本重判证据：**第二轮对抗性复审**（本会话 2026-08-28 下午，全部从当前代码/真实 PostgreSQL/独立 OS 进程/真实 TTL 取证，不采信文档自证）+
  修复（migrate() 事务语义 BLOCKER、m0 profile 3 项 gate FAIL、契约注册表缺 PG 实现）+ 修复后全绿门禁

## 复审方法（对抗性，非文档自证）

- 环境：docker `research-system-postgres-1`（healthy，端口 15432）、`uv run --frozen --no-sync`、Python 3.12.13、psycopg 3.2.13
- 独立探针（保留于 `scratch/probe_*.py`，可复跑）：stale worker fencing、scheduled recovery（真实
  `LeaseRecoveryScheduler`）、outbox crash 语义（B/C/D）、DB failure 分类、cancel/complete/expiry 竞争、
  canonical state 纯 PG 重建、migration 失败注入、perf/EXPLAIN
- 真实跨进程：`tests/postgres/test_cross_process_real.py`（subprocess worker + 真实 TTL 5s + `os._exit(9)` 硬杀）

## 检查结果（DoD 19 条重判矩阵）

| # | 退出条件 | 结果 | 证据（本会话实测） |
| --- | --- | --- | --- |
| 1 | PostgreSQL Contract 独立验证 | PASS（修复后） | 契约注册表 `workflow_engine` 加入 `_postgres_workflow_factory`（本会话）；`tests/contracts/test_agent_runtime_contract.py` 31 passed 含 PG 参数化 |
| 2 | 生产 canonical state 位于 PostgreSQL | PASS | `probe_canonical_state.py`：run/task/evidence/claim/budget/approval/artifact 全部仅从 PG 重建成功 |
| 3 | SQLite/PG semantic parity | PASS | `test_workflow_engine_parity.py` 5 场景双实现一致（ids/ordering/timestamps/JSON/NULL/enums/uniqueness/optimistic concurrency/idempotency） |
| 4 | migrations/bootstrap 可重复 | PASS（修复后） | **本会话发现并修复 BLOCKER**：`migrate()` 原用非 autocommit + 嵌套 savepoint，失败文件回滚全部先前文件；修复为每文件独立事务。`probe_migration.py` + `test_migration_files.py`（新增 `test_late_migration_failure_keeps_prior_files_committed`）5 passed |
| 5 | real concurrent claim 正确 | PASS | `test_cross_process_real.py`：双 subprocess 竞争恰好一 owner、`leases` 行数=1 |
| 6 | stale lease fencing 正确 | PASS | `probe_stale_worker.py`：B 持有新 generation 时 A 的旧 lease heartbeat/complete 均抛 `InvalidInputError`，canonical state 不被覆盖 |
| 7 | scheduled recovery 自动运行 | PASS | `probe_scheduled_recovery.py`：真实 `LeaseRecoveryScheduler`（app.py lifespan 同一代码）自动恢复 + 恰一 `retry_scheduled` 事件；双 scheduler 并发不 double-recover |
| 8 | process kill/restart 能恢复 | PASS | `test_pg_crash_restart.py`：`os._exit(9)` 硬杀 → B 恢复 → claim+complete；无重复事实/无 stuck RUNNING/无孤儿 lease |
| 9 | transactional outbox crash 语义 | PASS | `probe_outbox.py`：B（已提交未发布→重启发布）C/D（并发 publisher 全 drain、consumer 按 event_id 幂等）；不宣称 exactly-once |
| 10 | DB failure 不破坏 canonical state | PASS | `probe_db_failure.py`：refused→`PermanentPortError(CONFIGURATION)` 脱敏；dropped→`TransientPortError`；新连接恢复幂等；失败事务无部分状态 |
| 11 | cancel/recovery/completion races | PASS | `probe_cancel_race.py`：CANCELLED 后 stale complete 被拒、cancel 后 recover 不复活、真实 subprocess cancel-vs-complete 3 轮均合法 |
| 12 | idempotency 仍成立 | PASS | `test_idempotency.py` + `test_workflow_engine_pg.py` + parity：submit/acquire/complete/event/cancel 重复执行均 dedup |
| 13 | Temporal qualification 独立可信 | PASS | 16Q 重审：12 PASS/2 NEUTRAL/2 FAIL，门禁 Q1/Q2/Q9/Q11 PASS；pin 占位于本会话复核为真实 commit/sha256（WP-D） |
| 14 | ADOPT/REJECT 有完整 evidence | PASS | DEFER 基于 Q12/Q13 运维成本（本地 dev 3 服务 ~2GB、HA 运维），非"实现麻烦所以不做"；M16 触发条件明确（>50 workers / cross-run saga / p95>200ms） |
| 15 | Temporal 不拥有 Canonical State | N/A（DEFER） | 无 temporal 代码；`.importlinter.domain` + `.importlinter.postgres` 双禁止 |
| 16 | M13 不感知 DB implementation | PASS | `test_m13_pg_run_e2e.py`：PG stores 装配下 console_demo run 达 SUCCEEDED；API/UI 无 DB 分支 |
| 17 | security/resource boundary | PASS | DSN 错误脱敏实测；动态 SQL 全参数化；`pg_stat_activity` 无 idle-in-txn；无连接泄漏 |
| 18 | 无未关闭 BLOCKER | PASS（修复后） | 首轮 BLOCKER-1/2/3 均有真实跨进程复现测试锁定；本会话新发现 migrate BLOCKER 已修 + 回归测试 |
| 19 | full quality gate 全绿 | PASS（修复后） | m0 profile **19/19 deterministic checks PASS**（`python/tests` 2162 passed/2 skipped；ruff 0；mypy 535 files 0；TS 5 项 + framework 8 项全绿） |

## 本重判轮 Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-01 | BLOCKER | `migrate()` 嵌套 savepoint 语义导致失败迁移回滚全部先前文件 | 修复（autocommit + 每文件独立事务）+ 回归测试（本会话） |
| F-02 | MAJOR | m0 profile 3 项 gate FAIL（format-check/typecheck/tests source-limit）与计划"21/21 PASS"声明不符 | 修复 + 计划证据更正（实际 19 项） |
| F-03 | MINOR | 契约注册表缺 PG workflow_engine（Contract PASS 声明无注册表证据） | 补齐 `_postgres_workflow_factory`（本会话） |
| F-04 | MINOR | `research_task(task_id=...)` 参数被忽略（fixture 硬编码 ID） | 已列入 WP-C 修复（本计划） |
| F-05 | MINOR | expired-lease 扫描为 Seq Scan（空表时 planner 选择） | 保留：索引存在，规模增大后使用；非结构性退化 |

## 结论

- 结果：`PASS`
- 理由：19 条 DoD 逐项实测复核，全部满足；首轮 BLOCKER/MAJOR 修复有真实跨进程复现测试锁定；本重判轮新发现 1 BLOCKER + 1 MAJOR + 3 MINOR 已修复或列入收口计划；m0 19/19 单次聚合全绿。
- 后续动作：M14 可标记 DONE（随计划状态闭环）；M16/M18/M19 不自动开工；Remaining Debt 收口见 WP-A..WP-D（本计划）。
