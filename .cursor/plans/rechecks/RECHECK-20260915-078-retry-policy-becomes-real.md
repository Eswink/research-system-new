---
id: RECHECK-20260915-078
plan_id: PLAN-20260915-078
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-003-cycle15
baseline_ref: e830def
checked_head: e830def+worktree
---

# RECHECK-20260915-078 — 重试策略落地（GOAL-003 cycle 15）

## 检查范围

PLAN-20260915-078 声称的交付面：Domain 侧 `FailureAction` + `TaskContract.disposition` /
`decide_failure` 纯函数 + Port 的 `TaskCompletion.failure_category`；SQLite 与 PG 两个
adapter 的 complete/claim/acquire 三条路径（判据、可 claim 状态表、交付时 attempt 与
`task_json` 同步）；新增用例（SQLite 8 条、PG parity 2 条、状态驱动枚举门禁 3 条）。

**未覆盖**（见告警）：退避时延、`failure_policy` 的消费、指数退避、跨进程重试治理。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 缺口是"声明了但没人驱动"（实测，不是推断） | 限定写法 `ResearchTaskState.State.<NAME>` 扫生产代码（adapters/services/packages/apps/tools/scripts，排除 fakes）：收口前 `RETRY_SCHEDULED` 与 `DEAD_LETTER` 命中 **0**；`TaskCompletion` 无失败类别字段；`retry_policy` 无消费者 | PASS（收口前） |
| 判据只有一份（Domain 纯函数） | `decide_failure` 在 `packages/domain/tasks.py`；SQLite `_complete_impl` 与 PG `complete_impl` 都只调用它，各自没有第二套 if 规则（grep 两条 `decide_failure` 调用点） | PASS |
| 可重试失败重排（AC-01） | `test_a_retryable_failure_is_rescheduled_and_claimable_again`：状态 → `RETRY_SCHEDULED`、`TASK_RETRY_SCHEDULED` 事件在 outbox、**能再被 claim**、再次 claim 后 attempt 1 → 2（投影与列同口径） | PASS |
| 交付代次与投影同步 | `test_a_reclaimed_task_projection_advances_with_the_hand_out`：走**不依赖 retry_policy** 的路径（租约过期 → `recover_expired_leases` → 再交付），断言 lease 的 fence 1 → 2 且投影 attempt = 2 | PASS |
| 次数用尽进死信（AC-02） | `test_attempts_exhausted_goes_to_dead_letter`：`max_attempts=2`，两次失败后状态 `DEAD_LETTER`、attempt = 2、`claim_next` 返回 None | PASS |
| 三条反证（AC-03） | 不可重试类别（`POLICY_DENIED`）→ FAILED；未分类（category=None）→ FAILED；无 `retry_policy` → FAILED | PASS |
| at-least-once 不回退（AC-04） | `test_replaying_a_completion_after_a_retry_is_still_idempotent`：重排之后重放同一次完成，`calls[-1].result_summary == "deduped"` 且状态不变 | PASS |
| 成功不受影响（AC-05） | `test_a_successful_completion_is_untouched_by_the_retry_path`：outcome=SUCCEEDED → SUCCEEDED，且不发 `TASK_RETRY_SCHEDULED` | PASS |
| PG/SQLite 同语义（AC-06） | `tests/postgres/test_workflow_retry_policy_pg.py` 两条逐条对应 SQLite（重排 + 死信 + attempt 计数）；本地实跑 **2 passed**。**顺带抓到一处真实分歧**：PG 的 complete 也在递增 attempt（与 SQLite 的 claim 递增口径不一致）⇒ 已按同一口径修正 | PASS（抓到真实分歧） |
| 状态驱动的枚举门禁（AC-07） | `tests/domain/test_task_state_drivers.py`：状态集合 == 登记表；登记"有驱动"的必须有生产命中；登记"没驱动"的必须没有命中（三条用例，反向也查） | PASS |
| 门禁与记录（AC-08） | m0 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3681 passed / 10 skipped**）；`tests/adapters+tests/domain+tests/postgres+tests/contracts`（m0 DSN 口径）**1297 passed / 5 skipped**；三条新用例套件合跑 **13 passed**（SQLite 8 / 门禁 3 / PG parity 2）；mypy **876 files clean**；ruff/format 干净；RECHECK-078 + MEM-053 + GOAL 记账 + ALL_PLAN | PASS |

## 告警

- **W-1（没有退避）**：重排后立即可被 claim（`RETRY_SCHEDULED` 与 `QUEUED` 同权）。
  失败很快的任务会在 `max_attempts` 次内热循环。指数退避要么给 `RetryPolicy` 加
  `backoff_seconds`（schema + loader 变更），要么加 `retry_at` 列 + claim 过滤——两者都是
  独立决定，本轮刻意不做。
- **W-2（`failure_policy` 仍是零消费者）**：`on_validation_failure: DEAD_LETTER` 这类键
  的**键名空间没有和 `FailureCategory` 对齐**，直接消费等于自己发明语义（本轮选择**不猜**）。
  它和 `retry_policy` 原本是同一类缺口，现在只剩它没做。
- **W-3（attempt 的语义变了）**：从"提交时的快照"变成"已经开始的尝试次数"，且**只在交付
  lease 时**（claim / acquire 两条路径）随交付代次一起前进。绕过交付路径直接改状态不会让
  计数前进（域不变量把 attempt>1 与 lease 绑在一起，正是防线）。
- **W-4（枚举门禁是文本级）**：按 `ResearchTaskState.State.<NAME>` 限定写法扫描；
  别名导入（`from ... import State`）会漏报。本仓写法统一，风险低但存在。
- **W-5（PG parity 用例在 PG 不可达时 skip）**：`tests/postgres/**` 按 conftest 的
  postgres marker 跳过；本地与 CI 的 ubuntu job 都实跑，但跳过时结论以 SQLite +
  contract suite 为准。
- **W-6（交付会重写 task_json）**：为了让 attempt 列与投影同步且满足域不变量，**每一次**
  交付（claim / acquire，含重试与过期回收后的再交付）都会重编码任务 JSON。若未来有消费者
  把 task_json 当作"提交时的原始快照"来比对，需要改成读投影（`list_tasks` 对 status
  已经是投影口径）。这条口径有回归用例把着：`test_a_reclaimed_task_projection_advances_with_the_hand_out`
  用"租约过期 → 回收 → 再交付"这条**不依赖 retry_policy** 的路径断言投影 attempt 前进。

## 结论

本轮把三件**声明了却没人用**的东西接上：`retry_policy`（可重试 ⇒ 重排、次数用尽 ⇒ 死信）、
Domain 的 `RETRY_SCHEDULED`/`DEAD_LETTER` 两个状态（从"命中 0"变成有生产驱动方）、
以及重试分类缺的那个输入（`TaskCompletion.failure_category`）。判据只有一份（Domain 纯函数），
SQLite 与 PG 共用；PG parity 用例还抓出一处真实分歧（attempt 在两侧递增时机不同），已按
同一口径修正。另加一条**枚举门禁**把"状态 → 谁驱动"钉住，下一次"声明了但没人走进去"
会直接判红。

结果为 **PASS_WITH_WARNINGS**：W-1/W-2 是本轮明确不做的相邻缺口（退避、`failure_policy`），
W-3…W-6 是语义变更与门禁的适用边界。本轮两次换过 attempt 的推进口径（complete → claim →
"交付即一次尝试"，列与 task_json 同一条更新），过程中的门禁红（50 行函数上限、450 行文件上限）
都是**抽出助手**解决的，没有放宽阈值。**未宣称"可靠性已经完整"**：AGENTS.md §7 的退避与
circuit breaker 在本路径上仍未落地。
