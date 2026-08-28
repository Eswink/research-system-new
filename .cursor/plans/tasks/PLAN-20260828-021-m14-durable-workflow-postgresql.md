---
id: PLAN-20260828-021
slug: m14-durable-workflow-postgresql
title: M14 Durable Workflow + PostgreSQL
status: DONE
created_at: 2026-08-28
updated_at: 2026-08-28
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "补齐流程计划与文档对齐（2026-08-28 批准）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260828-022-m14-durable-workflow-postgresql.md
memory_entries: []
---

# PLAN-20260828-021 — M14 Durable Workflow + PostgreSQL

> 本文件为 M14 立项计划。2026-08-28 独立复审判定 FAIL（3 BLOCKER + 2 MAJOR +
> MINOR）；修复轮（WP-A..WP-K，见 .cursor/plans/m14_repair_*.plan.md 批准的计划）
> 完成：BLOCKER 全部修复并有真实跨进程复现测试锁定；Canonical State 域状态迁
> 移至 PG；测试整改（parity + 真实 multiprocessing + 迁移幂等）；文档与经验收口。
> **独立复审重判（WP-J2）已于 2026-08-28 完成：RECHECK-20260828-022 判定 PASS**；
> 本计划状态 DONE，M14 → DONE（随 MILESTONES/BACKLOG 状态同步）。

## 目标

让工作流跨进程、跨重启真正 durable，Canonical State 落到 PostgreSQL，完成 Temporal 采用/不采用决策（决策已落地：DEFER，见 ADR-0025）。M14 DoD 全部验证通过 + m0 profile 全绿 + 独立复审 PASS 后进入 DONE。

## 范围

- 包含：
  - PostgreSQL adapter（canonical state + task queue，清偿 BACKLOG P1 债）
  - `recover_expired_leases` 定时自愈（清偿 P2 债；`services/api/scheduler.py`）
  - Temporal upstream qualification 与采用/不采用决策（已完成：DEFER，ADR-0025）
  - 跨进程调度（`tests/postgres/test_cross_process.py`）
  - PostgreSQL adapter 通过 WorkflowEngine contract suite（`test_workflow_engine_pg.py`/`test_type_parity.py`）
- 不包含：
  - 多 worker 分区调度（M16）、SLO 保障（M19）、OpenHands 自身持久化迁移
  - Temporal 引入（DEFERRED，M16 重评）
  - 把 Temporal history 当 Canonical State（ADR-0002）

## 架构与数据流

- 所有者模块：
  - Adapter: `adapters/postgres/`（base/workflow_engine/workflow_submit/workflow_acquire/workflow_ops/cancel_run/leases/outbox/projections/serialization/db + migrations/001_initial.sql）
  - Entry: `services/api/scheduler.py`（recover_expired_leases 定时自愈）
  - Application: 沿用 `packages/application/run_orchestration/`（Port 契约不变）
- 输入：`SqliteWorkflowEngine` 的 contract suite（验收基线）；ADR-0002（PostgreSQL Canonical State）；ADR-0016（可靠性语义）
- 输出：PostgresWorkflowEngine 通过 WorkflowEngine contract suite；跨进程重启恢复 E2E；lease 自愈测试；Temporal 决策证据闭环
- Canonical State：PostgreSQL Domain Entity 唯一真相；Temporal history / outbox 为执行痕迹
- 关键语义：at-least-once + idempotency + deduplication（AGENTS.md §7）；`FOR UPDATE SKIP LOCKED` 跨进程 lease

## 验收条件

- [x] AC-01 PostgreSQL adapter 通过 WorkflowEngine contract suite（双实现 parity：Fake/SQLite/PG）——证据：`tests/contracts/test_agent_runtime_contract.py` 31 passed（含 `_postgres_workflow_factory`）+ `test_workflow_engine_parity.py` 5 场景
- [x] AC-02 跨进程重启恢复 E2E（`tests/postgres/test_cross_process.py`）——证据：`test_cross_process_real.py` 真实 subprocess + `test_pg_crash_restart.py`（`os._exit(9)` 硬杀）
- [x] AC-03 lease 定时自愈测试（`recover_expired_leases` 调度 + `tests/postgres/test_lease_fencing.py`）——证据：`probe_scheduled_recovery.py` 真实 `LeaseRecoveryScheduler` 自动恢复 + 双 scheduler 无 double-recover
- [x] AC-04 Temporal 决策有证据闭环（`docs/references/upstream/M14_TEMPORAL_QUALIFICATION.md` 16Q + ADR-0025）——证据：16Q 12 PASS/2 NEUTRAL/2 FAIL；pin 2026-08-28 复核真实 commit/sha256（WP-D）
- [x] AC-05 outbox 事务性跨 PG 验证（`tests/postgres/test_outbox_pg.py`）——证据：+ `probe_outbox.py` B/C/D crash 语义
- [x] AC-06 m0 profile 全绿；独立复审 PASS——证据：m0 19/19 deterministic checks（2162 passed/2 skipped）；RECHECK-20260828-022 PASS
- [x] AC-07 迁移/文档一致（MILESTONES M14 DoD 映射、BACKLOG P1/P2 清偿标注）——证据：BACKLOG 债务清偿标注（WP-A/WP-B 收口轮）

## 实施清单

- [x] STEP-01 Temporal qualification（16Q matrix，DEFER 决策；2026-08-27）
- [x] STEP-02 ADR-0025 落地（Temporal Deferral，2026-08-27）
- [x] STEP-03 PostgreSQL adapter 实现（初版 + 2026-08-28 修复轮 BLOCKER-1/2/3 + MAJOR-1/2 修复）
- [x] STEP-04 contract suite parity 验证（`tests/postgres/test_workflow_engine_parity.py` SQLite vs PG；PG stores `test_domain_stores_pg.py`）
- [x] STEP-05 跨进程 E2E + lease 自愈 + outbox 验证（`test_cross_process_real.py` 真实 subprocess；`test_pg_crash_restart.py`；outbox relay）
- [x] STEP-06 scheduler 接线（`OutboxRelayScheduler` + `LeaseRecoveryScheduler` 在 `_lifespan`）+ migration 002 验证
- [x] STEP-07 m0 profile 全绿 + 独立复审 + 完成记录（2026-08-28：m0 19/19；RECHECK-022 PASS）
- [x] STEP-08 MILESTONES/BACKLOG 状态更新（2026-08-28：M14 → DONE，随本文件）

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用（立项阶段） | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | AC-04 | file | `docs/references/upstream/M14_TEMPORAL_QUALIFICATION.md`（16Q：PASS 12/NEUTRAL 2/FAIL 2；占位 digest 已标注未验证） | DEFER 决策 |
| EV-02 | AC-04 | file | `docs/adr/ADR-0025-temporal-defer.md` | Accepted |
| EV-03 | STEP-03/04 | file | `adapters/postgres/*.py`；`tests/postgres/*.py` | 修复轮完成（见 WP-E/F/G/H 证据） |
| EV-04 | STEP-05 | check | `uv run --frozen --no-sync pytest tests/postgres tests/e2e/test_pg_crash_restart.py` | 39 passed（含真实 subprocess cross-process + crash/restart） |
| EV-05 | STEP-05 | check | crash-loop 5/5 独立验证（真实 TTL 5s，硬 kill → recover → claim + complete） | CYCLE ok=5 bad=0 |
| EV-06 | STEP-06 | check | `pytest tests/postgres/test_migration_files.py` | bootstrap [1,2] 幂等；不兼容 schema 无部分应用 |
| EV-07 | STEP-07 | check | 全量离线 pytest + PG + ruff + mypy + import-linter + validate_bundle + governance | 2091 offline / 39 PG；全绿 |
| EV-08 | AC-06 | check | m0 profile 单次聚合（2026-08-28 重判轮复验） | 19/19 deterministic checks PASS；python/tests 2162 passed/2 skipped |
| EV-09 | AC-06 | file | `RECHECK-20260828-022-m14-durable-workflow-postgresql.md`（WP-J2 重判） | PASS |
| EV-10 | AC-01 | check | `pytest tests/contracts/test_agent_runtime_contract.py`（含 `_postgres_workflow_factory`） | 31 passed |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-27 | Temporal DEFER（M14 不引入） | Q12/Q13 运维成本 > M14 收益；M16 重评 | ADR-0025；PostgresWorkflowEngine 为生产 adapter |
| 2026-08-28 | M14 立项（APPROVED） | 用户请求已授权立项；工作树已有产物 | 本文件；DoD 验证待完成 |
| 2026-08-28 | 独立复审判定 M14 FAIL（3 BLOCKER + 2 MAJOR） | 隐式事务写丢失（BLOCKER-1）、并发 claim 双 owner（BLOCKER-2）、fencing 失效（BLOCKER-3）、CANCELLED 可被恢复（MAJOR-1）、PG outbox 无 relay（MAJOR-2） | 修复轮启动 |
| 2026-08-28 | 修复轮：autocommit + 事务块 + owner lease fencing + terminal 守卫 + outbox relay + 域迁移 002 | 以真实跨进程复现测试为每个 BLOCKER 锁定 | WP-A..WP-K；`tests/postgres/test_cross_process_real.py` |
| 2026-08-28 | 第二轮对抗性复审：新发现 migrate BLOCKER + m0 3 项 gate FAIL + 契约注册表缺 PG | 独立取证（probe + 真实 PG + 真实 subprocess） | 本会话修复 + WP-C/WP-D 收口 |
| 2026-08-28 | **WP-J2 重判 PASS**（RECHECK-022） | DoD 19 条逐项实测全满足；BLOCKER 全闭环 | 本文件 AC 全勾选；M14 → DONE |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-27 | — | IN_PROGRESS（隐式） | 工作树产物开始落地（Temporal qualification + adapter 初版） | git status untracked |
| 2026-08-28 | — | APPROVED | 正式立项计划创建 | 本文件 |
| 2026-08-28 | APPROVED | IN_PROGRESS | 独立复审 FAIL → 修复轮实施 | RECHECK-（独立复审记录）+ 本文件 |
| 2026-08-28 | IN_PROGRESS | DONE | WP-J2 独立复审重判 PASS（RECHECK-022）；m0 19/19；AC-01..07 全勾选 | RECHECK-20260828-022 + EV-08..10 |

## 影响报告

- Domain/API/schema：无 Domain 变更（PostgreSQL 为 adapter 层替换）
- 安全/凭据：PG 连接凭据经环境/SecretValue，不入库
- 兼容性/迁移：SQLite→PostgreSQL 语义差异（锁、事务）需 contract parity 验证；历史 SQLite run 迁移策略由 `tools/snapshot_migrate.py` 提供（2026-08-28 收口轮）
- 上游版本：`psycopg[binary]==3.2.13`（uv.lock）；temporalio 未引入（DEFERRED，pin 2026-08-28 复核真实化）
- 下一项任务：M14 已 DONE；M15/M16/M18 依 DAG 并行（不自动开工）
- 无可复用事实：M14 全部运行事实已记录于 RECHECK-20260828-022 与既有工程记录，无新增可复用事实需写入 `.cursor/memory/`（不创建伪记忆）
