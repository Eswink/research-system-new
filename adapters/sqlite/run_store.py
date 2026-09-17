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
from packages.domain.protocol_source import ProtocolBody, ProtocolSource
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
        "protocol_source": _encode_source(run.protocol_source),
        "protocol_body": _encode_body(run.protocol_body),
        "created_at": run.created_at.value.isoformat(),
        "updated_at": run.updated_at.value.isoformat(),
    }


def _encode_source(source: ProtocolSource | None) -> dict[str, Any] | None:
    """装配来源（GOAL-003 cycle 20）：None = 该 run 早于来源登记，显式保留空值。"""
    if source is None:
        return None
    return {
        "protocol_path": source.protocol_path,
        "draft_id": source.draft_id,
        "draft_revision": source.draft_revision,
    }


def _decode_source(record: dict[str, Any] | None) -> ProtocolSource | None:
    if not record:
        return None
    return ProtocolSource(
        protocol_path=record.get("protocol_path"),
        draft_id=record.get("draft_id"),
        draft_revision=record.get("draft_revision"),
    )


def _encode_body(body: ProtocolBody | None) -> dict[str, Any] | None:
    """冻结正文（GOAL-004 cycle 1）：None = 该 run 早于正文冻结，显式保留空值。"""
    if body is None:
        return None
    return {"text": body.text, "digest": str(body.digest)}


def _decode_body(record: dict[str, Any] | None) -> ProtocolBody | None:
    """解码冻结正文；digest 与正文不符时构造即失败（值对象不变量，不静默修）。"""
    if not record:
        return None
    text = record.get("text")
    digest = record.get("digest")
    if not isinstance(text, str) or not isinstance(digest, str):
        return None
    return ProtocolBody(text=text, digest=Digest.parse(digest))


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
        protocol_source=_decode_source(record.get("protocol_source")),
        protocol_body=_decode_body(record.get("protocol_body")),
        created_at=Timestamp(datetime.fromisoformat(record["created_at"])),
        updated_at=Timestamp(datetime.fromisoformat(record["updated_at"])),
    )
