---
id: MEM-20260917-060
title: "停车语义要成为读面事实：同一判据升级成一句读，不新增会撒谎的原因字段"
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260917-085-parked-run-read-surface.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260917-085-parked-run-read-surface.md
supersedes: []
tags:
  - canonical-state
  - read-surface
  - clock
  - pause-resume
  - retry
  - honest-boundary
---

# 停车语义要成为读面事实

## 做了什么

`PAUSED` 有三种来源（重排到期续跑、用户暂停、重建被拒后放回），读面过去只有一个
`PAUSED`。本轮把守护线程用的判据升级成**读面可用的同一句读**：

```text
port:  WorkflowEngine.retry_schedule(run_id) -> RetrySchedule(scheduled, due, next_retry_at)
SQLite: 分类在 adapter 内，用 timestamp_now（生产 DB 时钟 / 测试注入时钟）
PG:     同判据，用 server_now
API:    paused_dispatch.kind = RETRY_SCHEDULED | USER_PAUSED | UNKNOWN（仅 PAUSED 非空）
```

判据只有两件 canonical 事实：run 行 `state`、任务行 `status == RETRY_SCHEDULED` 与
`retry_at`。**没有新增"停车原因"字段**。

## 为什么这样做

1. **同一个问题不要有两处判据**：守护线程问"能不能再交付一次"（要 ids：
   `due_retry_task_ids`），运维问"会不会自己走、下一条什么时候到"（要计数与最近期限）。
   两句读必须出自**同一列、同一个时钟**——否则"守护线程说能走、读面说在等"这类矛盾
   迟早出现（契约用例就钉了 `due == len(due_retry_task_ids)`）。
2. **"现在"只在 adapter 里取**：调用方不拿墙钟去比。分类在 adapter 内用权威时钟
   （生产：DB/注入时钟），读面模块零时钟调用——这样测试与生产对"到期"的理解永远一致。
3. **不新增原因字段**：`pause_reason` 这类字段会被后来的状态变更悄悄写脏（resume 之后
   忘了清、失败后被别的路径改掉），于是读面开始撒谎。**从既有事实推导**永远不会漂：
   任务面有重排 ⇒ 到期会自己走；没有 ⇒ 只有人工能动。
4. **读不到就 UNKNOWN，不猜**：没有 workflow 读面（或 adapter 边界报错）时给 `UNKNOWN`；
   不是 `PAUSED` 时给 `null`（"不适用"不是"false"）。第三种来源**有意**归入
   `RETRY_SCHEDULED + due_now=true`，并把"拒绝原因不在读面"写进 API 文档——如实登记，
   不假装它可见。

## 怎么做与复现

```bash
python -m pytest tests/adapters/sqlite/test_workflow_retry_schedule.py -q   # 注入时钟的边界（599s/600s）
RESEARCHOS_POSTGRES_DSN=<test dsn> python -m pytest tests/postgres/test_workflow_retry_schedule_pg.py -q
python -m pytest tests/contracts/test_retry_schedule_contract.py -q         # 两个读面不会各说各话
python -m pytest tests/api/test_run_pause_view_api.py -q                    # HTTP 边界
```

## 适用边界（踩过的坑）

- **HTTP 级用例拿不到注入时钟**：产品装配里的引擎用真实时钟，所以 API 级"到期翻转"只能
  **推进 canonical 事实**（把那一行 `retry_at` 写到过去）；真正的**边界时刻**语义必须在
  adapter 级用注入时钟钉（599s 仍 scheduled / 600s 转 due）。两边都写，才既有语义又有接线。
- **Fake 没有写 `RETRY_SCHEDULED` 的路径** ⇒ 它的两个读面永远是"没有重排"（与
  `due_retry_task_ids` 同源）。这不是"没有重排"，是"Fake 不会产生重排"——用 Fake 装配的
  场景别指望读面能区分停车来源；这条限制已钉成显式用例。
- **450 行硬上限会拦"顺手加一个方法"**：`adapters/postgres/workflow_engine.py` 加完读面
  452 行 ⇒ 把分类挪进 projections（与既有"投影返回 port 值对象"同型），引擎方法留扁平转发。
- **全量门禁的红先怀疑环境并发**：被 kill 的 m0 会留孙子 pytest 进程继续跑，PG 表被并发
  `TRUNCATE`（新用例读到 0 条重排）、docker 用例读到残留容器。**先隔离复跑**，再决定是否
  改产品代码（[[m0-profile-roots-and-count]]）。
- 相关：[[MEM-20260917-059]]（冻结被解析的那份字节）、[[MEM-20260915-057]]（派发先迁移
  状态再交付）、[[MEM-20260915-047]]（声明了却没消费者的配置等于谎言）。

## 来源

- PLAN-20260917-085 / RECHECK-20260917-085（GOAL-20260917-004 cycle 2 = EC-02）。
