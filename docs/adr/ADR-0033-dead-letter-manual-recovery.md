# ADR-0033 — 死信的人工恢复（Dead-Letter Manual Recovery）

Status: Accepted
Date: 2026-10-07
Deciders: Eswink（single owner）
Scope: `packages/domain/task_state.py`（ResearchTask 状态机：`DEAD_LETTER` 的出边与
`terminal()` 语义）、`packages/application/ports/workflow_engine.py`（新 Port 方法
`requeue`）、`adapters/{sqlite,postgres,fakes}/`（三个实现）、
`docs/reliability/RUN_STATE_MACHINE.md`（迁移表）。关联 ADR-0016（at-least-once +
idempotency + outbox）、ADR-0030（验收门拒收的处置 —— **未被本 ADR 改动**）

## Context

AGENTS.md §7 明文要求 `dead-letter / manual recovery`。2026-10-07 的实测（GOAL-20261007-032
建档勘察）把它逐条量成四个机械事实：

1. **`DEAD_LETTER` 在状态机里没有出边**：`_TRANSITIONS` 里没有任何 `(DEAD_LETTER, *)` 键，
   且 `terminal()` 含它 ⇒ **今天没有任何产品路径**能把一条死信任务重新派发。
   这不是散文：`tests/adapters/sqlite/test_workflow_dead_letter_surface.py` 的
   `test_dead_letter_has_no_outgoing_transition` 逐一遍历 `Transition` 枚举并断言**每一个**
   从 `DEAD_LETTER` 出发都非法。
2. **死信是真实的落点**：`max_attempts` 打满 + 可重试类别 ⇒ `DEAD_LETTER`
   （`TaskContract.decide_failure` 的规则 4）。也就是说：一条任务真的会走到那里。
3. **恢复路径的缺席有用户可见后果**：run 级重建续跑（`services/api/run_resume.py`）按
   `idempotency_key` 重算剩余工作，但它对死信任务**无能为力** —— 交付仍要过
   `acquire_lease`，而该路径的 `terminal()` 守卫会**点名拒绝**它。
   ⇒ 死信任务在今天的系统里是**绝对死点**：唯一的出路是人工改库。
4. **改它是改语义**：`DEAD_LETTER ∈ terminal()` 是既有的设计决定（`terminal()` 被 5 个
   adapter 守卫点消费：`sqlite/workflow_ops.py` 的 `acquire_lease`、`sqlite/cancel_run.py`、
   `postgres/cancel_run.py`、`postgres/workflow_acquire.py`、`postgres/workflow_ops.py`）。
   ⇒ 按本仓惯例，改语义必须留 ADR，**不得静默改**。

`ADR-0030`（验收门拒收的处置）在同一片语义面上仍是 `Proposed`，但它问的是**另一个问题**
（「验收门拒收要不要新增**进入** `DEAD_LETTER` 的路径」），不是「`DEAD_LETTER` 要不要有一条
**出边**」。它列出的候选里，对本 ADR 有直接参考价值的是它的**机制观察**（选项 D 一节）：

> 「**不必新增『从终态出发的迁移』** …… 拒收路径落在**非终态**上（`RUNNING` / `LEASED`），
> 那里**已有** `FAIL` / `SCHEDULE_RETRY` 边界可达。」

本 ADR 的决策点正是「**这一次**要不要真的新增一条从终态出发的迁移（人工恢复这条路没有
非终态可落——任务已经在终态里），以及新增之后 `terminal()` 的语义怎么写才不撒谎」。

## Decision

**新增一条且仅一条从 `DEAD_LETTER` 出发的迁移，并把「人工恢复」写成 Port 上的一等能力。**

五条具体决定：

1. **状态机加一条出边**：`(DEAD_LETTER, Transition.REQUEUE) → QUEUED`。
   `Transition.REQUEUE` 是**新事件名**（不重用 `ENQUEUE`）——重用一个已被
   `(RETRY_SCHEDULED, ENQUEUE)` / `(CREATED, ENQUEUE)` 占用的名字，会让「哪条路径在
   驱动这次迁移」在读面与测试上都不可区分。
2. **`terminal()` 保持逐字不变**：`DEAD_LETTER` **仍在** `terminal()` 里，语义读作
   「**对自动路径终态**」：claim / acquire / 租约恢复 / 退避派发都不碰它（五个守卫点
   逐字不动，由既有判据继续钉住）。**人工**恢复（`requeue`）是**唯一**会走这条出边的
   调用方，且它走的是 domain 状态机（`ResearchTaskState.transition`），不是绕过它。
   ⇒ 「终态」与「可人工恢复」不矛盾：前者描述**谁不会再自动动它**，后者描述**人可以
   显式动它**。
3. **Port 新增 `requeue(task_id) -> str`**（三个实现同形：SQLite / PostgreSQL / Fake）：
   把一条 `DEAD_LETTER` 任务写回 `QUEUED`、成功返回 `"restored"`。
   **重复恢复零第二次副作用**；**点名失败**：任务不存在 / 状态不是 `DEAD_LETTER`
   （**含「已恢复」**与其它终态）⇒ `InvalidInputError`，消息含任务 id 与实际状态
   （**不得**静默）。在途重放（同一次请求重试）由控制面的 `Idempotency-Key`
   承担；**新**请求打在已恢复的任务上被点名拒绝。
4. **不重置尝试预算、不动 `fence_seq`**：`fence_seq` 是租约代次，M16 §8 的单调性不允许
   回退；恢复只给任务**再一次交付**的机会 —— 下一次交付照常推进代次（`attempt` 由交付
   路径按代次重写），若再次失败仍按 `decide_failure` 落回死信（人工可再恢复一次）。
   **人工动作不静默放大自动重试预算**：恢复不是"重置计数器"，是"把这条任务放回
   交付面"。（探测结果：恢复后第一次交付的 `attempt` 由 `fence_seq + 1` 决定，
   与死信前的最后一次尝试**不同**，所以用量记账的 `attempt` 作用域不会碰撞。）
5. **事件复用 `task.retry_scheduled`（`reason=manual_requeue`）**：与租约恢复
   （`reason=lease_expired`）同形 ——「任务回到可交付面」是同一类 canonical 事实。
   词表不因本动作扩张（`EventType` 计数保持 38），既有词表判据逐字不动。

### 为什么不是别的选项

- **不改状态机、在 adapter 层直接 UPDATE 回 `QUEUED`**：绕过状态机 = 静默改语义，
  本季（GOAL-032）的全局禁令明文禁止；且三个实现会各有一套隐蔽的写路径。
- **新增独立状态（如 `REQUEUED`）**：多一个状态要进 canonical manifest + 读面分类 +
  本仓的状态机文档，代价远大于收益；`QUEUED` 就是「等人来取」的既有语义，没有偏差。
- **保持 `terminal()` 不含 `DEAD_LETTER`**：那会**放大**语义变化面 —— 5 个守卫点里的
  「终态不可重新租约」将不再覆盖死信任务，自动路径会开始捞它（**无人值守的重试**，
  与「等人工」的意图相反）。
- **新增 `task.requeued` 事件**：会扩张 canonical 事件词表（38 → 39），连带既有词表
  判据的钉定值与会话面（`test_m5_domain_increments.py` 的 `DOCUMENTED_EVENT_TYPES`、
  `EVENT_MODEL.md`、`CONSOLE_PAGE_MAP.md`）四处同步 —— 而本动作的 canonical 事实与
  租约恢复**同类**（"任务回到可交付面"），复用既有事件是**更小且更诚实**的面。
- **等 ADR-0030 拍板再说**：ADR-0030 的问题（拒收要不要进死信）与本 ADR 的问题
  （死信能不能人工出）**可分别决定**，且 §7 对后者的要求是**明文**的。两个决定并行
  不矛盾：本 ADR 落户后，`on_validation_failure` 的消费若将来取 ADR-0030 的方案
  A/B/D，也能复用这条恢复路径。

## Consequences

- **`DEAD_LETTER` 不再是绝对死点**：一条死信任务可被显式恢复到 `QUEUED`，
  下一次派发（claim / run 级重建续跑）就能再取到它。
- **自动路径的语义逐字不变**：五个守卫点的 `terminal()` 判定未动，既有判据继续有效；
  「无出边」的那条既有判据按**新事实重新定基**（受判面从「所有事件都非法」改为
  「**恰有** `REQUEUE` 一条合法出边，其余仍非法」——**扩大**而不是缩小受判面），
  逐字节对照与「强度未降」自证随 GOAL-032 的记录交付。
- **事件词表零扩张**：复用 `task.retry_scheduled` + `reason=manual_requeue`；
  `EventType` 的 38 条与既有词表判据一字不动。
- **`terminal()` 的读法收紧为「自动路径终态」**：这条读法写在状态机 docstring、
  本 ADR 与 `RUN_STATE_MACHINE.md` 三处，由 GOAL-032 的新判据钉住。
- **仍然没有**：自动恢复（超时后自动重生 / 指数再入队）、按 run 批量恢复、
  恢复的审批门（`require_approval`）、恢复后 run 的自动继续（run 级入口仍是
  `POST /runs/{id}/resume`）。恢复是**人工、单条、显式**的动作。
- 本 ADR **不改** `ADR-0030` 的 `Status: Proposed`（它的决策轴仍未拍板），
  **不改**任何 `policy.yaml` 规则，**不新增** allow。

## Evidence / References

- 缺口实测（GOAL-20261007-032 建档勘察）：`packages/domain/task_state.py` 的
  `_TRANSITIONS` / `terminal()`；`tests/adapters/sqlite/test_workflow_dead_letter_surface.py`
  的 `test_dead_letter_has_no_outgoing_transition`（逐一遍历事件枚举）。
- `terminal()` 的消费点（改动的射程）：`adapters/sqlite/workflow_ops.py`（acquire 守卫）、
  `adapters/sqlite/cancel_run.py`、`adapters/postgres/cancel_run.py`、
  `adapters/postgres/workflow_acquire.py`、`adapters/postgres/workflow_ops.py`（完成校验 +
  幂等集）。
- 死信的到达路径：`packages/domain/tasks.py::TaskContract.decide_failure`（规则 4）。
- run 级恢复的边界：`services/api/run_resume.py`、`packages/application/run_orchestration/
  service.py::_remaining_specs`、`packages/application/run_orchestration/rebuild_readiness.py`。
- 未拍板的邻接决策：`docs/adr/ADR-0030-validation-failure-consumption.md`（`Status: Proposed`，
  本 ADR 不改它；`tests/tooling/test_pending_validation_failure_registration.py` 继续钉住
  它必须仍是 `Proposed`）。
- 上游登记：GOAL-20260929-026 的 `R26-1`（「死信人工恢复路径不存在」）；
  `docs/architecture/WORKFLOW_RELIABILITY.md` §10（九项义务的判定落点，本 ADR 落地后
  `dead-letter · manual recovery` 从「只有半边成立」推进到两半成立）。
