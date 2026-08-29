"""SqliteBudgetLedger：预算预留与用量账本的 SQLite 持久化（M13-R1 WP-M1）。

与 FakeBudgetLedger 同语义（reserve 确定性引用 / release 幂等 /
record_usage 拒绝重复 entry_id / snapshot 只读），持久化到两张表：
reservations（预留行 + 释放标记）与 usage_entries（append-only）。
M14 PostgreSQL canonical state 落地后走同一 BudgetLedger Port。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from packages.application.ports.budget_ledger import LedgerSnapshot
from packages.application.ports.errors import InvalidInputError
from packages.domain.budget import (
    BudgetPolicy,
    BudgetReservation,
    LedgerCostStatus,
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.serialization import digest_of

_SCHEMA = """
CREATE TABLE IF NOT EXISTS budget_reservations (
    reservation_ref TEXT PRIMARY KEY,
    reservations_json TEXT NOT NULL,
    policy_json TEXT NOT NULL,
    released INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS budget_usage_entries (
    entry_id TEXT PRIMARY KEY,
    entry_json TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
"""


class SqliteBudgetLedger(SqliteAdapterBase):
    """SQLite 持久化 BudgetLedger；reserve/release/record_usage/snapshot。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("budget_ledger")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def reserve(self, reservations: tuple[BudgetReservation, ...], policy: BudgetPolicy) -> str:
        self._record("reserve", policy.id)
        ref = f"budget-reservation:{digest_of((policy, reservations)).hex_value}"
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO budget_reservations"
                " (reservation_ref, reservations_json, policy_json, released, created_at)"
                " VALUES (?, ?, ?, 0, ?)",
                (
                    ref,
                    json.dumps(
                        [_encode_reservation(item) for item in reservations],
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    json.dumps(_encode_policy(policy), ensure_ascii=False, sort_keys=True),
                    now_iso(None),
                ),
            )
        self._record("reserve", policy.id, result=ref)
        return ref

    def release(self, reservation_ref: str) -> None:
        """幂等释放：未知/已释放的引用为 no-op（at-least-once 收敛语义）。"""
        self._record("release", reservation_ref)
        with self._conn:
            cursor = self._conn.execute(
                "UPDATE budget_reservations SET released = 1 WHERE reservation_ref = ?"
                " AND released = 0",
                (reservation_ref,),
            )
        released = cursor.rowcount
        self._record("release", reservation_ref, result=f"released {released}")

    def record_usage(self, entry: UsageLedgerEntry) -> None:
        self._record("record_usage", entry.entry_id)
        with self._conn:
            try:
                self._conn.execute(
                    "INSERT INTO budget_usage_entries (entry_id, entry_json, recorded_at)"
                    " VALUES (?, ?, ?)",
                    (
                        entry.entry_id,
                        json.dumps(_encode_entry(entry), ensure_ascii=False, sort_keys=True),
                        now_iso(None),
                    ),
                )
            except sqlite3.IntegrityError as error:
                self._record("record_usage", entry.entry_id, error="InvalidInputError")
                raise InvalidInputError(f"duplicate usage entry: {entry.entry_id}") from error
        self._record("record_usage", entry.entry_id, result="appended")

    def snapshot(self) -> LedgerSnapshot:
        self._record("snapshot", "")
        with self._conn:
            reservation_rows = self._conn.execute(
                "SELECT reservations_json FROM budget_reservations WHERE released = 0"
            ).fetchall()
            entry_rows = self._conn.execute(
                "SELECT entry_json FROM budget_usage_entries ORDER BY recorded_at, entry_id"
            ).fetchall()
        reservations = tuple(
            _decode_reservation(item)
            for row in reservation_rows
            for item in json.loads(row["reservations_json"])
        )
        entries = tuple(_decode_entry(json.loads(row["entry_json"])) for row in entry_rows)
        self._record("snapshot", "", result=f"{len(reservations)}/{len(entries)}")
        return LedgerSnapshot(reservations=reservations, entries=entries)


def _encode_reservation(item: BudgetReservation) -> dict[str, Any]:
    return {
        "id": item.id,
        "scope": item.scope,
        "resource_type": item.resource_type.value,
        "quantity": item.quantity,
        "unit": item.unit,
    }


def _decode_reservation(record: dict[str, Any]) -> BudgetReservation:
    return BudgetReservation(
        id=record["id"],
        scope=record["scope"],
        resource_type=ResourceType(record["resource_type"]),
        quantity=record["quantity"],
        unit=record["unit"],
    )


def _encode_policy(policy: BudgetPolicy) -> dict[str, Any]:
    return {
        "id": policy.id,
        "hard_limits": dict(policy.hard_limits),
    }


def _encode_entry(entry: UsageLedgerEntry) -> dict[str, Any]:
    """全保真编码:M15 起不再丢弃 currency/agent_id/tool_id/source 等字段。"""
    return {
        "entry_id": entry.entry_id,
        "resource_type": entry.resource_type.value,
        "quantity": entry.quantity,
        "unit": entry.unit,
        "cost_status": entry.cost_status.value,
        "source": entry.source,
        "occurred_at": entry.occurred_at.isoformat(),
        "estimated_cost_minor": entry.estimated_cost_minor,
        "actual_cost_minor": entry.actual_cost_minor,
        "model_id": entry.model_id,
        "task_id": entry.task_id,
        "currency": entry.currency,
        "agent_id": entry.agent_id,
        "tool_id": entry.tool_id,
        "quantity_status": entry.quantity_status.value,
        "unavailable_reason": entry.unavailable_reason,
        "attempt": entry.attempt,
    }


def _decode_entry(record: dict[str, Any]) -> UsageLedgerEntry:
    """全保真解码;历史行缺新字段时解码为 KNOWN/attempt=1(不重解释历史数字)。"""
    return UsageLedgerEntry(
        entry_id=record["entry_id"],
        resource_type=ResourceType(record["resource_type"]),
        quantity=record["quantity"],
        unit=record["unit"],
        cost_status=LedgerCostStatus(record["cost_status"]),
        source=record.get("source", "unknown"),
        occurred_at=datetime.fromisoformat(record["occurred_at"]),
        estimated_cost_minor=record.get("estimated_cost_minor"),
        actual_cost_minor=record.get("actual_cost_minor"),
        model_id=record.get("model_id"),
        task_id=record.get("task_id"),
        currency=record.get("currency", "USD"),
        agent_id=record.get("agent_id"),
        tool_id=record.get("tool_id"),
        quantity_status=_quantity_status(record),
        unavailable_reason=record.get("unavailable_reason"),
        attempt=record.get("attempt", 1),
    )


def _quantity_status(record: dict[str, Any]) -> LedgerQuantityStatus:
    """历史行无 quantity_status 字段 → KNOWN(不重解释历史数字)。"""
    value = record.get("quantity_status")
    if value is None:
        return LedgerQuantityStatus.KNOWN
    return LedgerQuantityStatus(value)
