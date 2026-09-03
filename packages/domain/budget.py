"""Budget / Quota / Usage Ledger 域实体定义。

来源：docs/architecture/BUDGET_QUOTA.md、docs/architecture/DOMAIN_MODEL.md。
UsageLedger 是 append-only：追加即锁定，禁止修改或删除历史条目。
成本未知时标记 UNKNOWN，不伪造金额。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Sequence

from packages.domain.core import Timestamp
from packages.domain.enums import BudgetThreshold


class LedgerCostStatus(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"


class LedgerQuantityStatus(StrEnum):
    """M15:quantity 本身的可信度;UNKNOWN 表示"无法计量",绝不解释为 0。"""

    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"


class ResourceType(StrEnum):
    MODEL_TOKENS = "MODEL_TOKENS"
    MODEL_REQUESTS = "MODEL_REQUESTS"
    MODEL_COST = "MODEL_COST"
    # deterministic scorer / evaluation runner 的使用量不属于模型调用；
    # 分离后不会把无 LLM 的 scorer 伪装为 MODEL_REQUESTS。
    EVALUATION_SCORER = "EVALUATION_SCORER"
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
    threshold_ratios: dict[str, Decimal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("budget policy id must not be empty")
        if any(quantity < 0 for quantity in self.hard_limits.values()):
            raise ValueError("budget hard limits must be non-negative")
        if any(not 0 <= ratio <= 1 for ratio in self.threshold_ratios.values()):
            raise ValueError("budget threshold ratios must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class UsageLedgerEntry:
    """append-only 记账条目。"""

    entry_id: str
    resource_type: ResourceType
    # PA-1 W3: duration resources (seconds) may be fractional; token/call
    # counts stay integers by convention (documented at ResourceType).
    quantity: int | float
    unit: str
    cost_status: LedgerCostStatus
    source: str
    occurred_at: datetime
    estimated_cost_minor: int | None = None
    actual_cost_minor: int | None = None
    currency: str = "USD"
    # 直接 run 归属用于独立评测/实验等没有 task 投影的用量；task_id 仍保留
    # 细粒度归属。run 级读取以 `run_id OR task_id∈run_task_ids` 过滤。
    run_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    tool_id: str | None = None
    model_id: str | None = None
    # M15 加性字段(默认保持既有构造与不变量有效;历史行解码为 KNOWN)
    quantity_status: LedgerQuantityStatus = LedgerQuantityStatus.KNOWN
    unavailable_reason: str | None = None
    attempt: int = 1

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
        if self.quantity_status is LedgerQuantityStatus.UNKNOWN and not self.unavailable_reason:
            raise ValueError("UNKNOWN quantity entry must carry unavailable_reason")
        if self.attempt < 1:
            raise ValueError("ledger attempt must be >= 1")


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
