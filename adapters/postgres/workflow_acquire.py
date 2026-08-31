"""PostgresWorkflowEngine — acquire lease path."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, cast

from adapters.postgres.db import server_now
from adapters.postgres.leases import lease_from_row, new_lease
from adapters.postgres.serialization import decode_timestamp_pg
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import TaskLease
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState


@dataclass(frozen=True, slots=True)
class AcquirePayload:
    task_id: str
    ttl: timedelta
    owned_lease_ids: frozenset[str] = frozenset()


def _require_task(conn: Any, record: Any, task_id: str) -> Any:
    row: Any = conn.execute(
        "SELECT * FROM tasks WHERE task_id = %s FOR UPDATE", (task_id,)
    ).fetchone()
    if row is None:
        record("acquire_lease", task_id, error="InvalidInputError")
        raise InvalidInputError(f"unknown task: {task_id}")
    if row["status"] in ResearchTaskState.terminal():
        record("acquire_lease", task_id, error="InvalidInputError")
        msg = f"task {task_id} is terminal ({row['status']}); cannot acquire lease"
        raise InvalidInputError(msg)
    return row


def _get_existing_lease(conn: Any, task_id: str) -> Any:
    return conn.execute("SELECT * FROM leases WHERE task_id = %s FOR UPDATE", (task_id,)).fetchone()


def _insert_lease(conn: Any, task_id: str, lease: Any, outbox: Any, row: Any) -> None:
    conn.execute(
        "INSERT INTO leases (task_id, lease_id, agent_id, expires_at, heartbeat_at) "
        "VALUES (%s, %s, %s, %s, %s)",
        (task_id, lease.lease_id, lease.agent_id, lease.expires_at.value, lease.heartbeat_at.value),
    )
    conn.execute(
        "UPDATE tasks SET status = %s WHERE task_id = %s",
        (ResearchTaskState.State.LEASED, task_id),
    )
    outbox.publish(
        EventType.TASK_LEASED,
        {"task_id": task_id, "lease_id": lease.lease_id},
        run_id=str(row["run_id"]),
        task_id=task_id,
    )


def acquire_lease_impl(
    conn: Any,
    record: Any,
    outbox: Any,
    payload: AcquirePayload,
    now: Any,
) -> TaskLease:
    task_id = payload.task_id
    ttl = payload.ttl
    with conn.transaction():
        row: Any = _require_task(conn, record, task_id)
        existing: Any = _get_existing_lease(conn, task_id)
        if existing is not None:
            # Check whether the existing lease has expired.
            # If it has, lazy-reclaim inside this transaction (atomic with the checks above).
            expires_at: Any = decode_timestamp_pg(existing["expires_at"]).value
            if expires_at <= server_now(conn, now):
                # Expired: reclaim — delete old, insert new, do not return old
                conn.execute("DELETE FROM leases WHERE task_id = %s", (task_id,))
                agent_id = cast(str | None, row["assigned_agent_id"])
                lease = new_lease(task_id, agent_id, ttl, now)
                assert lease.expires_at is not None and lease.heartbeat_at is not None
                _insert_lease(conn, task_id, lease, outbox, row)
                record("acquire_lease", task_id, result=lease.lease_id)
                return lease
            # Not expired: return existing lease ONLY to the same owner (idempotent retry).
            # A different engine/process must be rejected — same generation must never
            # have two legal owners (BLOCKER-2). Owner identity is tracked by the
            # engine via `owned_lease_ids` (the lease ids it has acquired).
            if existing["lease_id"] not in payload.owned_lease_ids:
                record("acquire_lease", task_id, error="InvalidInputError")
                raise InvalidInputError(f"task {task_id} is already leased")
            record("acquire_lease", task_id, result="deduped")
            return lease_from_row(cast(dict[str, object], existing))
        agent_id = cast(str | None, row["assigned_agent_id"])
        lease = new_lease(task_id, agent_id, ttl, now)
        assert lease.expires_at is not None and lease.heartbeat_at is not None
        _insert_lease(conn, task_id, lease, outbox, row)
        record("acquire_lease", task_id, result=lease.lease_id)
        return lease
