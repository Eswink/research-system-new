"""PG run_projection: mirrors sqlite/run_projection.py for PG."""

from __future__ import annotations

from typing import Any

from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env
from adapters.postgres.projections import list_tasks as pg_list_tasks


class PostgresRunProjection:
    def __init__(
        self,
        *,
        dsn: str | None = None,
        connection: Any | None = None,
    ) -> None:
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresRunProjection requires dsn or connection")
            self._conn = pg_connect(resolved)
        # needs a publisher for events(); store a reference to a PG publisher
        # In PG assembly, events come from the SQLite publisher (control-plane);
        # projection reads tasks from PG directly and events from the publisher.
        self._events: Any = None

    def bind_events(self, events: Any) -> None:
        self._events = events

    def close(self) -> None:
        if self._owns_connection:
            try:
                self._conn.close()
            except Exception:
                pass

    def list_tasks(self, run_id: str) -> Any:
        rows = pg_list_tasks(self._conn, run_id)
        return tuple((row.task, row.contract) for row in rows)

    def events(self, run_id: str) -> Any:
        if self._events is None:
            return ()
        published = getattr(self._events, "published", ())
        if callable(published):
            published = published()
        return tuple(
            sorted(
                (envelope for envelope in published if getattr(envelope, "run_id", None) == run_id),
                key=lambda item: item.event_id,
            )
        )

    def recent_events(self, limit: int) -> Any:
        """跨 run 最近事件（newest-first）；sink published 已按 created_at 排序。"""
        if self._events is None:
            return ()
        published = getattr(self._events, "published", ())
        if callable(published):
            published = published()
        capped = max(0, int(limit))
        tail = list(published)[-capped:] if capped else []
        return tuple(reversed(tail))
