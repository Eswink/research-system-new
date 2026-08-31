"""TaskLease helpers for PostgresWorkflowEngine.

Reuses domain Timestamp/ID types; stores TIMESTAMPTZ directly (no ISO string).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import cast

from packages.application.ports.workflow_engine import TaskLease
from packages.domain.core import Timestamp
from packages.domain.serialization import digest_of
from packages.domain.tasks import ResearchTask, TaskContract


def new_lease(  # noqa: PLR0913 - lease identity is a complete value object
    task_id: str,
    agent_id: str | None,
    ttl: timedelta,
    now: Callable[[], datetime] | None,
    *,
    worker_id: str | None = None,
    fence: int = 0,
) -> TaskLease:
    now_value = datetime.now(timezone.utc) if now is None else now()
    if now_value.tzinfo is None or now_value.utcoffset() is None:
        raise ValueError("now() must return timezone-aware datetime")
    utc = now_value.astimezone(timezone.utc)
    return TaskLease(
        lease_id=str(uuid.uuid4()),
        task_id=task_id,
        agent_id=agent_id,
        expires_at=Timestamp(utc + ttl),
        heartbeat_at=Timestamp(utc),
        worker_id=worker_id,
        fence=fence,
    )


def lease_from_row(row: dict[str, object]) -> TaskLease:
    """Convert dict_row (psycopg) to TaskLease; TIMESTAMPTZ → Timestamp."""
    from adapters.postgres.serialization import decode_timestamp_pg

    worker_id = row.get("worker_id")
    fence_raw = row.get("fence")
    return TaskLease(
        lease_id=str(row["lease_id"]),
        task_id=str(row["task_id"]),
        agent_id=str(row["agent_id"]) if row["agent_id"] is not None else None,
        expires_at=decode_timestamp_pg(row["expires_at"]),  # type: ignore[arg-type]
        heartbeat_at=decode_timestamp_pg(row["heartbeat_at"]),  # type: ignore[arg-type]
        worker_id=str(worker_id) if worker_id is not None else None,
        fence=int(cast(int, fence_raw) or 0),
    )


def request_digest(task: ResearchTask, contract: TaskContract) -> str:
    return str(digest_of({"task": task, "contract": contract}))
