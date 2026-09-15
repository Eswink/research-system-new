"""SqliteProjectStore：ProjectStore Port 的 SQLite 实现（PLAN-041 WP-A）。

与 SqliteAgentStore 同构（JSON-blob-per-row + upsert + KeyError 语义）；
配置面共享连接由 composition root 注入。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, cast

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, parse_iso
from packages.domain.core import Timestamp
from packages.domain.projects import ProjectDefinition, ProjectStatus

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    project_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

_LIST_SQL = "SELECT project_json FROM projects ORDER BY created_at, project_id"
_GET_SQL = "SELECT project_json FROM projects WHERE project_id = ?"
_UPSERT_SQL = (
    "INSERT INTO projects (project_id, project_json, created_at, updated_at)"
    " VALUES (?, ?, ?, ?)"
    " ON CONFLICT (project_id) DO UPDATE SET"
    " project_json = excluded.project_json,"
    " updated_at = excluded.updated_at"
)


def _encode(project: ProjectDefinition) -> dict[str, Any]:
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status.value,
        "created_at": project.created_at.value.isoformat(),
        "updated_at": project.updated_at.value.isoformat(),
    }


def _decode(payload: dict[str, Any]) -> ProjectDefinition:
    return ProjectDefinition(
        id=payload["id"],
        name=payload["name"],
        status=ProjectStatus(payload["status"]),
        created_at=Timestamp(parse_iso(payload["created_at"])),
        updated_at=Timestamp(parse_iso(payload["updated_at"])),
    )


class SqliteProjectStore(SqliteAdapterBase):
    """SQLite 持久化 ProjectStore；list/get/save + close 语义。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("project_store")
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

    def list_projects(self) -> list[ProjectDefinition]:
        self._ensure_open()
        rows = self._run(_LIST_SQL).fetchall()
        projects = [_decode(cast(dict[str, Any], json.loads(row["project_json"]))) for row in rows]
        self._record("list_projects", "", result=str(len(projects)))
        return projects

    def get_project(self, project_id: str) -> ProjectDefinition:
        self._ensure_open()
        row = self._run(_GET_SQL, (project_id,)).fetchone()
        if row is None:
            self._record("get_project", project_id, error="KeyError")
            raise KeyError(f"project not found: {project_id!r}")
        self._record("get_project", project_id)
        return _decode(cast(dict[str, Any], json.loads(row["project_json"])))

    def save_project(self, project: ProjectDefinition) -> None:
        self._ensure_open()
        payload = json.dumps(_encode(project), ensure_ascii=False, sort_keys=True)
        created = project.created_at.value.isoformat()
        updated = project.updated_at.value.isoformat()
        with self._conn:
            self._run(_UPSERT_SQL, (project.id, payload, created, updated))
        self._record("save_project", project.id)

    def delete_project(self, project_id: str) -> None:
        """删除注册行（只此一行；研究数据由调用方先确认无引用，不静默级联）。"""
        self._ensure_open()
        cursor = self._run("DELETE FROM projects WHERE project_id = ?", (project_id,))
        if cursor.rowcount == 0:
            self._record("delete_project", project_id, error="KeyError")
            raise KeyError(f"project not found: {project_id!r}")
        self._conn.commit()
        self._record("delete_project", project_id)
