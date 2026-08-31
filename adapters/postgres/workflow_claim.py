"""PostgresWorkflowEngine — claim_next path (M16 WP2).

Pulls the next QUEUED EXECUTION task matching a worker's capability/partition
filter and atomically leases it, serialized by `FOR UPDATE SKIP LOCKED` so
multiple schedulers/workers claim disjoint work without a second coordinator.
The `leases` row remains the sole ownership authority; partition is only a
filter. Each claim advances `tasks.fence_seq` and records it on the lease.

All query values are bound via psycopg placeholders; the two SQL variants
(with / without the partition filter) are complete static constants — no
dynamic query string is ever assembled from input.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, cast

from adapters.postgres.leases import new_lease
from packages.application.ports.workflow_engine import ClaimRequest, TaskLease
from packages.domain.enums import TaskKind
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState

# Static SQL constants (values bound as parameters below).
_SELECT_WITH_PARTITION = (
    "SELECT task_id, run_id, assigned_agent_id, fence_seq FROM tasks "
    "WHERE kind = %s AND status = %s AND cancelled = FALSE "
    "AND (required_capability IS NULL OR required_capability = ANY(%s)) "
    "AND (partition IS NULL OR partition = ANY(%s)) "
    "ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
)
_SELECT_CAPABILITY_ONLY = (
    "SELECT task_id, run_id, assigned_agent_id, fence_seq FROM tasks "
    "WHERE kind = %s AND status = %s AND cancelled = FALSE "
    "AND (required_capability IS NULL OR required_capability = ANY(%s)) "
    "ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
)
_INSERT_LEASE = (
    "INSERT INTO leases (task_id, lease_id, agent_id, expires_at, heartbeat_at, "
    "worker_id, fence) VALUES (%s, %s, %s, %s, %s, %s, %s)"
)
_MARK_LEASED = "UPDATE tasks SET status = %s, fence_seq = %s WHERE task_id = %s"


@dataclass(frozen=True, slots=True)
class ClaimPayload:
    request: ClaimRequest
    ttl: timedelta


def _select_claimable(conn: Any, request: ClaimRequest) -> Any:
    caps = list(request.capabilities)
    if request.relax_partitions:
        return conn.execute(
            _SELECT_CAPABILITY_ONLY,
            (TaskKind.EXECUTION.value, ResearchTaskState.State.QUEUED, caps),
        ).fetchone()
    parts = list(request.partitions)
    return conn.execute(
        _SELECT_WITH_PARTITION,
        (TaskKind.EXECUTION.value, ResearchTaskState.State.QUEUED, caps, parts),
    ).fetchone()


def claim_next_impl(
    conn: Any,
    record: Any,
    outbox: Any,
    payload: ClaimPayload,
    now: Any,
) -> TaskLease | None:
    request = payload.request
    ttl = payload.ttl
    with conn.transaction():
        row = _select_claimable(conn, request)
        if row is None:
            record("claim_next", request.worker_id, result="none")
            return None
        task_id = cast(str, row["task_id"])
        new_fence = int(row["fence_seq"]) + 1
        lease = new_lease(
            task_id,
            cast("str | None", row["assigned_agent_id"]),
            ttl,
            now,
            worker_id=request.worker_id,
            fence=new_fence,
        )
        assert lease.expires_at is not None and lease.heartbeat_at is not None
        conn.execute(
            _INSERT_LEASE,
            (
                task_id,
                lease.lease_id,
                lease.agent_id,
                lease.expires_at.value,
                lease.heartbeat_at.value,
                lease.worker_id,
                lease.fence,
            ),
        )
        conn.execute(
            _MARK_LEASED,
            (ResearchTaskState.State.LEASED, new_fence, task_id),
        )
        outbox.publish(
            EventType.TASK_LEASED,
            {"task_id": task_id, "lease_id": lease.lease_id, "fence": new_fence},
            run_id=str(row["run_id"]),
            task_id=task_id,
        )
    record("claim_next", request.worker_id, result=f"{task_id}@fence={new_fence}")
    return lease
