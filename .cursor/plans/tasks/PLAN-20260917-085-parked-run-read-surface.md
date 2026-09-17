---
id: PLAN-20260917-085
slug: parked-run-read-surface
title: 停车语义读面：运维面判定"到期会自己走"还是"只有人工能动"
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260917-004
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260917-004 cycle 2 = EC-02（承接 GOAL-003「终止与收口 · BLOCKED 记录（2026-09-18）」后继入口第 3 项）。授权来源：2026-09-17 用户 goal 模式指令（新建承接 GOAL-004 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260917-085-parked-run-read-surface.md
memory_entries:
  - MEM-20260917-060
---

# PLAN-20260917-085 — 停车语义读面（GOAL-004 cycle 2 = EC-02）

## 目标

cycle 18/19 之后，一条 run 停 `PAUSED` 有三种来源，而**运维读面看不出区别**：

1. **重排停车**：某个任务被重排（`RETRY_SCHEDULED` + `retry_at`），到期后守护线程会
   自己把它续跑起来（cycle 19）；
2. **用户暂停**：`POST /runs/{id}/pause`，只有人工 resume 才会动；
3. **重建被拒后放回停车**：守护线程按冻结正文重建被诚实拒绝时写回 `PAUSED`
   （cycle 20 的 W-4），读面同样看不出它"试过了、被拒了"。

守护线程自己是靠**任务面**区分的（`due_retry_task_ids`），但人打开 `GET /runs/{id}`
只看得到一个 `PAUSED`。本轮把那个判据做成**读面事实**（而不是给 run 加一个会撒谎的
"原因"字段）：读面回答"这条停车会不会自己走、下一个到期是什么时候、现在是否已到期"。

## 口径

1. **判据来自 canonical 事实**：① run 行状态；② 任务行的 `RETRY_SCHEDULED` 与 `retry_at`。
   不引入"停车原因"字段（字段会被后来的状态变更悄悄写脏），也不读进程内暂存。
2. **"现在"只在 adapter 里取**：due/scheduled 的分类发生在 adapter 内部、用**权威时钟**
   （生产：DB 时钟；测试：注入时钟）——与写 `retry_at`、与 `due_retry_task_ids` 同一个源，
   调用方不自己拿墙钟去比（cycle 19 的既有纪律）。
3. **读不到就 UNKNOWN，不猜**：没有 workflow 读面时给 `UNKNOWN`；状态不是 `PAUSED`
   时整个视图为 `null`（不适用）。
4. **第三种来源明确归入**（EC 判据允许的另一条路）：重建被拒后放回的 `PAUSED` 在任务面
   表现为"重排已到期但没动"（`RETRY_SCHEDULED` + `due_now=true`），**写进文档**；
   拒绝原因当前不在读面（只在本进程遥测/日志），登记为后继入口——不假装它可见。
5. **一个调用、一个时钟**：读面不逐任务问、不把 `retry_at` 交给调用方比较。

## 验收条件

- [x] AC-01 **到期读面（port）**：`WorkflowEngine.retry_schedule(run_id)` 回答
  `scheduled`（未到期条数）/ `due`（已到期条数，含无 deadline 的立即重排）/
  `next_retry_at`（最近一条未到期 deadline），分类在 adapter 内用权威时钟完成；
  SQLite/PG/Fake 三实现同判据，PG parity 实跑非 skip。
- [x] AC-02 **重排停车可判定**：run 有未到期的重排 ⇒ `GET /runs/{id}` 的
  `paused_dispatch.kind == "RETRY_SCHEDULED"`、`next_retry_at` 等于那条 deadline、
  `due_now == false`；到期后（注入时钟越过 deadline）同一读面给出 `due_now == true`。
- [x] AC-03 **用户暂停可判定**：run 停在 `PAUSED` 且任务面没有任何重排 ⇒
  `kind == "USER_PAUSED"`、`next_retry_at == null`、`due_now == false`。
- [x] AC-04 **不猜**：没有 workflow 读面 ⇒ `kind == "UNKNOWN"`；run 不是 `PAUSED` ⇒
  `paused_dispatch == null`；列表读面与详情读面同判据（同一处 classify）。
- [x] AC-05 **门禁与记录**：定向 + 契约快照重生成 + web 类型同步 + m0 23 项 + RECHECK-085
  + MEM + GOAL-004 cycle 2 记账（迭代日志/EC 状态/child_plans/ALL_PLAN 投影）。

## 实施清单

- [x] WP-A **port + 三个 adapter**：`RetrySchedule` 值对象（application/ports）+
  SQLite/PG/Fake 实现（adapter 内权威时钟分类）+ 单测/PG parity。
- [x] WP-B **读面**：`services/api/run_pause_view.py`（唯一 classify 处）+
  `RunDetailDto.paused_dispatch`（`PausedDispatchDto`：kind/next_retry_at/due_now）+
  详情与列表两处接线 + OpenAPI 快照重生成 + web 类型 + `docs/api/CONTROL_PLANE_API.md`
  （含"第三种来源归入其一"的诚实边界）。
- [x] WP-C **用例 + 收口**：API 用例（重排停车/到期/用户暂停/无 workflow/非停车）+
  定向 + m0 → commit（每 WP 独立）→ push → CI 六 job → RECHECK-085 + MEM + GOAL-004 回写。

## 证据

- 提交：`9b163cf`（WP-A：port + 三实现 + 单测/PG parity/契约）、`fd8654f`（WP-B：读面 +
  DTO/OpenAPI/web 类型 + 文档）、`98569c1`（PG 分类挪进 projections：450 行硬上限）、
  `c2cdc98`（WP-C：API 用例）、`f62bda4`（格式）。
- 定向：SQLite 6 / PG parity 5（实跑非 skip）/ 契约 8 / API 7 / OpenAPI 快照 8 全 passed；
  受影响广度复跑 1137 passed / 2 skipped。
- web 门：lint / typecheck / unit 76 / build / stub e2e 83 / live e2e 36 全绿。
- m0：**PASS: profile=m0; 23 deterministic checks**；全量 pytest **3804 passed / 10 skipped**
  （485.85s）。首跑 10 红为环境并发污染（被 kill 的上一轮留下孙子 pytest 进程 + 残留容器），
  清理后 23/23——隔离复跑该 PG 文件 5 passed 证明非产品缺陷（详见 RECHECK-085「反证与实测」）。
- 记录：RECHECK-20260917-085（PASS_WITH_WARNINGS，W-1…W-5）+ MEM-20260917-060。

## 状态历史

- 2026-09-17 建档（GOAL-20260917-004 cycle 2 = EC-02）；`status: IN_PROGRESS`。
- 2026-09-17 收口：WP-A/WP-B/WP-C 完成；m0 23/23 + 定向全绿；RECHECK-085
  **PASS_WITH_WARNINGS**；`status: DONE`。

## 影响报告

- **Domain**：无新字段、无状态机变化（判据全部来自既有 canonical 事实）。
- **API/schema**：`RunDetailDto` 新增可空 `paused_dispatch`（向后兼容）；OpenAPI 快照需重生成。
- **持久化**：无迁移（只读任务行既有列 `status`/`retry_at`）。
- **安全/凭据**：无新凭据面；读面只暴露时间事实（不含任务内容）。
- **兼容性/迁移风险**：无破坏性迁移；旧客户端忽略新字段即可。
- **上游版本影响**：无新依赖。
