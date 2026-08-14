"""BudgetLedger Port：预算预留、幂等释放与 append-only 用量记账。

职责：reserve（预算预留，返回预留引用）；release（幂等释放预留，
run 收敛到成功/失败/取消后归还配额，BUDGET_QUOTA.md §2）；
record_usage（追加用量条目，重复 entry_id 必须拒绝）；
snapshot（只读视图，供阈值评估）。
非职责：不做 usage 采集（ModelGateway / ExecutionBackend 只上报原始用量，
由 application 归账后调用 record_usage）；不决定预算策略
（domain BudgetPolicy 定义）；不伪造 cost
（成本未知时 LedgerCostStatus.UNKNOWN，docs/architecture/BUDGET_QUOTA.md §4）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from packages.domain.budget import (
    BudgetPolicy,
    BudgetReservation,
    UsageLedgerEntry,
)


@dataclass(frozen=True, slots=True)
class LedgerSnapshot:
    reservations: tuple[BudgetReservation, ...] = field(default_factory=tuple)
    entries: tuple[UsageLedgerEntry, ...] = field(default_factory=tuple)


@runtime_checkable
class BudgetLedger(Protocol):
    """append-only 预算账本；由 adapter/Fake 实现。"""

    def reserve(self, reservations: tuple[BudgetReservation, ...], policy: BudgetPolicy) -> str: ...

    def release(self, reservation_ref: str) -> None: ...

    def record_usage(self, entry: UsageLedgerEntry) -> None: ...

    def snapshot(self) -> LedgerSnapshot: ...
