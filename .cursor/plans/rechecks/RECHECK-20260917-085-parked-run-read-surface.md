---
id: RECHECK-20260917-085
plan_id: PLAN-20260917-085
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-004-cycle2
baseline_ref: 2dbf3c7
checked_head: f62bda4+worktree
---

# RECHECK-20260917-085 — 停车语义读面（GOAL-004 cycle 2 = EC-02）

## 检查范围

PLAN-20260917-085 声称的交付面：① `WorkflowEngine.retry_schedule(run_id)` 读面
（未到期条数 / 已到期条数 / 最近未到期期限），分类在 adapter 内用**权威时钟**完成；
② 控制面 `GET /runs/{id}`（与列表）的 `paused_dispatch`：重排停车 / 用户暂停 / UNKNOWN
三值，仅 `PAUSED` 时非空；③ 判据只读 canonical 事实（run 行状态 + 任务行
`RETRY_SCHEDULED`/`retry_at`），**不新增"停车原因"字段**；④ OpenAPI/文档/web 类型同源；

**未覆盖**（见告警）：第三种停车来源（重建被拒后放回）在读面里与"重排已到期"同形，
拒绝原因不可见；读面不回答"是哪条任务在等"；Fake 的两个读面永远为空（无写入路径）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 到期读面（AC-01） | SQLite 注入时钟 6 用例：deadline 前 `scheduled=1` 且回带该期限、599s 仍 scheduled / 600s 转 `due=1`、无退避的立即重排即 `due`、混合时 `next_retry_at` 取最近未到期、空 run 与未知 run 全零、按 run 不串台；**PG parity 5 用例实跑非 skip**（pinned test DSN）；契约 8 用例钉"两个读面不会各说各话"（`due == len(due_retry_task_ids)`、`scheduled + due` = 重排条数） | PASS |
| 重排停车可判定（AC-02） | API 用例（真装配 + 真 SQLite）：任务走引擎到 `RETRY_SCHEDULED`（backoff=600）⇒ `paused_dispatch.kind == "RETRY_SCHEDULED"`、`due_now is False`、`next_retry_at` 与**库里那条 `retry_at` 同一瞬间**（读面回答 canonical 事实）；把同一行推到过去 ⇒ 同一读面 `due_now is True`、`next_retry_at is None` | PASS |
| 用户暂停可判定（AC-03） | API 用例：`PAUSED` run 只有 QUEUED 任务（没有任何重排）⇒ `{"kind": "USER_PAUSED", "next_retry_at": None, "due_now": False}` | PASS |
| 不猜（AC-04） | API 用例：`deps.workflow = None` ⇒ `kind == "UNKNOWN"`；run 为 `RUNNING` ⇒ `paused_dispatch is None`（"不适用"不是"false"）；列表与详情共用 `_detail_dto` 单一 classify（用例断言两者相等，且同一期限） | PASS |
| 判据唯一、读面不写（口径 1/2/5） | `grep` 证据：`paused_dispatch_view` 全仓仅一处定义、一处调用（`routers/runs.py:43`）；`run_pause_view.py` 中**没有任何**时钟调用（`datetime`/`now()`/`time()` 零命中）——"现在"只在 adapter 里取；用例连读两次后任务行与 run 状态逐字不变 | PASS |
| 门禁与记录（AC-05） | m0 = **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3804 passed / 10 skipped**，485.85s）；web 门 lint/typecheck/unit(76)/build/stub e2e(83)/live e2e(36) 全绿；OpenAPI 快照重生成（+41 行）；RECHECK-085 + MEM-060 + GOAL/ALL_PLAN 记账 | PASS |

## 反证与实测

- **Fake 上两个读面都空**（不是"没有重排"，是"Fake 不会产生重排"）：`complete` 只记完成，
  全仓没有写 `RETRY_SCHEDULED` 的路径（grep：`RETRY_SCHEDULED` 在 `adapters/fakes/*.py`
  仅 2 处出现，都是读）。本 EC 的读面用例跑 SQLite/PG，Fake 的限制被显式钉成用例。
- **读到"现在"的纪律**：读面不自己比时间——`run_pause_view.py` 零时钟调用；比较发生在
  `adapters/{sqlite,postgres}` 的 `retry_schedule` 内（`timestamp_now` / `server_now`），
  与写 `deadline`、与调度器 `due_retry_task_ids` 同一个源。
- **"到期翻转"的验证口径**：产品装配里的引擎用真实时钟（测试不注入），所以 API 级用例
  推进的是 **canonical 事实**（把那一行 `retry_at` 写到过去），断言的是"同一读面在事实变化
  后改口"；**边界时刻语义（599s vs 600s）由 adapter 级注入时钟用例覆盖**。两者合起来才是
  AC-02 的完整证据——单看 API 级不能证明边界，单看 adapter 级不能证明 HTTP 面接线。
- **450 行硬上限实测拦截**（本轮第一次 m0 红）：`adapters/postgres/workflow_engine.py`
  加完读面后 452 行 ⇒ 把分类与值对象构造挪进 `adapters/postgres/projections.py`
  （与既有"投影返回 port 值对象"同型），引擎方法收敛成扁平转发（446 行）。**门禁与断言
  一字未改**；PG parity 复跑 5 passed。
- **本轮第一次全量 m0 的 10 红是环境并发污染**（非本改动）：前一次 m0 被 kill 后其**孙子
  进程**（`python -m pytest`）继续跑完并毒化资源——PG 表被并发 `TRUNCATE`（本轮新用例读到
  `due=0`，隔离复跑 5 passed）、docker 用例读到残留 `research-os-exec-*` 容器、网络/分区类
  用例随机红。清理（按 `CommandLine` 匹配杀孤儿 + 确认 `docker ps -a --filter
  "name=research-os-exec" -q | wc -l == 0`）后复跑 **23/23**。判定依据是隔离复跑，不是
  "再跑一次就好了"。

## 告警

- **W-1（第三种停车来源不可区分，有意归入其一）**：重建被拒后放回的 `PAUSED` 在读面里
  表现为 `RETRY_SCHEDULED` + `due_now=true`（"重排已到期但没动"）；**拒绝原因不可见**
  （只在本进程遥测/日志）。已写进 `docs/api/CONTROL_PLANE_API.md` 的"诚实边界"，并登记为
  后继入口（要区分它需要把拒绝原因变成 canonical 事实，属产品语义决策）。
- **W-2（Fake 读面恒空）**：Fake 没有写 `RETRY_SCHEDULED` 的路径，两个读面在 Fake 上永远
  是"没有重排"；契约用例把这条限制显式钉住。影响面：用 Fake 装配的场景无法用读面区分
  两种停车——生产/SQLite/PG 装配不受影响。
- **W-3（只回答"有没有"，不回答"是哪条"）**：读面按 run 聚合（计数 + 最近期限），不返回
  任务 id；`GET /runs/{id}/tasks` 的任务投影不带 `retry_at`。要定位到具体任务需要再加一句
  读（当前未提供，不在本 EC 判据内）。
- **W-4（`next_retry_at` 的语义边界）**：它只表示"最近一条**未到期**期限"；"已到期但还没
  被处理"的条数由 `due_now`（布尔）表达，读面不回答"迟到多久"、也不回答"守护线程为什么
  还没动它"。
- **W-5（`paused_dispatch` 不在事件流里）**：读面随请求新鲜（每次 GET 现算），SSE/事件流
  不推送该字段变化——客户端若缓存列表页需要自己轮询（与既有 `state` 字段同口径）。

## 门禁

- 定向套件：`tests/adapters/sqlite/test_workflow_retry_schedule.py` **6 passed**；
  `tests/postgres/test_workflow_retry_schedule_pg.py` **5 passed**（pinned test DSN，实跑非 skip）；
  `tests/contracts/test_retry_schedule_contract.py` **8 passed**；
  `tests/api/test_run_pause_view_api.py` **7 passed**；
  `tests/contracts/test_openapi_snapshot.py` **8 passed**（`RunDetailDto` 新增 `paused_dispatch`
  后重生成 `docs/api/openapi.m13.json`，+41 行）。
- 受影响广度复跑：`tests/{api,contracts,adapters/sqlite,postgres,application/run_orchestration,application/ops}`
  **1137 passed / 2 skipped**（PG 段 pinned DSN）；随后 m0 的全量 pytest **3804 passed / 10 skipped**。
- web 门：`typescript/{format:check,lint,typecheck,boundaries,test,web-lint,web-test,web-typecheck,web-build}`
  全绿（unit 76 passed / stub e2e 83 passed / live e2e 36 passed；`apiFixtures.ts` 的
  `RunDetailDto` 夹具同步 `paused_dispatch: null`）。
- m0：`PASS: profile=m0; 23 deterministic checks`（全量 pytest **3804 passed / 10 skipped**，
  485.85s；首跑 10 红已证明为**环境并发污染**：清理孤儿 pytest 与残留容器后 23/23）。

## 结论

`PAUSED` 的三种来源过去在读面上完全同形（只有一个 `PAUSED`）。本轮把守护线程的判据
（`due_retry_task_ids`）升级成**读面可用的同一判据**：`retry_schedule` 在 adapter 内用
权威时钟分类，控制面据此给出 `RETRY_SCHEDULED`（含 `next_retry_at` 与 `due_now`）、
`USER_PAUSED`、`UNKNOWN`——判据只有 canonical 事实，没有第二个会被写脏的"停车原因"
字段，读面不自己比时间、不写任何状态。

结果为 **PASS_WITH_WARNINGS**：W-1 是有意归入其一的第三种来源（拒绝原因不可见，已写进
文档并登记后继入口），W-2/W-3/W-4/W-5 是适用范围与口径的如实登记。**未宣称"读面能解释
每一次停车"**：它回答的是"会不会自己走、下一条什么时候到、现在是否已到期"，不回答
"为什么被拒"、"是哪条任务"、"守护线程为何还没动"。
