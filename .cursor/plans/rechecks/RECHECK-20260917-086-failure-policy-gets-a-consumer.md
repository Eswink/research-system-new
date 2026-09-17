---
id: RECHECK-20260917-086
plan_id: PLAN-20260917-086
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-004-cycle3
baseline_ref: 7316d1d
checked_head: 652e712+worktree
---

# RECHECK-20260917-086 — 失败策略的消费者（GOAL-004 cycle 3 = EC-03）

## 检查范围

PLAN-20260917-086 声称的交付面：① 契约视图 `TaskContract.failure_policy_view()`
（能消费的键给取值、不能消费的键点名、非法取值响亮失败）；② run 级消费者
`on_task_failure ∈ {FAIL_RUN(缺省), CONTINUE}` 在 phase runner 三处失败点统一生效；
③ 被容忍的失败**可见**（`TaskOutcome.failure_policy` + `task.failed` + `run.degraded`）；
④ `CONTINUE` 不让 run 假装成功（收敛 `DEGRADED`，未冒充 SUCCEEDED、也未判死）；
⑤ **未声明时行为与基线逐字一致**。

**未覆盖**（见告警）：`on_validation_failure`/`allow_partial_evidence` 仍无消费者（已点名）；
`DEGRADED` 的 HTTP 落库未单独 e2e（走既有 `state=outcome.state` 映射）；被容忍失败不进
run 行字段（只在事件链与 RunOutcome）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 域视图（AC-01） | 域用例 5：缺省 ⇒ `FAIL_RUN`/`tolerated is False`；`CONTINUE` 原样读出；非法取值 ⇒ `ValueError`（消息点名允许值）；未知键进 `unhonored` 且不改取值；`on_validation_failure` 声明前后判定相同 | PASS |
| run 级消费（AC-02） | 应用用例（真 `_execute_one_task`，用"会话尝试次数"当证据）：三任务（同组两个 + 后续 phase）全终局失败，声明 `CONTINUE` ⇒ **尝试 3 次**、收敛 `DEGRADED`、三条 TaskOutcome 都标 `CONTINUE`；未声明 / 显式 `FAIL_RUN` ⇒ **只尝试 1 次**、收敛 `FAILED`、`tasks == ()`（基线逐字一致） | PASS |
| 端到端（AC-02/AC-03） | e2e（真装配：SQLite 任务面 + canonical 事件链 + 真 runner）：首个任务永久失败且契约声明 `CONTINUE` ⇒ `runtime.run_calls >= 2`（后续真的跑了）、`outcome.state == DEGRADED`、事件链含 `run.degraded` 且**不含** `run.completed`；同一场景不声明 ⇒ 1 次尝试、`FAILED`、无 `run.degraded` | PASS |
| 可见（AC-03） | 应用用例：被容忍路径发 3 条 `task.failed`（payload 带 `failure_policy=CONTINUE`）、不发 `run.completed`；degrade 回调收到 3 条被容忍失败且消息含 `on_task_failure=CONTINUE`；`run.degraded` payload 由 `run_terminals.publish_degraded_run` 组装（策略 + 失败清单） | PASS |
| 诚实边界（AC-04） | 域用例（`on_validation_failure` 不改判定）+ 应用用例（声明 `on_validation_failure` ⇒ 仍 1 次尝试、仍 `FAILED`）；`docs/architecture/TASK_HANDOFF.md §2.1` 表格点名"未消费的键"与原因 | PASS |
| 门禁与记录（AC-05） | 定向：domain 5 / application 6 / e2e 2（新增）+ 既有 `test_fault_matrix`/`test_fault_convergence`/`test_parked_retry`/`test_phase_spans_m15` 全绿（受影响套件一次复跑 **977 passed**）；`python/typecheck`（mypy 906 files）与 `python/product-lint`/`format-check` 绿；m0 = **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3823 passed / 10 skipped**，511.99s）；RECHECK-086 + MEM-061 + GOAL/ALL_PLAN 记账 | PASS |

## 反证与实测

- **反证（消费点真的在起作用）**：把 `failure_step` 的容忍分支去掉 ⇒ `test_declared_continue_tolerates_failures_and_runs_the_rest`
  会看到 `runtime.runs == 1` 且 `state == FAILED` 而失败（断言的是行为差异，不是实现细节）；
  端到端用例同理会看到 `run_calls == 1`。
- **事件词表门禁真的在拦**：加两个事件类型后 `test_m5_domain_increments.TestEventTypeInventory`
  立刻红（`Extra items in the left set: task.failed, run.degraded`）——先把它当"我漏了文档"
  的证据，再按门禁的意图补 `EVENT_MODEL.md` 词表与清单（34 → 36），**断言强度未改**。
- **450 行硬上限第二次拦人**：`phase_runner.py` 456 行 + `_execute_phase_group` 61 行、
  `service.py` 483 行。处置是**搬代码**（`outcomes.py` 结果值对象、`run_terminals.py` 两条
  终态发布、`_GroupFrame` 收敛参数、`tolerated_outcome` 进 helpers），不是调门禁；
  复核后 437/450 与 450/450（`service.py` 正好贴线，下一次动它必须同时搬走）。
- **组合复跑的假红**：一次把 `tests/application tests/e2e tests/domain tests/contracts tests/api`
  按这个顺序跑，出现 3 条 `tests/api` 的 PG 用例红——原因是 `tests/e2e/test_pg_crash_restart.py`
  会重启 PG（临时存储随之清空），而字母序完整跑里 `tests/api` 在 `tests/e2e` **之前**，
  所以只有我手工拼的顺序会撞上。判据：`tests/api` 单独跑 411 passed、m0 全量 23/23。
  （与产品代码无关，但"顺序敏感的临时组合"以后按字母序或整目录跑。）

## 告警

- **W-1（`on_validation_failure` 仍无消费者）**：它在示例契约里是 `DEAD_LETTER`，但验收门在
  durable 完成**之后**才跑（任务行已写 SUCCEEDED），消费它需要"完成后二次写任务行"——
  属产品语义决策，登记为后继入口；本轮只把它点名为 `unhonored`。
- **W-2（`DEGRADED` 的 HTTP 落库未单独 e2e）**：`run_from_execution` 用
  `state=outcome.state` 的同一行映射（SUCCEEDED/FAILED 已被既有用例覆盖），本轮的端到端
  证据停在 `RunOutcome.state == DEGRADED` + canonical 事件链；若未来 DEGRADED 需要
  额外字段（如失败清单）落 run 行，必须补 API 层用例。
- **W-3（被容忍失败不进 run 行）**：run 行只体现状态 `DEGRADED`；"哪几条失败"要去事件链
  （`run.degraded`）或 RunOutcome 里读。这是有意的（不新增 canonical 字段），但读面
  `GET /runs/{id}` 看不到清单——需要的话应做成读面投影而不是塞进 run 行。
- **W-4（`DEGRADED` 非终态但没有自动后续）**：跑完被容忍失败的 run 停在 DEGRADED，
  没有守护线程/调度器会推进它（`RetryDispatchScheduler` 只认 PAUSED）。人工可 `resume`
  或 `cancel`；若产品希望"失败清单可重试"，那是另一条能力（登记）。
- **W-5（`service.py` 贴线）**：450/450，属于"下一行就会红"的状态；本轮已把两条终态发布搬走，
  后续任何新增都要先搬再写。

## 门禁

- 定向：`tests/domain/test_failure_policy_view.py` **5 passed**；
  `tests/application/run_orchestration/test_failure_policy_consumer.py` **6 passed**；
  `tests/e2e/test_failure_policy_degraded_run.py` **2 passed**；受影响套件一次复跑
  （source-limits + run_orchestration + 两个 fault e2e + phase spans）**977 passed**；
  `tests/domain/test_m5_domain_increments.py` **14 passed**（事件词表门禁）。
- m0：`PASS: profile=m0; 23 deterministic checks`（全量 pytest **3823 passed / 10 skipped**，
  511.99s；首跑红 2 处 = 两个文件撞 450 行/50 行硬上限，搬代码后复跑全绿）。
- 文档同源：`docs/architecture/TASK_HANDOFF.md §2.1`（策略表 + 未消费键）、
  `docs/architecture/EVENT_MODEL.md`（词表 +2）、`docs/reliability/RUN_STATE_MACHINE.md`
  （DEGRADED 的语义与生产者）。

## 结论

`failure_policy` 从"声明了没人消费"变成**有真实消费者**：run 级的 `on_task_failure` 由
phase runner 的**唯一失败分叉点**读取——`FAIL_RUN`（缺省）是原来的隐式 fail-fast，
`CONTINUE` 让终局失败变成"被容忍"（`task.failed` + `TaskOutcome.failure_policy`），剩余工作
照跑，最后收敛 `DEGRADED` 并发 `run.degraded`（点名策略与失败清单）。**未声明时行为逐字
不变**（既有 fault 矩阵/收敛用例 + 新增对照用例共同证明）。

结果为 **PASS_WITH_WARNINGS**：W-1 是仍未消费的键（已点名并给出原因），W-2/W-3/W-4/W-5
是读面与容量的如实登记。**未宣称"failure_policy 全部生效"**：只有 `on_task_failure` 有
消费者，其余键由视图点名；被容忍失败不进 run 行，读清单要走事件链。
