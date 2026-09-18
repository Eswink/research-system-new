---
id: MEM-20260918-071
title: "批量读面必须是单条读的'同一次读做 N 遍'——同判靠共用装配，N+1 靠调用计数钉"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.9
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-097-dispatch-list-batch-read.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-097-dispatch-list-batch-read.md
supersedes: []
tags:
  - read-surface
  - n-plus-one
  - ports
  - test-determinism
---

# 批量读面：同判要结构，N+1 要计数

## 做了什么

GOAL-005 cycle 5（EC-05 ①）把控制面列表路径的 N+1 清掉：`GET /projects/{id}/runs` 此前对
每条 run 各调一次 `WorkflowEngine.dispatch_ownership`（每条内部两次读）⇒ 查询数 `2N`。
现在 port 新增 `dispatch_ownership_many(run_ids)`，列表路径一次批量读（**两条 SQL**），
三实现（SQLite / PG / Fake）与 `dispatch_ownership` **共用同一段装配**
（`_dispatch_ownerships` / `_ownership_of` / `projections.dispatch_ownership_many`），单 run
方法只负责"取一条 + 单独记账"。

## 为什么这样做

- **"同判"必须是结构性的，否则迟早漂移**：如果批量版另写一遍判据（哪怕今天结果一样），
  下次改判据只改一处就会出现"列表说有人在派发、详情说没有"。把单 run 读实现成
  "批量读的一条"，是唯一不用靠人去同步两处的做法。
- **N+1 的判据要用调用计数，不是数 SQL、也不是看耗时**：adapter 自己的 call log
  （`method_calls`）就能钉住"整页一次批量、逐 run 零次"；反证 = 改回逐 run 读 ⇒ 哨兵红
  （实跑 `assert 0 == (0 + 1)`）。
- **绑定参数不做 IN 拼接**：SQLite 侧用 `json_each(?)`（一个参数传 JSON 数组，`IN
  (SELECT value FROM json_each(?))`），PG 侧用 `= ANY(%s)`（psycopg 适配 list）——
  动态长度过滤不需要把值拼进 SQL，也不需要拼占位符串。
- **空入参不读库**：列表页没有 run 时也发一条 `SELECT ... IN ()` 是没意义的往返。

## 怎么做与复现

```bash
# 同判 + 空入参（三实现）
uv run --frozen --no-sync python -B -m pytest tests/contracts/test_dispatch_ownership_contract.py -q
# N+1 哨兵 + 三态同判 + 降级边界
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  uv run --frozen --no-sync python -B -m pytest tests/api/test_run_dispatch_view_api.py -q
# 反证：把 routers/runs.py 的列表路径改回 `[_detail_dto(deps, run) for run in runs]`
#       ⇒ 期望哨兵红（批量调用数 0 != 1）
```

## 适用边界（踩过的坑）

- **两条 SQL 仍无快照保证**：批量读内部是"重排 + 租约"两次读，并发写期间两读之间可能前移
  （EC-05 ② 未做；port docstring 与 `PORTS.md` 已如实写明）。批量读消掉的是 **N+1**，
  不是撕裂读。
- **改别名要全仓搜旧名**：把投影函数改成批量版后，引擎里 `retry_schedule` 仍在调旧别名
  ⇒ 10 条红（`NameError`）。教训：重命名投影入口时先 `grep` 旧别名的所有调用点。
- **Fake 是弱同判**：Fake 无过期语义（"活"= 仍在租约表里），三态覆盖要用真 SQLite 引擎。
- **列表未分页 ⇒ 未加上限**：批量入参是整页 id；将来分页/超大项目时要给上限或分块。
- 相关：[[MEM-20260917-064]]（这条读面的来源与既有诚实边界）、
  [[MEM-20260918-070]]（PG 用例的时钟判定，同类读面纪律）。

## 来源

- PLAN-20260918-097 / RECHECK-20260918-097（GOAL-20260918-005 cycle 5 = EC-05 ①）。
- 上游：RECHECK-20260917-089 W-2（列表 N+1 的告警）。
