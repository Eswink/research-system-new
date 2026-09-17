---
id: PLAN-20260915-081
slug: parked-retry-run-level-redispatch
title: 停下来的重试：声明了退避的重排不再伪装成 run 失败，改由 resume 真重派
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 18 = cycle 17（PLAN-20260915-080）「下一轮输入」的第一项（run 级重派）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」+ 2026-09-17 用户拍板恢复条件②（显式变更 budget.max_cycles 10→20 并置回 ACTIVE）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-081-parked-retry-run-level-redispatch.md
memory_entries:
  - MEM-20260915-056
---

# PLAN-20260915-081 — 停下来的重试（GOAL-003 cycle 18）

## 目标

cycle 17 把"退避 > 0 ⇒ 把下一次尝试交回派发方"落地了，任务落 `RETRY_SCHEDULED`（带
`retry_at`）。但对 AGENT_SESSION 任务，**没有派发方**：探针实测（收口前）

```text
$ python -B scratch/goal3-cycle18-probe1-parked-retry.py
声明 3600s 退避 + 瞬态失败：
  phase runner 返回 = FAILED
  on_pause 拿到的 specs = 0
  durable 任务 = RETRY_SCHEDULED/attempt=1
  FAILED 之后 RESUME = InvalidTransitionError
  runtime 共执行 2 次；deadline 前 InvalidInputError；到期后 lease fence=2
```

三条硬事实：

1. **run 死了**：任务失败 ⇒ run 判 `FAILED`，而 `FAILED` 是终态（`FAILED --RESUME-->`
   不在迁移表里）⇒ 那条 `RETRY_SCHEDULED` 变成**孤儿**：durable 侧声明得好好的，
   没有任何入口能再来取它。
2. **上下文也没了**：`on_pause` 拿到的 specs = 0，phase runner 没有把"要重派的
   任务 + 后面的 specs"交回 service，即使有人想续跑也无从下手。
3. **durable 侧其实是准备好的**：deadline 之前 `acquire_lease` 拒绝（守卫有效），
   到期之后能租到 `fence=2` 并真的再执行一次——缺的只是 run 级的派发方。

## 口径

1. **"重排未到期"不是失败**：执行器把这次尝试的结果标成 `retry_deferred`（不是普通
   FAILED），run 级据此**停车**而不是判失败。
2. **停车 = 已有的 PAUSED + 暂存上下文**：复用 PLAN-20260915-048 的协作式暂停机制——
   失败的任务与它**后面的所有 specs** 一起经 `on_pause` 交回 service 暂存，
   run 状态落 `PAUSED`（`PAUSED --RESUME--> RUNNING` 是既有合法迁移）。
3. **resume 就是派发方**（本轮）：`POST /runs/{id}/resume`（或 `resume_paused`）在到期后
   续跑会真的执行第二次尝试；没到期就 resume 只是**重新停车**（不执行、不判失败）。
4. **deadline 只有一个权威**：到期与否由 durable 的 `retry_at` 决定（cycle 16/17 已建），
   本轮只把"没到期"从 `InvalidInputError` 细分出一个**类型化**的 `RetryNotDueError`
   （仍是 `InvalidInputError` 子类，既有调用方语义不变），让执行器能区分"现在不是交付
   时机"和"这个任务交付不了"。
5. **不扩大战场**：自动重派（守护线程/调度器按时扫 PAUSED 且到期的 run 并 resume）
   **本轮不做**，如实登记为下一轮首选项；本轮交付的是"停车 + 有人能真的把它跑完"。
6. **行为变化要留证据**：探针收口前/后各跑一次；端到端用例证明"到期后 resume 真的
   执行了第二次尝试且 run 跑完"。

## 范围

- `packages/application/ports/errors.py`：新增 `RetryNotDueError(InvalidInputError)`。
- `adapters/sqlite/workflow_ops.py`、`adapters/postgres/workflow_acquire.py`：
  deadline 守卫改抛 `RetryNotDueError`（不变量与消息不变）。
- `packages/application/run_orchestration/task_executor.py`：
  `TaskExecutionResult.retry_deferred`；`_acquire_or_fail` 返回 `TaskLease | _AcquireFailure`
  （带 `not_due`）；`_refused` 决定"再停一次"还是"安全收敛"。
- `packages/application/run_orchestration/phase_runner.py`：`_GroupRun` 参数对象 +
  `_park_for_retry`（PAUSED + 交回 specs）；`task_phase_helpers.PhaseStep.retry_deferred`。
- 新增用例：`tests/e2e/test_retry_park_and_resume.py`（5）、
  `tests/application/run_orchestration/test_parked_retry.py`（4）。
- **不改**：Domain 状态机（用既有 PAUSED/RESUME）、schema、API 路由（PAUSED 的 resume
  路径已存在）、service 的暂存机制（`outcome.state == PAUSED and paused` 已通用）。

## 验收条件

- [x] AC-01 **run 不判失败**：声明退避 + 瞬态失败 ⇒ `execute_phases` 返回 `PAUSED`
  （收口前 `FAILED`），且 `RUN_FAILED` 事件不出现。
- [x] AC-02 **上下文交回**：`on_pause` 拿到"失败的任务 + 其后所有 specs"（收口前 0 条）；
  组内先前成功的任务仍计入 `outcome.tasks`。
- [x] AC-03 **没到期就 resume 不破坏 run**：重新停车、一次都不执行、还能再次 resume。
- [x] AC-04 **到期后 resume 真的重试**：第二次尝试执行、后续 phase 跑完、run `SUCCEEDED`，
  且该任务的 `attempt == 2`（交付代次）。
- [x] AC-05 **对照组不变**：无重试策略 ⇒ 任务 `FAILED` + run `FAILED`；声明了重试但
  无退避 ⇒ 同一次调用里完成第二次尝试（cycle 17 语义）。
- [x] AC-06 **门禁与记录**：m0 23 项 + 定向套件 + RECHECK-081 + MEM-056 +
  GOAL cycle 18 记账 + ALL_PLAN 行。

## 实施清单

- [x] WP-A 执行器：`retry_deferred` + `RetryNotDueError` 分支（两个 adapter 的类型化拒绝）
- [x] WP-B phase runner：`_park_for_retry` + 交回 specs + `PhaseStep.retry_deferred`
- [x] WP-C 端到端与单元用例 + 探针前后对照 + 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
探针收口后（`scratch/goal3-cycle18-probe1-parked-retry.py` 原文）：
  phase runner 返回 = PAUSED          （收口前 FAILED）
  on_pause 拿到的 specs = 1           （收口前 0）
  durable 任务 = RETRY_SCHEDULED/attempt=1
  FAILED 之后 RESUME = 合法 → RUNNING （收口前 InvalidTransitionError）
  runtime 共执行 2 次；deadline 前 RetryNotDueError；到期后 lease fence=2
定向：tests/e2e/test_retry_park_and_resume.py 5 passed；
      tests/application/run_orchestration/test_parked_retry.py 4 passed（9 passed in 0.43s）
宽口径：tests/application+adapters+domain+e2e+postgres+contracts 1990 passed / 7 skipped（4:51）
静态：mypy Success: no issues found in 884 source files；
      ruff check apps services packages adapters tests 全过；ruff format --check 894 files
m0：第 1 轮红于 framework/validate（PLAN-081 未登记 ALL_PLAN，补行后复跑）
    PASS: profile=m0; 23 deterministic checks（全量 pytest 3719 passed / 10 skipped，8:06）
CI：见 GOAL 迭代日志第 18 行（收口提交推送后回填）
```

## 影响报告

- **Domain/API/schema**：无 Domain / schema / 路由变化；变的是"任务失败后 run 怎么走"
  （可重排 ⇒ PAUSED 而非 FAILED）与 acquire 拒绝的**错误类型**（子类，语义不变）。
- **安全/凭据**：无变化。
- **兼容性/迁移风险**：① 声明了退避的契约上，run 不再以 FAILED 结束——依赖
  "瞬态失败 ⇒ RUN FAILED"的调用方/看板需要改读 PAUSED + 任务的 `RETRY_SCHEDULED`；
  ② 未声明退避（缺省立即重排）与未声明重试策略的路径**行为完全不变**（有用例对照）；
  ③ `RetryNotDueError` 是 `InvalidInputError` 子类，`except InvalidInputError` 的既有
  代码不受影响。
- **可观测性**：重排的 deadline 仍由 `task.retry_scheduled` 事件携带（cycle 16 起）；
  run 侧表现为 `PAUSED` + `RunOutcome.message`。**未做**读面上"这次 PAUSED 是重排停车
  还是用户暂停"的显式区分（登记为下一轮候选）。
- **上游版本影响**：无新依赖。
- **下一项任务**：自动重派（调度器/守护线程按 `retry_at` 到期 resume 停车中的 run）。

## 已知风险

- **停车依赖进程内上下文**：`_paused` 暂存是进程内的（与 PLAN-048 的暂停同源）。进程重启后
  `has_paused_context` 为假 ⇒ resume 会诚实报 `continuation=NONE`，run 停在 PAUSED 等人工
  介入——**不假装**能跨进程续跑（跨进程恢复需要持久化执行上下文，另立决定）。
- **轮询缺席**：本轮没有自动重派，长退避（如 3600s）的任务要等到有人 resume。
- **停车期间预算预留仍持有**：`_release_if_terminal` 只在终态释放，PAUSED 不释放——
  这是有意的（重试需要预算），读账时要知道预留会跟着停车一起挂着。

## 状态历史

- 2026-09-18 创建（IN_PROGRESS）：derive 用探针量出"run FAILED 且 RESUME 不合法 ⇒
  声明的重排是孤儿"，据此定口径：重排未到期 ≠ 失败（停车 PAUSED）+ 用既有 resume 机制
  做真重派 + deadline 判定用类型化拒绝细分 + 自动重派登记为下一轮。
- 2026-09-18 收口（DONE）：AC-01…AC-06 全绿。探针收口后：`phase runner 返回` `FAILED →
  PAUSED`、`on_pause specs` `0 → 1`、`RESUME` `InvalidTransitionError → 合法 → RUNNING`；
  定向 9 passed（e2e 5 + 应用层 4）、宽口径 1990 passed / 7 skipped、mypy 884 files clean、
  ruff/format 干净、m0 23/23（第 1 轮红于 ALL_PLAN 漏登记，补行后复跑）。**未扩面**：
  自动重派仍缺席（W-1，下一轮首选项），跨进程续跑与"两种 PAUSED 的读面区分"如实登记。
