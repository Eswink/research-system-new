"""SqliteApprovalStore：待决审批的 SQLite 持久化（M13-R1 WP-M1）。

实现 ApprovalStore Port（不依赖 services.api entry 层）：API 重启后
待决审批不丢失。ApprovalRecord 为不可变值对象，version 变化经 replace
写覆盖行。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from packages.application.ports.approval_store import ApprovalRecord, ApprovalSpec

_SCHEMA = """
CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    approval_json TEXT NOT NULL,
    saved_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_approvals_run ON approvals(run_id);
"""


class SqliteApprovalStore(SqliteAdapterBase):
    """SQLite 持久化审批存储（ApprovalStore Port 实现）。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("approval_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def register(self, spec: ApprovalSpec) -> ApprovalRecord:
        import uuid

        approval = ApprovalRecord(
            id=uuid.uuid4().hex,
            run_id=spec.run_id,
            action=spec.action,
            risk=spec.risk,
            context=spec.context,
            policy_source=spec.policy_source,
            requested_event_id=spec.requested_event_id,
            version="",
        )
        self.replace(approval)
        return approval

    def list_pending(self) -> tuple[ApprovalRecord, ...]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT approval_json FROM approvals ORDER BY saved_at, approval_id"
        ).fetchall()
        records = tuple(_decode(json.loads(row["approval_json"])) for row in rows)
        pending = tuple(record for record in records if record.status == "PENDING")
        self._record("list_pending", "", result=str(len(pending)))
        return pending

    def list_for_run(self, run_id: str) -> tuple[ApprovalRecord, ...]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT approval_json FROM approvals WHERE run_id = ? ORDER BY saved_at, approval_id",
            (run_id,),
        ).fetchall()
        records = tuple(_decode(json.loads(row["approval_json"])) for row in rows)
        self._record("list_for_run", run_id, result=str(len(records)))
        return records

    def get(self, approval_id: str) -> ApprovalRecord | None:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT approval_json FROM approvals WHERE approval_id = ?", (approval_id,)
        ).fetchone()
        if row is None:
            self._record("get", approval_id, result="None")
            return None
        self._record("get", approval_id, result=approval_id)
        return _decode(json.loads(row["approval_json"]))

    def replace(self, approval: ApprovalRecord) -> None:
        self._ensure_open()
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO approvals (approval_id, run_id, approval_json, saved_at)"
                " VALUES (?, ?, ?, ?)",
                (
                    approval.id,
                    approval.run_id,
                    json.dumps(_encode(approval), ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("replace", approval.id)


def _encode(approval: ApprovalRecord) -> dict[str, Any]:
    return {
        "id": approval.id,
        "run_id": approval.run_id,
        "action": approval.action,
        "risk": approval.risk,
        "context": approval.context,
        "policy_source": approval.policy_source,
        "requested_event_id": approval.requested_event_id,
        "status": approval.status,
        "version": approval.version,
    }


def _decode(record: dict[str, Any]) -> ApprovalRecord:
    return ApprovalRecord(
        id=record["id"],
        run_id=record["run_id"],
        action=record["action"],
        risk=record["risk"],
        context=record["context"],
        policy_source=record["policy_source"],
        requested_event_id=record["requested_event_id"],
        status=record.get("status", "PENDING"),
        version=record.get("version", ""),
    )
