---
id: RECHECK-20260917-089
plan_id: PLAN-20260917-089
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-004-cycle6
baseline_ref: bcc13b8
checked_head: 925ac6c+worktree
---

# RECHECK-20260917-089 — 统一派发读面（GOAL-004 cycle 6 = EC-05 第②半）

## 检查范围

PLAN-20260917-089 声称的交付面：**一个** port 读回答"这条 run 现在有没有活的派发方、
是哪一个"——`WorkflowEngine.dispatch_ownership(run_id)` 同时给出重排读面与**活**租约持有者
（三实现同判据），控制面 `GET /runs/{id}`（与列表）新增 `dispatch` 字段（
`NONE`/`RETRY_DISPATCH`/`WORKER_CLAIM`/`BOTH`，加诚实降级 `UNKNOWN`），`paused_dispatch`
改为**消费同一次读**（取值与语义逐字不变）；"活"的判据是回收判据的补集（未过期 + 持有者
不是 LOST worker），由 adapter 用权威时钟给出。

**不在本 PLAN**：EC-05 第①半（每线程连接）已在 cycle 5 交付（PLAN-088 / RECHECK-088）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 三态可判定（AC-01） | 契约套件（Fake/SQLite/PG 三实现）：空 run ⇒ `NONE` 且无持有者；未知 run 同形；一条 claim ⇒ `WORKER_CLAIM` 且持有者点名 task/worker/fence/到期；`complete` 后回到 `NONE`；按 run 隔离；持久化两实现上"重排 + 持有" ⇒ `BOTH` | PASS |
| "活"有牙齿（AC-02） | SQLite 注入时钟：过期租约不算持有（且**同一个用例里**要求 `recover_expired_leases` 同判动手）、边界秒仍算活、LOST worker 不算持有（回收同样动手）、控制面持有的租约（`worker_id=None`）算持有；PG parity 逐条对应（含 LOST 那一条：`mark_lost` 后读面 `NONE`、回收实跑 1） | PASS |
| 读面收敛（AC-03） | API 用例 7 条：`WORKER_CLAIM`（持有者点名 + **不含 `lease_id`**）、`RETRY_DISPATCH`（数字与库里那条 `retry_at` 同源）、`NONE`（同时 `paused_dispatch=USER_PAUSED`）、`BOTH`、`UNKNOWN`（`workflow=None`）、列表与详情同判、读两次不改 canonical 事实；EC-02 的既有停车用例 **8 条断言未改**继续绿 | PASS |
| 反证有效（AC-04） | 三次实测（Edit 改→跑→改回）：① 去掉"过期不算活" ⇒ SQLite/PG 各 1 红（契约 18 条仍绿）；② 去掉 LOST 判据 ⇒ 各 1 红；③ 去掉路由器 `dispatch` 装配 ⇒ 新 API 用例 **7 红** | PASS |
| 文档/类型同步（AC-05） | `CONTROL_PLANE_API.md`（`dispatch` 与 `paused_dispatch` 的关系 + 诚实边界）、`PORTS.md`（port 增量）、OpenAPI 快照重生成（+106 行，快照契约 8 passed）、web `types.ts` + `apiFixtures.ts` | PASS |

## 反证与实测

- **反证 ③ 暴露一处假绿并已修复（判据只增强）**：第一次跑"去掉路由器装配"时 7 条里只红 5 条
  —— 列表同判用例与只读性用例都拿"两次读同一个字段"做相等断言，`dispatch=None` 时两侧同为空、
  相等仍然成立（与 cycle 4 重放用例同类假绿）。修法是把"先钉住读面真的答了"
  （`kind == WORKER_CLAIM`）写进这两条断言，复跑反证 ③ ⇒ **7 红**。产品代码未因此改动。
- **`lease_id` 有意不进读面**：它是作业面提交结果的凭据（结果提交路径校验
  `(task_id, lease_id, fence)`），控制面读面只给 `task_id`/`worker_id`/`fence`/`expires_at`。
  用例 `test_a_worker_claim_is_visible_without_leaking_the_lease_credential` 直接断言
  `"lease_id" not in holder`（负向断言，防将来"顺手加一个字段"）。
- **读面的时钟来自 adapter，不来自调用方**：`GET /runs/{id}` 不拿墙钟比；SQLite 用
  `timestamp_now`（与写 `retry_at`/`expires_at`、与回收方同源），PG 用 `server_now`
  （生产 DB 时钟 / 测试注入时钟）。API 层的到期用例沿用 EC-02 的手法（推**库里的**事实，
  不推墙钟）。
- **`paused_dispatch` 的语义是"逐字不变"而不只是"用例还绿"**：分类输入从
  `workflow.retry_schedule(...)` 换成同一次 `dispatch_ownership(...)` 的 DTO；`UNKNOWN`
  仍表示"读不到"（没有 workflow 或 `PortError`），绝不因此退回 `USER_PAUSED`
  （`PausedDispatchDto` 取值的三个来源逐一保留）。
- **一次读而不是两次**：路由器里 `dispatch` 与 `paused_dispatch` 出自**同一次**
  `dispatch_ownership` 调用（`_detail_dto` 里只有一处读），两个字段不会因为"读两次"
  在并发写期间各说各话。
- **450 行硬上限拦了一次（本改动引入）**：`adapters/postgres/workflow_engine.py` 加完新方法
  后 479 行 ⇒ m0 的 `tests/tooling/test_python_source_limits.py` 红。处置是**搬代码**：
  `due_retries` / `dispatch_ownership` 组合进 `adapters/postgres/projections.py`（与 SQLite
  侧同形），`_resolve_connection` 上移 `adapters/postgres/db.py::resolve_connection`（连接装配
  口径，说明"外部注入的连接不归调用方"）；改完 **443 行**、mypy 917 files 绿、定向 2108 例绿。
  **未改门禁、未改断言。**
- **一次类型修复**：m0 首跑的 `python/typecheck` 3 红——`WorkerRegistration` 的**显式导出**
  位置是 `packages.domain.workers`（两处测试改成从那里 import），`_task(..., kind=...)` 参数
  注解写成 `str`（应为 `TaskKind`）。均为测试侧笔误，产品无缺陷。

## 告警

- **W-1（`ClaimRequest.lease_ttl_seconds` 无人消费）**：`ClaimRequest` 声明了
  `lease_ttl_seconds`（默认 300），但 SQLite/PG/Fake 三实现的取租路径都只用**引擎构造时的**
  `lease_ttl_seconds`，请求里的这个字段当前**没有任何消费者**（既有事实，非本 PLAN 引入）。
  本轮实测踩到：契约/SQLite 用例里给 `ClaimRequest(lease_ttl_seconds=600)` 不改变 TTL，
  必须把引擎 TTL 调大。登记为后继入口（要么消费、要么从 port 摘掉），**本 PLAN 不动它**。
- **W-2（列表路径 N+1）**：`GET /projects/{id}/runs` 对**每条** run 做一次
  `dispatch_ownership`（两次 SQL）。今天 run 数量小，读面是运维视图；数量增长后需要批量读面
  （一次读多 run）。已写进 `CONTROL_PLANE_API.md` 的诚实边界，未预先优化。
- **W-3（"活"不含执行健康度）**：读面回答"谁持有"，**不回答**持有者是否还在正常工作
  （心跳新鲜度在前、长跑 worker 的 `renew_lease`、卡死判定都不在这里）。LOST worker 是通过
  回收判据（`workers.state='LOST'`）体现的，不是"心跳不新鲜"的实时推断。
- **W-4（Fake 无过期语义）**：Fake 的"活" = 仍在租约表里（没有时钟/回收路径），因此契约套件
  只在两个持久化实现上钉"过期/LOST"两条判据，Fake 的限制另有一条用例显式钉住
  （`test_the_fake_never_expires_a_lease_it_holds`）。看到 Fake 上 `dispatch` 说"持有"时，
  那不是"租约还新鲜"，而是"Fake 不会过期"。
- **W-5（PG 两读不构成快照）**：PG 实现里重排与租约是**同一个连接上的两次查询**，不承诺
  跨表快照一致（并发写期间两读之间可能前移）。读面是观测，不是事务保证——已写进方法文档；
  若将来需要强一致读，属新增能力。
- **W-6（`kind` 的名字与"控制面自持"的张力）**：`WORKER_CLAIM` 也覆盖 `worker_id=None` 的
  租约（agent session 投递），取名沿用 EC 的"worker claim / retry dispatch"词汇。读面用
  `holder.worker_id` 如实区分两者，文档已点名；若要更精确的词表属后续变更。

## 门禁

- 定向（DSN 按固化配方，PG 实跑非 skip）：`tests/api tests/contracts tests/adapters
  tests/application tests/e2e tests/postgres` **2108 passed / 7 skipped**（347.66s）。
- 类型/风格：`mypy` **Success: no issues found in 917 source files**；ruff check/format 绿；
  `tests/tooling/test_python_source_limits.py` **927 passed**（450 行/50 行硬上限）。
- web 门：lint（0 error）/ typecheck / unit **76** / build / stub e2e **83** / live e2e **36**
  全绿。
- m0：首跑 2 红（`python/typecheck` 3 处类型 + `python/tests` 1 处 450 行硬上限，均为本改动
  引入）；处置是修类型与**搬代码**（见上），未改门禁；复跑见迭代日志第 6 行。

## 结论

派发读面从"两个派发方各持一半事实、没有一处答得出"变成**一个调用一个答案**：
`WorkflowEngine.dispatch_ownership(run_id)` 同时给出重排读面与活租约持有者，`kind` 取
`NONE`/`RETRY_DISPATCH`/`WORKER_CLAIM`/`BOTH`；控制面 `dispatch` 字段在任何 run 状态上都
可用，`paused_dispatch` 改为消费同一次读（取值与语义不变）。"活"的判据与
`recover_expired_leases` 的回收判据**互补**，两个持久化实现的用例都在同一个测试里同时断言
两侧，因此读面不会把"马上要被回收"说成"有人在派发"。

结果为 **PASS_WITH_WARNINGS**：W-1 是被实测撞到的既有 port 漂移（请求级 TTL 无人消费），
W-2…W-6 是列表 N+1、健康度不在读面、Fake 无过期语义、PG 两读无快照、`kind` 词表张力五条
如实边界。**未宣称**：读面能判断派发方健康、能替代 worker registry、或能回答"为什么卡住"。
