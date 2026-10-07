"""死信的人工恢复（ADR-0033 / `R26-1`；SqliteWorkflowEngine.requeue 的实现拆分）。

与 `cancel_run.py` 同形：独立模块承载单条写路径，避免 `workflow_engine` 超过源码规模
约束。**目标状态由 domain 状态机给出**（`Transition.REQUEUE` 是那条出边唯一的机械事实源），
本模块只负责落库与发事件。状态与事件同事务写 outbox。

四条纪律（ADR-0033 的决策原文）：

1. **重复恢复零新副作用**：第二次调用不写库、不发事件（它被**点名拒绝**——状态已不是
   `DEAD_LETTER`；消息含任务 id 与实际状态）。在途重放由控制面的 `Idempotency-Key`
   承担（同一 key 重放不第二次触达本函数）。
2. **点名失败**：任务不存在 / 状态不是 `DEAD_LETTER`（含「已恢复」与其它终态）⇒
   `InvalidInputError`，**不得**静默。
3. **不动 `fence_seq`、不重置尝试预算**：`fence_seq` 是租约代次，M16 §8 的单调性不允许
   回退；恢复只给任务**再一次交付**的机会——下一次交付照常推进代次（`attempt` 由交付
   路径按代次重写），若再次失败仍按 `decide_failure` 落回死信（人工可再恢复一次）。
   人工动作**不静默放大**自动重试预算。
4. **事件复用 `task.retry_scheduled`**（`reason=manual_requeue`）：与租约恢复
   （`reason=lease_expired`）同形——「任务回到可交付面」是同一类 canonical 事实，
   词表不因本动作扩张。
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace

from adapters.sqlite.outbox import OutboxWriter
from adapters.sqlite.serialization import decode_task, encode_task
from packages.application.ports.errors import InvalidInputError
from packages.domain.events import EventType
from packages.domain.state_base import InvalidTransitionError
from packages.domain.task_state import ResearchTaskState


def _queued_task_json(task_json: str, contract_json: str) -> str:
    """task_json 里的状态改为 `QUEUED`（`attempt` / `lease_id` 原样保留）。

    投影（`list_tasks`）的状态取列，但一次交付会（`_with_attempt`）用 `task_json`
    重建任务——两份不能各说一套，所以恢复时把 JSON 一起改。`attempt` 不动：
    它描述**上一次交付**的代次，下次交付由交付路径重写。
    """
    entry = decode_task(task_json, contract_json)
    queued = replace(entry.task, status=ResearchTaskState.State.QUEUED)
    return encode_task(queued, entry.contract)[0]


def requeue_task(
    conn: sqlite3.Connection,
    outbox: OutboxWriter,
    task_id: str,
) -> str:
    """人工恢复一条死信任务；返回 `restored`（成功时）。

    点名失败：不存在 / 状态不是 `DEAD_LETTER`（含「已恢复」与其它终态）各自抛
    `InvalidInputError`（消息不同，读面可逐条区分）。
    """
    row = conn.execute(
        "SELECT run_id, status, task_json, contract_json FROM tasks WHERE task_id = ?",
        (task_id,),
    ).fetchone()
    if row is None:
        raise InvalidInputError(f"unknown task: {task_id}")
    status = str(row["status"])
    # 目标状态由 **domain 状态机**给出（不是本模块的字面量）——"这条边存在"由
    # `_TRANSITIONS` 回答；「已恢复」（QUEUED / RETRY_SCHEDULED）与其它终态都在这里
    # 被**点名拒绝**（唯一合法的起点是 DEAD_LETTER）。
    try:
        target = ResearchTaskState.transition(status, ResearchTaskState.Transition.REQUEUE)
    except InvalidTransitionError as error:
        raise InvalidInputError(
            f"task {task_id} is in state {status}; only DEAD_LETTER can be requeued"
        ) from error
    task_json = _queued_task_json(str(row["task_json"]), str(row["contract_json"]))
    with conn:
        conn.execute(
            "UPDATE tasks SET status = ?, retry_at = NULL, task_json = ? WHERE task_id = ?",
            (target, task_json, task_id),
        )
        # 防御性清租约：死信在完成时已删租约，但若库里有一条陈旧租约行，
        # `acquire_lease` 会把它当成"重放"直接返回（陈旧 fence）⇒ 恢复就白做了。
        # 正常路径上这行不改变任何可观察状态，只保证"恢复后真的可交付"这条承诺。
        conn.execute("DELETE FROM leases WHERE task_id = ?", (task_id,))
        outbox.publish(
            EventType.TASK_RETRY_SCHEDULED,
            {"task_id": task_id, "reason": "manual_requeue", "previous_status": status},
            run_id=str(row["run_id"]),
            task_id=task_id,
        )
    return "restored"
