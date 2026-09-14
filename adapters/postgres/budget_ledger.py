"""PG budget_ledger: mirrors sqlite/budget_ledger.py."""

from __future__ import annotations

import json
from typing import Any, cast

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env, now_iso
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


class PostgresBudgetLedger(PostgresAdapterBase):
    def __init__(
        self,
        *,
        dsn: str | None = None,
        connection: Any | None = None,
    ) -> None:
        super().__init__("budget_ledger")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresBudgetLedger requires dsn or connection")
            self._conn = pg_connect(resolved)

    def close(self) -> None:
        if self._owns_connection:
            try:
                self._conn.close()
            except Exception:
                pass
        super().close()

    def reserve(self, reservations: tuple[BudgetReservation, ...], policy: BudgetPolicy) -> str:
        self._record("reserve", policy.id)
        ref = f"budget-reservation:{digest_of((policy, reservations)).hex_value}"
        with self._conn.transaction():
            self._conn.execute(
                "INSERT INTO budget_reservations (reservation_ref, reservations_json, policy_json,"
                " released, created_at) VALUES (%s, %s::jsonb, %s::jsonb, FALSE, %s)"
                " ON CONFLICT (reservation_ref) DO UPDATE SET"
                " reservations_json=EXCLUDED.reservations_json,"
                " policy_json=EXCLUDED.policy_json, created_at=EXCLUDED.created_at",
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
        self._record("release", reservation_ref)
        with self._conn.transaction():
            self._conn.execute(
                "UPDATE budget_reservations SET released=TRUE WHERE reservation_ref=%s"
                " AND released=FALSE",
                (reservation_ref,),
            )
        self._record("release", reservation_ref, result="released")

    def record_usage(self, entry: UsageLedgerEntry) -> None:
        self._record("record_usage", entry.entry_id)
        try:
            with self._conn.transaction():
                self._conn.execute(
                    "INSERT INTO budget_usage_entries (entry_id, entry_json, recorded_at)"
                    " VALUES (%s, %s::jsonb, %s)",
                    (
                        entry.entry_id,
                        json.dumps(_encode_entry(entry), ensure_ascii=False, sort_keys=True),
                        now_iso(None),
                    ),
                )
        except Exception as exc:
            from psycopg.errors import UniqueViolation

            if isinstance(exc, UniqueViolation):
                self._record("record_usage", entry.entry_id, error="InvalidInputError")
                raise InvalidInputError(f"duplicate usage entry: {entry.entry_id}") from exc
            raise
        self._record("record_usage", entry.entry_id, result="appended")

    def record_usage_batch(self, entries: tuple[UsageLedgerEntry, ...]) -> tuple[str, ...]:
        """原子追加一批 usage；已存在 id 是 at-least-once 重放 no-op。"""
        self._ensure_open()
        self._record("record_usage_batch", str(len(entries)))
        ids = [entry.entry_id for entry in entries]
        if len(ids) != len(set(ids)):
            raise InvalidInputError("duplicate usage entry within batch")
        inserted: list[str] = []
        with self._conn.transaction():
            for entry in entries:
                row: Any = self._conn.execute(
                    "INSERT INTO budget_usage_entries (entry_id, entry_json, recorded_at)"
                    " VALUES (%s, %s::jsonb, %s)"
                    " ON CONFLICT (entry_id) DO NOTHING RETURNING entry_id",
                    (
                        entry.entry_id,
                        json.dumps(_encode_entry(entry), ensure_ascii=False, sort_keys=True),
                        now_iso(None),
                    ),
                ).fetchone()
                if row is not None:
                    inserted.append(str(row["entry_id"]))
        result = tuple(inserted)
        self._record("record_usage_batch", str(len(entries)), result=str(len(result)))
        return result

    def snapshot(self) -> LedgerSnapshot:
        self._record("snapshot", "")
        reservation_rows: Any = self._conn.execute(
            "SELECT reservation_ref, reservations_json FROM budget_reservations"
            " WHERE released=FALSE"
        ).fetchall()
        entry_rows: Any = self._conn.execute(
            "SELECT entry_json FROM budget_usage_entries ORDER BY recorded_at, entry_id"
        ).fetchall()
        by_ref = {
            str(row["reservation_ref"]): tuple(
                _decode_reservation(item) for item in _as_list(row["reservations_json"])
            )
            for row in reservation_rows
        }
        reservations = tuple(item for items in by_ref.values() for item in items)
        entries = tuple(_decode_entry(_json_of(row["entry_json"])) for row in entry_rows)
        self._record("snapshot", "", result=f"{len(reservations)}/{len(entries)}")
        return LedgerSnapshot(
            reservations=reservations,
            entries=entries,
            reservations_by_ref=by_ref,
        )


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, str):
        return cast(list[Any], json.loads(value))
    if isinstance(value, list):
        return value
    return []


def _json_of(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return cast(dict[str, Any], json.loads(value))
    if isinstance(value, dict):
        return value
    return cast(dict[str, Any], json.loads(json.dumps(value)))


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
    return {"id": policy.id, "hard_limits": dict(policy.hard_limits)}


def _encode_entry(entry: UsageLedgerEntry) -> dict[str, Any]:
    """全保真编码:M15 起不再丢弃 currency/agent_id/tool_id/source 等字段。"""
    # PA-1 W3: Decimal quantities (fractional duration seconds) serialize
    # canonical-safe as strings; integral Decimals stay ints.
    from decimal import Decimal

    raw_quantity: object = entry.quantity
    quantity: object = raw_quantity
    if isinstance(quantity, Decimal):
        quantity = str(quantity) if quantity != quantity.to_integral_value() else int(quantity)
    return {
        "entry_id": entry.entry_id,
        "resource_type": entry.resource_type.value,
        "quantity": quantity,
        "unit": entry.unit,
        "cost_status": entry.cost_status.value,
        "source": entry.source,
        "occurred_at": entry.occurred_at.isoformat(),
        "estimated_cost_minor": entry.estimated_cost_minor,
        "actual_cost_minor": entry.actual_cost_minor,
        "model_id": entry.model_id,
        "run_id": entry.run_id,
        "task_id": entry.task_id,
        "currency": entry.currency,
        "agent_id": entry.agent_id,
        "tool_id": entry.tool_id,
        "quantity_status": entry.quantity_status.value,
        "unavailable_reason": entry.unavailable_reason,
        "attempt": entry.attempt,
    }


def _decode_entry(record: dict[str, Any]) -> UsageLedgerEntry:
    from datetime import datetime
    from decimal import Decimal

    quantity = record["quantity"]
    if isinstance(quantity, str):
        quantity = Decimal(quantity)
    return UsageLedgerEntry(
        entry_id=record["entry_id"],
        resource_type=ResourceType(record["resource_type"]),
        quantity=quantity,
        unit=record["unit"],
        cost_status=LedgerCostStatus(record["cost_status"]),
        source=record.get("source", "unknown"),
        occurred_at=datetime.fromisoformat(record["occurred_at"]),
        estimated_cost_minor=record.get("estimated_cost_minor"),
        actual_cost_minor=record.get("actual_cost_minor"),
        model_id=record.get("model_id"),
        run_id=record.get("run_id"),
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
