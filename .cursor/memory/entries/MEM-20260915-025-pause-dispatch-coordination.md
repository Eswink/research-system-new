---
id: MEM-20260915-025
title: 协作式暂停只存一份事实（runs 行的 canonical state）；夹具没有 runs_store 时派发断言是空的
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
scope: repository
confidence: 0.85
review_after: 2026-12-15
source_plans:
  - .cursor/plans/tasks/PLAN-20260914-048-pause-resume-dispatch-coordination.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-048-pause-resume-dispatch-coordination.md
supersedes: []
tags:
  - workflow
  - pause
  - dispatch
  - fixtures
  - canonical-state
---

# MEM-20260915-025 — 暂停事实的单一来源与夹具侧的派发断言前提

## 做了什么

cycle 8（PLAN-048）把 `pause/resume` 从"只改状态"做成协作式执行协调：
`runs` 行的 canonical state 就是暂停信号，派发面与执行器都读它。

## 事实一：不要第二个暂停标志位

暂停事实**只**来自 `runs` 行的 `run_json.state = 'PAUSED'`：

- 派发面读它：SQLite `json_extract(run_json,'$.state')`、PostgreSQL
  `run_json ->> 'state'`，两处都写在 `claim_next` 的**候选扫描内**
  （`NOT EXISTS`），不是扫描后过滤——否则被暂停 run 的排队任务会占满候选窗口，
  把其他 run 饿死。
- 执行器读它：`RunOrchestrationService.pause_requested(run_id)` →
  `WorkflowEngine.run_state(run_id) == PAUSED`（未知 run → False，fail-open）。

若另建 `run_holds` 表，状态与标志会出现两个写点、可能漂移（控制面写状态、派发面读
标志）。`runs` 表只有 `run_json`（无独立 state 列），但 JSON 路径查询在两侧都可用
（SQLite 内置 JSON1 已实测）。

## 事实二：夹具里没有 runs_store 时，"暂停不派发"是空断言

`tests/api/run_fixtures.py` 原先不装配 `runs_store`（run 只进内存注册表）。而
`claim_next` 读的是共享连接上的 `runs` 表——没有 store 就没有行，暂停在派发面看不见，
测试会"绿而不真"。已在 `_run_ready_sqlite_stores` 补
`SqliteRunStore(connection=connection)`，与生产 `composition.py` 同侧。

## 事实三：进程内 run 是同步执行，pause 不会抢占

`POST /runs` 在请求内跑完整条链（阻塞式 handler，单事件循环无并发插入点）。因此
pause 的真实效果是：(a) 派发面（worker/队列）立即停止认领；(b) 执行器在下一次
phase 组边界读到 PAUSED 后零任务执行返回。**不存在**"打断正在执行的 worker"语义，
已持租约不撤销。

## 为什么这样做

"看起来 paused" 与 "真的不再派发" 是两件事。把暂停绑到 canonical state 上，任何
读状态的消费者（控制面、派发面、执行器）看到的是同一个事实；夹具侧补齐 `runs_store`
才能让断言语义成立。

## 怎么做与复现

- 契约（三实现）：`pytest -q tests/contracts/test_pause_dispatch_contract.py`（9 passed；
  PG 需 `RESEARCHOS_POSTGRES_DSN` 指向测试容器）。
- 执行器边界：`pytest -q tests/application/test_pause_coordination.py`（5 passed）。
- API 语义与派发效果：`pytest -q tests/api/test_pause_resume_api.py`（5 passed）。

## 适用边界

- 适用于 run 级暂停/恢复与任何"按 run 控制派发"的后续能力；不适用于取消
  （`cancel_run` 仍是终止态迁移 + 任务置 CANCELLED）。
- 跨进程暂停上下文不持久化：重启后 `continuation=NONE`，只解除暂停。
- 若将来为 run 增加独立 `state` 列，必须保持"暂停事实单一来源"，不要新增第二个标志。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260914-048-pause-resume-dispatch-coordination.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260915-048-pause-resume-dispatch-coordination.md`
- 代码：`adapters/sqlite/workflow_ops.py::_claim_candidates`、
  `adapters/postgres/workflow_claim.py`（两条静态 SQL）、
  `adapters/fakes/workflow_engine.py`、`packages/application/run_orchestration/{phase_runner,service}.py`、
  `services/api/routers/approvals.py`、`tests/api/run_fixtures.py`
- 相关：MEM-20260914-024（live 夹具与 live 链）、MEM-20260912-019（SQLite 组成事实）
