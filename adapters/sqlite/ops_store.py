"""SqliteOpsStore：OpsStore Port 的 SQLite 实现（PLAN-20260915-059 WP-A）。

与 SqliteProjectStore/SqliteLibraryStore 同构（JSON-blob-per-row + upsert +
KeyError 语义）；配置面共享连接由 composition root 注入。规则与事故分表，
均按 project_id 建索引（列表查询不做全表读）。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso, parse_iso
from packages.domain.core import Timestamp
from packages.domain.ops_control import AlertRule, Incident
from packages.domain.ops_view import AlertKind, AlertSeverity

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ops_alert_rules (
    rule_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    rule_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ops_alert_rules_project
    ON ops_alert_rules (project_id, created_at, rule_id);
CREATE TABLE IF NOT EXISTS ops_incidents (
    incident_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    run_id TEXT,
    status TEXT NOT NULL,
    incident_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ops_incidents_project
    ON ops_incidents (project_id, created_at, incident_id);
"""


def _iso(value: Timestamp | None) -> str:
    return value.value.isoformat() if value is not None else now_iso(None)


def _rule_encode(rule: AlertRule) -> dict[str, Any]:
    return {
        "id": rule.id,
        "project_id": rule.project_id,
        "name": rule.name,
        "kind": rule.kind.value if rule.kind is not None else None,
        "max_severity": rule.max_severity.value if rule.max_severity is not None else None,
        "enabled": rule.enabled,
        "created_at": rule.created_at.value.isoformat() if rule.created_at is not None else None,
        "updated_at": rule.updated_at.value.isoformat() if rule.updated_at is not None else None,
    }


def _rule_decode(payload: dict[str, Any]) -> AlertRule:
    kind = payload.get("kind")
    severity = payload.get("max_severity")
    created = payload.get("created_at")
    updated = payload.get("updated_at")
    return AlertRule(
        id=payload["id"],
        project_id=payload["project_id"],
        name=payload["name"],
        kind=AlertKind(kind) if kind is not None else None,
        max_severity=AlertSeverity(severity) if severity is not None else None,
        enabled=bool(payload.get("enabled", True)),
        created_at=Timestamp(parse_iso(created)) if created is not None else None,
        updated_at=Timestamp(parse_iso(updated)) if updated is not None else None,
    )


def _incident_encode(incident: Incident) -> dict[str, Any]:
    def iso(value: Timestamp | None) -> str | None:
        return value.value.isoformat() if value is not None else None

    return {
        "id": incident.id,
        "project_id": incident.project_id,
        "title": incident.title,
        "severity": incident.severity.value,
        "status": incident.status,
        "run_id": incident.run_id,
        "assignee": incident.assignee,
        "resolution": incident.resolution,
        "opened_at": iso(incident.opened_at),
        "updated_at": iso(incident.updated_at),
        "closed_at": iso(incident.closed_at),
    }


def _incident_decode(payload: dict[str, Any]) -> Incident:
    def ts(key: str) -> Timestamp | None:
        raw = payload.get(key)
        return Timestamp(parse_iso(raw)) if raw is not None else None

    return Incident(
        id=payload["id"],
        project_id=payload["project_id"],
        title=payload["title"],
        severity=AlertSeverity(payload["severity"]),
        status=payload["status"],
        run_id=payload.get("run_id"),
        assignee=payload.get("assignee"),
        resolution=payload.get("resolution"),
        opened_at=ts("opened_at"),
        updated_at=ts("updated_at"),
        closed_at=ts("closed_at"),
    )


class SqliteOpsStore(SqliteAdapterBase):
    """SQLite 持久化 OpsStore（规则 CRUD + 事故登记/更新）。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("ops_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def list_rules(self, project_id: str) -> list[AlertRule]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT rule_json FROM ops_alert_rules"
            " WHERE project_id = ? ORDER BY created_at, rule_id",
            (project_id,),
        ).fetchall()
        rules = [_rule_decode(json.loads(row["rule_json"])) for row in rows]
        self._record("list_rules", project_id, result=str(len(rules)))
        return rules

    def get_rule(self, rule_id: str) -> AlertRule:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT rule_json FROM ops_alert_rules WHERE rule_id = ?", (rule_id,)
        ).fetchone()
        if row is None:
            self._record("get_rule", rule_id, error="KeyError")
            raise KeyError(f"alert rule not found: {rule_id!r}")
        self._record("get_rule", rule_id, result=rule_id)
        return _rule_decode(json.loads(row["rule_json"]))

    def save_rule(self, rule: AlertRule) -> None:
        self._ensure_open()
        created = _iso(rule.created_at)
        updated = _iso(rule.updated_at)
        payload = json.dumps(_rule_encode(rule), ensure_ascii=False, sort_keys=True)
        with self._conn:
            self._conn.execute(
                "INSERT INTO ops_alert_rules"
                " (rule_id, project_id, rule_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT (rule_id) DO UPDATE SET"
                " rule_json = excluded.rule_json, updated_at = excluded.updated_at",
                (rule.id, rule.project_id, payload, created, updated),
            )
        self._record("save_rule", rule.id)

    def delete_rule(self, rule_id: str) -> None:
        self._ensure_open()
        with self._conn:
            cursor = self._conn.execute("DELETE FROM ops_alert_rules WHERE rule_id = ?", (rule_id,))
        if cursor.rowcount == 0:
            self._record("delete_rule", rule_id, error="KeyError")
            raise KeyError(f"alert rule not found: {rule_id!r}")
        self._record("delete_rule", rule_id)

    def list_incidents(self, project_id: str) -> list[Incident]:
        self._ensure_open()
        rows = self._conn.execute(
            "SELECT incident_json FROM ops_incidents"
            " WHERE project_id = ? ORDER BY created_at, incident_id",
            (project_id,),
        ).fetchall()
        incidents = [_incident_decode(json.loads(row["incident_json"])) for row in rows]
        self._record("list_incidents", project_id, result=str(len(incidents)))
        return incidents

    def get_incident(self, incident_id: str) -> Incident:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT incident_json FROM ops_incidents WHERE incident_id = ?", (incident_id,)
        ).fetchone()
        if row is None:
            self._record("get_incident", incident_id, error="KeyError")
            raise KeyError(f"incident not found: {incident_id!r}")
        self._record("get_incident", incident_id, result=incident_id)
        return _incident_decode(json.loads(row["incident_json"]))

    def save_incident(self, incident: Incident) -> None:
        self._ensure_open()
        opened = _iso(incident.opened_at)
        updated = _iso(incident.updated_at)
        payload = json.dumps(_incident_encode(incident), ensure_ascii=False, sort_keys=True)
        with self._conn:
            self._conn.execute(
                "INSERT INTO ops_incidents"
                " (incident_id, project_id, run_id, status, incident_json, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT (incident_id) DO UPDATE SET"
                " status = excluded.status, incident_json = excluded.incident_json,"
                " updated_at = excluded.updated_at",
                (
                    incident.id,
                    incident.project_id,
                    incident.run_id,
                    incident.status,
                    payload,
                    opened,
                    updated,
                ),
            )
        self._record("save_incident", incident.id, result=incident.status)
