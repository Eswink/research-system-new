"""SqliteRunProjection：RunProjection Port 的 SQLite 实现。

复用 SqliteWorkflowEngine 的 projections（list_tasks）与 outbox 事件读取；
M14 PostgreSQL 实现走同一 Port。
"""

from __future__ import annotations

import sqlite3

from adapters.sqlite.projections import list_tasks as sqlite_list_tasks
from packages.application.ports.event_publisher import EventPublisher
from packages.domain.events import EventEnvelope
from packages.domain.tasks import ResearchTask, TaskContract


class SqliteRunProjection:
    """SQLite 只读投影（tasks + events）。"""

    def __init__(
        self,
        connection: sqlite3.Connection,
        events: EventPublisher,
    ) -> None:
        self._conn = connection
        self._events = events

    def list_tasks(self, run_id: str) -> tuple[tuple[ResearchTask, TaskContract], ...]:
        rows = sqlite_list_tasks(self._conn, run_id)
        return tuple((row.task, row.contract) for row in rows)

    def events(self, run_id: str) -> tuple[EventEnvelope, ...]:
        published = getattr(self._events, "published", ())
        return tuple(
            sorted(
                (envelope for envelope in published if envelope.run_id == run_id),
                key=lambda item: item.event_id,
            )
        )
