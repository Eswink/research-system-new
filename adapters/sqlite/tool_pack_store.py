"""SqliteToolPackStore：ToolPackStore Port 的 SQLite 实现（GOAL-003 / EC-02）。

与 SqliteToolProviderRegistry 同构（JSON-blob-per-row + KeyError/InvalidInput 语义）。
两处语义要点：

- **生效版本与待批准更新同一行写入**（`manifest_json` + `pending_json`）：崩溃后
  不会出现"批准了不存在的东西"或"扩张被静默生效"。
- `install` 对已存在 pack_id 抛 InvalidInputError、`replace` 对不存在抛
  InvalidInputError（沿用 Port 契约，防止静默覆盖）；`revoke` 清空待批准更新
  （REVOKED 是终态，不允许再挂着未批准的扩张）。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, parse_iso
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.tool_pack_store import ToolPackRecord
from packages.domain.core import Timestamp
from packages.domain.enums import ToolPackState
from packages.domain.tools import manifest_document, manifest_from_document

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tool_packs (
    pack_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    pending_json TEXT,
    revoked_reason TEXT,
    installed_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS tool_packs_state ON tool_packs (state, pack_id);
"""

_COLUMNS = (
    "pack_id",
    "state",
    "manifest_json",
    "pending_json",
    "revoked_reason",
    "installed_at",
)


def _encode(record: ToolPackRecord) -> tuple[str, str, str, str | None, str | None, str, str]:
    pending = record.pending_manifest
    return (
        record.pack_id,
        record.state.value,
        json.dumps(manifest_document(record.manifest), ensure_ascii=False, sort_keys=True),
        (
            json.dumps(manifest_document(pending), ensure_ascii=False, sort_keys=True)
            if pending is not None
            else None
        ),
        record.revoked_reason,
        record.installed_at.value.isoformat(),
        Timestamp.now().value.isoformat(),
    )


def _decode(row: dict[str, Any]) -> ToolPackRecord:
    pending = row.get("pending_json")
    return ToolPackRecord(
        pack_id=str(row["pack_id"]),
        state=ToolPackState(str(row["state"])),
        manifest=manifest_from_document(json.loads(str(row["manifest_json"]))),
        installed_at=Timestamp(value=parse_iso(str(row["installed_at"]))),
        revoked_reason=row.get("revoked_reason"),
        pending_manifest=(
            manifest_from_document(json.loads(str(pending))) if pending is not None else None
        ),
    )


class SqliteToolPackStore(SqliteAdapterBase):
    """SQLite 持久化 ToolPackStore；共享连接由 composition root 注入。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("tool_pack_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def install(self, record: ToolPackRecord) -> None:
        self._ensure_open()
        values = _encode(record)
        if self._row(record.pack_id) is not None:
            self._record("install", record.pack_id, error="InvalidInputError")
            raise InvalidInputError(f"tool pack already installed: {record.pack_id}")
        with self._conn:
            self._conn.execute(
                "INSERT INTO tool_packs"
                " (pack_id, state, manifest_json, pending_json, revoked_reason,"
                " installed_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                values,
            )
        self._record("install", record.pack_id, result="stored")

    def replace(self, record: ToolPackRecord) -> None:
        self._ensure_open()
        values = _encode(record)
        if self._row(record.pack_id) is None:
            self._record("replace", record.pack_id, error="InvalidInputError")
            raise InvalidInputError(f"tool pack not installed: {record.pack_id}")
        with self._conn:
            self._conn.execute(
                "UPDATE tool_packs SET state = ?, manifest_json = ?, pending_json = ?,"
                " revoked_reason = ?, installed_at = ?, updated_at = ? WHERE pack_id = ?",
                (*values[1:], values[0]),
            )
        self._record("replace", record.pack_id, result="stored")

    def revoke(self, pack_id: str, reason: str) -> None:
        self._ensure_open()
        if self._row(pack_id) is None:
            self._record("revoke", pack_id, error="InvalidInputError")
            raise InvalidInputError(f"tool pack not installed: {pack_id}")
        with self._conn:
            self._conn.execute(
                "UPDATE tool_packs SET state = ?, revoked_reason = ?, pending_json = NULL,"
                " updated_at = ? WHERE pack_id = ?",
                (ToolPackState.REVOKED.value, reason, Timestamp.now().value.isoformat(), pack_id),
            )
        self._record("revoke", pack_id, result="revoked")

    def get(self, pack_id: str) -> ToolPackRecord | None:
        self._ensure_open()
        row = self._row(pack_id)
        self._record("get", pack_id, result="hit" if row is not None else "miss")
        return _decode(row) if row is not None else None

    def snapshot(self) -> dict[str, ToolPackRecord]:
        self._ensure_open()
        rows = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM tool_packs ORDER BY pack_id"
        ).fetchall()
        result = {str(row[0]): _decode(dict(zip(_COLUMNS, row, strict=True))) for row in rows}
        self._record("snapshot", "*", result=f"{len(result)} records")
        return result

    def _row(self, pack_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM tool_packs WHERE pack_id = ?",
            (pack_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(zip(_COLUMNS, row, strict=True))
