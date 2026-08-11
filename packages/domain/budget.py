"""Budget / Quota / Usage Ledger 域实体定义。

来源：docs/architecture/BUDGET_QUOTA.md、docs/architecture/DOMAIN_MODEL.md。
UsageLedger 是 append-only：追加即锁定，禁止修改或删除历史条目。
成本未知时标记 UNKNOWN，不伪造金额。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Sequence

from packages.domain.core import Timestamp
from packages.domain.enums import BudgetThreshold


class LedgerCostStatus(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"


class ResourceType(StrEnum):
    MODEL_TOKENS = "MODEL_TOKENS"
    MODEL_REQUESTS = "MODEL_REQUESTS"
    MODEL_COST = "MODEL_COST"
    TOOL_REQUESTS = "TOOL_REQUESTS"
    TOOL_COST = "TOOL_COST"
    CPU_TIME = "CPU_TIME"
    GPU_TIME = "GPU_TIME"
    MEMORY = "MEMORY"
    STORAGE = "STORAGE"
    NETWORK = "NETWORK"
    WALL_CLOCK = "WALL_CLOCK"
    AGENT_TURNS = "AGENT_TURNS"
    PARALLELISM = "PARALLELISM"


@dataclass(frozen=True, slots=True)
class BudgetReservation:
    id: str
    scope: str
    resource_type: ResourceType
    quantity: int
    unit: str
    reserved_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("reservation id must not be empty")
        if self.quantity < 0:
            raise ValueError("reservation quantity must be non-negative")
        if not self.unit:
            raise ValueError("reservation unit must not be empty")


@dataclass(frozen=True, slots=True)
class BudgetPolicy:
    id: str
    thresholds: dict[ResourceType, BudgetThreshold] = field(default_factory=dict)
    hard_limits: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("budget policy id must not be empty")


@dataclass(frozen=True, slots=True)
class UsageLedgerEntry:
    """append-only 记账条目。"""

    entry_id: str
    resource_type: ResourceType
    quantity: int
    unit: str
    cost_status: LedgerCostStatus
    source: str
    occurred_at: datetime
    estimated_cost_minor: int | None = None
    actual_cost_minor: int | None = None
    currency: str = "USD"
    task_id: str | None = None
    agent_id: str | None = None
    tool_id: str | None = None
    model_id: str | None = None

    def __post_init__(self) -> None:
        if not self.entry_id:
            raise ValueError("ledger entry id must not be empty")
        if self.quantity < 0:
            raise ValueError("ledger quantity must be non-negative")
        if not self.unit:
            raise ValueError("ledger unit must not be empty")
        if not self.source:
            raise ValueError("ledger source must not be empty")
        Timestamp(self.occurred_at)
        if self.cost_status is LedgerCostStatus.KNOWN and self.estimated_cost_minor is None:
            raise ValueError("KNOWN cost entry must carry estimated_cost_minor")


class UsageLedger:
    """append-only Usage Ledger：entries 一旦追加即不可修改。"""

    __slots__ = ("_entries",)

    def __init__(self, entries: Sequence[UsageLedgerEntry] = ()) -> None:
        self._entries: list[UsageLedgerEntry] = list(entries)

    def append(self, entry: UsageLedgerEntry) -> None:
        if any(existing.entry_id == entry.entry_id for existing in self._entries):
            raise ValueError(f"duplicate ledger entry: {entry.entry_id}")
        self._entries.append(entry)

    def entries(self) -> tuple[UsageLedgerEntry, ...]:
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
