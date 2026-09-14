"""SqliteRunStore：ResearchRun 状态的 SQLite 持久化（M13-R1 WP-M1）。

M13-R1 修复：run_registry（内存 dict）在 API 重启后丢失全部 run 状态，
且 /runs/{id}/events 被内存注册表 gate 挡住（事件已持久仍 404）。
本实现与 SqliteModelStore 同构（JSON-blob-per-row），延续 M13 控制面
配置存储模式；M14 PostgreSQL canonical state 落地后走同一 RunStore Port。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import RUNS_SCHEMA_SQL, connect, now_iso
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.run import ResearchRun

# 与 db.SCHEMA_SQL 同源：`runs` 是共享 canonical 表（控制面写入、派发面只读 state）。
_SCHEMA = RUNS_SCHEMA_SQL


class SqliteRunStore(SqliteAdapterBase):
    """SQLite 持久化 RunStore；list/get/save + close 语义。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("run_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def list_runs(self, project_id: str | None = None) -> list[ResearchRun]:
        self._ensure_open()
        if project_id is None:
            rows = self._conn.execute(
                "SELECT run_json FROM runs ORDER BY created_at DESC, run_id"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT run_json FROM runs WHERE project_id = ? ORDER BY created_at DESC, run_id",
                (project_id,),
            ).fetchall()
        runs = [_decode(json.loads(row["run_json"])) for row in rows]
        self._record("list_runs", project_id or "", result=str(len(runs)))
        return runs

    def get_run(self, run_id: str) -> ResearchRun:
        self._ensure_open()
        row = self._conn.execute("SELECT run_json FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            self._record("get_run", run_id, error="KeyError")
            raise KeyError(f"run not found: {run_id!r}")
        self._record("get_run", run_id, result=run_id)
        return _decode(json.loads(row["run_json"]))

    def save_run(self, run: ResearchRun) -> None:
        self._ensure_open()
        payload = _encode(run)
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO runs (run_id, project_id, run_json, created_at)"
                " VALUES (?, ?, ?, ?)",
                (
                    run.id.value,
                    run.project_id,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("save_run", run.id.value)


def _encode(run: ResearchRun) -> dict[str, Any]:
    return {
        "id": run.id.value,
        "project_id": run.project_id,
        "protocol_id": run.protocol_id,
        "state": run.state,
        "manifest_digest": str(run.manifest_digest) if run.manifest_digest else None,
        "manifest_semantic_digest": (
            str(run.manifest_semantic_digest) if run.manifest_semantic_digest else None
        ),
        "pricing_version": run.pricing_version,
        "pricing_digest": run.pricing_digest,
        "created_at": run.created_at.value.isoformat(),
        "updated_at": run.updated_at.value.isoformat(),
    }


def _decode(record: dict[str, Any]) -> ResearchRun:
    return ResearchRun(
        id=ID(record["id"]),
        project_id=record["project_id"],
        protocol_id=record["protocol_id"],
        state=record["state"],
        manifest_digest=Digest.parse(record["manifest_digest"])
        if record.get("manifest_digest")
        else None,
        manifest_semantic_digest=Digest.parse(record["manifest_semantic_digest"])
        if record.get("manifest_semantic_digest")
        else None,
        pricing_version=record.get("pricing_version"),
        pricing_digest=record.get("pricing_digest"),
        created_at=Timestamp(datetime.fromisoformat(record["created_at"])),
        updated_at=Timestamp(datetime.fromisoformat(record["updated_at"])),
    )
