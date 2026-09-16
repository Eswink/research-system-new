"""SqliteScheduleStore：ScheduleStore Port 的 SQLite 实现（GOAL-003 EC-03）。

与 SqliteToolPackStore / SqliteOpsStore 同构（行级记录 + SqliteAdapterBase 的
open 校验与访问记录）。语义要点：

- 定义是**配置**：`save_definition` 对已存在行做替换（PATCH 语义），因此天然幂等；
- **运行事实不入库**：run_count / last_run_at 是进程内观测（见 `ScheduleRegistry`），
  重启归零是诚实的（它不是配置）。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect
from packages.domain.schedules import ScheduleDefinition, ScheduleJob

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schedules (
    name TEXT PRIMARY KEY,
    job TEXT NOT NULL,
    interval_seconds REAL NOT NULL,
    enabled INTEGER NOT NULL,
    builtin INTEGER NOT NULL,
    note TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS schedules_job ON schedules (job, name);
"""

_COLUMNS = ("name", "job", "interval_seconds", "enabled", "builtin", "note")


def _decode(row: sqlite3.Row | tuple[object, ...]) -> ScheduleDefinition:
    values = dict(zip(_COLUMNS, row, strict=True))
    return ScheduleDefinition(
        name=str(values["name"]),
        job=ScheduleJob(str(values["job"])),
        interval_seconds=float(values["interval_seconds"]),
        enabled=bool(values["enabled"]),
        builtin=bool(values["builtin"]),
        note=str(values["note"]),
    )


class SqliteScheduleStore(SqliteAdapterBase):
    """SQLite 持久化 ScheduleStore；共享连接由 composition root 注入。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("schedule_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def list_definitions(self) -> list[ScheduleDefinition]:
        self._ensure_open()
        rows = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM schedules ORDER BY name"
        ).fetchall()
        definitions = [_decode(row) for row in rows]
        self._record("list_definitions", "*", result=f"{len(definitions)} rows")
        return definitions

    def get_definition(self, name: str) -> ScheduleDefinition | None:
        self._ensure_open()
        row = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM schedules WHERE name = ?",
            (name,),
        ).fetchone()
        self._record("get_definition", name, result="hit" if row is not None else "miss")
        return _decode(row) if row is not None else None

    def save_definition(self, definition: ScheduleDefinition) -> None:
        """插入或替换（PATCH 语义，幂等）；同一行始终是这条定义的完整事实。"""
        self._ensure_open()
        with self._conn:
            self._conn.execute(
                "INSERT INTO schedules (name, job, interval_seconds, enabled, builtin, note)"
                " VALUES (?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(name) DO UPDATE SET job = excluded.job,"
                " interval_seconds = excluded.interval_seconds, enabled = excluded.enabled,"
                " builtin = excluded.builtin, note = excluded.note,"
                " updated_at = datetime('now')",
                (
                    definition.name,
                    definition.job.value,
                    definition.interval_seconds,
                    int(definition.enabled),
                    int(definition.builtin),
                    definition.note,
                ),
            )
        self._record("save_definition", definition.name, result="stored")

    def delete_definition(self, name: str) -> None:
        self._ensure_open()
        with self._conn:
            self._conn.execute("DELETE FROM schedules WHERE name = ?", (name,))
        self._record("delete_definition", name, result="deleted")
