"""SqliteNotificationReadStore：通知已读标记（WP-G，NotificationReadStore Port）。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso

_SCHEMA = """
CREATE TABLE IF NOT EXISTS notification_reads (
    event_id TEXT PRIMARY KEY,
    read_at TEXT NOT NULL
);
"""


class SqliteNotificationReadStore(SqliteAdapterBase):
    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("notification_read_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def mark_read(self, event_id: str) -> None:
        self._ensure_open()
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO notification_reads(event_id, read_at) VALUES (?, ?)",
                (event_id, now_iso(None)),
            )
        self._record("mark_read", event_id, result="ok")

    def read_event_ids(self) -> frozenset[str]:
        self._ensure_open()
        rows = self._conn.execute("SELECT event_id FROM notification_reads").fetchall()
        return frozenset(str(row[0]) for row in rows)
