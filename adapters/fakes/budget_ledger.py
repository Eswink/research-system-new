"""FakeBudgetLedger：append-only 预算账本（复用 domain UsageLedger 语义）。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.budget_ledger import LedgerSnapshot
from packages.application.ports.errors import InvalidInputError
from packages.domain.budget import (
    BudgetPolicy,
    BudgetReservation,
    UsageLedger,
    UsageLedgerEntry,
)
from packages.domain.serialization import digest_of


class FakeBudgetLedger(FakeBase):
    """reserve 返回确定性引用；record_usage 拒绝重复 entry_id（append-only）。"""

    def __init__(self) -> None:
        super().__init__("budget_ledger")
        self._reservations: list[BudgetReservation] = []
        self._ledger = UsageLedger()

    def reserve(self, reservations: tuple[BudgetReservation, ...], policy: BudgetPolicy) -> str:
        self._enter("reserve", policy.id)
        self._reservations.extend(reservations)
        ref = f"budget-reservation:{digest_of((policy, reservations)).hex_value}"
        self._record("reserve", policy.id, result=ref)
        return ref

    def record_usage(self, entry: UsageLedgerEntry) -> None:
        self._enter("record_usage", entry.entry_id)
        try:
            self._ledger.append(entry)
        except ValueError as error:
            self._record("record_usage", entry.entry_id, error="InvalidInputError")
            raise InvalidInputError(str(error)) from error
        self._record("record_usage", entry.entry_id, result="appended")

    def snapshot(self) -> LedgerSnapshot:
        self._enter("snapshot", "")
        self._record("snapshot", "")
        return LedgerSnapshot(
            reservations=tuple(self._reservations),
            entries=self._ledger.entries(),
        )
