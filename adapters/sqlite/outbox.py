"""Transactional Outbox 写入助手（SqliteWorkflowEngine 事务内调用）。"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from adapters.sqlite.db import now_iso
from adapters.sqlite.leases import timestamp_now
from adapters.sqlite.serialization import encode_envelope
from packages.domain.events import EventEnvelope, EventType, digest_of_payload


@dataclass(frozen=True, slots=True)
class OutboxWriter:
    """事务内 outbox 写入器（conn + 时钟注入）。"""

    conn: sqlite3.Connection
    now: Callable[[], datetime] | None = None

    def publish(
        self,
        event_type: EventType,
        payload: dict[str, object],
        *,
        run_id: str,
        task_id: str,
    ) -> None:
        """事务内写 outbox（调用方持有写锁/事务）。"""
        envelope = EventEnvelope(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            schema_version="1",
            occurred_at=timestamp_now(self.now),
            actor="system:workflow-engine",
            scope=f"run:{run_id} task:{task_id}",
            payload=payload,
            payload_digest=digest_of_payload(payload),
            run_id=run_id,
            task_id=task_id,
        )
        self.conn.execute(
            "INSERT OR IGNORE INTO outbox_events (event_id, envelope_json, created_at)"
            " VALUES (?, ?, ?)",
            (envelope.event_id, encode_envelope(envelope), now_iso(self.now)),
        )
