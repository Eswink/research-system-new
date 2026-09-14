"""SqliteLibraryStore：LibraryStore Port 的 SQLite 实现（PLAN-20260914-044 WP-A）。

与 SqliteProjectStore 同构（JSON-blob-per-row + upsert + KeyError 语义）；
配置面共享连接由 composition root 注入。kind 过滤在 SQL 层完成（避免全表读）。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, cast

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, parse_iso
from packages.domain.core import Timestamp
from packages.domain.library import LibraryResource, ResourceKind, ResourceStatus

_SCHEMA = """
CREATE TABLE IF NOT EXISTS library_resources (
    resource_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    resource_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS library_resources_project_kind
    ON library_resources (project_id, kind);
"""

_LIST_SQL = (
    "SELECT resource_json FROM library_resources"
    " WHERE project_id = ? ORDER BY created_at, resource_id"
)
_LIST_KIND_SQL = (
    "SELECT resource_json FROM library_resources"
    " WHERE project_id = ? AND kind = ? ORDER BY created_at, resource_id"
)
_GET_SQL = "SELECT resource_json FROM library_resources WHERE resource_id = ?"
_UPSERT_SQL = (
    "INSERT INTO library_resources"
    " (resource_id, project_id, kind, resource_json, created_at, updated_at)"
    " VALUES (?, ?, ?, ?, ?, ?)"
    " ON CONFLICT (resource_id) DO UPDATE SET"
    " project_id = excluded.project_id,"
    " kind = excluded.kind,"
    " resource_json = excluded.resource_json,"
    " updated_at = excluded.updated_at"
)


def _encode(resource: LibraryResource) -> dict[str, Any]:
    return {
        "id": resource.id,
        "project_id": resource.project_id,
        "kind": resource.kind.value,
        "name": resource.name,
        "description": resource.description,
        "content_ref": resource.content_ref,
        "tags": list(resource.tags),
        "status": resource.status.value,
        "created_at": resource.created_at.value.isoformat(),
        "updated_at": resource.updated_at.value.isoformat(),
    }


def _decode(payload: dict[str, Any]) -> LibraryResource:
    tags = payload.get("tags") or []
    return LibraryResource(
        id=payload["id"],
        project_id=payload["project_id"],
        kind=ResourceKind(payload["kind"]),
        name=payload["name"],
        description=payload.get("description", ""),
        content_ref=payload.get("content_ref"),
        tags=tuple(str(tag) for tag in tags),
        status=ResourceStatus(payload["status"]),
        created_at=Timestamp(parse_iso(payload["created_at"])),
        updated_at=Timestamp(parse_iso(payload["updated_at"])),
    )


class SqliteLibraryStore(SqliteAdapterBase):
    """SQLite 持久化 LibraryStore；list/get/save + close 语义。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("library_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
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

    def list_resources(
        self, project_id: str, kind: ResourceKind | None = None
    ) -> list[LibraryResource]:
        self._ensure_open()
        if kind is None:
            rows = self._run(_LIST_SQL, (project_id,)).fetchall()
        else:
            rows = self._run(_LIST_KIND_SQL, (project_id, ResourceKind(kind).value)).fetchall()
        resources = [
            _decode(cast(dict[str, Any], json.loads(row["resource_json"]))) for row in rows
        ]
        self._record("list_resources", project_id, result=str(len(resources)))
        return resources

    def get_resource(self, resource_id: str) -> LibraryResource:
        self._ensure_open()
        row = self._run(_GET_SQL, (resource_id,)).fetchone()
        if row is None:
            self._record("get_resource", resource_id, error="KeyError")
            raise KeyError(f"library resource not found: {resource_id!r}")
        self._record("get_resource", resource_id)
        return _decode(cast(dict[str, Any], json.loads(row["resource_json"])))

    def save_resource(self, resource: LibraryResource) -> None:
        self._ensure_open()
        payload = json.dumps(_encode(resource), ensure_ascii=False, sort_keys=True)
        with self._conn:
            self._run(
                _UPSERT_SQL,
                (
                    resource.id,
                    resource.project_id,
                    resource.kind.value,
                    payload,
                    resource.created_at.value.isoformat(),
                    resource.updated_at.value.isoformat(),
                ),
            )
        self._record("save_resource", resource.id)
