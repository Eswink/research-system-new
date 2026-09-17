---
id: RECHECK-20260915-081
plan_id: PLAN-20260915-081
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-003-cycle18
baseline_ref: 192c6e1
checked_head: 192c6e1+worktree
---

# RECHECK-20260915-081 — 停下来的重试（GOAL-003 cycle 18）

## 检查范围

PLAN-20260915-081 声称的交付面：① 声明了退避的重排不再把 run 判失败（改停 `PAUSED`，
失败任务与后续 specs 经 `on_pause` 交回 service）；② deadline 之前再执行/再 resume
只是**重新停车**（不执行、不判失败、不破坏 run）；③ 到期后 resume 续跑真的执行第二次
尝试并跑完 run；④ deadline 守卫的错误类型细分（`RetryNotDueError`）；⑤ 两个对照组
（无重试策略 / 有重试无退避）行为不变。

**未覆盖**（见告警）：自动重派（守护线程/调度器按时扫 PAUSED 并 resume）、跨进程续跑
（进程内暂存）、读面区分"重排停车 vs 用户暂停"。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| run 不再判失败（AC-01） | 探针收口前 `phase runner 返回 = FAILED` → 收口后 `PAUSED`；e2e 用例断言 `outcome.state == PAUSED`、outbox 无 `RUN_FAILED`、有 `TASK_RETRY_SCHEDULED` | PASS |
| 上下文真的交回（AC-02） | 探针 `on_pause 拿到的 specs` 0 → 1；单元用例：组内第一个任务成功、第二个重排 ⇒ 交回 `[第二个, 第三个]`，`outcome.tasks` 里保留已成功的第一个 | PASS |
| 没到期就 resume 不破坏 run（AC-03） | e2e：停车后立刻 `resume_paused` ⇒ 结果仍 `PAUSED`、`execution_attempts` 仍为 1（一次都没跑）、`has_paused_context` 仍为真 | PASS |
| 到期后 resume 真的重试（AC-04） | e2e：注入时钟推过 `retry_at` ⇒ `resume_paused` 续跑，`execution_attempts == 2`、两个任务 `SUCCEEDED`、被重试任务 `attempt == 2`、run `SUCCEEDED`；**不调用** `recover_expired_leases` 也成立（失败完成已释放租约） | PASS |
| 类型化拒绝（AC-01 支撑） | `RetryNotDueError(InvalidInputError)`；探针 `deadline 前 RetryNotDueError`（收口前是裸 `InvalidInputError`）；两个 adapter 同一类型；cycle 17 的 `pytest.raises(InvalidInputError)` 用例不改仍绿 | PASS |
| 对照组不变（AC-05） | e2e：无重试策略 ⇒ 任务 `FAILED` + run `FAILED` + 无暂停上下文；有重试无退避 ⇒ `execution_attempts == 2`、run `SUCCEEDED`（同一次调用内重试） | PASS |
| 门禁与记录（AC-06） | 定向 **9 passed**（e2e 5 + 应用层 4）；宽口径 `tests/application+adapters+domain+e2e+postgres+contracts` **1990 passed / 7 skipped**（4:51）；mypy **884 files clean**；`ruff check apps services packages adapters tests` 全过、`ruff format --check` **894 files already formatted**；m0 第 1 轮红于 `framework/validate`——`任务计划未加入 ALL_PLAN: PLAN-20260915-081`（收口时漏登记，**不是门禁缺陷**）⇒ 登记 ALL_PLAN 行后复跑 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3719 passed / 10 skipped**）；RECHECK-081 + MEM-056 + GOAL 记账 + ALL_PLAN | PASS |

## 告警

- **W-1（自动重派仍缺席）**：本轮把"重排变成孤儿"改成"停车 + 有人能真的跑完"，但**没有人
  自动来跑**——长退避（探针用 3600s）的任务会一直停在 PAUSED，直到控制面 `POST
  /runs/{id}/resume`。下一轮首选项：调度器/守护线程按 `retry_at` 到期 resume。
- **W-2（停车依赖进程内上下文）**：`_paused` 暂存与 PLAN-048 的暂停同源，进程重启后
  resume 诚实报 `continuation=NONE`、run 停在 PAUSED 等人工介入。**未假装**跨进程续跑。
- **W-3（读面不区分两种 PAUSED）**：用户暂停与"重排停车"在 run 状态上都是 `PAUSED`；
  区分它们要读任务面（`RETRY_SCHEDULED` + `retry_at`）或事件流。登记为下一轮候选。
- **W-4（停车期间预算预留挂着）**：`_release_if_terminal` 只在终态释放，PAUSED 不释放
  （重试需要预算）——读账时预留会跟着停车一起挂着。
- **W-5（`retry_deferred` 只表达"交回派发方"）**：它不携带 deadline；需要 deadline 的
  读者走 durable 面（`task.retry_scheduled` 事件 / 任务行 `retry_at`），不在结果对象里复制。
- **W-6（探针口径）**：收口前/后的数字都来自同一脚本 + 真实 `SqliteWorkflowEngine`
  （非 mock），脚本在 `scratch/`（gitignored），输出原文抄进本文件与 PLAN 的证据段。

## 结论

本轮把 cycle 17 留下的"声明了退避的重排没有派发方"从**孤儿状态**改成**可派发的停车
状态**：run 停 `PAUSED` 而不是终态 `FAILED`，失败的任务与后续 specs 交回 service，
到期后 resume 会真的执行第二次尝试并跑完整条 run。探针数字：`phase runner 返回`
`FAILED → PAUSED`、`on_pause specs` `0 → 1`、`RESUME` `InvalidTransitionError →
合法 → RUNNING`。

结果为 **PASS_WITH_WARNINGS**：W-1（没有自动派发方）是本轮明确不做、下一轮必须做的
相邻缺口；W-2…W-6 是语义边界与适用范围的如实登记。**未宣称"重试闭环已经自动完成"**：
本轮交付的是停车 + 人工/控制面触发可以真的续跑。
