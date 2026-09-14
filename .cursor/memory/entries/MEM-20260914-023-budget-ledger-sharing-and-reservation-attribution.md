---
id: MEM-20260914-023
title: 预算账本实例必须共享；run 预留归属只能由登记 ref 证明（作用域匹配是退化路径）
status: ACTIVE
created_at: 2026-09-14
updated_at: 2026-09-14
scope: repository
confidence: 0.9
review_after: 2026-12-14
source_plans:
  - .cursor/plans/tasks/PLAN-20260914-046-budget-adjust-ledger-and-forecast.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260914-046-budget-adjust-ledger-and-forecast.md
supersedes: []
tags:
  - budget
  - ledger
  - fixtures
  - provenance
  - api
---

# MEM-20260914-023 — 预算账本实例共享与预留归属的权威来源

## 做了什么

cycle 6（PLAN-046）把 `budget_adjust` 从恒 501 接到 BudgetLedger，并新增
`GET /runs/{id}/cost-forecast`。两处踩到同一个结构事实，值得后续 cycle 直接复用。

## 事实一：预算账本实例必须全链共享

生产 `services/api/composition.py` 用**同一个** `SqliteBudgetLedger` 实例装配
编排 deps、PreflightContext（`budget_ledger=`）与 `ApiDeps.budget`。
但 `tests/api/run_fixtures.py` 曾各自 `FakeBudgetLedger()` 三次——preflight 的预留
写进 A，控制面从 B 读，导致**夹具内预算读链恒空**（API 无预算/预测为空）。已改为
共享同一实例；若再次出现"预算/预测读到的永远为空"，先查实例是否被拆开。

## 事实二：run ↔ 预留的归属只能由 ref 证明

正式 preflight 预留（`protocol_compile/requirements.py::budget_reservations`）作用域是
`phase:<phase.id>`，**不含 run id**；`LedgerSnapshot.reservations` 又被摊平、不含
`reservation_ref`。因此快照本身无法把预留归到某个 run。唯一权威链路是
冻结 manifest 登记的 `budget_reservation_ref`（运行期在
`RunOrchestrationService._reservation_refs`，budget_adjust 后登记新 ref）。

处置：`LedgerSnapshot` 新增 `reservations_by_ref: Mapping[str, tuple[BudgetReservation, ...]]`
（带默认值，Fake/Sqlite/Postgres 三实现同步填充；SQLite/PG 侧数据本来就有
`reservation_ref` 列）。消费端（forecast 路由）按 `RESERVATION_REF > RUN_SCOPE >
NONE` 三态归属，退化路径必须在响应里标注，且不可归的预留条数进
`unattributed_reserved`（不并入总量、也不伪装为零）。

## 为什么这样做

"按作用域猜归属"会让别的 run 的 phase 预留混入预测（或让本 run 的预留恒为 0，
显示成"消耗超出预留"的假象）；append-only 账本 + ref 认领是唯一不产生假事实的路径。
跨进程重启后进程内 ref 丢失 → 退化路径 + 显式标注，属已知边界而非静默降级。

## 影响

- 任何新的 run 级预算/用量读端点都应走 `reservations_by_ref` 而不是 scope 前缀匹配。
- 测试夹具装配预算面时，共享同一实例（与生产同侧），否则 e2e 可能"绿而不真"。

## 怎么做与复现

- 复现 1（实例共享）：`run_fixtures.make_run_ready_deps()` 共享同一
  `FakeBudgetLedger`（`_RunReadyContext.budget`），生产对照见
  `services/api/composition.py::_sqlite_store_parts`（`budget` 同时进
  `OrchestrationDependencies` 与 `PreflightContext`）。
  验证：`pytest tests/api/test_budget_forecast_api.py -q` 中的
  `test_real_run_reservation_visible_then_adjust_takes_effect`（冻结链路真实 run，
  preflight 预留可见 → 调整后预测跟随 5000）；夹具拆开时该用例会失败。
- 复现 2（归属）：`pytest tests/domain/test_cost_forecast.py -q`——
  `test_phase_scoped_reservations_are_allowed_when_ref_attributed`
  （`phase:<id>` 预留只在 ref 认领时归属）、
  `test_other_run_reservations_are_rejected_as_caller_error`
  （把别的 run 的预留传给投影 = 调用方错误）。
  快照侧：`LedgerSnapshot.reservations_by_ref`（Fake/Sqlite/Postgres 三实现）。
- 复现 3（退化标注）：`pytest tests/api/test_budget_forecast_api.py -q -k unknown`，
  响应含 `attribution`（`RESERVATION_REF`/`RUN_SCOPE`/`NONE`）与
  `unattributed_reserved`。

## 适用边界

适用于 Configuration/Budget 面按 run 读取预留与用量；不改变 append-only 语义，
也不引入跨进程 ref 恢复（进程重启后 ref 不可解析是**已知边界**，退化为
`RUN_SCOPE` 并在响应标注）。用户自定义 budget policy 覆盖（catalog overrides）
解析失败时端点诚实 503，不落默认策略。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260914-046-budget-adjust-ledger-and-forecast.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260914-046-budget-adjust-ledger-and-forecast.md`
- 代码：`packages/application/ports/budget_ledger.py`（`reservations_by_ref`）、
  `packages/domain/cost_forecast.py`、`services/api/routers/budget_forecast.py`、
  `adapters/{fakes,sqlite,postgres}/budget_ledger.py`、`tests/api/run_fixtures.py`
- 相关：MEM-20260912-019（SQLite 组成的表侧事实）、MEM-20260913-021（夹具/CI 假绿）
