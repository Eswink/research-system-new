---
id: RECHECK-20260915-079
plan_id: PLAN-20260915-079
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-003-cycle16
baseline_ref: d9beea7
checked_head: d9beea7+worktree
---

# RECHECK-20260915-079 — 重排后的退避（GOAL-003 cycle 16）

## 检查范围

PLAN-20260915-079 声称的交付面：① 上一轮"`retry_policy` 零消费者"口径的就地校正
（PLAN-078 / RECHECK-078 / MEM-053 / GOAL row 15）；② 策略面退避（`RetryPolicy` 两个
可选字段 + `TaskContract.retry_delay` 纯函数 + schema/loader/解码）；③ `tasks.retry_at`
列与两个 adapter 的 complete/claim/acquire 三条路径；④ 新增用例（domain 7、SQLite 4、
PG parity 3）。

**未覆盖**（见告警）：应用层 in-process 重试循环的退避与 attempt 口径统一、
`failure_policy` 的消费、退避与 circuit breaker 的联动。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 校正：上一轮"零消费者"过宽 | `packages/application/run_orchestration/task_executor.py` 逐行核对：`:83` `_retry_policy`、`:87` `_retryable`（`retryable_categories`）、`:111` 起用 `max_attempts` 刹车 | PASS（四处记录已就地标注 + 追加更正条目，未改写历史结论） |
| 策略面能声明退避（AC-01） | `RetryPolicy.backoff_seconds` / `max_backoff_seconds` + `schemas/task-contract.schema.json` 两个属性 + loader 读取 + 两处解码共用一份；`examples/contracts/task_contracts.yaml` 有一条真实契约声明 `30s/300s` | PASS |
| 计算是纯函数且有界（AC-02） | `tests/domain/test_retry_backoff.py`：指数增长（30/60/120）、cap 只封顶（30/60/100/100）、无策略/无基数/基数为 0 ⇒ 0、三个非法值在构造时被拒、`attempt=0` 被拒 | PASS（7 passed） |
| 重排不会立刻被 claim（AC-03） | SQLite：`test_a_rescheduled_task_is_not_claimable_before_its_deadline`（60s：立刻 None、59s None、60s 拿到且 `fence=2`）；PG：`test_pg_holds_a_rescheduled_task_until_its_deadline`（库里 `retry_at` 在未来 → claim None） | PASS |
| 到期后可 claim（AC-04） | 同上两例的"推过 deadline"分支（SQLite 推时钟、PG 把 `retry_at` 挪到过去） | PASS |
| 向后兼容（AC-05） | SQLite `test_a_task_without_backoff_is_still_claimable_immediately`（0.94s 内立即拿到）；PG `test_pg_without_backoff_is_still_claimable_immediately`；既有 `tests/postgres/test_workflow_retry_policy_pg.py` 两条仍绿 | PASS |
| 交付即清（AC-06） | SQLite `test_the_deadline_is_written_and_cleared_not_left_behind`（直读列 → NULL）；PG `test_pg_clears_the_deadline_on_hand_out` | PASS |
| 不占候选窗口 | SQLite `test_an_unexpired_retry_does_not_block_another_claimable_task`：一个 3600s 冷却的重试与另一个可 claim 任务并存时，取走的是后者 | PASS |
| 门禁与记录（AC-08） | m0（见下）；`tests/domain+tests/adapters+tests/postgres+tests/contracts` **1311 passed / 5 skipped**；mypy **879 files clean**；ruff/format 干净；RECHECK-079 + MEM-054 + GOAL 记账 + ALL_PLAN | PASS |

## 告警

- **W-1（退避只覆盖 durable 层）**：`task_executor` 的 in-process 重试循环（同一 lease 内的
  瞬时错误）仍会立刻重试，且它用自己的局部 `attempts` 计数。同一个 `max_attempts` 目前是
  **两套账**：in-process 的局部计数与 durable 的 `attempt` 列互不相认。本轮如实不做。
- **W-2（时钟来源）**：SQLite 用注入时钟（`timestamp_now`），PG 用 `server_now`
  （生产 = 数据库时钟、测试 = 注入时钟）。deadline 的**写入**与 claim 的**比较**在两侧都
  取自同一个源，但两 adapter 的源在进程外并不相同——跨机部署时以 PG 为准。
- **W-3（没有抖动）**：指数退避没有 jitter，同一批任务会在同一时刻集中到期（thundering
  herd）。策略面没有 jitter 字段，本轮不发明语义。
- **W-4（cap 语义是硬约束）**：`max_backoff_seconds < backoff_seconds` 直接拒（否则 cap 会
  静默压低基数）；这意味着"上限应小于基数"这种写法在本地就报错，而不是被静默接受。
- **W-5（PG parity 用例在 PG 不可达时 skip）**：同前几轮，跳过时结论以 SQLite + contract
  suite 为准。
- **W-6（事件字段是附加的）**：`task.retry_scheduled` 新增 `retry_at`（重排且真的声明了退避
  时才有值）。既有消费者按 `outcome`/`attempt` 读不受影响。

## 结论

本轮做了两件事。第一件是**记录校正**：上一轮写下的"`retry_policy` 零消费者"过宽，
应用层 in-process 重试循环一直在消费它——四处记录就地标注 + 追加更正条目，并把由此发现的
"一个 `max_attempts` 两套账"登记为下一轮输入。第二件是**退避落地**：策略面新增两个可选字段、
Domain 纯函数算时延、`tasks.retry_at` 落库、两个 adapter 的 claim 在扫描内过滤未到期的重试，
交付即清。AGENTS.md §7 的四条（retry classification / exponential backoff / dead-letter /
manual recovery）到这一轮为止**前三条都有真实驱动方**，第四条（人工恢复入口）仍未做。

结果为 **PASS_WITH_WARNINGS**：W-1 是明确不做的相邻缺口（in-process 循环），W-2/W-3/W-4/W-5/W-6
是语义边界与门禁适用范围。**未宣称"可靠性已经完整"**：circuit breaker、jitter、人工恢复入口
在本路径上都还没有。
