"""TaskLease 构造与序列化助手（SqliteWorkflowEngine 共享）。"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

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


def lease_from_row(row: sqlite3.Row) -> TaskLease:
    from adapters.sqlite.serialization import decode_timestamp

    keys = row.keys()
    return TaskLease(
        lease_id=row["lease_id"],
        task_id=row["task_id"],
        agent_id=row["agent_id"],
        expires_at=decode_timestamp(row["expires_at"]),
        heartbeat_at=decode_timestamp(row["heartbeat_at"]),
        worker_id=row["worker_id"] if "worker_id" in keys and row["worker_id"] else None,
        fence=int(row["fence"]) if "fence" in keys and row["fence"] is not None else 0,
    )


def iso(timestamp: Timestamp) -> str:
    return timestamp.value.isoformat().replace("+00:00", "Z")


def timestamp_now(now: Callable[[], datetime] | None) -> Timestamp:
    value = datetime.now(timezone.utc) if now is None else now()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("now() must return timezone-aware datetime")
    return Timestamp(value.astimezone(timezone.utc))


def request_digest(task: ResearchTask, contract: TaskContract) -> str:
    return str(digest_of({"task": task, "contract": contract}))
