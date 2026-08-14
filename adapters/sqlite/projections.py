"""SqliteWorkflowEngine 的可观察投影（M5 Fake 语义对齐 + outbox 读取）。"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from adapters.sqlite.db import now_iso
from adapters.sqlite.serialization import TaskRow, decode_envelope, decode_task
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.events import EventEnvelope


def list_tasks(conn: sqlite3.Connection, run_id: str) -> tuple[TaskRow, ...]:
    """run 内任务投影（canonical state 读取，非审计事件）。"""
    rows = conn.execute(
        "SELECT task_json, contract_json, status FROM tasks WHERE run_id = ? ORDER BY created_at",
        (run_id,),
    ).fetchall()
    result: list[TaskRow] = []
    for row in rows:
        entry = decode_task(row["task_json"], row["contract_json"])
        result.append(
            TaskRow(task=replace(entry.task, status=row["status"]), contract=entry.contract)
        )
    return tuple(result)


def deliveries(conn: sqlite3.Connection) -> dict[str, int]:
    """投递投影：每个 idempotency key（或 task id）恰一次（M5 语义对齐）。"""
    keys = [
        row["idempotency_key"]
        for row in conn.execute(
            "SELECT idempotency_key FROM tasks WHERE idempotency_key IS NOT NULL"
        )
    ]
    task_ids = [
        row["task_id"]
        for row in conn.execute("SELECT task_id FROM tasks WHERE idempotency_key IS NULL")
    ]
    return {key: 1 for key in [*keys, *task_ids]}


def completed(conn: sqlite3.Connection) -> dict[str, TaskCompletion]:
    """完成投影：status 为 SUCCEEDED/FAILED 的任务（M5 语义对齐）。"""
    rows = conn.execute(
        "SELECT task_id, status FROM tasks WHERE status IN ('SUCCEEDED', 'FAILED')"
    ).fetchall()
    return {
        row["task_id"]: TaskCompletion(task_id=row["task_id"], outcome=row["status"])
        for row in rows
    }


def cancelled(conn: sqlite3.Connection) -> set[str]:
    """取消投影：cancelled=1 的任务（M5 语义对齐）。"""
    rows = conn.execute("SELECT task_id FROM tasks WHERE cancelled = 1").fetchall()
    return {row["task_id"] for row in rows}


def pending_outbox(conn: sqlite3.Connection) -> tuple[EventEnvelope, ...]:
    """未投递的 outbox 事件（供 EventPublisher 轮询）。"""
    rows = conn.execute(
        "SELECT envelope_json FROM outbox_events WHERE published_at IS NULL ORDER BY created_at"
    ).fetchall()
    return tuple(decode_envelope(row["envelope_json"]) for row in rows)


def mark_outbox_published(
    conn: sqlite3.Connection, event_ids: tuple[str, ...], now: Callable[[], datetime] | None
) -> None:
    """标记事件已投递（幂等）。"""
    if not event_ids:
        return
    with conn:
        for event_id in event_ids:
            conn.execute(
                "UPDATE outbox_events SET published_at = ? WHERE event_id = ?",
                (now_iso(now), event_id),
            )
