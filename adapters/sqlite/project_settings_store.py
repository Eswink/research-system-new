"""SqliteProjectSettingsStore：项目设置记录的 SQLite 持久化（M13-R1；PLAN-041 项目化）。

按 project_id 精确读取（get(project_id)）；保存按项目 upsert。examples 回退
只属于控制面合并层（catalog_merge，且仅默认 example-project 允许），store
本身不隐式播种。项目删除不提供（归档即终态，M18 deferred 不含租户语义）。
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

    def get(self, project_id: str) -> ProjectSettings | None:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT settings_json FROM project_settings WHERE project_id = ?", (project_id,)
        ).fetchone()
        if row is None:
            self._record("get", project_id, result="None")
            return None
        decoded = json.loads(row["settings_json"])
        self._record("get", project_id, result=decoded.get("project_id", ""))
        return ProjectSettings.from_mapping(
            decoded["project_id"],
            {
                "team_template": decoded["team_template_id"],
                "default_model_profile": decoded.get("default_model_profile_id"),
                "budget": decoded["budget_policy_id"],
                "workspace_backend": decoded["workspace_backend"],
                "compute_profile": decoded.get("compute_profile"),
                "policy": decoded.get("policy_id", "project-policy"),
                "protocol": decoded.get("reference_protocol"),
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
            "reference_protocol": settings.reference_protocol,
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
