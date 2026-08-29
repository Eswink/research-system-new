"""M15 cost 聚合(re-export projection.aggregate_costs;per-dimension 汇总)。"""

from __future__ import annotations

from packages.application.cost.pricing import PricingTable
from packages.application.cost.projection import (
    CostAmount,
    CostAmountStatus,
    DimensionCost,
    aggregate_costs,
    project_dimensions,
)
from packages.domain.budget import UsageLedgerEntry


def total_cost(
    entries: tuple[UsageLedgerEntry, ...],
    pricing: PricingTable | None,
) -> CostAmount:
    """run 级总额:先按维度投影,再聚合(UNKNOWN/不可计价优先暴露)。"""
    return aggregate_costs([dimension.amount for dimension in project_dimensions(entries, pricing)])


def summary_lines(
    entries: tuple[UsageLedgerEntry, ...],
    pricing: PricingTable | None,
) -> tuple[str, ...]:
    """确定性文本摘要(API/Console 只读展示用;浏览器不做任何计算)。"""
    lines: list[str] = []
    for dimension in project_dimensions(entries, pricing):
        amount = dimension.amount
        value = "n/a" if amount.minor_units is None else str(amount.minor_units)
        lines.append(
            f"{dimension.dimension}/{dimension.resource_key}: {amount.status.value} {value}"
            f" {amount.currency} (pricing={amount.pricing_version})"
        )
    return tuple(lines)


__all__ = [
    "CostAmount",
    "CostAmountStatus",
    "DimensionCost",
    "summary_lines",
    "total_cost",
]
