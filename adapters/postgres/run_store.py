"""PostgreSQL adapter for RunStore (M14 domain state)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, cast

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env, now_iso
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.protocol_source import ProtocolSource
from packages.domain.run import ResearchRun


class PostgresRunStore(PostgresAdapterBase):
    """PostgreSQL RunStore; list/get/save port: run_id -> JSONB row."""

    def __init__(
        self,
        *,
        dsn: str | None = None,
        connection: Any | None = None,
    ) -> None:
        super().__init__("run_store")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresRunStore requires dsn or connection")
            self._conn = pg_connect(resolved)

    def close(self) -> None:
        if self._owns_connection:
            try:
                self._conn.close()
            except Exception:
                pass
        super().close()

    def list_runs(self, project_id: str | None = None) -> list[ResearchRun]:
        self._ensure_open()
        if project_id is None:
            rows: Any = self._conn.execute(
                "SELECT run_json FROM runs ORDER BY created_at DESC, run_id"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT run_json FROM runs WHERE project_id = %s ORDER BY created_at DESC, run_id",
                (project_id,),
            ).fetchall()
        runs = [_decode(_json_of(row["run_json"])) for row in rows]
        self._record("list_runs", project_id or "", result=str(len(runs)))
        return runs

    def get_run(self, run_id: str) -> ResearchRun:
        self._ensure_open()
        row: Any = self._conn.execute(
            "SELECT run_json FROM runs WHERE run_id = %s", (run_id,)
        ).fetchone()
        if row is None:
            self._record("get_run", run_id, error="KeyError")
            raise KeyError(f"run not found: {run_id!r}")
        self._record("get_run", run_id, result=run_id)
        return _decode(_json_of(row["run_json"]))

    def save_run(self, run: ResearchRun) -> None:
        self._ensure_open()
        payload = _encode(run)
        with self._conn.transaction():
            self._conn.execute(
                "INSERT INTO runs (run_id, project_id, run_json, created_at)"
                " VALUES (%s, %s, %s::jsonb, %s)"
                " ON CONFLICT (run_id) DO UPDATE SET project_id=EXCLUDED.project_id,"
                " run_json=EXCLUDED.run_json, created_at=EXCLUDED.created_at",
                (
                    run.id.value,
                    run.project_id,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("save_run", run.id.value)


def _json_of(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return cast(dict[str, Any], json.loads(value))
    if isinstance(value, dict):
        return value
    return cast(dict[str, Any], json.loads(json.dumps(value)))


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
        created_at=Timestamp(datetime.fromisoformat(record["created_at"])),
        updated_at=Timestamp(datetime.fromisoformat(record["updated_at"])),
    )
