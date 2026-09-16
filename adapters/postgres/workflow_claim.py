"""PostgresWorkflowEngine — claim_next path (M16 WP2).

Pulls the next claimable EXECUTION task (QUEUED, or RETRY_SCHEDULED after a
retryable failure — PLAN-20260915-078) matching a worker's capability/partition
filter and atomically leases it, serialized by `FOR UPDATE SKIP LOCKED` so
multiple schedulers/workers claim disjoint work without a second coordinator.
The `leases` row remains the sole ownership authority; partition is only a
filter. Each claim advances `tasks.fence_seq` and records it on the lease. The
same hand-out also advances `attempt` and rewrites `task_json`, so the projection
never lags the delivery generation.

All query values are bound via psycopg placeholders; the two SQL variants
(with / without the partition filter) are complete static constants — no
dynamic query string is ever assembled from input.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, cast

from adapters.postgres.leases import new_lease
from adapters.postgres.serialization import reencode_task_json
from packages.application.ports.workflow_engine import ClaimRequest, TaskLease
from packages.domain.enums import TaskKind
from packages.domain.events import EventType
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState

# Static SQL constants (values bound as parameters below). Both variants carry the
# cooperative-pause filter (PLAN-20260914-048): a task whose run is canonically
# PAUSED is never dispatched. Held leases are untouched — pause stops new claims,
# it does not revoke anything.
_SELECT_WITH_PARTITION = (
    "SELECT task_id, run_id, assigned_agent_id, fence_seq, task_json, contract_json FROM tasks "
    "WHERE kind = %s AND status IN (%s, %s) AND cancelled = FALSE "
    "AND (required_capability IS NULL OR required_capability = ANY(%s)) "
    "AND (partition IS NULL OR partition = ANY(%s)) "
    "AND NOT EXISTS (SELECT 1 FROM runs WHERE runs.run_id = tasks.run_id "
    "AND runs.run_json ->> 'state' = %s) "
    "ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
)
_SELECT_CAPABILITY_ONLY = (
    "SELECT task_id, run_id, assigned_agent_id, fence_seq, task_json, contract_json FROM tasks "
    "WHERE kind = %s AND status IN (%s, %s) AND cancelled = FALSE "
    "AND (required_capability IS NULL OR required_capability = ANY(%s)) "
    "AND NOT EXISTS (SELECT 1 FROM runs WHERE runs.run_id = tasks.run_id "
    "AND runs.run_json ->> 'state' = %s) "
    "ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
)
_INSERT_LEASE = (
    "INSERT INTO leases (task_id, lease_id, agent_id, expires_at, heartbeat_at, "
    "worker_id, fence) VALUES (%s, %s, %s, %s, %s, %s, %s)"
)
# 一次交付就是一个时刻：状态、交付代次、尝试序号与 task_json 必须在同一条更新里落账
# （PLAN-20260915-078——投影读 task_json，落后就会把重试的用量记进上一次尝试的 entry id）。
_MARK_LEASED = (
    "UPDATE tasks SET status = %s, fence_seq = %s, attempt = %s, task_json = %s WHERE task_id = %s"
)


@dataclass(frozen=True, slots=True)
class ClaimPayload:
    request: ClaimRequest
    ttl: timedelta


def _select_claimable(conn: Any, request: ClaimRequest) -> Any:
    paused = ResearchRunState.State.PAUSED
    # 排了下一次尝试的任务与首次排队同样可派发（PLAN-20260915-078）。
    queued = ResearchTaskState.State.QUEUED
    retry = ResearchTaskState.State.RETRY_SCHEDULED
    caps = list(request.capabilities)
    if request.relax_partitions:
        return conn.execute(
            _SELECT_CAPABILITY_ONLY,
            (TaskKind.EXECUTION.value, queued, retry, caps, paused),
        ).fetchone()
    parts = list(request.partitions)
    return conn.execute(
        _SELECT_WITH_PARTITION,
        (TaskKind.EXECUTION.value, queued, retry, caps, parts, paused),
    ).fetchone()


def _hand_out(conn: Any, lease: TaskLease, row: Any) -> None:
    """把这次交付落账：lease 行 + 任务状态/代次/尝试序号/task_json（同一事务内）。"""
    assert lease.expires_at is not None and lease.heartbeat_at is not None
    conn.execute(
        _INSERT_LEASE,
        (
            lease.task_id,
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
        (
            ResearchTaskState.State.LEASED,
            lease.fence,
            lease.fence,
            reencode_task_json(
                row["task_json"],
                row["contract_json"],
                attempt=lease.fence,
                lease_id=lease.lease_id,
            ),
            lease.task_id,
        ),
    )


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
        # 每次 claim 让 fence_seq 前进一代（M16 §8）。它就是**已交付次数**，也就是本次
        # 尝试的序号（PLAN-20260915-078）：重排后的任务被再次取走时，这一代就是下一次尝试。
        new_fence = int(row["fence_seq"]) + 1
        lease = new_lease(
            task_id,
            cast("str | None", row["assigned_agent_id"]),
            ttl,
            now,
            worker_id=request.worker_id,
            fence=new_fence,
        )
        _hand_out(conn, lease, row)
        outbox.publish(
            EventType.TASK_LEASED,
            {"task_id": task_id, "lease_id": lease.lease_id, "fence": new_fence},
            run_id=str(row["run_id"]),
            task_id=task_id,
        )
    record("claim_next", request.worker_id, result=f"{task_id}@fence={new_fence}")
    return lease
