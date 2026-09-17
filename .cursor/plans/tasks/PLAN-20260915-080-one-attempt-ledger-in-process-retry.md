---
id: PLAN-20260915-080
slug: one-attempt-ledger-in-process-retry
title: 一次尝试一套账：in-process 重试改走 durable 尝试（并让 acquire 入口也守退避 deadline）
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 17 = cycle 16（PLAN-20260915-079）「下一轮输入」的第一项（in-process 与 durable 的 attempt 两套账）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」+ 2026-09-17 用户拍板恢复条件②（显式变更 budget.max_cycles 10→20 并置回 ACTIVE）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-080-one-attempt-ledger-in-process-retry.md
memory_entries:
  - MEM-20260915-055
---

# PLAN-20260915-080 — 一次尝试一套账（GOAL-003 cycle 17）

## 目标

cycle 16 的记录里登记了"一个 `max_attempts` 两套账"。本轮先用探针把它量出来，再修：

```text
$ python -B scratch/goal3-cycle17-probe1-two-ledgers.py
max_attempts=3 backoff=None: 第一次 execute_task 调 runtime 3 次；累计 9 次
                              [首轮 status=LEASED / 交付 3 代 / durable attempt=3 / runtime 共调用 9 次]
max_attempts=3 backoff=3600: 第一次 execute_task 调 runtime 3 次；累计 9 次
max_attempts=2 backoff=None: 第一次 execute_task 调 runtime 2 次；累计 6 次
```

三条硬事实：

1. **一次交付 = `max_attempts` 次执行，而 durable 的 `attempt` 只前进一格**：in-process
   循环用局部 `attempts` 计数（上限 `max_attempts`），durable 的 `attempt` 计的是**交付代次**
   ⇒ 每次交付都"再来一遍预算"：`max_attempts=3` 在 3 次交付下实测执行 **9 次**。
2. **退避对这个循环无效**：声明 `backoff_seconds=3600` 时 in-process 仍旧**立刻**跑满
   3 次（退避是 durable 的事实，而这个循环不看它）。
3. **失败后 canonical state 说谎**：瞬态失败耗尽局部预算时，`execute_task` **不调用
   `complete()`**（返回 FAILED 结果、由 phase runner 判 run 失败）⇒ 任务行停在 **LEASED**，
   而 cycle 15/16 的 `RETRY_SCHEDULED`/`DEAD_LETTER`/退避判据在这条路径上**永远不可达**
   （没有失败类别进 engine）。

## 口径

1. **一次尝试 = 一次 durable 尝试**：in-process 的每一次重试都要先把它那次失败**落账**
   （`complete(outcome=FAILED, failure_category=<本次类别>)`），再由 durable 判据决定
   （RETRY / DEAD_LETTER / FAIL）。`attempt` 只有一处：交付代次（`lease.fence`）。
2. **预算 = 总执行次数**：`max_attempts` 限制的是"这个任务一共能被执行几次"，
   不是"每次交付能执行几次"。用尽后 durable 侧必须落到 `DEAD_LETTER`（而不是停在 LEASED）。
3. **退避 > 0 ⇒ 不在此进程里等**：durable 判据给出 `retry_at` 时，in-process 循环**停止**，
   把"下一次尝试"交回派发方（worker/claim）。退避 = 0（缺省）时保持今天的行为：
   同一个调用内继续下一次尝试。
4. **acquire 入口也守 deadline**：cycle 16 只在 `claim_next` 的候选扫描里过滤了
   `retry_at`；按 task_id `acquire_lease` 也能把没到期的重试任务租出去——同一个不变量
   （"deadline 之前不得交付"）必须在**每个交付入口**成立（同 cycle 13/14 的枚举手法）。
5. **不扩大战场**：run 级重派（`RETRY_SCHEDULED` 的 AGENT_SESSION 任务由谁再执行）**本轮
   不做**——phase runner 的失败语义（任务失败 ⇒ run 失败）保持不变，如实登记为下一轮输入。
6. **行为变化要留证据**：探针脚本收口前/后各跑一次，执行次数与 durable 状态写进 PLAN/RECHECK。

## 范围

- 修改 `packages/application/run_orchestration/task_executor.py`：循环改为
  "acquire → 执行（attempt = lease.fence）→ 失败则 complete(category) → 按 durable 处置决定
  是否继续"；`_attempt_once` 的失败路径带上类别。
- 修改 `adapters/sqlite/workflow_ops.py`（`_acquire_impl`：RETRY_SCHEDULED 且未到 `retry_at`
  ⇒ 拒绝，`InvalidInputError`）、`adapters/postgres/workflow_acquire.py`（同一口径）。
- 新增用例：`tests/application/run_orchestration/test_execute_task_one_ledger.py`、
  `tests/adapters/sqlite/test_workflow_acquire_backoff.py`、
  `tests/postgres/test_workflow_acquire_backoff_pg.py`。
- 更新既有用例 `tests/application/run_orchestration/test_execute_task_accounting.py`：
  断言**不动**（执行次数、无重复 entry、预算耗尽语义都是更强的同向断言），
  若因语义变化需要调整，逐条在 RECHECK 里说明"旧断言编码的是什么、新语义为什么不同"。
- **不改**：Domain、schema（无新字段）、claim 的扫描过滤（cycle 16 已做）。

## 验收条件

- [x] AC-01 **总执行次数 ≤ max_attempts**：探针重跑，`max_attempts=3` 在任意多次交付下
  runtime 调用次数 **≤ 3**（收口前实测 9）——收口后累计 3 次，第 2 次交付被"已终态"拒绝。
- [x] AC-02 **失败必须落账**：瞬态失败耗尽后任务不再停在 `LEASED`——durable 侧是
  `DEAD_LETTER`（可重试类别、次数用尽）或 `RETRY_SCHEDULED`（退避 > 0、留给派发方）。
- [x] AC-03 **退避 > 0 时 in-process 不再自旋**：声明 3600s 退避时，一次 `execute_task`
  调用内 runtime 只执行 **1 次**，其余交给派发方（收口前实测 3 次）。
- [x] AC-04 **acquire 入口守 deadline**：`RETRY_SCHEDULED` 且未到 `retry_at` 的任务，
  `acquire_lease` 拒绝（SQLite + PG 各一条）；到期后可租（两条）。
- [x] AC-05 **不重复记账**：每个 attempt 号唯一 ⇒ 每个 `entry_id` 唯一（M15 BLOCKER-5 的
  回归仍在：套件跑绿）。
- [x] AC-06 **门禁与记录**：m0 23 项 + 受影响定向套件 + RECHECK-080 + MEM-055 +
  GOAL cycle 17 记账 + ALL_PLAN 行。

## 实施清单

- [x] WP-A `execute_task` 一套账（attempt = 交付代次；失败落账；退避交给派发方）
- [x] WP-B acquire 入口守 `retry_at`（两个 adapter + 用例）
- [x] WP-C 探针收口前/后对照 + 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
探针收口前（同一脚本，输出已抄进上方「目标」段）：
  max_attempts=3 backoff=None : 第一次 execute_task 调 runtime 3 次；累计 9 次
                               [首轮 status=LEASED / 交付 3 代 / durable attempt=3 / runtime 共调用 9 次]
  max_attempts=3 backoff=3600 : 第一次 execute_task 调 runtime 3 次；累计 9 次
  max_attempts=2 backoff=None : 第一次 execute_task 调 runtime 2 次；累计 6 次
探针收口后（原文，`scratch/goal3-cycle17-probe1-two-ledgers.py`）：
  max_attempts=3 backoff=None : 第一次 … 3 次；累计 3 次
    [DEAD_LETTER / durable attempt=3 / 第 2 次交付被拒: InvalidInputError: task … is terminal (DEAD_LETTER); cannot acquire lease]
  max_attempts=3 backoff=3600 : 第一次 … 1 次；累计 2 次
    [RETRY_SCHEDULED / durable attempt=1 / 第 3 次交付被拒: … is waiting for its retry backoff until 2026-09-17T12:00:00Z]
  max_attempts=2 backoff=None : 第一次 … 2 次；累计 2 次 [DEAD_LETTER / durable attempt=2 / 第 2 次交付被拒: … is terminal]
  注：backoff=3600 的第 2 次执行是探针把**注入时钟推过 deadline** 之后才交付的（探针每轮 +3600s），
      第 3 次又被 deadline 挡住 ⇒ 退避没有被绕过，只是到期后合法交付。
定向（m0 DSN 口径，四条合跑 17 passed in 0.41s）：
  tests/application/run_orchestration/test_execute_task_one_ledger.py        3 passed
  tests/adapters/sqlite/test_workflow_acquire_backoff.py                     2 passed
  tests/postgres/test_workflow_acquire_backoff_pg.py                         2 passed（PG 实跑，非 skip）
  tests/application/run_orchestration/test_execute_task_accounting.py       10 passed（断言未改）
宽口径：tests/application+adapters+domain+postgres+contracts+e2e  1981 passed / 7 skipped（4:58）
m0：第 1 轮红于 framework/validate（MEM-055 未登记 INDEX；补行后复跑）
    PASS: profile=m0; 23 deterministic checks（全量 pytest 3708 passed / 10 skipped，8:11）
静态：mypy Success: no issues found in 882 source files；
      ruff check apps services packages adapters tests 全过；ruff format --check 892 files already formatted
CI：见 GOAL 迭代日志第 17 行（收口提交推送后回填）
```

## 影响报告

- **Domain/API/schema**：无 Domain / schema / API 变化；变的是 application 层循环语义与
  adapter 的 acquire 守卫。
- **安全/凭据**：无变化。
- **兼容性/迁移风险**：行为变化两处——① 瞬态失败的"总执行次数"从
  `max_attempts × 交付次数` 收敛到 `max_attempts`（更少执行、更早失败）；② 声明了退避的
  任务不再在进程内自旋（由派发方按 deadline 重派）。两者都只影响"可重试的瞬态失败"路径，
  成功路径与 permanent 失败路径不变。
- **可观测性**：失败尝试的 usage 记账沿用 `_attempt_scope`；新增的 attempt 号来自
  durable 交付代次，读面（`task.attempt`）与账本因此一致。
- **上游版本影响**：无新依赖。
- **下一项任务**：run 级重派（`RETRY_SCHEDULED` 的 AGENT_SESSION 任务由谁再执行）；
  锁粒度（每线程连接）；`failure_policy` 仍是零消费者；「按声明给 adapter 接线」仍待 escalation。

## 已知风险

- **重派依赖派发方**：退避 > 0 时把重试交回派发方；对 AGENT_SESSION 任务，run 已经失败，
  没有派发方会再来取——本轮**如实登记**这个"声明了但没有派发方"的状态（AC-05 只保证
  canonical state 不再说谎，不假装重派已实现）。
- **进程内重试缩短为 0 次的可能性**：若策略把 `max_attempts` 设得与已交付次数相等，循环
  第一次 acquire 后即判定预算用尽 ⇒ 该次调用不执行、直接失败（与"预算用尽"语义一致）。
- **PG acquire 的时钟**：与 cycle 16 同源（`server_now`），写入与比较必须同一个源。

## 状态历史

- 2026-09-17 创建（IN_PROGRESS）：derive 用探针量出三条硬事实（执行次数 = max_attempts ×
  交付代次、退避在 in-process 无效、失败后任务停在 LEASED），据此定口径：一次尝试一套账 +
  每个交付入口守 deadline + 退避交给派发方 + 如实登记"没有派发方"的缺口。
- 2026-09-17 收口（DONE）：AC-01…AC-06 全绿。收口后探针：`max_attempts=3` 累计 **3 次**
  （收口前 9）且落 `DEAD_LETTER`、声明 3600s 退避时一次调用只跑 **1 次**（收口前 3）；
  定向 17 passed（新 7 + 既有 accounting 10 未改断言）、宽口径 1981 passed / 7 skipped、
  mypy 882 files clean、ruff/format 干净、m0 23/23（首轮红于 `framework/validate` 的 INDEX
  漏登记，补行后复跑）。**未扩面**：run 级重派仍缺席（W-1），如实登记为下一轮输入。
