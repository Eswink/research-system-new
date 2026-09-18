# ADR-0030 — 验收门拒收的处置（Validation-Failure Consumption）

Status: Proposed
Date: 2026-09-18
Deciders: Eswink（single owner）— **待拍板**：本 ADR 是草案，不构成已接受的决策
Scope: `packages/domain/task_state.py`（ResearchTask 状态机）、`packages/domain/failure_policy.py`
（`on_validation_failure` 声明面）、`packages/application/run_orchestration/task_executor.py`
（durable `complete` 在验收门之前的次序）、`packages/application/run_orchestration/task_phase_helpers.py`
（`register_and_gate` 的拒收分叉）、`packages/application/run_orchestration/run_terminals.py`
（run 级结局）；关联 ADR-0002（canonical state manifest）、ADR-0014（task contract / handoff）、
ADR-0016（at-least-once + idempotency + outbox）

## Context

四件可复核的事实（都能在代码里逐行对照，不是推断）：

1. **拒收发生在 durable 成功之后**：`task_executor._attempt_once` 先
   `engine.complete(live, TaskCompletion(task_id=..., outcome="SUCCEEDED"))` —— 这一步把任务行
   写成 durable 终态并释放租约；随后调用链才走 `task_phase_helpers.register_and_gate` →
   `evaluate_gate` → `evaluate_task_gate`（验收门）。
2. **拒收只落在 run 级**：门不过 ⇒ `failure_step(deps, tctx, "task <id> rejected by
   acceptance gate", False)`，它的两个分支是
   ① `deps.fail(run_id, message, False)` ⇒ `run_terminals.publish_failed_run` 发 `run.failed`
   （payload 的 `message` 就是那句话），RunOutcome 收敛 `FAILED`；
   ② 契约声明 `on_task_failure: CONTINUE` 时 ⇒ 被容忍 ⇒ 最终 `run_terminals.publish_degraded_run`
   发 `run.degraded`（`tolerated_failures[].message` 同样带那句话）。
   **两条分支都不改任务行**。
3. **任务行停在 `SUCCEEDED` 且不可回头**：`ResearchTaskState._TRANSITIONS` 里 `SUCCEEDED`
   属于 `terminal()`，**没有任何从它出发的迁移**；`DEAD_LETTER` 只能从 `RETRY_SCHEDULED`
   经 `Transition.DEAD_LETTER` 到达 ⇒ 今天没有任何路径能把"已被门拒收"表达在任务行上。
4. **声明面已如实登记、但没有权威决策记录**：`on_validation_failure` 是 `failure_policy`
   自由 dict 里的**未知键** ⇒ 进 `failure_policy_view().unhonored` 被点名、**不改变任何判定**
   （`tests/domain/test_failure_policy_view.py`、`tests/application/run_orchestration/
   test_failure_policy_consumer.py` 钉住）；示例契约不声明它（GOAL-005 cycle 3 = EC-03）。
   边界在三处文档里各自表述过（`failure_policy.py` docstring、`docs/architecture/
   TASK_HANDOFF.md` §2.1、`examples/contracts/task_contracts.yaml` 注释），但**没有一处**是
   "待拍板的决策本身（选项 + 代价 + 触发条件）"。

**差距**：运维写 `on_validation_failure: DEAD_LETTER` 的意图是"门拒收的任务进死信等人工"；
今天这个意图无处落地 —— 任务行说"成功"、run 说"失败/降级"，两者都不表达"这次交付被门拒收"。
声明被**点名**（不静默），但**不生效**。

## Decision needed

需要拍板的轴只有一条，但它牵动三处语义：

> **验收门拒收之后，任务行（canonical 事实）应该是什么？**

随之而来的次生问题：谁读它（控制面读面如何区分"成功且通过验收"与"成功但验收未过"）、
如何恢复（人工队列 / 单任务重跑 / 整条 run 重跑）、以及历史行怎么解释（既有 run 里这些
`SUCCEEDED` 行要不要回溯标注）。

## Options

### A. 从终态出发新增迁移：`SUCCEEDED --VALIDATION_REJECTED--> DEAD_LETTER`

- **做法**：状态机加一条从 `SUCCEEDED` 出发的迁移；拒收时 `engine.complete(...)` 之后再写一次
  任务行（`DEAD_LETTER`）。
- **收益**：与 `on_validation_failure: DEAD_LETTER` 的字面语义最贴近；复用既有死信状态。
- **代价**：**打破 `SUCCEEDED` 的终态语义**（`terminal()` 的假设在所有消费点都要重新审查：
  剩余工作计算、run 收敛、读面分类、幂等键去重）；事件链要能解释"先成功、后死信"的次序；
  与 outbox / at-least-once 的幂等语义要有新规则（同一任务两次终态事件）；读面对历史行的
  解释需要新口径。

### B. 新增独立终态：`VALIDATION_REJECTED`（从 `SUCCEEDED` 的迁移）

- **做法**：新增 canonical 状态与迁移；`terminal()` 重新分类（哪些算成功、哪些要人工）。
- **收益**：语义最诚实 —— "已交付但被门拒收"是可区分的一等事实。
- **代价**：**成本最高**：状态机扩张 + 全部 `terminal()` 消费点重分类 + 读面/报表/成本口径
  要决定"这条算不算做完了"；新增状态还要进 `docs/reliability/RUN_STATE_MACHINE.md` 与
  ADR-0002 的 canonical manifest。

### C. 维持 run 级处置（现状）+ 读面点名

- **做法**：任务行不动（保持 `SUCCEEDED`），把"run 因门拒收失败/降级"在读面讲清楚
  （今天只有事件链的 `message`；控制面读面没有专门的拒收归因）。
- **收益**：**零 canonical 改动**、零迁移风险；与 ADR-0002 的 canonical 边界完全一致。
- **代价**：任务行与 run 结论长期不一致；"哪条任务被门拒收"要靠事件链文本匹配
  （与 EC-06 已登记的一等边界同源：失败原因不是结构化任务级归因）；运维要自己搭补偿。

### D. 把验收门挪到 durable `SUCCEEDED` **之前**（次序重排）

- **做法**：调整 `_attempt_once` / `register_and_gate` 的次序 —— 先跑门、再落 durable 终态；
  拒收路径落在**非终态**上（`RUNNING` / `LEASED`），那里**已有** `FAIL` / `SCHEDULE_RETRY`
  边界可达。
- **收益**：**不必新增"从终态出发的迁移"**，也不必新增状态；`on_validation_failure` 的语义
  可以落在既有非终态判定上（例如"拒收 ⇒ `RUNNING → FAILED`"或"⇒ `DEAD_LETTER`"，后者只需
  一条**从非终态出发**的新迁移，不破坏终态语义）。
- **代价**：重排 durable 写入次序属 **Reliable Workflow 面**（ADR-0016 语义），必须先确认
  门的输入面（`registration`：会话产物入册 + artifact/evidence 引用）是否依赖"任务已成功"
  这一状态，以及失败路径上租约/事件的次序；对既有事件次序与用例的冲击面是五个选项里最大的
  （但都在既有边界内）。另外"未通过的尝试是否要释放租约、是否算一次 attempt"要一并决定。

### E. 不做（今天的处置：声明被点名、行为按缺省）

- **做法**：保持现状；示例契约不声明它。
- **收益**：零改动、零风险；语义诚实（不假装消费）。
- **代价**：`on_validation_failure` 永远只是"被点名的未知键"；所有补偿靠运维。

## Why not now（本循环为何不自行决定）

- **A / B 直接改 canonical 状态机与终态语义** ⇒ 命中 GOAL-006 的 `escalation_triggers`
  （"需要修改 Accepted ADR / 核心安全策略 / **Canonical State 边界**"）与 ADR-0002 的权威面；
- **D 不破坏终态语义，但要重排 durable 写入次序**（`complete` 与 artifact 登记、租约、
  事件链的次序）⇒ 属 Reliable Workflow 决策面，需要独立的射程与验证；
- **A / B / D 都会改变读面对历史行与"这条 run 要不要人工"的解释** ⇒ 产品语义决策。

⇒ 本循环只做三件不越界的事：把决策需要的事实、选项与代价写清（本 ADR）；把等宽口径
**同源**指向这里（`docs/INDEX.md` 登记 + 三处声明面指针）；保留"声明不改变行为"的既有判据
并由一条用例把同源收敛钉住。

## Trigger（何时必须拍板）

出现下列任一情况时，本 ADR 必须被拍板（Accept / 选其中一个选项 / 明确 Reject）：

- 运营需要"门拒收后自动进死信/人工队列"（而不是靠人读 run 事件）；
- 读面消费者要求**区分**"成功且通过验收"与"成功但验收未过"；
- 任何任务要实现 `on_validation_failure` 的执行期语义（含用户契约要求该键生效）；
- 或需要对既有 run 的 `SUCCEEDED` 历史行做回溯标注。

## Consequences（本 ADR 处于 Proposed 期间）

- `on_validation_failure` 继续是"**声明的意图被点名但不生效**"——这是诚实边界，不是缺陷；
  声明它的契约行为与不声明**逐字相同**（有用例钉住）。
- 门拒收的 canonical 事实**只有 run 级**：`run.failed`（或 `on_task_failure: CONTINUE` 下的
  `run.degraded`），payload 的 message 含 `rejected by acceptance gate`；任务行保留 `SUCCEEDED`。
- 恢复路径是 run 级的（既有 `POST /runs/{id}/resume` 与 run 级重投递语义），**不**针对单个任务
  回退；"哪条任务被拒收"今天只能从事件链的 message 读出。
- 本 ADR 一旦被接受并实施，必须同时更新：`docs/reliability/RUN_STATE_MACHINE.md`、
  `docs/architecture/TASK_HANDOFF.md` §2.1、`packages/domain/failure_policy.py`（把
  `on_validation_failure` 从 `unhonored` 提升为已知键）、示例契约、以及读面口径。

## Evidence / References

- 代码（事实 1–3）：`packages/application/run_orchestration/task_executor.py`（`_attempt_once`
  的 `engine.complete`）、`packages/application/run_orchestration/task_phase_helpers.py`
  （`register_and_gate` / `evaluate_gate` / `failure_step`）、
  `packages/application/run_orchestration/run_terminals.py`（`publish_failed_run` /
  `publish_degraded_run`）、`packages/domain/task_state.py`（`_TRANSITIONS` / `terminal()`）。
- 声明面（事实 4）：`packages/domain/failure_policy.py`、`docs/architecture/TASK_HANDOFF.md`
  §2.1、`examples/contracts/task_contracts.yaml`。
- 用例（"声明不改变行为"）：`tests/domain/test_failure_policy_view.py`、
  `tests/application/run_orchestration/test_failure_policy_consumer.py`。
- 同源收敛判据：`tests/tooling/test_pending_validation_failure_registration.py`。
- 上游登记：`RECHECK-20260918-095` W-2（同形未消费项）、GOAL-20260918-005 收口结论第 3 项、
  GOAL-20260918-006 EC-02。
