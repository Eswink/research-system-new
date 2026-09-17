---
id: RECHECK-20260915-082
plan_id: PLAN-20260915-082
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-003-cycle19
baseline_ref: 4d95b48
checked_head: 4d95b48+worktree
---

# RECHECK-20260915-082 — 无人值守的续跑（GOAL-003 cycle 19）

## 检查范围

PLAN-20260915-082 声称的交付面：① 新增读面 `WorkflowEngine.due_retry_task_ids(run_id)`
（与 claim 候选扫描同一判据、adapter 内用权威时钟比较）；② 新增 `RetryDispatchScheduler`
守护线程，把**重排已到期**的停车 run 自动续跑；③ 新作业进受控词表（`ScheduleJob.RETRY_DISPATCH`
+ `JOB_PURPOSE` + `BUILTIN_SCHEDULES` + ops 读面回落事实 + docs + API 用例镜像）；
④ 诚实边界：本进程无续跑上下文 ⇒ 跳过、用户暂停 ⇒ 不碰、跑完再扫 ⇒ 0。

**未覆盖**（见告警）：跨进程续跑（上下文仍是进程内暂存）、读面对"重排停车 vs 用户暂停"
的显式区分、`resume_paused` 失败路径的补偿。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 读面只在到期后回答（AC-01） | SQLite 注入时钟：deadline 前 1s 空、到点给出该任务；无重排任务/未知 run 恒空（3 用例）；PG parity 同判据 2 用例实跑（非 skip） | PASS |
| 无人值守真的跑完（AC-02） | e2e 全回路（真 `SqliteWorkflowEngine` + 真 `SqliteRunStore` + 注入时钟）：守护线程一次 pass ⇒ run `SUCCEEDED`、`execution_attempts == 2`、任务全部 `COMPLETED`；探针收口前/后：`无人 resume` → `派发 1 个 run ⇒ canonical run=SUCCEEDED，runtime 共执行 2 次` | PASS |
| 没到期不动 / 跑完幂等（AC-03） | e2e：到期前 pass 返回 0 且 `execution_attempts` 仍为 1；跑完后再 pass 返回 0（第二轮无派发） | PASS |
| 用户暂停不碰（AC-04） | 单测：run 停在 `PAUSED` 但任务面无到期重排 ⇒ 该 run 不被派发（读面空即跳过） | PASS |
| 重启不伪装（AC-05） | e2e：新建 `RunOrchestrationService`（模拟重启，`has_paused_context` 为假）⇒ pass 返回 0、run 仍 `PAUSED`、runtime 不再执行 | PASS |
| 迁移顺序（AC-06） | 单测断言两次落库顺序 `[(RUNNING), (SUCCEEDED)]`；续跑失败 ⇒ `[(RUNNING)]` 且 run 留 `RUNNING`（不假装续跑过）。**此条是 e2e 抓出来的**：第一版直接 `resume_paused` ⇒ 续跑被自己的暂停谓词挡住、`assert 1 == 2` | PASS |
| 派发方可见可控（AC-07） | `ScheduleJob.RETRY_DISPATCH` + `JOB_PURPOSE` + `BUILTIN_SCHEDULES`（15s）+ `FALLBACK_ENTRIES`（无 store 也可见）+ `docs/api/CONTROL_PLANE_API.md` 合法 job 列表 + `tests/api/test_ops_schedules_api.py::_BUILTIN_NAMES` 镜像同步；`ensure_builtins` 返回值改排序（新增成员不再让"顺序变了"冒充"内容变了"） | PASS |
| 门禁与记录（AC-08） | 定向 **11 passed**（e2e 2 + ops/scheduler 6 + sqlite 3）+ PG parity **2 passed** + ops 调度套件 **31 passed**；宽口径 `tests/application+adapters+domain+e2e+postgres+contracts` **2003 passed / 7 skipped**（5:29）；mypy **888 files clean**；`ruff check apps services packages adapters tests` 全过、`ruff format --check` **898 files already formatted**；m0 第 1 轮红于 `framework/validate`——`ALL_PLAN 勾选与 DONE 状态不一致: PLAN-20260915-082`（收口时把该行先写成 `[x]` 而计划仍是 `IN_PROGRESS`，**收口自伤、不是门禁缺陷**）⇒ 修正投影后第 2 轮 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3736 passed / 10 skipped**）；RECHECK-082 + MEM-057 + GOAL 记账 + ALL_PLAN | PASS |

## 告警

- **W-1（跨进程续跑仍缺席）**：续跑上下文与 PLAN-048 同源（进程内 `_paused` 暂存），
  进程重启后守护线程**如实跳过**、run 停 `PAUSED` 等人工/控制面介入——本轮没有做持久化
  执行上下文，也没有假装做到。下一轮候选。
- **W-2（用户暂停与重排停车读面同形）**：两者在 canonical run 状态上都是 `PAUSED`。
  本守护线程靠任务面（`RETRY_SCHEDULED` + 到期项）区分——**判定正确**，但读面本身仍不
  区分，控制台/运维看不到"这是自动会走的停车还是等人按的停车"。
- **W-3（`resume_paused` 失败后 run 留 RUNNING）**：上下文竞态（另一个 resume 先取走）
  或续跑抛错时，守护线程返回 0、run 留在 `RUNNING`（派发已释放、没有 continuation）。
  与 API 面"解除暂停但不伪装续跑"同义，但**没有补偿动作**：这个 run 不会自己再回到
  `PAUSED`，需要人工/控制面处理。
- **W-4（守护线程与 worker 的判定面不同源）**：`claim_next` 只派发 EXECUTION 任务，
  本守护线程管的是 AGENT_SESSION 任务的重排——两个派发方各管一半，没有统一读面能看到
  "这个 run 现在有没有活的派发方"。本轮靠探针把事实量出来，未做统一。
- **W-5（Fake 的到期语义是"立刻"）**：`FakeWorkflowEngine.due_retry_task_ids` 返回该 run
  全部 `RETRY_SCHEDULED` 任务（Fake 没有写入 deadline 的路径）——真实 deadline 判定由两个
  持久化 adapter 的用例覆盖，Fake 侧不假装有时钟语义。
- **W-6（探针口径）**：收口前/后数字来自同一脚本 + 真实 `SqliteWorkflowEngine`（非 mock），
  脚本在 `scratch/`（gitignored），输出原文抄进本文件与 PLAN 的证据段。

## 结论

cycle 18 交付"停车 + 有人按 resume 就能真的跑完"，但探针量出**没有人会自动按**（worker
的 `claim_next` 只扫 EXECUTION、lease 恢复面 0 条、`retry_at` 不在任务投影里 ⇒ 读面根本
回答不了"到没到期"）。本轮补齐这条链：读面（到期判定）+ 守护线程（到期续跑）+ 受控词表
与读面可见性。探针数字：`无人 resume` → `派发 1 个 run ⇒ canonical run=SUCCEEDED，
runtime 共执行 2 次`。

结果为 **PASS_WITH_WARNINGS**：W-1（跨进程）是明确不做、需要持久化执行上下文的相邻缺口；
W-2…W-6 是语义边界与适用范围的如实登记。**未宣称"重试闭环全自动且跨进程可靠"**：本轮的
自动续跑以"本进程持有续跑上下文"为前提，重启后诚实跳过。
