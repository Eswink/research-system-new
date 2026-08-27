---
id: PLAN-20260828-021
slug: m14-durable-workflow-postgresql
title: M14 Durable Workflow + PostgreSQL
status: APPROVED
created_at: 2026-08-28
updated_at: 2026-08-28
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "补齐流程计划与文档对齐（2026-08-28 批准）"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260828-021 — M14 Durable Workflow + PostgreSQL

> 本文件为 M14 立项计划（状态 APPROVED，**未完成**）。工作树已有未提交产物：`adapters/postgres/`（PostgresWorkflowEngine 等 11 模块）、`tests/postgres/`（7 测试文件）、`services/api/scheduler.py`、`docs/adr/ADR-0025-temporal-defer.md`、`docs/references/upstream/M14_TEMPORAL_QUALIFICATION.md`、`docker-compose.m14.yml`、`.importlinter.postgres`、`UPSTREAM_COMPONENTS.yaml`/`pyproject.toml`/`uv.lock` 变更。DoD 验证与独立复审尚未完成，不得宣称 DONE。

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

- [ ] AC-01 PostgreSQL adapter 通过 WorkflowEngine contract suite（双实现 parity：Fake/SQLite/PG）
- [ ] AC-02 跨进程重启恢复 E2E（`tests/postgres/test_cross_process.py`）
- [ ] AC-03 lease 定时自愈测试（`recover_expired_leases` 调度 + `tests/postgres/test_lease_fencing.py`）
- [ ] AC-04 Temporal 决策有证据闭环（`docs/references/upstream/M14_TEMPORAL_QUALIFICATION.md` 16Q + ADR-0025）
- [ ] AC-05 outbox 事务性跨 PG 验证（`tests/postgres/test_outbox_pg.py`）
- [ ] AC-06 m0 profile 全绿；独立复审 PASS
- [ ] AC-07 迁移/文档一致（MILESTONES M14 DoD 映射、BACKLOG P1/P2 清偿标注）

## 实施清单

- [x] STEP-01 Temporal qualification（16Q matrix，DEFER 决策；2026-08-27）
- [x] STEP-02 ADR-0025 落地（Temporal Deferral，2026-08-27）
- [ ] STEP-03 PostgreSQL adapter 实现（工作树已有初版，需逐项验证）
- [ ] STEP-04 contract suite parity 验证（PG vs SQLite vs Fake）
- [ ] STEP-05 跨进程 E2E + lease 自愈 + outbox 验证
- [ ] STEP-06 scheduler 接线 + migration 文件验证
- [ ] STEP-07 m0 profile 全绿 + 独立复审 + 完成记录
- [ ] STEP-08 MILESTONES/BACKLOG 状态更新（IN_PROGRESS → DONE，附证据）

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用（立项阶段） | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | AC-04 | file | `docs/references/upstream/M14_TEMPORAL_QUALIFICATION.md`（16Q：PASS 12/NEUTRAL 2/FAIL 2） | DEFER 决策 |
| EV-02 | AC-04 | file | `docs/adr/ADR-0025-temporal-defer.md` | Accepted |
| EV-03 | STEP-03/04 | file | `adapters/postgres/*.py`；`tests/postgres/*.py` | 待验证（PENDING） |
| EV-04 | STEP-05 | check | `uv run --frozen --no-sync pytest tests/postgres`（需 PG 服务） | 待验证（PENDING） |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-27 | Temporal DEFER（M14 不引入） | Q12/Q13 运维成本 > M14 收益；M16 重评 | ADR-0025；PostgresWorkflowEngine 为生产 adapter |
| 2026-08-28 | M14 立项（APPROVED） | 用户请求已授权立项；工作树已有产物 | 本文件；DoD 验证待完成 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-27 | — | IN_PROGRESS（隐式） | 工作树产物开始落地（Temporal qualification + adapter 初版） | git status untracked |
| 2026-08-28 | — | APPROVED | 正式立项计划创建 | 本文件 |

## 影响报告

- Domain/API/schema：无 Domain 变更（PostgreSQL 为 adapter 层替换）
- 安全/凭据：PG 连接凭据经环境/SecretValue，不入库
- 兼容性/迁移：SQLite→PostgreSQL 语义差异（锁、事务）需 contract parity 验证；历史 SQLite run 迁移策略待定
- 上游版本：`psycopg[binary]==3.2.13`（uv.lock）；temporalio 未引入（DEFERRED）
- 下一项任务：M14 DoD 验证（STEP-03..07）；完成后 M15/M16/M18 依 DAG 并行
