"""Usage Ledger append-only 专项测试。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.domain.budget import (
    BudgetReservation,
    LedgerCostStatus,
    ResourceType,
    UsageLedger,
    UsageLedgerEntry,
)


def _entry(entry_id: str, *, known_cost: int | None = None) -> UsageLedgerEntry:
    return UsageLedgerEntry(
        entry_id=entry_id,
        resource_type=ResourceType.MODEL_TOKENS,
        quantity=100,
        unit="tokens",
        cost_status=LedgerCostStatus.KNOWN if known_cost is not None else LedgerCostStatus.UNKNOWN,
        estimated_cost_minor=known_cost,
        source="relay",
        occurred_at=datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc),
        task_id="task-1",
        agent_id="agent-1",
        model_id="model-alpha",
    )


def test_ledger_entries_are_append_only() -> None:
    ledger = UsageLedger()
    ledger.append(_entry("e1", known_cost=25))
    ledger.append(_entry("e2"))
    assert len(ledger) == 2
    assert ledger.entries()[0].entry_id == "e1"
    assert ledger.entries()[1].entry_id == "e2"


def test_ledger_rejects_duplicate_entry_id() -> None:
    ledger = UsageLedger()
    ledger.append(_entry("e1"))
    with pytest.raises(ValueError, match="duplicate"):
        ledger.append(_entry("e1"))


def test_ledger_entries_are_frozen() -> None:
    ledger = UsageLedger()
    ledger.append(_entry("e1"))
    entries = ledger.entries()
    with pytest.raises(Exception):
        entries[0].quantity = 999  # type: ignore[misc]


def test_ledger_unknown_cost_requires_no_amount() -> None:
    ledger = UsageLedger()
    ledger.append(_entry("e1"))
    assert ledger.entries()[0].cost_status is LedgerCostStatus.UNKNOWN
    assert ledger.entries()[0].estimated_cost_minor is None


def test_ledger_known_cost_requires_amount() -> None:
    with pytest.raises(ValueError):
        UsageLedgerEntry(
            entry_id="bad",
            resource_type=ResourceType.MODEL_COST,
            quantity=1,
            unit="usd-minor",
            cost_status=LedgerCostStatus.KNOWN,
            source="relay",
            occurred_at=datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc),
        )


def test_ledger_negative_quantity_rejected() -> None:
    with pytest.raises(ValueError):
        UsageLedgerEntry(
            entry_id="bad",
            resource_type=ResourceType.MODEL_TOKENS,
            quantity=-1,
            unit="tokens",
            cost_status=LedgerCostStatus.UNKNOWN,
            source="relay",
            occurred_at=datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc),
        )


def test_budget_reservation_requires_quantity_non_negative() -> None:
    with pytest.raises(ValueError):
        BudgetReservation(
            id="r1", scope="run", resource_type=ResourceType.CPU_TIME, quantity=-1, unit="s"
        )
    reservation = BudgetReservation(
        id="r1", scope="run", resource_type=ResourceType.CPU_TIME, quantity=60, unit="s"
    )
    assert reservation.quantity == 60
