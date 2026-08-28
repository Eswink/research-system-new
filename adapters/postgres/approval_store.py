"""PG approval_store: mirrors sqlite/approval_store.py with PG types."""

from __future__ import annotations

import json
import uuid
from typing import Any, cast

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env, now_iso
from packages.application.ports.approval_store import ApprovalRecord, ApprovalSpec


class PostgresApprovalStore(PostgresAdapterBase):
    def __init__(
        self,
        *,
        dsn: str | None = None,
        connection: Any | None = None,
    ) -> None:
        super().__init__("approval_store")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresApprovalStore requires dsn or connection")
            self._conn = pg_connect(resolved)

    def close(self) -> None:
        if self._owns_connection:
            try:
                self._conn.close()
            except Exception:
                pass
        super().close()

    def register(self, spec: ApprovalSpec) -> ApprovalRecord:
        self._ensure_open()
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
        rows: Any = self._conn.execute(
            "SELECT approval_json FROM approvals ORDER BY saved_at, approval_id"
        ).fetchall()
        records = tuple(_decode(_json_of(row["approval_json"])) for row in rows)
        pending = tuple(record for record in records if record.status == "PENDING")
        self._record("list_pending", "", result=str(len(pending)))
        return pending

    def list_for_run(self, run_id: str) -> tuple[ApprovalRecord, ...]:
        self._ensure_open()
        rows: Any = self._conn.execute(
            "SELECT approval_json FROM approvals WHERE run_id = %s ORDER BY saved_at, approval_id",
            (run_id,),
        ).fetchall()
        records = tuple(_decode(_json_of(row["approval_json"])) for row in rows)
        self._record("list_for_run", run_id, result=str(len(records)))
        return records

    def get(self, approval_id: str) -> ApprovalRecord | None:
        self._ensure_open()
        row: Any = self._conn.execute(
            "SELECT approval_json FROM approvals WHERE approval_id = %s", (approval_id,)
        ).fetchone()
        if row is None:
            self._record("get", approval_id, result="None")
            return None
        self._record("get", approval_id, result=approval_id)
        return _decode(_json_of(row["approval_json"]))

    def replace(self, approval: ApprovalRecord) -> None:
        self._ensure_open()
        with self._conn.transaction():
            self._conn.execute(
                "INSERT INTO approvals (approval_id, run_id, approval_json, saved_at)"
                " VALUES (%s, %s, %s::jsonb, %s)"
                " ON CONFLICT (approval_id) DO UPDATE SET run_id=EXCLUDED.run_id,"
                " approval_json=EXCLUDED.approval_json, saved_at=EXCLUDED.saved_at",
                (
                    approval.id,
                    approval.run_id,
                    json.dumps(_encode(approval), ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("replace", approval.id)


def _json_of(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return cast(dict[str, Any], json.loads(value))
    if isinstance(value, dict):
        return value
    return cast(dict[str, Any], json.loads(json.dumps(value)))


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
