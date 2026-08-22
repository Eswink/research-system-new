"""run 级任务取消（SqliteWorkflowEngine.cancel / cancel_run 的实现拆分）。

独立模块承载任务取消逻辑，避免 workflow_engine 超过源码规模约束；
取消语义与 domain 状态机一致：终止态任务 noop、已取消任务 dedup、
状态与 TASK_CANCELLED 事件同事务写 outbox。
"""

from __future__ import annotations

import sqlite3

from adapters.sqlite.outbox import OutboxWriter
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState


def cancel_task(
    conn: sqlite3.Connection,
    outbox: OutboxWriter,
    task_id: str,
) -> str | None:
    """取消单个任务；返回取消结果摘要（None=成功/未知任务，deduped/terminal_noop）。"""
    row = conn.execute(
        "SELECT run_id, cancelled, status FROM tasks WHERE task_id = ?", (task_id,)
    ).fetchone()
    if row is None:
        return None
    if row["cancelled"]:
        return "deduped"
    if row["status"] in ResearchTaskState.terminal():
        return "terminal_noop"
    with conn:
        conn.execute(
            "UPDATE tasks SET cancelled = 1, status = ? WHERE task_id = ?",
            (ResearchTaskState.State.CANCELLED, task_id),
        )
        conn.execute("DELETE FROM leases WHERE task_id = ?", (task_id,))
        outbox.publish(
            EventType.TASK_CANCELLED,
            {"task_id": task_id},
            run_id=str(row["run_id"]),
            task_id=task_id,
        )
    return None


def cancel_run_tasks(
    conn: sqlite3.Connection,
    outbox: OutboxWriter,
    run_id: str,
) -> int:
    """取消 run 下所有未终止任务；返回实际取消数量（协作式、幂等）。"""
    rows = conn.execute(
        "SELECT task_id, cancelled, status FROM tasks WHERE run_id = ?", (run_id,)
    ).fetchall()
    cancelled_count = 0
    for row in rows:
        if row["cancelled"] or row["status"] in ResearchTaskState.terminal():
            continue
        with conn:
            conn.execute(
                "UPDATE tasks SET cancelled = 1, status = ? WHERE task_id = ?",
                (ResearchTaskState.State.CANCELLED, row["task_id"]),
            )
            conn.execute("DELETE FROM leases WHERE task_id = ?", (row["task_id"],))
            outbox.publish(
                EventType.TASK_CANCELLED,
                {"task_id": row["task_id"]},
                run_id=run_id,
                task_id=row["task_id"],
            )
        cancelled_count += 1
    return cancelled_count
