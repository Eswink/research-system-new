"""Postgres projections (mirrors sqlite/projections.py).

Reads use JSONB/ TIMESTAMPTZ columns; decodes via postgres serialization helpers.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from adapters.postgres.serialization import (
    TaskRow,
    decode_envelope,
    decode_task,
    decode_timestamp_pg,
)
from packages.application.ports.workflow_engine import RetrySchedule, TaskCompletion
from packages.domain.events import EventEnvelope
from packages.domain.task_state import ResearchTaskState


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


def retry_schedule(conn: Any, run_id: str, now: datetime) -> RetrySchedule:
    """该 run 的重排读面（未到期条数 / 已到期条数 / 最近未到期期限）。

    与 claim 候选扫描、`due_retry_task_ids` 同一列同一判据；`now` 由调用方按权威
    时钟给出（生产：`server_now` → DB 时钟；测试：注入时钟），与写 `retry_at` 时
    同一个源。分类在 SQL 之外做，好让"最近未到期期限"和计数出自同一遍扫描。
    """
    rows: Any = conn.execute(
        "SELECT retry_at FROM tasks WHERE run_id = %s AND status = %s",
        (run_id, ResearchTaskState.State.RETRY_SCHEDULED),
    ).fetchall()
    scheduled = 0
    due = 0
    next_retry_at: datetime | None = None
    for row in rows:
        deadline = row["retry_at"]
        if deadline is None:
            due += 1
            continue
        value = _as_utc(deadline)
        if value <= now:
            due += 1
            continue
        scheduled += 1
        if next_retry_at is None or value < next_retry_at:
            next_retry_at = value
    return RetrySchedule(
        scheduled=scheduled,
        due=due,
        next_retry_at=decode_timestamp_pg(next_retry_at) if next_retry_at is not None else None,
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:  # defensive: treat naive DB result as UTC
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def live_lease_holders(
    conn: Any, run_id: str, now: datetime
) -> tuple[tuple[str, str | None, int, datetime | None], ...]:
    """该 run 里**活着**的租约持有者（SQLite 侧同一个判据，见 sqlite/projections.py）。

    "活"= `recover_expired_leases` 回收判据的补集：未过期（`expires_at >= now`）且持有者
    不是 LOST worker。`now` 由调用方按权威时钟给出（生产：`server_now` → DB 时钟；测试：
    注入时钟），与回收方同一个源。`lease_id` 有意不读（作业面凭据不进控制面读面）。
    """
    rows: Any = conn.execute(
        "SELECT l.task_id AS task_id, l.worker_id AS worker_id, l.fence AS fence,"
        " l.expires_at AS expires_at FROM leases AS l JOIN tasks AS t ON t.task_id = l.task_id"
        " WHERE t.run_id = %s AND l.expires_at >= %s"
        " AND (l.worker_id IS NULL OR l.worker_id NOT IN"
        " (SELECT worker_id FROM workers WHERE state = 'LOST'))"
        " ORDER BY l.task_id",
        (run_id, now),
    ).fetchall()
    return tuple(
        (
            str(row["task_id"]),
            None if row["worker_id"] is None else str(row["worker_id"]),
            int(row["fence"] or 0),
            None if row["expires_at"] is None else _as_utc(row["expires_at"]),
        )
        for row in rows
    )


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
