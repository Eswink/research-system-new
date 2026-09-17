---
id: PLAN-20260915-082
slug: unattended-retry-dispatch
title: 无人值守的续跑：重排到期的停车 run 由守护线程自动派发
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 19 = cycle 18（PLAN-20260915-081）「下一轮输入」的第一项（自动重派）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」+ 2026-09-17 用户拍板恢复条件②（显式变更 budget.max_cycles 10→20 并置回 ACTIVE）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-082-unattended-retry-dispatch.md
memory_entries:
  - MEM-20260915-057
---

# PLAN-20260915-082 — 无人值守的续跑（GOAL-003 cycle 19）

## 目标

cycle 18 让"重排未到期"的失败把 run 停在 `PAUSED` 并把上下文交回 service；`resume`
能真的跑完——但**没有人自动按**。探针（`scratch/goal3-cycle19-probe1-unattended-parked-run.py`）
把进程里所有候选派发方逐个问过（**收口前**）：

```text
1) 停车：run=PAUSED runtime 执行 1 次
2) 时钟推过 deadline（+3600s）
3) durable：status=RETRY_SCHEDULED attempt=1（任务投影里**没有** retry_at —— 期限只在任务行/事件里）
4) worker 派发面 claim_next = None（没有可派发的 EXECUTION 任务）
5) lease 恢复面 recover_expired_leases = 0 条
6) 无人 resume 时：进程里没有任何组件会自己动手；人工 resume 才续跑
```

两条硬事实：

1. **worker 不是这条路的重派方**：`claim_next` 只扫 EXECUTION 任务（AGENT_SESSION 任务
   本来就不归它派），所以"到期"对停车中的 run 没有任何意义。
2. **读面缺口**：`retry_at` 不在任务投影里（只在任务行与 `task.retry_scheduled` 事件里）
   ⇒ 任何想按时续跑的组件都**没有办法问出**"这个 run 现在到没到期"。

## 口径

1. **派发方 = 守护线程**：新增 `RetryDispatchScheduler`（与 lease-recovery / reaper 同形的
   `PeriodicDaemon`），每轮扫 canonical `PAUSED` 的 run，把到期的续跑一次。
2. **到期判定只认读面**：新增 `WorkflowEngine.due_retry_task_ids(run_id)`，判据与 claim
   候选扫描**同一张表**（`RETRY_SCHEDULED` 且 `retry_at` 为空或已过），比较在 adapter 内
   用**权威时钟**做（生产 DB 时钟 / 测试注入时钟）——守护线程不自己拿墙钟去比。
3. **状态迁移顺序与 API 面一致**：协作式暂停谓词读的就是 canonical run 状态，所以必须
   **先** `PAUSED → RUNNING` 并落库，**再** `resume_paused`，最后把续跑结果写回
   （续跑又停回 PAUSED 就如实写回 PAUSED）。这条本轮由 e2e 用例抓出来（第一版忘了迁移，
   续跑被自己的暂停谓词立刻挡住）。
4. **诚实边界不许伪装**：本进程没有续跑上下文（重启后）⇒ 跳过、不改状态、不偷偷执行；
   用户手动暂停（没有到期的重排）⇒ 不碰；单个 run 失败不影响整轮。
5. **派发方要可读可控**：新作业进受控词表（`ScheduleJob.RETRY_DISPATCH` + 内置定义 +
   ops 读面回落事实），与其它守护线程一样能被 `/ops/schedules` 看到、能 trigger/停用。
6. **行为变化要留证据**：探针收口前/后同脚本对照；e2e 跑完整回路。

## 范围

- `packages/application/ports/workflow_engine.py`：`due_retry_task_ids` 读面。
- 三个 adapter：`adapters/sqlite/projections.py` + `sqlite/workflow_engine.py`、
  `adapters/postgres/workflow_engine.py`、`adapters/fakes/workflow_engine.py`。
- `packages/domain/schedules.py`：`ScheduleJob.RETRY_DISPATCH` + `JOB_PURPOSE` +
  `BUILTIN_SCHEDULES`；`packages/application/ops/schedule_registry.py`：
  `ensure_builtins` 返回排序后的新建名字（词表顺序不渗进返回值）。
- `services/api/scheduler.py`：`RetryDispatchDeps` + `RetryDispatchScheduler`；
  `services/api/app.py`：`_start_retry_dispatch` + 生命周期启停；`schedule_support.py` 回落事实。
- 用例：`tests/application/ops/test_retry_dispatch_scheduler.py`（6）、
  `tests/e2e/test_retry_dispatch_full_loop.py`（2）、
  `tests/adapters/sqlite/test_workflow_due_retries.py`（3）、
  `tests/postgres/test_workflow_due_retries_pg.py`（2，PG 实跑）。
- 同步更新：`tests/api/test_ops_schedules_api.py` 的词表镜像、`docs/api/CONTROL_PLANE_API.md`
  的合法 job 列表。
- **不改**：Domain 运行状态机、schema、claim 语义、cycle 18 的停车/暂存机制。

## 验收条件

- [x] AC-01 **读面只在到期后回答**：SQLite 注入时钟（deadline 前 1s 不是 due、到点是 due）；
  PG parity 同判据实跑；没有重排的任务与未知 run 一律空。
- [x] AC-02 **无人值守真的跑完**：e2e 全回路（真 SQLite + 真 run store + 注入时钟）——
  守护线程一次 pass 后 run `SUCCEEDED`、runtime 执行 2 次、任务全部 COMPLETED。
- [x] AC-03 **没到期不动 / 跑完幂等**：到期前 pass 返回 0 且不执行；跑完再 pass 返回 0。
- [x] AC-04 **用户暂停不碰**：单测覆盖（共享 run 状态但无到期重排）。
- [x] AC-05 **重启不伪装**：本进程无上下文 ⇒ 0 派发、run 留 PAUSED、不偷偷再执行。
- [x] AC-06 **迁移顺序**：先迁 RUNNING 再续跑；续跑失败留 RUNNING（派发已释放、没有
  continuation），不透支"已续跑"。
- [x] AC-07 **派发方可见可控**：新作业进读面（builtin 定义 + 回落事实），API/词表镜像同步，
  docs 更新。
- [x] AC-08 **门禁与记录**：m0 23 项 + 定向套件 + RECHECK-082 + MEM-057 +
  GOAL cycle 19 记账 + ALL_PLAN 行。

## 实施清单

- [x] WP-A 读面：`due_retry_task_ids`（port + Fake/SQLite/PG + parity 用例）
- [x] WP-B 守护线程：`RetryDispatchScheduler` + 启停接线 + 词表/回落事实/docs
- [x] WP-C 用例（单测 6 + e2e 2 + 读面 5）+ 探针前后对照 + 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
探针（scratch/goal3-cycle19-probe1-unattended-parked-run.py，真实 SqliteWorkflowEngine，非 mock）
  收口前：6) 无人 resume 时：run=?（进程里没有任何组件会自己动手；人工 resume 才续跑）
          —— 另有 4) claim_next = None、5) recover_expired_leases = 0 条
  收口后：6) 重排派发面（守护线程一次 pass）：派发 1 个 run ⇒ canonical run=SUCCEEDED，
             runtime 共执行 2 次
定向
  tests/e2e/test_retry_dispatch_full_loop.py + tests/application/ops/test_retry_dispatch_scheduler.py
    + tests/adapters/sqlite/test_workflow_due_retries.py            → 11 passed
  tests/postgres/test_workflow_due_retries_pg.py（PG 实跑，非 skip） → 2 passed
  tests/api/test_ops_schedules_api.py + tests/application/ops/*      → 31 passed
宽口径 tests/application+adapters+domain+e2e+postgres+contracts      → 2003 passed / 7 skipped（5:29）
静态  ruff check apps services packages adapters tests → 全过；ruff format --check → 898 files already formatted
      mypy → Success: no issues found in 888 source files
m0    第 1 轮红于 framework/validate（ALL_PLAN 勾选与 DONE 状态不一致：收口时把 PLAN-082 行
      先写成 [x] 而计划仍是 IN_PROGRESS —— 收口自伤，不是门禁缺陷）
      第 2 轮 → PASS: profile=m0; 23 deterministic checks（全量 pytest 3736 passed / 10 skipped）
CI    （收口提交推送后填）
```

## 影响报告

- **Domain/API/schema**：Domain 只加了一个受控作业词表成员（`ScheduleJob.RETRY_DISPATCH`）
  与一条内置定义；**没有**新的 run 状态、没有 schema 变化、没有新路由。`/ops/schedules`
  读面多一行（内置作业），fallback 回落事实同步。
- **安全/凭据**：无变化。
- **兼容性/迁移风险**：① 线上既有部署新增一个内置定义（`ensure_builtins` 幂等补齐，既有
  定义不被覆盖）；② 新增守护线程 ⇒ 启动时多一个线程（与既有 4 个同形、FAILED 留痕、
  不静默）；③ 读面 `ensure_builtins` 返回值改为排序（仅影响返回顺序，调用方本来只用集合语义）；
  ④ 只有**停车中的 run**会被自动续跑，用户暂停的 run 不受影响（有用例钉住）。
- **可观测性**：守护线程每轮发 `retry.dispatch_pass` span（FAILED 留痕），并写入与其它守护
  线程相同的运行事实（`run_count`/`last_outcome`/`last_error`），可见于 `/ops/schedules`。
- **上游版本影响**：无新依赖。
- **下一项任务**：跨进程续跑（持久化执行上下文）或锁粒度；`failure_policy` 仍零消费者。

## 已知风险

- **仍然依赖进程内上下文**：重启后停车的 run 不会被自动续跑（守护线程如实跳过），
  跨进程恢复需要持久化执行上下文（另立决定）。
- **两个进程同时跑守护线程**：都是按 canonical 状态 + durable deadline 判定，重复 pass
  只会有一个真的取到上下文（`resume_paused` 对已消费上下文抛错），另一个跳过——但仍属
  "多实例共享 SQLite/PG"的既有边界（锁粒度问题同源）。
- **自动续跑不设次数上限之外的限制**：`max_attempts` 是唯一预算（durable 判据），
  连续失败会一路重排到用尽——这与声明一致，但长退避会让 run 长时间停着（可接受）。

## 状态历史

- 2026-09-18 创建（IN_PROGRESS）：derive 用探针枚举进程内所有候选派发方，实测
  `claim_next=None`、`recover_expired_leases=0`、没有组件会自己动手，且 `retry_at` 不在
  任务投影里 ⇒ 本轮 = 读面（到期判定）+ 守护线程（到期续跑）+ 词表/读面可见可控。
- 2026-09-18 实现（WP-A/WP-B）：读面三个 adapter 同签名（Fake 无 deadline 语义，如实
  只答"该 run 的可重排任务"）；守护线程先迁 canonical 再续跑（第一版直接调
  `resume_paused` ⇒ 被自己的暂停谓词挡住、e2e `assert 1 == 2`，修正后 2 passed）；
  新作业进词表/内置定义/回落事实/docs/API 用例镜像；`ensure_builtins` 返回值改排序
  （新增成员不再让"顺序变了"冒充"内容变了"）。
- 2026-09-18 收口（DONE）：定向 11 + PG parity 2 + ops 31；宽口径 2003 passed / 7 skipped；
  mypy 888 files clean；ruff/format 干净；m0 第 1 轮红于 `framework/validate`（**收口自伤**：
  ALL_PLAN 行先写成 `[x]` 而计划仍 `IN_PROGRESS` ⇒ "勾选与 DONE 状态不一致"；不是门禁缺陷），
  修正投影后第 2 轮 **23/23**。RECHECK-082 = PASS_WITH_WARNINGS（W-1 跨进程续跑仍缺席、
  W-2 读面不区分两种 PAUSED、W-3 续跑失败留 RUNNING 无补偿、W-4 两个派发方各管一半、
  W-5 Fake 到期语义、W-6 探针口径）。
