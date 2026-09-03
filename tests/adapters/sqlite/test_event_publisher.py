"""PA-1 F7: SqliteOutboxEventPublisher durability semantics.

publish() self-commits at once (every sibling sqlite store does the same),
so an event survives a crash and is visible to a second connection (the
API-restart timeline case); a later failure in the caller's flow still rolls
back together with the event write. Raw sqlite3 check_same_thread semantics
are left to the adapter — this suite only asserts cross-connection outcomes.
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

from adapters.sqlite.db import connect
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from packages.domain.core import Timestamp
from packages.domain.events import EventEnvelope, EventType, digest_of_payload


def _envelope(event_id: str | None = None) -> EventEnvelope:
    payload = {"marker": "f7"}
    return EventEnvelope(
        event_id=event_id or str(uuid.uuid4()),
        event_type=EventType.RUN_COMPLETED,
        schema_version="1",
        occurred_at=Timestamp.now(),
        actor="system:test",
        scope="run:f7",
        payload=payload,
        payload_digest=digest_of_payload(payload),
        run_id="run-f7",
        trace_id="trace-f7",
    )


def test_publish_visible_to_second_connection_immediately(tmp_path: Path) -> None:
    db = str(tmp_path / "f7.db")
    publisher = SqliteOutboxEventPublisher(db_path=db)
    publisher.publish(_envelope())
    reader = connect(db)
    try:
        rows = reader.execute("SELECT event_id FROM outbox_events").fetchall()
        assert len(rows) == 1  # committed, not riding an open transaction
    finally:
        reader.close()
        publisher.close()


def test_publish_self_commits_independently(tmp_path: Path) -> None:
    db = str(tmp_path / "f7-manual.db")
    conn = connect(db)
    publisher = SqliteOutboxEventPublisher(connection=conn)
    reader = sqlite3.connect(str(tmp_path / "f7-manual.db"))
    try:
        publisher.publish(_envelope())
        assert reader.execute("SELECT count(*) FROM outbox_events").fetchone()[0] == 1
    finally:
        reader.close()
        publisher.close()
        conn.close()


def test_publish_idempotent_by_event_id(tmp_path: Path) -> None:
    db = str(tmp_path / "f7-dedup.db")
    publisher = SqliteOutboxEventPublisher(db_path=db)
    envelope = _envelope("fixed-event-id")
    publisher.publish(envelope)
    publisher.publish(envelope)
    reader = connect(db)
    try:
        assert reader.execute("SELECT count(*) FROM outbox_events").fetchone()[0] == 1
    finally:
        reader.close()
        publisher.close()
