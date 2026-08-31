"""PostgresWorkflowEngine — heartbeat/complete/recovery paths (166-382)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, cast

from adapters.postgres.db import db_time_expr, server_now
from adapters.postgres.leases import new_lease
from adapters.postgres.serialization import decode_timestamp_pg
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import TaskCompletion, TaskLease
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState


@dataclass(frozen=True, slots=True)
class CompletePayload:
    lease: TaskLease
    completion: TaskCompletion
    now: Any = None


def heartbeat_impl(conn: Any, record: Any, lease: TaskLease, ttl: timedelta, now: Any) -> TaskLease:
    # lease_id rotates each heartbeat (M14 fencing); worker_id + fence are the
    # stable identity of this claim generation and must be preserved.
    renewed = new_lease(
        lease.task_id, lease.agent_id, ttl, now, worker_id=lease.worker_id, fence=lease.fence
    )
    assert renewed.expires_at is not None and renewed.heartbeat_at is not None
    with conn.transaction():
        cur: Any = conn.execute(
            "UPDATE leases SET lease_id = %s, expires_at = %s, heartbeat_at = %s, "
            "worker_id = %s, fence = %s "
            "WHERE task_id = %s AND lease_id = %s",
            (
                renewed.lease_id,
                renewed.expires_at.value,
                renewed.heartbeat_at.value,
                renewed.worker_id,
                renewed.fence,
                lease.task_id,
                lease.lease_id,
            ),
        )
        if cur.rowcount == 0:
            record("heartbeat", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"no matching lease for task: {lease.task_id}")
    record("heartbeat", lease.task_id)
    return renewed


def _validate_completion_lease(conn: Any, record: Any, lease: Any, now: Any) -> bool:
    """Return True if completion may proceed; False if it is an idempotent noop.

    Raises InvalidInputError for unknown/cancelled task, lease mismatch, stale
    fence, or expired lease (M16 §8 fencing).
    """
    task_row: Any = conn.execute(
        "SELECT run_id, status, cancelled FROM tasks WHERE task_id = %s FOR UPDATE",
        (lease.task_id,),
    ).fetchone()
    if task_row is None:
        record("complete", lease.task_id, error="InvalidInputError")
        raise InvalidInputError(f"unknown task: {lease.task_id}")
    if task_row["cancelled"]:
        record("complete", lease.task_id, error="InvalidInputError")
        raise InvalidInputError(f"task {lease.task_id} is cancelled; cannot complete")
    if task_row["status"] in (
        ResearchTaskState.State.SUCCEEDED,
        ResearchTaskState.State.FAILED,
    ):
        return False
    lease_row: Any = conn.execute(
        "SELECT lease_id, expires_at, fence FROM leases WHERE task_id = %s FOR UPDATE",
        (lease.task_id,),
    ).fetchone()
    if lease_row is None or lease_row["lease_id"] != lease.lease_id:
        record("complete", lease.task_id, error="InvalidInputError")
        raise InvalidInputError(f"no matching lease for task: {lease.task_id}")
    # fencing: a stale worker whose claim generation was superseded carries an
    # old fence and cannot write authoritative completion (M16 §8).
    if int(lease_row["fence"]) != lease.fence:
        record("complete", lease.task_id, error="InvalidInputError")
        raise InvalidInputError(
            f"stale fence for task {lease.task_id}: lease generation superseded"
        )
    expires_at: Any = decode_timestamp_pg(lease_row["expires_at"]).value
    if expires_at <= server_now(conn, now):
        record("complete", lease.task_id, error="InvalidInputError")
        raise InvalidInputError(f"lease for task {lease.task_id} has expired")
    return True


def complete_impl(conn: Any, record: Any, outbox: Any, payload: CompletePayload) -> None:
    lease: Any = payload.lease
    completion: Any = payload.completion
    with conn.transaction():
        if not _validate_completion_lease(conn, record, lease, payload.now):
            record("complete", lease.task_id, result="deduped")
            return
        task_row: Any = conn.execute(
            "SELECT run_id FROM tasks WHERE task_id = %s", (lease.task_id,)
        ).fetchone()
        status = (
            ResearchTaskState.State.SUCCEEDED
            if completion.outcome == "SUCCEEDED"
            else ResearchTaskState.State.FAILED
        )
        conn.execute("DELETE FROM leases WHERE task_id = %s", (lease.task_id,))
        conn.execute("UPDATE tasks SET status = %s WHERE task_id = %s", (status, lease.task_id))
        outbox.publish(
            EventType.TASK_COMPLETED,
            {"task_id": lease.task_id, "outcome": completion.outcome},
            run_id=str(task_row["run_id"]),
            task_id=lease.task_id,
        )
        record("complete", lease.task_id, result=completion.outcome)


def recover_impl(conn: Any, record: Any, outbox: Any, now: Any) -> int:
    # Single lease authority (M16 §5): a lease is recoverable when it has
    # expired on the database clock OR its owning worker is already LOST.
    # Both are decided here, in one determination, so lost-worker leases are
    # never released through a second path.
    time_sql, time_params = db_time_expr(now)
    with conn.transaction():
        expired: Any = conn.execute(
            "SELECT leases.task_id FROM leases "
            f"WHERE leases.expires_at < {time_sql} "
            "OR leases.worker_id IN (SELECT worker_id FROM workers WHERE state = 'LOST') "
            "FOR UPDATE SKIP LOCKED",
            (*time_params,),
        ).fetchall()
        recovered = 0
        for row in expired:
            task_id = cast(str, row["task_id"])
            task_row: Any = conn.execute(
                "SELECT run_id, cancelled, status FROM tasks WHERE task_id = %s FOR UPDATE",
                (task_id,),
            ).fetchone()
            if task_row is None:
                continue
            if task_row["cancelled"] or task_row["status"] in ResearchTaskState.terminal():
                # stale lease on terminal/cancelled task: just drop the lease
                conn.execute("DELETE FROM leases WHERE task_id = %s", (task_id,))
                continue
            conn.execute("DELETE FROM leases WHERE task_id = %s", (task_id,))
            conn.execute(
                "UPDATE tasks SET status = %s WHERE task_id = %s",
                (ResearchTaskState.State.QUEUED, task_id),
            )
            outbox.publish(
                EventType.TASK_RETRY_SCHEDULED,
                {"task_id": task_id, "reason": "lease_expired"},
                run_id=str(task_row["run_id"]),
                task_id=task_id,
            )
            recovered += 1
        record("recover_expired_leases", f"{recovered} recovered")
        return recovered
