---
id: PLAN-20260918-097
slug: dispatch-list-batch-read
title: 列表路径的派发读面不再 N+1：批量读面与逐 run 读同判（EC-05 ①）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-005
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-005 cycle 5 = EC-05（GOAL-004 收口结论表第 4 项 / RECHECK-089 W-2）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-005 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-097-dispatch-list-batch-read.md
memory_entries:
  - MEM-20260918-071
---

# PLAN-20260918-097 — 列表路径的批量派发读面（GOAL-005 cycle 5 = EC-05 ①）

## 目标

GOAL-004 收口把「`GET /projects/{id}/runs` 的列表路径对每条 run 各做一次
`dispatch_ownership`（每条还要读两件事实）」登记为读面语义边界残留（RECHECK-089 W-2）。
EC-05 的 ① 项要求：**列表路径不再逐 run 读**，且**批量读面与逐 run 读同判**（含
`NONE`/`WORKER_CLAIM`/`RETRY_DISPATCH` 三态与 `dispatch` 读不到的边界）；文档面（Fake 无
过期语义 + `WORKER_CLAIM` 也覆盖控制面自持租约）**必做**。

## 口径

- **同判是结构性的，不是"两边都测一遍"**：单 run 读就是批量读的**一条**——三实现里
  单 run 方法都改成"调用同一段装配再单独记账"，所以不存在第二套判据；契约用例
  （`test_the_batch_read_equals_the_per_run_read`）对三实现逐个断言"逐字相等"。
- **N+1 的判据是调用计数**（用 adapter 自己的 call log，不数 SQL）：列表请求后
  `dispatch_ownership_many` 恰好一次、`dispatch_ownership` **零次**。
- **不改判定、不改响应形状、不改时钟**：`kind`/`retry`/`holders` 的取值与
  `UNKNOWN` 的降级口径逐字不变；查询过滤全走**绑定参数**
  （SQLite `json_each(?)`、PG `= ANY(%s)`），SQL 里不拼值。
- ② PG 两读快照（同一快照的一致性）**本轮不做**（EC-05 允许"至少一项"），既有诚实边界
  保留在 port docstring 与 `PORTS.md`（"不承诺跨表快照一致"），并在 RECHECK 的告警里点名。

## 验收条件

- **AC-01 同判**：契约用例在三实现上断言"批量读 == 逐 run 读"（含未知 run 也是
  `NONE` 条目、空入参 ⇒ 空 dict）。
- **AC-02 不再 N+1**：列表请求后 adapter 的 `dispatch_ownership_many` 调用数 +1、
  `dispatch_ownership` 调用数 **不变**；**反证**：把列表路径改回逐 run 读 ⇒ 该用例红。
- **AC-03 三态与降级边界**：同一页里 `NONE`/`WORKER_CLAIM`/`RETRY_DISPATCH` 逐行与
  `GET /runs/{id}` **同值**；没有 workflow 读面 ⇒ 逐行 `UNKNOWN`（不是 `NONE`）；
  空页不读派发面。
- **AC-04 文档面（EC-05 必做）**：`docs/api/CONTROL_PLANE_API.md` 写明 Fake 无过期语义、
  `WORKER_CLAIM` 也覆盖控制面自持租约；`docs/architecture/PORTS.md` 记批量读面。
- **AC-05 门禁**：定向 + m0 全绿；CI 六 job 到终态并记账。

## 实施清单

### WP-A — port 与三实现（已完成）

- `packages/application/ports/workflow_engine.py`：新增
  `dispatch_ownership_many(run_ids) -> dict[str, DispatchOwnership]` + 契约说明
  （同判 / 全量条目 / 零写零缓存 / 空入参不读库）。
- `adapters/sqlite/projections.py`、`adapters/postgres/projections.py`：新增批量投影
  （`retry_schedules` / `live_lease_holders_many`；单 run 版变成薄封装）+ 把重排行分类
  抽成 `_summarize_retries` 供两处共用；PG 侧装配抽成 `dispatch_ownership_many`。
- `adapters/{sqlite,postgres}/workflow_engine.py`：单 run 与批量走**同一段**
  `_dispatch_ownerships`（装配只有一处），各自只负责记账。
- `adapters/fakes/workflow_engine.py`：`dispatch_ownership` 与
  `dispatch_ownership_many` 共用 `_ownership_of`；批量只记一次调用，不把内部装配记成 N 次。

### WP-B — 控制面列表路径（已完成）

- `services/api/run_dispatch_view.py`：`dispatch_ownership_read_many`（读不到 ⇒ 空 dict，
  调用方给 `UNKNOWN`）。
- `services/api/routers/runs.py`：`_detail_dto(..., dispatch=...)`；
  `GET /projects/{id}/runs` 先取 run 列表、再一次批量读、再逐行装配；详情路径不变
  （`dispatch=None` ⇒ 自己读一次）。

### WP-C — 用例与反证（已完成）

- `tests/contracts/test_dispatch_ownership_contract.py`：批量 ≡ 逐 run（三实现）、空入参。
- `tests/api/test_run_dispatch_view_api.py`：N+1 哨兵（调用计数）、同页三态逐行同判、
  无 workflow ⇒ 逐行 `UNKNOWN`、空页不读派发面。**反证**实跑见「证据」。

### WP-D — 文档与记录（已完成）

`CONTROL_PLANE_API.md`（列表路径 + 两条易读错的事实）/ `PORTS.md`（批量读面）；
RECHECK-20260918-097、MEM-20260918-071、`ALL_PLAN`、`memory/INDEX.md`、GOAL-005 回写。

## 证据

- **反证（实跑）**：把列表路径改回 `[_detail_dto(deps, run) for run in runs]` ⇒
  `tests/api/test_run_dispatch_view_api.py -k list` **1 failed / 3 passed / 7 deselected**，
  红点 = `assert workflow.method_calls("dispatch_ownership_many") == batch_before + 1`
  （`assert 0 == (0 + 1)`）⇒ 哨兵有判别力；恢复批量读后复跑绿。
- **定向**：`tests/api tests/contracts tests/adapters/sqlite tests/postgres tests/adapters`
  ⇒ **1425 passed / 5 skipped**（235.04s）；其中批量/列表新用例
  `tests/api/test_run_dispatch_view_api.py + tests/contracts/test_dispatch_ownership_contract.py`
  ⇒ **35 passed**（13.48s）。
- **参数绑定**：批量过滤 SQL 里没有拼进去的值——SQLite 用 `json_each(?)`（一次绑定一个
  JSON 数组）、PG 用 `= ANY(%s)`（psycopg 把 list 适配成数组）；两者都是既有的仓库范式
  （PG 的 `ANY(%s)` 在 `workflow_claim.py` 已在用）。
- **门禁**：m0 全量，见「状态历史」。

## 状态历史

- 2026-09-18 建档（GOAL-20260918-005 cycle 5 = EC-05 ①，driver=client-goal /
  owner=root-agent）：先确认 N+1 真实存在（`list_runs` → `_detail_dto` → 每条一次
  `dispatch_ownership`）；`status: IN_PROGRESS`。
- 2026-09-18 收口：WP-A…WP-D 完成；反证 1 红（正是哨兵）；定向 **1425 passed / 5 skipped**；
  `status: DONE`。
- 2026-09-18 收口门禁返工（记录，不改判据）：① m0 首跑 `python/product-lint` 红
  （新 import 未排序）⇒ 合并既有 import；② 复跑 `test_python_source_size_limits` 红
  （`adapters/postgres/workflow_engine.py` 459 > 450）⇒ **搬代码**：把派发读面的装配与记账
  移到新模块 `adapters/postgres/workflow_dispatch.py`（与既有 `workflow_claim`/`workflow_ops`/
  `workflow_submit` 同形），引擎方法只留 `_ensure_open` + 错误边界；文件 447 行；
  ③ 路由 docstring 改为**消费者可读**的说明（不含 cycle/EC 编号）并**重新生成**
  `docs/api/openapi.m13.json`（列表路由 `description` 一处变化，随本轮提交）。

## 影响报告

- **Domain / API / schema**：Domain 无变化。Port 新增一个方法（`dispatch_ownership_many`）
  ⇒ 三实现同步；HTTP 响应形状**不变**（`dispatch` 的取值与 `UNKNOWN` 降级逐字不变）；
  OpenAPI 快照有 **1 处**变化——列表路由的 `description` 增加一行消费者可见说明
  （"整页由一次批量读回答"），已用 `tools/gen_openapi.py` 重新生成并随本轮提交，
  快照契约测试实跑绿（不是"快照没变"）。
- **持久化 / 迁移**：无迁移；批量查询只读 `tasks`/`leases`/`workers`。
- **安全 / 凭据**：无凭据面变化；批量过滤是绑定参数（不拼 SQL）；
  `lease_id` 仍不进读面。
- **兼容性 / 迁移风险**：低。列表路径的查询数由 `2N` 降到 `2`；若将来有实现漏了批量方法，
  `WorkflowEngine` Protocol 的 `runtime_checkable` 契约会先红（`test_interface_compatibility`）。
- **上游版本影响**：无。
- **下一项任务**：GOAL-005 cycle 6 = EC-06（历史行可追溯，三选一）。
