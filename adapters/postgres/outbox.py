"""Postgres transactional outbox writer (used inside caller's transaction)."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from adapters.postgres.serialization import encode_envelope
from packages.domain.core import Timestamp
from packages.domain.events import EventEnvelope, EventType, digest_of_payload


@dataclass(frozen=True, slots=True)
class PgOutboxWriter:
    """Write outbox inside the caller's psycopg transaction.

    `conn` must be an open psycopg Connection with an active transaction
    (caller manages commit/rollback).
    """

    conn: object  # psycopg.Connection[dict]
    now: Callable[[], datetime] | None = None

    def publish(
        self,
        event_type: EventType,
        payload: dict[str, object],
        *,
        run_id: str,
        task_id: str,
    ) -> None:
        now_value = datetime.now(timezone.utc) if self.now is None else self.now()
        if now_value.tzinfo is None or now_value.utcoffset() is None:
            raise ValueError("now() must return timezone-aware datetime")
        utc = now_value.astimezone(timezone.utc)
        envelope = EventEnvelope(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            schema_version="1",
            occurred_at=Timestamp(utc),
            actor="system:workflow-engine",
            scope=f"run:{run_id} task:{task_id}",
            payload=payload,
            payload_digest=digest_of_payload(payload),
            run_id=run_id,
            task_id=task_id,
        )
        conn_any: object = self.conn
        envelope_json = encode_envelope(envelope)
        cur = conn_any
        sql = (
            "INSERT INTO outbox_events (event_id, envelope_json, created_at) "
            "VALUES (%s, %s::jsonb, now()) ON CONFLICT (event_id) DO NOTHING"
        )
        cur.execute(sql, (envelope.event_id, envelope_json))  # type: ignore[attr-defined]
