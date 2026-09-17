---
id: RECHECK-20260915-080
plan_id: PLAN-20260915-080
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-003-cycle17
baseline_ref: 1dd2a89
checked_head: 1dd2a89+worktree
---

# RECHECK-20260915-080 — 一次尝试一套账（GOAL-003 cycle 17）

## 检查范围

PLAN-20260915-080 声称的交付面：① `execute_task` 的尝试序号改为 durable 交付代次、
失败一律 `complete(FAILED, category)` 落账、声明退避时把下一次尝试交回派发方；
② `acquire_lease`（SQLite + PG）也守 `retry_at` deadline；③ 新增用例（executor 3、
SQLite acquire 2、PG parity 2）与探针收口前/后对照。

**未覆盖**（见告警）：run 级重派（`RETRY_SCHEDULED` 的 AGENT_SESSION 任务由谁再执行）、
session 级失败的类别（不可重试，保守）、锁粒度、`failure_policy`。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 缺口是量出来的（不是推断） | 探针 `scratch/goal3-cycle17-probe1-two-ledgers.py`：`max_attempts=3` 时 runtime 被执行 **3 次/交付**、3 次交付共 **9 次**；声明 3600s 退避仍立刻跑满 3 次；失败后任务停在 **LEASED** | PASS（收口前实测） |
| 总执行次数 ≤ max_attempts（AC-01） | 探针收口后：`max_attempts=3` 累计 **3 次**（收口前 9）、`max_attempts=2` 累计 **2 次**（收口前 6）；`test_exhausted_transient_failure…` 断言 `runtime.runs == 3` | PASS |
| 失败必须落账（AC-02） | 同一用例：任务落 `DEAD_LETTER`、`attempt=3`；outbox 里 `task.retry_scheduled` ×2 + `task.completed`（`action=DEAD_LETTER`）×1；收口前同一个探针显示 `status=LEASED` | PASS |
| 退避 > 0 时不自旋（AC-03） | 探针收口后：`backoff=3600` 一次调用只执行 **1 次**；用例断言 `result.message == "retry deferred to the dispatcher"` 且任务留 `RETRY_SCHEDULED` | PASS |
| acquire 守 deadline（AC-04） | SQLite `test_acquire_refuses_a_task_that_is_still_waiting_for_its_backoff`（600s：立刻拒、599s 拒、600s 放行且 `fence=2`）；PG 同名 parity（注入时钟推过 deadline 后放行） | PASS |
| 不重复记账（AC-05） | attempt 号 = 交付代次 ⇒ 每次尝试的 `_attempt_scope` 唯一；既有 `tests/application/run_orchestration/test_execute_task_accounting.py` **26 passed 未改断言**（含 M15 BLOCKER-5 的"无重复 entry"两条） | PASS |
| 向后兼容 | 无退避声明的策略行为不变（`backoff=None` 的两条用例：预算耗尽语义、acquire 立即可租）；`tests/adapters/tests/contracts/tests/e2e` 全绿 | PASS |
| 门禁与记录（AC-06） | m0 第 1 轮红于 `framework/validate`——`工程记忆未加入 INDEX: MEM-20260915-055`（收口时漏登记，**不是门禁缺陷**）⇒ 补 `.cursor/memory/INDEX.md` 一行后复跑 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3708 passed / 10 skipped**）；定向 **17 passed**（新 7 + 既有 accounting 10，PG 两条实跑非 skip）；`tests/application+adapters+domain+postgres+contracts+e2e` **1981 passed / 7 skipped**（4:58）；mypy **882 files clean**（`mypy` 按 pyproject 作用域）；`ruff check apps services packages adapters tests` 全过、`ruff format --check` 892 文件已格式化；RECHECK-080 + MEM-055 + GOAL 记账 + ALL_PLAN | PASS |

## 告警

- **W-1（run 级重派仍未实现）**：退避 > 0 时任务留给派发方，但 phase runner 的失败语义是
  "任务失败 ⇒ run 失败"，而 `claim_next` 只派发 EXECUTION（worker）任务 ⇒ 对 AGENT_SESSION
  任务，"声明了退避的重排"目前**没有派发方**会再来取。本轮只保证 canonical state 不再说谎
  （不是停在 LEASED），**不假装**重派已实现——已登记为下一轮首选项。
- **W-2（session 级失败仍不可重试）**：`_run_session` 返回 FAILED 时没有失败类别
  （`AgentSessionResult` 里没有这个字段），完成时不带类别 ⇒ durable 判据按"不可判定"处理
  （FAIL）。这是保守口径，不是缺陷修复；要支持"会话失败也走重试策略"需要先给会话结果一个
  类别来源（另立决定）。
- **W-3（心跳轮换 lease_id）**：失败落账必须用**心跳之后**的租约（`live`），否则
  `complete` 会因 lease_id 不匹配报错。收口前的失败路径从不 complete，所以这个坑是
  本轮第一次暴露——已在代码注释与本节写明。
- **W-4（预算用尽时不执行）**：若进入 `execute_task` 时交付代次已 ≥ `max_attempts`，
  循环会在**不执行**的情况下判定用尽并返回失败（与"预算用尽"语义一致，但结果是"这次调用
  一次都没跑"）。durable 侧此时通常已是 DEAD_LETTER（acquire 会先被拒）。
- **W-5（探针依赖真实引擎）**：收口前/后的数字都来自同一个探针脚本 + 真实
  `SqliteWorkflowEngine`（非 mock），脚本在 `scratch/`（gitignored），输出原文抄进本文件与
  PLAN 的证据段。
- **W-6（PG parity 用例在 PG 不可达时 skip）**：同前几轮；跳过时结论以 SQLite + contract
  suite 为准。

## 结论

本轮把 cycle 16 登记的"一个 `max_attempts` 两套账"量出来并修掉：尝试序号改为 durable 的
交付代次、每次失败先落账再决定是否继续、声明退避就把下一次尝试交回派发方，并让
`acquire_lease` 也守 `retry_at`（此前只有 `claim_next` 守）。探针数字：`max_attempts=3`
从"3 次交付共执行 9 次、任务停在 LEASED"变成"总共 3 次、落 DEAD_LETTER"；声明 3600s 退避时
从"立刻跑满 3 次"变成"一次调用只跑 1 次"。

结果为 **PASS_WITH_WARNINGS**：W-1（没有派发方来接 `RETRY_SCHEDULED` 的 AGENT_SESSION 任务）
是本轮明确不做、且必须马上做的相邻缺口；W-2…W-6 是语义边界与适用范围的如实登记。
**未宣称"重试闭环已经完整"**：dispatch 侧的重派仍然缺席。
