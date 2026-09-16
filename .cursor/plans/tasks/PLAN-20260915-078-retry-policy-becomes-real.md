---
id: PLAN-20260915-078
slug: retry-policy-becomes-real
title: 重试策略落地：可重试失败重排、次数用尽进死信、状态机的"没人驱动"变成可门禁的枚举
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 15 = RECHECK-20260915-077 后继（下一个「承诺 vs 实现」缺口）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」+ 2026-09-17 用户拍板恢复条件②（显式变更 budget.max_cycles 10→20 并置回 ACTIVE）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-078-retry-policy-becomes-real.md
memory_entries:
  - MEM-20260915-053-a-declared-state-with-no-driver
---

# PLAN-20260915-078 — 重试策略落地（GOAL-003 cycle 15）

## 目标

`TaskContract.retry_policy` 的 `max_attempts` 是**必填字段**，Domain 状态机里写着
`RETRY_SCHEDULED` 与 `DEAD_LETTER` 两个状态、`(RUNNING, SCHEDULE_RETRY)` /
`(RETRY_SCHEDULED, DEAD_LETTER)` 等迁移，`schemas/task-contract.schema.json` 与 loader
都接受这些字段——但**没有任何生产调用方**：

- 两个 engine 的 `complete()` 把任何非 `SUCCEEDED` 的完成一律写成 `FAILED`；
- `retry_policy` 零消费者（`max_attempts` 写了也没人看）；
- `RETRY_SCHEDULED` / `DEAD_LETTER` 两个状态**没有任何 adapter/服务会设置**
  （探针：限定写法 `ResearchTaskState.State.<NAME>` 扫生产代码，命中 0）；
- `TaskCompletion` 只有 `outcome`，**没有失败类别**——重试分类的输入根本不存在，
  所以"按类别决定可否重试"在今天的接口上不可能表达。

AGENTS.md §7 要求的是 "retry classification / exponential backoff /
dead-letter / manual recovery"；现在这四条里**一条也没有落地**。本轮把前三条里
"分类 + 重排 + 死信"做成真的行为，并把"策略写了没人用"这类缺口变成可门禁的枚举。

## 口径

1. **判据下沉到 Domain 纯函数**：`TaskContract.decide_failure(attempt, category)` →
   `RETRY` / `DEAD_LETTER` / `FAIL`。两个 adapter 调同一个判据，不做两套 if。
2. **规则**（顺序即优先级）：没有 `retry_policy` 或没给类别 ⇒ `FAIL`（不可判定就不重试）；
   类别不在 `retryable_categories` ⇒ `FAIL`；可重试且 `attempt < max_attempts` ⇒ `RETRY`；
   可重试但次数用尽 ⇒ `DEAD_LETTER`。
3. **attempt 的语义钉死**：attempt = **已经开始的尝试次数**，在**每一次交付 lease**
   （claim 或 acquire）的那一刻随交付代次一起写进 `attempt` 列**和** `task_json`
   （域不变量 `attempt > 1` 必须带 `lease_id`，只有此刻两边同时成立）。完成路径**不**动它。
   投影与列必须同一条更新落账：`list_tasks` 读 task_json，落后一代就会让重试产生的用量
   一直落在上一次尝试的 entry id 上（`_attempt_scope` 的 attempt 后缀永不出现）。
4. **重排即可再派发**：`RETRY_SCHEDULED` 与 `QUEUED` 同为可 claim 状态——扫描与
   "写事务内复核"必须用**同一张**可 claim 表，否则重试任务会在复核那步被判 contended。
5. **at-least-once 不回退**：这次完成已经落账（lease 已删）时，重放 `complete` 仍是
   幂等 noop；`RETRY_SCHEDULED` 属于"已落账"（它是处置结果，不是"还没完成"）。
6. **两个 adapter 同语义**：SQLite 与 PG 的 claim/complete 两条路径都改，PG 侧另有用例
   与 SQLite 逐条对应（同一 Port 的两个实现必须给同一结论）。
7. **如实标注没做的**：退避（指数或固定）**本轮不做**——策略面上没有退避字段，
   要么加 schema 字段要么写死常量，两者都要单独决定；记进已知风险与下一轮输入。

## 范围

- 修改：`packages/domain/enums.py`（`FailureAction`）、`packages/domain/tasks.py`
  （`disposition` / `decide_failure` 纯函数）、`packages/application/ports/workflow_engine.py`
  （`TaskCompletion.failure_category`，缺省 None 向后兼容）。
- 修改：`adapters/sqlite/workflow_ops.py`（complete 判据 + 可 claim 表 + 交付时 attempt 同步）、
  `adapters/sqlite/serialization.py`（`decode_contract`）；新增
  `adapters/sqlite/workflow_claim.py`（候选扫描 / 落租约：交付一次 lease 就写 status +
  fence_seq + attempt + task_json + TASK_LEASED，两个交付入口共用）、
  `adapters/sqlite/completion.py`（把处置翻成事件：RETRY ⇒ `TASK_RETRY_SCHEDULED`，
  否则 `TASK_COMPLETED` 带 action/status）。
- 修改：`adapters/postgres/workflow_ops.py`（同判据）、`adapters/postgres/workflow_claim.py`
  （可 claim 表 + `_hand_out`：状态/代次/attempt/task_json 一条更新）、
  `adapters/postgres/workflow_acquire.py`（acquire 也是交付一次 lease ⇒ 同一条更新）、
  `adapters/postgres/serialization.py`（`decode_contract_json` + `task_json_text` +
  `reencode_task_json`）。
- 新增：`tests/adapters/sqlite/test_workflow_retry_policy.py`（8 条，含"回收后再交付 ⇒
  投影 attempt 前进"的回归条）、`tests/postgres/test_workflow_retry_policy_pg.py`（2 条 parity）、
  `tests/domain/test_task_state_drivers.py`（3 条枚举门禁）。
- **不改**：Domain 状态机本身（迁移表已经够用）、任何 API/DTO/schema、FakeWorkflowEngine
  （它只记录完成，不建任务生命周期，contract suite 里不涉及本轮的判据）。

## 验收条件

- [x] AC-01 **可重试失败重排**：可重试类别 + 还有次数 ⇒ `RETRY_SCHEDULED`，
      `TASK_RETRY_SCHEDULED` 事件，且**能再被 claim**（再次 claim 时 attempt 递增）。
- [x] AC-02 **次数用尽进死信**：可重试但 `attempt >= max_attempts` ⇒ `DEAD_LETTER`，
      不再被派发。
- [x] AC-03 **不可重试 / 未分类 / 无策略 ⇒ FAILED**（三条反证，行为与策略出现前一致）。
- [x] AC-04 **at-least-once 不回退**：重排之后重放同一次完成仍是 `deduped` noop。
- [x] AC-05 **成功不受影响**：`SUCCEEDED` 仍写 `SUCCEEDED`，不触发重试路径。
- [x] AC-06 **PG/SQLite 同语义**：同一场景两个 adapter 结论一致（PG 用例逐条对应 SQLite）。
- [x] AC-07 **状态驱动的枚举门禁**：任务状态机的每个状态要么登记"由谁驱动"，
      要么登记"为什么没有"，并被生产代码扫描对账（新增状态不接线即红）。
- [x] AC-08 **门禁与记录**：m0 23 项 + 受影响定向套件 + RECHECK-078 + MEM-053 + GOAL 记账 +
      ALL_PLAN 行。

## 实施清单

- [x] WP-A Domain 判据（`FailureAction` + `decide_failure`）+ `TaskCompletion.failure_category`
- [x] WP-B SQLite：complete 判据 / 可 claim 表 / claim 时 attempt 递增 + task_json 同步
- [x] WP-C PG 同语义（complete / claim / decode_contract_json）
- [x] WP-D 用例（SQLite 7 + PG parity 2 + 状态枚举门禁 3）+ 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
# 缺口（收口前）：限定写法扫生产代码，命中 0 = 没有任何生产驱动方
RUNNING 0 / WAITING_FOR_TOOL 0 / WAITING_FOR_APPROVAL 0
RETRY_SCHEDULED 0 / DEAD_LETTER 0     ← 本轮之前

$ python -m pytest tests/adapters/sqlite/test_workflow_retry_policy.py \
      tests/domain/test_task_state_drivers.py tests/postgres/test_workflow_retry_policy_pg.py -q
13 passed              # SQLite 8 / 枚举门禁 3 / PG parity 2（m0 DSN 口径，PG 实跑非 skip）
$ python -m pytest tests/adapters tests/domain tests/postgres tests/contracts -q
1297 passed, 5 skipped
$ python -m mypy
Success: no issues found in 876 source files
$ sh scratch/run-m0-cycle12.sh
PASS: profile=m0; 23 deterministic checks     # 全量 pytest 3681 passed / 10 skipped
```

## 影响报告

- **Domain/API/schema**：Domain 新增 `FailureAction` 枚举与 `TaskContract.decide_failure`
  纯函数（无 schema 变更——`retry_policy` 字段早就在 schema 里）；Port 的 `TaskCompletion`
  新增**可选**字段 `failure_category`，缺省 None 向后兼容，既有构造点无需改动。
- **安全/凭据**：无变化。
- **兼容性/迁移风险**：`retry_policy=None` 的契约（含仓内既有 fixture 与测试契约）
  行为**完全不变**（一律 FAIL）。只有显式声明了 retry policy 的契约才会走新路径。
  任务表新增的 `attempt` 递增改变的是"attempt 的语义"——从"提交时的快照"变成
  "已开始的尝试次数"，probe/脚本若断言过 attempt 需按新语义看（已 grep：无）。
- **可观测性**：`complete` 的 call record 从 `result=outcome` 变成 `result=处置动作`
  （RETRY/FAIL/DEAD_LETTER）；`TASK_COMPLETED` 事件新增 `action`/`status` 字段（附加，不破坏既有消费者）。
- **上游版本影响**：无新依赖。
- **下一项任务**：退避时延（策略缺字段）；`failure_policy` 仍是未消费者（本轮没碰）；
  锁粒度/每线程连接；「按声明给 adapter 接线」仍待 escalation。

## 已知风险

- **没有退避**：重排后立即可被 claim（`RETRY_SCHEDULED` 与 `QUEUED` 同权）。
  失败很快的任务会在 `max_attempts` 次内热循环；指数退避需要策略字段或新列，本轮刻意不做。
- **attempt 随每一次交付前进**：claim 与 acquire 都是"交付一次 lease"，两条路径都会把
  `attempt` 推到本代（列 + task_json 同一条更新）。绕过交付路径直接改状态不会让计数前进
  （域不变量把 attempt>1 与 lease 绑在一起，正是为了防这种绕过）。
- **task_json 不再是"提交时的快照"**：交付会重写它（status 列本来就是投影口径，
  现在 attempt/lease_id 也是）。若未来有消费者要拿 task_json 当原始快照比对，必须改读投影。
- **dealer choice**：`failure_policy`（如 `on_validation_failure: DEAD_LETTER`）仍然
  **零消费者**——它的键名空间没有和 `FailureCategory` 对齐，直接消费等于自己发明语义，
  本轮如实不碰，记进下一轮输入。
- **状态枚举门禁是文本级**：它按 `ResearchTaskState.State.<NAME>` 这个限定写法扫描，
  别名导入（`from ... import State`）会漏；本仓的实际写法统一，风险低。
- **PG 侧 parity 用例在 CI 上会 skip**（PG 不可达时）——本机与 CI 的 ubuntu job 实测
  都能跑（见证据），但 skip 时结论以 SQLite + contract suite 为准。

## 状态历史

- 2026-09-17 创建（IN_PROGRESS）：derive 时先用一处扫描拿到"声明了但没人驱动"的硬证据
  （限定写法扫生产代码：`RETRY_SCHEDULED`/`DEAD_LETTER` 命中 0，`retry_policy` 无消费者，
  `TaskCompletion` 没有类别字段），再定口径：判据下沉 Domain、两个 adapter 共用、
  attempt 语义与域不变量对齐。
- 2026-09-17 WP-A…C 完成（中途换了两次 attempt 口径，都如实记录）：第一版把 attempt 的推进
  放在 complete，结果对 SUCCEEDED 也走失败映射（成功写成了 FAILED）；第二版改到 claim 时递增
  ——但要让投影跟上就得在 SQL 里改 JSON，先把预算判据改成读 `fence_seq`（交付代次）绕开；
  最终版回到"交付一次 lease = 开始一次尝试"：**列与 task_json 在交付的同一条更新里一起推进**
  （`persist_new_lease` / `_hand_out`），完成路径只读 `attempt`。
- 2026-09-17 门禁红（**没有改门禁**）：50 行函数上限与 450 行文件上限在本轮顶穿 ⇒ 抽出
  `adapters/sqlite/workflow_claim.py`（候选扫描 / 落租约）、`adapters/sqlite/completion.py`
  （处置 → 事件）、`_hand_out`、`_require_current_lease`；`_complete_impl` 44 行、
  `claim_next_impl` 35 行、`_insert_lease` 40 行，均回到阈值内。
- 2026-09-17 DONE：全量门禁通过（m0 **PASS: profile=m0; 23 deterministic checks**，
  全量 pytest **3681 passed / 10 skipped**），ruff/format 干净、mypy **876 files clean**，
  `tests/adapters+tests/domain+tests/postgres+tests/contracts` **1297 passed / 5 skipped**，
  记录落盘（RECHECK-078 + MEM-053 + GOAL cycle 15 记账 + ALL_PLAN）。
