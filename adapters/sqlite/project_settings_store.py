"""SqliteProjectSettingsStore：项目设置单条记录的 SQLite 持久化（M13-R1）。

单条记录（settings）语义：覆盖 wizard 默认项目之后的设置；
M13 控制面只有 example-project 一个项目（多项目为 M14/M18 范围）。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from packages.application.ports import ProjectSettings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS project_settings (
    project_id TEXT PRIMARY KEY,
    settings_json TEXT NOT NULL,
    saved_at TEXT NOT NULL
);
"""


class SqliteProjectSettingsStore(SqliteAdapterBase):
    """SQLite 持久化 ProjectSettingsStore；get/save + close 语义。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("project_settings_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def get(self) -> ProjectSettings | None:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT settings_json FROM project_settings ORDER BY saved_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            self._record("get", "", result="None")
            return None
        decoded = json.loads(row["settings_json"])
        self._record("get", "", result=decoded.get("project_id", ""))
        return ProjectSettings.from_mapping(
            decoded["project_id"],
            {
                "team_template": decoded["team_template_id"],
                "default_model_profile": decoded.get("default_model_profile_id"),
                "budget": decoded["budget_policy_id"],
                "workspace_backend": decoded["workspace_backend"],
                "compute_profile": decoded.get("compute_profile"),
                "policy": decoded.get("policy_id", "project-policy"),
            },
        )

    def save(self, settings: ProjectSettings) -> None:
        self._ensure_open()
        payload = {
            "project_id": settings.project_id,
            "team_template_id": settings.team_template_id,
            "default_model_profile_id": settings.default_model_profile_id,
            "budget_policy_id": settings.budget_policy_id,
            "workspace_backend": settings.workspace_backend,
            "compute_profile": settings.compute_profile,
            "policy_id": settings.policy_id,
        }
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO project_settings (project_id, settings_json, saved_at)"
                " VALUES (?, ?, ?)",
                (
                    settings.project_id,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("save", settings.project_id)
