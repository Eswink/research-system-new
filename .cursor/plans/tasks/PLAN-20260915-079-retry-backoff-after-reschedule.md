---
id: PLAN-20260915-079
slug: retry-backoff-after-reschedule
title: 重排后的退避：策略面时延字段 + `retry_at` 列，让重试不再热循环（并校正上一轮"零消费者"口径）
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 16 = cycle 15（PLAN-20260915-078）「下一轮输入」的第一项。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」+ 2026-09-17 用户拍板恢复条件②（显式变更 budget.max_cycles 10→20 并置回 ACTIVE）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-079-retry-backoff-after-reschedule.md
memory_entries:
  - MEM-20260915-054
---

# PLAN-20260915-079 — 重排后的退避（GOAL-003 cycle 16）

## 目标

两件事，前一件是**校正上一轮的记录**，后一件是**补真缺口**：

**A. 口径校正**：cycle 15 的记录（PLAN-078「目标」段、RECHECK-078、MEM-053、GOAL row 15）
写的是"`retry_policy` **零消费者**（`max_attempts` 写了也没人看）"。这句话**过宽**：
应用层的 in-process 重试循环一直在消费它——

```text
packages/application/run_orchestration/task_executor.py
  :83  _retry_policy(contract)  -> contract.retry_policy or RetryPolicy(max_attempts=1)
  :87  _retryable(error, policy) -> TransientPortError + 类别在 retryable_categories 内
  :111 policy = _retry_policy(contract)  → attempts >= policy.max_attempts 才停
```

准确的说法是：**durable 层（WorkflowEngine 的 complete/claim）零消费**——它把任何非
SUCCEEDED 的完成一律写 FAILED，`RETRY_SCHEDULED`/`DEAD_LETTER` 没有生产驱动方
（这条扫描证据仍然成立）。校正按"追加 + 就地标注"做，不改写历史结论。

**B. 真缺口（退避）**：cycle 15 让 `RETRY_SCHEDULED` 与 `QUEUED` **同权**，
于是可重试失败会被**立刻**再次 claim：同一个固定时钟下"重排 → 再 claim"成功
（`test_a_retryable_failure_is_rescheduled_and_claimable_again` 就是这条行为的证据）。
失败很快的任务会在 `max_attempts` 内**热循环**，占满 worker 与外部配额。
AGENTS.md §7 明确要求实现 "retry classification / **exponential backoff** /
dead-letter / manual recovery"——分类与死信上一轮落地了，退避**没有**：
策略面（`RetryPolicy`：`max_attempts` + `retryable_categories`，schema 里
`additionalProperties: false`）根本没有时延字段，所以今天连"声明退避"都做不到。

## 口径

1. **时延是策略面的事实，不写死常量**：`RetryPolicy.backoff_seconds`（基数，可空 =
   不等待）+ `max_backoff_seconds`（上限，可空 = 不封顶）。缺省即今天的"立即重排"，
   既有契约行为不变。
2. **计算是 Domain 纯函数**：`TaskContract.retry_delay(attempt)` =
   `min(base * 2^(attempt-1), cap)`（`attempt` = 本次失败的尝试序号）；base 为 None/0 ⇒ 0。
   与 `decide_failure` 一样，两个 adapter 只是调用者。
3. **落库是列不是 JSON**：`tasks.retry_at`（可空）。claim 的候选扫描是静态 SQL +
   参数，过滤必须能写进 SQL；写进 task_json 就得在 SQL 里解 JSON，两个 adapter 各解一套。
4. **过滤在扫描内**：未到期的重试不得占用候选窗口（否则一个热重试任务能把别的 run
   饿死——与 PAUSED run 的排除同理）。到期后与首次排队同权。
5. **交付即清**：一次交付就是一个时刻，`retry_at` 在交付的同一条更新里置回 NULL。
6. **两侧同语义**：SQLite 与 PG 的 complete/claim/acquire 三条路径都改，PG 侧另有用例
   与 SQLite 逐条对应。
7. **如实标注没做的**：应用层 in-process 重试循环（`task_executor`）的退避不在本轮；
   它是同一契约的第二个消费者，且它的 attempt 计数（局部变量）与 durable 层的
   `attempt` 列尚未统一——记进已知风险与下一轮输入。

## 范围

- 修改：`packages/domain/tasks.py`（`RetryPolicy` 两个字段 + 校验 + `retry_delay` 纯函数）。
- 修改：`schemas/task-contract.schema.json`（retryPolicy 两个属性）、
  `adapters/contracts/tasks_loaders.py`（读取新字段）、
  `adapters/sqlite/serialization.py`（`_decode_retry_policy` 认新字段，缺省容忍）。
- 修改：`adapters/sqlite/db.py`（`tasks.retry_at`）、
  `adapters/sqlite/workflow_ops.py`（complete 处置时写 `retry_at`）、
  `adapters/sqlite/workflow_claim.py`（扫描过滤 + 交付清空）。
- 新增：`adapters/postgres/migrations/015_retry_backoff.sql`；修改
  `adapters/postgres/workflow_ops.py`、`adapters/postgres/workflow_claim.py`、
  `adapters/postgres/workflow_acquire.py`（同一口径）。
- 新增用例：`tests/domain/test_retry_backoff.py`、
  `tests/adapters/sqlite/test_workflow_retry_backoff.py`、
  `tests/postgres/test_workflow_retry_backoff_pg.py`。
- 校正：PLAN-078 / RECHECK-078 / MEM-053 / GOAL（row 15 就地标注 + 状态历史一条）。
- **不改**：Domain 状态机、OpenAPI/DTO、`task_executor` 的 in-process 循环（本轮只登记）。

## 验收条件

- [x] AC-01 **策略面能声明退避**：`backoff_seconds` / `max_backoff_seconds` 进 Domain、
  schema、loader；缺省（不写）仍是不等待。`examples/contracts/task_contracts.yaml` 有一条
  真实契约声明 `30s / 300s`（端到端：loader → Domain → 落库）。
- [x] AC-02 **计算是纯函数且有界**：`retry_delay(attempt)` 指数增长、被 cap 封顶、
  base 为 0/None 时为 0；非法值（负数、cap < base、attempt < 1）在构造/调用时被拒。
- [x] AC-03 **重排不会立刻被 claim**：未到期时 `claim_next` 返回 None（SQLite + PG）。
- [x] AC-04 **到期后可 claim**：时钟推过 deadline（SQLite）或把 `retry_at` 挪到过去（PG）
  后同一任务被正常取走，且 `fence` 前进到第二代（两个 adapter）。
- [x] AC-05 **向后兼容**：没有退避字段的契约行为与今天完全一致（SQLite + PG 两条用例，
  以及既有的两条 PG parity 用例仍绿）。
- [x] AC-06 **交付即清**：lease 交付后 `retry_at` 为空（SQLite 直读列 / PG 直查表）。
- [x] AC-07 **校正落地**：PLAN-078 / RECHECK-078 / MEM-053 / GOAL 的"零消费者"口径被
  就地标注为"durable 层零消费者"，并给出 in-process 消费者的文件行号证据。
- [x] AC-08 **门禁与记录**：m0 23 项 + 受影响定向套件 + RECHECK-079 + MEM-054 +
  GOAL cycle 16 记账 + ALL_PLAN 行。

## 实施清单

- [x] WP-0 记录校正（PLAN-078 / RECHECK-078 / MEM-053 / GOAL）
- [x] WP-A Domain：`RetryPolicy` 两字段 + `retry_delay`
- [x] WP-B schema / loader / decode（两处解码共用一份）
- [x] WP-C 落库与 claim：SQLite（SCHEMA_SQL + complete + claim）、PG（migration + 三条路径）
- [x] WP-D 用例（domain / SQLite / PG parity）+ 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
$ python -m pytest tests/domain/test_retry_backoff.py -q
7 passed
$ python -m pytest tests/adapters/sqlite/test_workflow_retry_backoff.py \
      tests/adapters/sqlite/test_workflow_retry_policy.py -q
12 passed
$ python -m pytest tests/postgres/test_workflow_retry_backoff_pg.py \
      tests/postgres/test_workflow_retry_policy_pg.py -q
5 passed                      # PG 实跑（m0 DSN 口径），非 skip
$ python -m pytest tests/domain tests/adapters tests/postgres tests/contracts -q
1311 passed, 5 skipped
$ python -m pytest tests/domain tests/adapters tests/postgres tests/contracts \
      tests/api tests/application tests/worker -q
2330 passed, 8 skipped
$ python -m mypy
Success: no issues found in 879 source files
$ sh scratch/run-m0-cycle12.sh
PASS: profile=m0; 23 deterministic checks     # 全量 pytest 3698 passed / 10 skipped
# 第 1 轮红：python/tests（e2e 重启后 outbox 里少了 TASK_COMPLETED——publish 被移出提交块，
#            见「状态历史」）；第 2 轮红：framework/validate（MEM-054 的 title 不是合法 YAML）；
# 第 3 轮 23/23 全绿。两处红都是本轮自伤，都按"改代码/改记录"修，未改门禁。
```

## 影响报告

- **Domain/API/schema**：`RetryPolicy` 新增两个**可选**字段（不进任何 API DTO）；
  `schemas/task-contract.schema.json` 的 `retryPolicy` 增两个属性（`additionalProperties`
  仍为 false，额外的键照旧被拒）。契约 JSON 由 canonical 编码器统一产出，新字段自动落盘。
- **安全/凭据**：无变化。
- **兼容性/迁移风险**：`tasks.retry_at` 是新列——SQLite 开发库需删档重建（gitignored），
  PG 走 migration 015；旧 row 的 `retry_at` 为 NULL = 不等待，与今天一致。
- **可观测性**：complete 的 call record 仍是处置动作；`TASK_RETRY_SCHEDULED` 事件新增
  `retry_at`（附加字段，不破坏既有消费者）。
- **上游版本影响**：无新依赖。
- **下一项任务**：in-process 重试循环的退避与 attempt 口径统一；锁粒度（每线程连接）；
  `failure_policy` 仍是零消费者；「按声明给 adapter 接线」仍待 escalation。

## 已知风险

- **退避只覆盖 durable 层**：`task_executor` 的 in-process 循环（同一 lease 内的瞬时错误）
  仍会立刻重试，且它用自己的局部 `attempts` 计数——同一个 `max_attempts` 目前是两套账。
  本轮如实登记，不假装统一。
- **时钟来源**：SQLite 用注入的 `now()`，PG 用数据库时钟（`now()`）；两侧语义一致
  （都以"写入时的权威时钟"算 deadline），但跨机部署时 PG 才是唯一权威。
- **cap 语义**：`max_backoff_seconds < backoff_seconds` 直接拒（否则 cap 会静默压低基数）。

## 状态历史

- 2026-09-17 创建（IN_PROGRESS）：derive 时先发现**上一轮记录过宽**（in-process 重试循环
  一直在消费 `retry_policy`），再确认真缺口（重排即可被 claim ⇒ 热循环；AGENTS.md §7 的
  "exponential backoff" 无字段可声明）⇒ 本轮 = 校正 + 退避落地。
- 2026-09-17 WP-0 校正落地：PLAN-078「目标」段就地标注 + 状态历史一条、RECHECK-078 的
  证据行改写 + 新增 W-7、MEM-053 就地标注 + 教训一条、GOAL row 15 就地标注 + 状态历史一条。
- 2026-09-17 WP-A…C 交付：`RetryPolicy` 两字段 + `retry_delay`（指数、可封顶）→ schema 两个
  属性 → loader/解码 → `tasks.retry_at` 列（SQLite SCHEMA_SQL + PG migration 015）→
  两个 adapter 的 complete 写 deadline、claim 在扫描内过滤、交付即清。
  途中修一处**自伤**：PG 最初用 SQL 的 `now()` 写 deadline 而 claim 用 `server_now`
  （测试注入时钟）比较，两边时钟不一致 ⇒ 收敛成"写入也走 `server_now`"。
- 2026-09-17 门禁红（**两轮都是本轮自伤，都按"改代码/改记录"修，没有改门禁**）：
  第 1 轮 `python/tests` **1 failed**——`tests/e2e/test_workflow_restart_recovery.py::test_outbox_survives_restart`
  报 `TASK_COMPLETED` 不在重启后的 outbox 里，根因是抽 `_write_disposition` 时**把
  `publish_completion_outcome` 移到了 `with self._conn:` 块之外**（连接上只有一个隐式事务，
  块外 publish 的事件停在没有提交的事务里，重启后的读取方看不到）⇒ 事件回到同一个提交块内
  并写明原因；第 2 轮 `framework/validate` 报 `frontmatter 无法解析` /
  `工程记忆 ID 无效: None`——MEM-054 的 `title` 里引号只包了半句（后面还跟着自由文本），
  不是合法 YAML ⇒ 整句加引号。第 3 轮 m0 **23/23**。
- 2026-09-17 DONE：`tests/e2e` + `tests/adapters/sqlite` 复跑 **137 passed**；
  四套件 **1311 passed / 5 skipped**、七套件 **2330 passed / 8 skipped**；
  mypy **879 files clean**；ruff/format 干净；m0 **PASS: profile=m0; 23 deterministic checks**
  （全量 pytest **3698 passed / 10 skipped**）。
