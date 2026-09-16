"""SqliteToolProviderRegistry：ToolProviderRegistry Port 的 SQLite 实现（PLAN-20260915-060）。

与 SqliteOpsStore/SqliteAgentStore 同构（JSON-blob-per-row + upsert + KeyError 语义）；
provider 是全局目录（非项目作用域），因此只按 provider_id 建主键，无项目索引。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, parse_iso
from packages.domain.core import Timestamp
from packages.domain.enums import EffectClass, EndpointHealth, ProviderType
from packages.domain.tool_registry import ProviderRegistration

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tool_provider_registrations (
    provider_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    pinned_revision TEXT NOT NULL,
    registration_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS tool_provider_registrations_state
    ON tool_provider_registrations (state, provider_id);
"""


def _iso(value: Timestamp | None) -> str | None:
    return value.value.isoformat() if value is not None else None


def _parsed(text: Any) -> Timestamp | None:
    return Timestamp(value=parse_iso(str(text))) if text else None


def _encode(registration: ProviderRegistration) -> dict[str, Any]:
    return {
        "id": registration.id,
        "kind": registration.kind.value,
        "capabilities": list(registration.capabilities),
        "effect_class": registration.effect_class.value,
        "pinned_revision": registration.pinned_revision,
        "transport": registration.transport,
        "protocol_version": registration.protocol_version,
        "network_domains": list(registration.network_domains),
        "health_check": registration.health_check,
        "state": registration.state,
        "registered_at": _iso(registration.registered_at),
        "updated_at": _iso(registration.updated_at),
        "approved_at": _iso(registration.approved_at),
        "revoked_at": _iso(registration.revoked_at),
        "revoked_reason": registration.revoked_reason,
        "last_health": registration.last_health,
        "health_detail": registration.health_detail,
        "health_checked_at": _iso(registration.health_checked_at),
        "schema_baseline_digest": registration.schema_baseline_digest,
        "last_schema_digest": registration.last_schema_digest,
        "schema_drift": registration.schema_drift,
        "schema_drift_since": _iso(registration.schema_drift_since),
    }


def _decode(raw: dict[str, Any]) -> ProviderRegistration:
    health = raw.get("last_health")
    return ProviderRegistration(
        id=str(raw["id"]),
        kind=ProviderType(str(raw["kind"])),
        capabilities=[str(item) for item in raw.get("capabilities") or []],
        effect_class=EffectClass(str(raw["effect_class"])),
        pinned_revision=str(raw["pinned_revision"]),
        transport=raw.get("transport"),
        protocol_version=raw.get("protocol_version"),
        network_domains=[str(item) for item in raw.get("network_domains") or []],
        health_check=bool(raw.get("health_check", False)),
        state=str(raw["state"]),
        registered_at=_parsed(raw.get("registered_at")),
        updated_at=_parsed(raw.get("updated_at")),
        approved_at=_parsed(raw.get("approved_at")),
        revoked_at=_parsed(raw.get("revoked_at")),
        revoked_reason=raw.get("revoked_reason"),
        last_health=EndpointHealth(str(health)).value if health else None,
        health_detail=raw.get("health_detail"),
        health_checked_at=_parsed(raw.get("health_checked_at")),
        # schema 指纹：旧行没有这些键 ⇒ None/False（诚实：老记录就是"没观测过"）
        schema_baseline_digest=raw.get("schema_baseline_digest"),
        last_schema_digest=raw.get("last_schema_digest"),
        schema_drift=bool(raw.get("schema_drift", False)),
        schema_drift_since=_parsed(raw.get("schema_drift_since")),
    )


class SqliteToolProviderRegistry(SqliteAdapterBase):
    """SQLite 持久化 ToolProviderRegistry；共享连接由 composition root 注入。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("tool_provider_registry")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def list_registrations(self) -> tuple[ProviderRegistration, ...]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT registration_json FROM tool_provider_registrations ORDER BY provider_id"
        ).fetchall()
        return tuple(_decode(json.loads(str(row[0]))) for row in rows)

    def get_registration(self, provider_id: str) -> ProviderRegistration:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT registration_json FROM tool_provider_registrations WHERE provider_id = ?",
            (provider_id,),
        ).fetchone()
        if row is None:
            raise KeyError(provider_id)
        return _decode(json.loads(str(row[0])))

    def save_registration(self, registration: ProviderRegistration) -> None:
        self._ensure_open()
        payload = _encode(registration)
        created = _iso(registration.registered_at) or _iso(registration.updated_at)
        updated = _iso(registration.updated_at) or created
        self._conn.execute(
            """
            INSERT INTO tool_provider_registrations
                (provider_id, state, pinned_revision, registration_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider_id) DO UPDATE SET
                state = excluded.state,
                pinned_revision = excluded.pinned_revision,
                registration_json = excluded.registration_json,
                updated_at = excluded.updated_at
            """,
            (
                registration.id,
                registration.state,
                registration.pinned_revision,
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
                str(created),
                str(updated),
            ),
        )
        self._conn.commit()
        self._record("save_registration", registration.id, result=registration.state)

    def delete_registration(self, provider_id: str) -> None:
        self._ensure_open()
        cursor = self._conn.execute(
            "DELETE FROM tool_provider_registrations WHERE provider_id = ?", (provider_id,)
        )
        if cursor.rowcount == 0:
            self._record("delete_registration", provider_id, error="KeyError")
            raise KeyError(provider_id)
        self._conn.commit()
        self._record("delete_registration", provider_id)
