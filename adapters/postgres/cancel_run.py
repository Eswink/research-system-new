"""Cancel helpers for PostgresWorkflowEngine (mirrors sqlite/cancel_run.py)."""

from __future__ import annotations

from typing import Any

from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState


def cancel_task(conn: Any, outbox: Any, task_id: str) -> str | None:
    with conn.transaction():
        row: Any = conn.execute(
            "SELECT run_id, cancelled, status FROM tasks WHERE task_id = %s FOR UPDATE",
            (task_id,),
        ).fetchone()
        if row is None:
            return None
        if row["cancelled"]:
            return "deduped"
        if row["status"] in ResearchTaskState.terminal():
            return "terminal_noop"
        conn.execute(
            "UPDATE tasks SET cancelled = TRUE, status = %s WHERE task_id = %s",
            (ResearchTaskState.State.CANCELLED, task_id),
        )
        conn.execute("DELETE FROM leases WHERE task_id = %s", (task_id,))
        outbox.publish(
            EventType.TASK_CANCELLED,
            {"task_id": task_id},
            run_id=str(row["run_id"]),
            task_id=task_id,
        )
    return None


def cancel_run_tasks(conn: Any, outbox: Any, run_id: str) -> int:
    with conn.transaction():
        rows: Any = conn.execute(
            "SELECT task_id, cancelled, status FROM tasks WHERE run_id = %s FOR UPDATE",
            (run_id,),
        ).fetchall()
        cancelled_count = 0
        for row in rows:
            if row["cancelled"] or row["status"] in ResearchTaskState.terminal():
                continue
            conn.execute(
                "UPDATE tasks SET cancelled = TRUE, status = %s WHERE task_id = %s",
                (ResearchTaskState.State.CANCELLED, row["task_id"]),
            )
            conn.execute("DELETE FROM leases WHERE task_id = %s", (row["task_id"],))
            outbox.publish(
                EventType.TASK_CANCELLED,
                {"task_id": row["task_id"]},
                run_id=run_id,
                task_id=row["task_id"],
            )
            cancelled_count += 1
        return cancelled_count
