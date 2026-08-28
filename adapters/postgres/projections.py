"""Postgres projections (mirrors sqlite/projections.py).

Reads use JSONB/ TIMESTAMPTZ columns; decodes via postgres serialization helpers.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import Any

from adapters.postgres.serialization import TaskRow, decode_envelope, decode_task
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.events import EventEnvelope


def _get_task_json(row: Any) -> str:
    val: Any = row["task_json"]
    if isinstance(val, str):
        return val
    return json.dumps(val, ensure_ascii=False, sort_keys=True)


def _get_contract_json(row: Any) -> str:
    val: Any = row["contract_json"]
    if isinstance(val, str):
        return val
    return json.dumps(val, ensure_ascii=False, sort_keys=True)


def _get_envelope_json(row: Any) -> str:
    val: Any = row["envelope_json"]
    if isinstance(val, str):
        return val
    return json.dumps(val, ensure_ascii=False, sort_keys=True)


def list_tasks(conn: Any, run_id: str) -> tuple[TaskRow, ...]:
    rows: Any = conn.execute(
        "SELECT task_json, contract_json, status FROM tasks WHERE run_id = %s ORDER BY created_at",
        (run_id,),
    ).fetchall()
    result: list[TaskRow] = []
    for row in rows:
        entry = decode_task(_get_task_json(row), _get_contract_json(row))
        result.append(
            TaskRow(task=replace(entry.task, status=row["status"]), contract=entry.contract)
        )
    return tuple(result)


def deliveries(conn: Any) -> dict[str, int]:
    rows: Any = conn.execute(
        "SELECT idempotency_key FROM tasks WHERE idempotency_key IS NOT NULL"
    ).fetchall()
    keys = [row["idempotency_key"] for row in rows]
    rows2: Any = conn.execute("SELECT task_id FROM tasks WHERE idempotency_key IS NULL").fetchall()
    task_ids = [row["task_id"] for row in rows2]
    return {key: 1 for key in [*keys, *task_ids]}


def completed(conn: Any) -> dict[str, TaskCompletion]:
    rows: Any = conn.execute(
        "SELECT task_id, status FROM tasks WHERE status IN ('SUCCEEDED', 'FAILED')"
    ).fetchall()
    return {
        row["task_id"]: TaskCompletion(task_id=row["task_id"], outcome=row["status"])
        for row in rows
    }


def cancelled(conn: Any) -> set[str]:
    rows: Any = conn.execute("SELECT task_id FROM tasks WHERE cancelled = TRUE").fetchall()
    return {row["task_id"] for row in rows}


def pending_outbox(conn: Any) -> tuple[EventEnvelope, ...]:
    rows: Any = conn.execute(
        "SELECT envelope_json FROM outbox_events WHERE published_at IS NULL ORDER BY created_at"
    ).fetchall()
    return tuple(decode_envelope(_get_envelope_json(row)) for row in rows)


def mark_outbox_published(
    conn: Any, event_ids: tuple[str, ...], now: Callable[[], datetime] | None
) -> None:
    if not event_ids:
        return
    from adapters.postgres.db import now_iso

    ts = now_iso(now)
    with conn.transaction():
        for event_id in event_ids:
            conn.execute(
                "UPDATE outbox_events SET published_at = %s WHERE event_id = %s",
                (ts, event_id),
            )
