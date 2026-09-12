"""SqliteCatalogOverrideStore：CatalogOverrideStore Port 的 SQLite 实现（WP-B）。

用户自定义 RoleDefinition / TeamTemplate 的持久覆盖（document JSON 行，
kind/id 两级键，与 examples/config yaml 子项同形）。配置面 SQLite 语义与
Endpoint/Model/Agent store 同侧（PG canonical 迁移属 M14 配置面 follow-up）。
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso

_SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog_overrides (
    kind TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    document_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (kind, entity_id)
);
"""

# 完整字面量 SQL（数据值一律 ? 绑定）。
_UPSERT_SQL = (
    "INSERT INTO catalog_overrides (kind, entity_id, document_json, updated_at)"
    " VALUES (?, ?, ?, ?)"
    " ON CONFLICT (kind, entity_id) DO UPDATE SET"
    " document_json = excluded.document_json, updated_at = excluded.updated_at"
)
_GET_SQL = "SELECT document_json FROM catalog_overrides WHERE kind = ? AND entity_id = ?"
_LIST_SQL = "SELECT document_json FROM catalog_overrides WHERE kind = ? ORDER BY entity_id"
_DELETE_SQL = "DELETE FROM catalog_overrides WHERE kind = ? AND entity_id = ?"


class SqliteCatalogOverrideStore(SqliteAdapterBase):
    """kind 维度 document upsert/list/get/delete；list 按 entity_id 排序。"""

    def __init__(
        self,
        db_path: str = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("catalog_override_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(db_path)
        bootstrapper = getattr(self._conn, "executescript")
        bootstrapper(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def _run(self, statement: str, params: tuple[Any, ...] = ()) -> Any:
        runner = getattr(self._conn, "execute")
        return runner(statement, params)

    def upsert(self, kind: str, entity_id: str, document: dict[str, Any]) -> None:
        self._ensure_open()
        payload = json.dumps(document, ensure_ascii=False, sort_keys=True)
        with self._conn:
            self._run(_UPSERT_SQL, (kind, entity_id, payload, now_iso(None)))
        self._record("upsert", f"{kind}/{entity_id}")

    def get(self, kind: str, entity_id: str) -> dict[str, Any] | None:
        self._ensure_open()
        row = self._run(_GET_SQL, (kind, entity_id)).fetchone()
        self._record("get", f"{kind}/{entity_id}", result="found" if row else "none")
        if row is None:
            return None
        parsed: dict[str, Any] = json.loads(row["document_json"])
        return parsed

    def list(self, kind: str) -> list[dict[str, Any]]:
        self._ensure_open()
        rows = self._run(_LIST_SQL, (kind,)).fetchall()
        self._record("list", kind, result=str(len(rows)))
        return [json.loads(row["document_json"]) for row in rows]

    def delete(self, kind: str, entity_id: str) -> bool:
        self._ensure_open()
        with self._conn:
            cursor = self._run(_DELETE_SQL, (kind, entity_id))
        removed = int(cursor.rowcount) > 0
        self._record("delete", f"{kind}/{entity_id}", result=str(removed))
        return removed
