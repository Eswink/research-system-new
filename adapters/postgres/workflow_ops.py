"""PostgresWorkflowEngine — heartbeat/complete/recovery paths (166-382)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, cast

from adapters.postgres.db import now_iso
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
    renewed = new_lease(lease.task_id, lease.agent_id, ttl, now)
    assert renewed.expires_at is not None and renewed.heartbeat_at is not None
    with conn.transaction():
        cur: Any = conn.execute(
            "UPDATE leases SET lease_id = %s, expires_at = %s, heartbeat_at = %s "
            "WHERE task_id = %s AND lease_id = %s",
            (
                renewed.lease_id,
                renewed.expires_at.value,
                renewed.heartbeat_at.value,
                lease.task_id,
                lease.lease_id,
            ),
        )
        if cur.rowcount == 0:
            record("heartbeat", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"no matching lease for task: {lease.task_id}")
    record("heartbeat", lease.task_id)
    return renewed


def complete_impl(conn: Any, record: Any, outbox: Any, payload: CompletePayload) -> None:
    lease: Any = payload.lease
    completion: Any = payload.completion
    now = payload.now
    with conn.transaction():
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
            record("complete", lease.task_id, result="deduped")
            return
        lease_row: Any = conn.execute(
            "SELECT lease_id, expires_at FROM leases WHERE task_id = %s FOR UPDATE",
            (lease.task_id,),
        ).fetchone()
        if lease_row is None or lease_row["lease_id"] != lease.lease_id:
            record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"no matching lease for task: {lease.task_id}")
        expires_at: Any = decode_timestamp_pg(lease_row["expires_at"]).value
        now_value: Any = now_iso(now)
        # fencing: expired lease cannot complete — stale worker (BLOCKER-3)
        if expires_at <= now_value:
            record("complete", lease.task_id, error="InvalidInputError")
            raise InvalidInputError(f"lease for task {lease.task_id} has expired")
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
    with conn.transaction():
        expired: Any = conn.execute(
            "SELECT leases.task_id FROM leases WHERE leases.expires_at < %s FOR UPDATE SKIP LOCKED",
            (now_iso(now),),
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
