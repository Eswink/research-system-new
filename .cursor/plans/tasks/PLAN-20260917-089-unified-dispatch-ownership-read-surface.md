---
id: PLAN-20260917-089
slug: unified-dispatch-ownership-read-surface
title: 统一派发读面：一个调用回答「这条 run 现在有没有活的派发方、是哪一个」（EC-05 第②半）
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260917-004
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260917-004 cycle 6 = EC-05 第②半（后继入口第 6 项的后半）。授权来源：2026-09-17 用户 goal 模式指令（新建承接 GOAL-004 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260917-089-unified-dispatch-ownership-read-surface.md
memory_entries:
  - MEM-20260917-064
---

# PLAN-20260917-089 — 统一派发读面（GOAL-004 cycle 6 = EC-05 第②半）

## 目标

两个派发方今天**各管一半**，没有一处答得出「这条 run 现在有没有活的派发方、是哪一个」：

- **retry dispatch**（`RetryDispatchScheduler`）：只对 `PAUSED` 的 run 判到期（
  `due_retry_task_ids`），读面 `paused_dispatch` 也只覆盖 `PAUSED`；
- **worker claim**（worker plane `claim_next` → `leases` 行）：租约事实**完全不在读面**——
  `leases` 表没有任何 run 级读口（PG 只有进程内用的 `claimed_by(task_id)`），
  一条 `RUNNING` 且任务正被 worker 持租约跑的 run，从控制面看不出"有人在派发它"。

本轮在 `WorkflowEngine` port 上加**一个**读：`dispatch_ownership(run_id)`，返回
canonical 两件事实（重排读面 + **活**租约持有者），并给三实现（Fake/SQLite/PG）
同一个判据；控制面 `GET /runs/{id}`（与列表）新增 `dispatch` 字段，`paused_dispatch`
改为**由同一次读**分类（一个 run 一次读、一个时钟，不再各读各的）。

**范围**：EC-05 ①（每线程连接）已在 cycle 5 交付（PLAN-20260917-088 / RECHECK-088）。
本 PLAN 只做 ②，独立可验收：三态（worker claim 持有 / retry dispatch 持有 / 两者皆无）
各有可判定答案，且"活"的判据由 adapter 用权威时钟给出（与回收租约的判据互补，
不是另一套）。

## 口径

1. **一个读，一个时钟**：`dispatch_ownership` 在 adapter 内用权威时钟
   （SQLite：`timestamp_now`；PG：`server_now`）判"租约还活不活"，与写 `retry_at`、
   与回收租约（`expires_at < now` 或 worker LOST）同一处口径。调用方不拿墙钟比。
2. **"活"= 回收判据的补集**：`expires_at >= now` **且** 持有者不是 LOST worker。
   `recover_expired_leases` 会动手的那条不算"活"——读面不许把"马上要被回收"说成持有。
3. **租约身份不外泄**：读面给 `task_id` / `worker_id` / `fence` / `expires_at`，
   **不给 `lease_id`**（那是作业面结果提交的凭据，读面不复制能力）。
4. **判据只读 canonical 事实**：`tasks`（重排）+ `leases`（持有）两张表，读面零写、
   零缓存、不新增"派发原因"字段；`kind` 四个取值只是这两件事实的组合，不是第二份真相。
5. **诚实降级**：没有 workflow 读面、或读面读不到（`PortError`）⇒ `kind=UNKNOWN`
   （与 EC-02 同一口径，不猜 "NONE"）；Fake 无租约过期语义 ⇒ 写在用例里显式钉住。
6. **判据只增强**：`paused_dispatch` 的既有取值与语义**逐字不变**（EC-02 的 API 用例
   继续钉住），只是改为消费同一次读的结果。

## 验收条件

- [x] AC-01 **三态可判定**（三实现契约套件）：空 run ⇒ `NONE` 且无持有者；
  一个已 claim 的任务 ⇒ `WORKER_CLAIM` 且持有者点名 `task_id`/`worker_id`/`fence`；
  完成/取消释放租约 ⇒ 回到 `NONE`；重排到期 + 持有租约 ⇒ `BOTH`。
- [x] AC-02 **"活"的判据有牙齿**（SQLite 注入时钟 + PG parity）：租约行仍在但已过期 ⇒
  不算持有（`NONE`）；持有者 worker 状态 LOST ⇒ 不算持有；`expires_at >= now` 的
  未过期租约 ⇒ 持有；两种回收判据都与 `recover_expired_leases` 的动手集合**互补**
  （用例：读面说"不活"的，回收会动它）。
- [x] AC-03 **读面收敛**：`GET /runs/{id}`（与列表）的 `dispatch` 三态各有 API 用例；
  `paused_dispatch` 的既有用例（含 UNKNOWN 与 `due_now`）**不改断言**继续绿；
  无 workflow ⇒ `dispatch.kind=UNKNOWN`；OpenAPI 快照 + web 类型/夹具同步重生成。
- [x] AC-04 **反证**：① 去掉"过期的租约不算活" ⇒ AC-02 的过期用例红；
  ② 去掉 LOST worker 判据 ⇒ LOST 用例红；③ 去掉路由器里的 `dispatch` 装配 ⇒
  AC-03 的三态用例红（避免"从不开火的守卫"）。
- [x] AC-05 **收口**：定向套件（契约/SQLite/PG parity/API）+ m0 23 项 + web 门
  （lint/typecheck/unit/build/stub e2e/live e2e）+ RECHECK-089 + MEM + GOAL/ALL_PLAN
  记账；`paused_dispatch` 文档与 `dispatch` 的关系写进 `CONTROL_PLANE_API.md` 与
  `docs/architecture/PORTS.md`。

## 实施清单

- [x] WP-A **port + 三实现 + 契约/单测**：`LeaseHolder`/`DispatchOwnership`（port，含
  `kind` 取值常量）、`dispatch_ownership(run_id)`；SQLite/PG `live_lease_holders`
  投影 + 引擎方法；Fake 实现；契约套件（三实现）+ SQLite 注入时钟单测
  （过期 / LOST / 重排 / BOTH）+ PG parity。
- [x] WP-B **控制面读面 + 文档**：DTO（`DispatchOwnershipDto` / `LeaseHolderDto` /
  `DispatchRetryDto`）、`run_pause_view` 改为消费同一次读、`run_dispatch_view`、
  路由器装配、OpenAPI 快照重生成、web `types.ts` + `apiFixtures.ts`、
  `CONTROL_PLANE_API.md` + `PORTS.md`。
- [x] WP-C **API 用例 + 反证 + 记录**：三态 API 用例 + 反证三跑（Edit 改回）、
  定向套件、m0、web 门、RECHECK-089 + MEM + GOAL/ALL_PLAN 回写。

## 证据

- 提交：`07213ee`（WP-A：port 读模型 + 三实现 + 契约套件 + SQLite 注入时钟单测 + PG parity）、
  `48fe31d`（WP-B：DTO/视图/路由器 + OpenAPI 快照 + web 类型与夹具 + 文档 + 7 条 API 用例）、
  `925ac6c`（修复：PG 引擎超 450 行 ⇒ 搬 `projections.py`/`db.py`；3 处 mypy 错误；
  两条 API 断言按反证结果增强）。
- 定向（DSN 按固化配方，PG 实跑非 skip）：`tests/api tests/contracts tests/adapters
  tests/application tests/e2e tests/postgres` **2108 passed / 7 skipped**（347.66s）；
  `tests/tooling/test_python_source_limits.py` **927 passed**；mypy **917 files** 绿。
- web 门：lint / typecheck / unit **76** / build / stub e2e **83** / live e2e **36** 全绿。
- 反证三跑（Edit 改→跑→改回）：① 去掉"过期不算活" ⇒ SQLite/PG 各 1 红；② 去掉 LOST 判据 ⇒
  各 1 红；③ 去掉路由器 `dispatch` 装配 ⇒ 新 API 用例 7 红（首跑 5 红 ⇒ 两条"两侧相等"用例
  假绿 ⇒ 补"先钉住读面真的答了"后复跑 7 红）。
- m0：首跑 2 红（3 处 mypy + PG 引擎 450 行硬上限；均本改动引入）⇒ 修类型 + 搬代码后复跑
  22/23（唯一红项 = MEM-064 frontmatter 的 YAML 引号，记录面问题）⇒ 修复后复跑 **PASS:
  profile=m0; 23 deterministic checks**（全量 pytest **3887 passed / 10 skipped**，521.87s）。
- 记录：RECHECK-20260917-089（PASS_WITH_WARNINGS，W-1…W-6）+ MEM-20260917-064。

## 状态历史

- 2026-09-17 建档（GOAL-20260917-004 cycle 6 = EC-05 第②半，driver=client-goal /
  owner=root-agent）；反向搜索确认缺口（`leases` 无 run 级读口、`paused_dispatch`
  只覆盖 `PAUSED`）；`status: IN_PROGRESS`。
- 2026-09-17 收口：WP-A/WP-B/WP-C 完成；契约 3 实现 + SQLite 注入时钟 7 + PG parity 4 +
  API 7 全绿，定向 2108 passed；反证三跑有效（含一处假绿修复）；RECHECK-089
  PASS_WITH_WARNINGS；`status: DONE`。

## 影响报告

- **Domain**：无变化（`DispatchOwnership` 是 port 层读模型）。
- **API/schema**：`GET /runs/{id}` 与列表新增 `dispatch` 字段（可选）；无新端点、
  无迁移、无写面。
- **持久化**：只读 `tasks` + `leases`（+ `workers` 的 LOST 判据），无 schema 变化。
- **安全/凭据**：读面**不暴露 `lease_id`**（作业面凭据不复制到控制面读面）；
  不变式保持：读面只读、不写、不缓存。
- **兼容性/迁移风险**：`paused_dispatch` 取值与语义不变（改为消费同一次读）；
  列表路径每 run 多一次读（N+1，登记为告警）。
- **上游版本影响**：无新依赖。
