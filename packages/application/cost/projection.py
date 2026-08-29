"""M15 Usage → Cost 投影(纯函数)。

唯一 usage 输入是 `BudgetLedger.snapshot()`(telemetry 绝不作为成本输入);
每个投影金额盖 `pricing_version` + `pricing_digest` 章,价格表后续变更产生
新版本,不能改写历史投影(CostAmount 不可变)。
五状态完备:`unknown` 绝不折叠为 0;未配置价格绝不伪造 0 成本。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from packages.application.cost.pricing import PriceDimension, PricingTable
from packages.domain.budget import (
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)


class CostAmountStatus(StrEnum):
    ACTUAL = "ACTUAL"  # 实测金额(entry.actual_cost_minor)
    ESTIMATED = "ESTIMATED"  # 估计金额(entry.estimated_cost_minor 或 定价表计算)
    MONETARY_UNAVAILABLE = "MONETARY_UNAVAILABLE"  # 未配置价格/单位不匹配 → 不可计价
    USAGE_UNKNOWN = "USAGE_UNKNOWN"  # quantity_status=UNKNOWN → 绝不解释为 0
    ZERO = "ZERO"  # quantity 已知为 0 → 显式零


@dataclass(frozen=True, slots=True)
class CostAmount:
    """一次投影金额;status 完备,不可变,盖章 pricing 快照。"""

    status: CostAmountStatus
    minor_units: int | None
    currency: str
    pricing_version: str
    pricing_digest: str


@dataclass(frozen=True, slots=True)
class DimensionCost:
    """一个 (dimension, resource_key) 分组的投影结果。"""

    dimension: str
    resource_key: str
    amount: CostAmount
    entry_count: int


def _dimension_of(entry: UsageLedgerEntry) -> tuple[PriceDimension, str] | None:
    """entry → 定价维度与 resource key;不可定价维度返回 None。"""
    resource_type = entry.resource_type
    if resource_type in (ResourceType.MODEL_TOKENS, ResourceType.MODEL_REQUESTS):
        return (PriceDimension.MODEL, entry.model_id or "unknown")
    if resource_type in (ResourceType.TOOL_REQUESTS, ResourceType.TOOL_COST):
        return (PriceDimension.TOOL, entry.tool_id or "unknown")
    if resource_type is ResourceType.CPU_TIME:
        return (PriceDimension.EXPERIMENT, entry.task_id or "unknown")
    if resource_type is ResourceType.MODEL_COST:
        return (PriceDimension.EVALUATION, entry.task_id or "unknown")
    return None


def project_entry_cost(
    entry: UsageLedgerEntry,
    pricing: PricingTable | None,
) -> CostAmount:
    """单条 ledger entry → CostAmount(五状态判定树,见模块 docstring)。"""
    version = pricing.version if pricing else "unpriced_v1"
    digest = pricing.pricing_digest() if pricing else unpriced_digest()
    currency = pricing.currency if pricing else "USD"

    if entry.quantity_status is LedgerQuantityStatus.UNKNOWN:
        return CostAmount(CostAmountStatus.USAGE_UNKNOWN, None, currency, version, digest)
    if entry.quantity == 0:
        return CostAmount(CostAmountStatus.ZERO, 0, currency, version, digest)
    if entry.actual_cost_minor is not None:
        return CostAmount(
            CostAmountStatus.ACTUAL, entry.actual_cost_minor, currency, version, digest
        )
    dimension_key = _dimension_of(entry)
    if dimension_key is None or pricing is None:
        return CostAmount(CostAmountStatus.MONETARY_UNAVAILABLE, None, currency, version, digest)
    price = pricing.price_for(*dimension_key)
    if price is None or price.unit != entry.unit:
        return CostAmount(CostAmountStatus.MONETARY_UNAVAILABLE, None, currency, version, digest)
    if entry.estimated_cost_minor is not None:
        return CostAmount(
            CostAmountStatus.ESTIMATED, entry.estimated_cost_minor, currency, version, digest
        )
    return CostAmount(
        CostAmountStatus.ESTIMATED,
        entry.quantity * price.unit_price_minor,
        currency,
        version,
        digest,
    )


def unpriced_digest() -> str:
    """出厂 unpriced_v1 的固定 digest(与 unpriced_table().pricing_digest() 一致)。"""
    from packages.application.cost.pricing import unpriced_table

    return unpriced_table().pricing_digest()


def project_dimensions(
    entries: Iterable[UsageLedgerEntry],
    pricing: PricingTable | None,
) -> tuple[DimensionCost, ...]:
    """按 (dimension, resource_key) 分组投影并聚合(确定性排序)。"""
    grouped: dict[tuple[str, str], list[UsageLedgerEntry]] = {}
    for entry in entries:
        dimension_key = _dimension_of(entry)
        key = (
            (dimension_key[0].value, dimension_key[1])
            if dimension_key is not None
            else ("unpriced", entry.resource_type.value)
        )
        grouped.setdefault(key, []).append(entry)
    results: list[DimensionCost] = []
    for (dimension, resource_key), group in sorted(grouped.items()):
        amounts = [project_entry_cost(entry, pricing) for entry in group]
        results.append(
            DimensionCost(
                dimension=dimension,
                resource_key=resource_key,
                amount=aggregate_costs(amounts),
                entry_count=len(group),
            )
        )
    return tuple(results)


def aggregate_costs(amounts: Iterable[CostAmount]) -> CostAmount:
    """聚合规则:UNKNOWN > 不可计价 > 实测/估计求和 > 显式零(顺序即优先级)。"""
    items = list(amounts)
    if not items:
        first = CostAmount(CostAmountStatus.ZERO, 0, "USD", "unpriced_v1", unpriced_digest())
        return first
    version = items[0].pricing_version
    digest = items[0].pricing_digest
    currency = items[0].currency
    if any(item.status is CostAmountStatus.USAGE_UNKNOWN for item in items):
        return CostAmount(CostAmountStatus.USAGE_UNKNOWN, None, currency, version, digest)
    if any(item.status is CostAmountStatus.MONETARY_UNAVAILABLE for item in items):
        return CostAmount(CostAmountStatus.MONETARY_UNAVAILABLE, None, currency, version, digest)
    if all(item.status is CostAmountStatus.ZERO for item in items):
        return CostAmount(CostAmountStatus.ZERO, 0, currency, version, digest)
    total = sum(
        (item.minor_units or 0)
        for item in items
        if item.status in (CostAmountStatus.ACTUAL, CostAmountStatus.ESTIMATED)
    )
    all_actual = all(item.status is CostAmountStatus.ACTUAL for item in items)
    return CostAmount(
        CostAmountStatus.ACTUAL if all_actual else CostAmountStatus.ESTIMATED,
        total,
        currency,
        version,
        digest,
    )


__all__ = [
    "CostAmount",
    "CostAmountStatus",
    "DimensionCost",
    "aggregate_costs",
    "project_dimensions",
    "project_entry_cost",
]
