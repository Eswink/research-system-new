"""跨 run 成本日序列投影（WP-D；纯函数，无 IO）。

诚实语义：
- 每一天独立按 (pricing_version, pricing_digest, currency) 分组聚合；
  同组才求和，混合定价的天标 mixed_pricing 并给出各定价组小计，
  绝不跨价格表静默求和；
- 无数据的日期不填充（NO_DATA 不是插值），绝不预测；
- UNKNOWN 计量语义沿用 project_entry_cost 五态。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date

from packages.application.cost.aggregation import total_cost
from packages.application.cost.amount import CostAmount, CostAmountStatus
from packages.application.cost.pricing import PricingTable
from packages.domain.budget import LedgerQuantityStatus, UsageLedgerEntry


@dataclass(frozen=True, slots=True)
class PricingGroup:
    pricing: PricingTable | None
    amount: CostAmount
    entry_count: int


@dataclass(frozen=True, slots=True)
class DayCost:
    day: date
    total: CostAmount
    groups: tuple[PricingGroup, ...]
    mixed_pricing: bool


def group_key(pricing: PricingTable | None) -> tuple[str, str]:
    if pricing is None:
        return ("unfrozen", "-")
    return (pricing.version, pricing.pricing_digest())


def bucket_days(entries: Iterable[UsageLedgerEntry]) -> dict[date, list[UsageLedgerEntry]]:
    buckets: dict[date, list[UsageLedgerEntry]] = {}
    for entry in entries:
        buckets.setdefault(entry.occurred_at.date(), []).append(entry)
    return buckets


def _group_amount(items: list[UsageLedgerEntry], pricing: PricingTable | None) -> CostAmount:
    amount = total_cost(tuple(items), pricing)
    return amount


def _day_total(groups: tuple[PricingGroup, ...], any_unknown: bool) -> CostAmount:
    if len(groups) == 1:
        return groups[0].amount
    # 混合定价：不求和；状态如实呈现（含 UNKNOWN 计量时为 USAGE_UNKNOWN 优先）
    blocked = any(
        group.amount.status
        in {
            CostAmountStatus.USAGE_UNKNOWN,
            CostAmountStatus.MONETARY_UNAVAILABLE,
            CostAmountStatus.NO_DATA,
            CostAmountStatus.CURRENCY_CONFLICT,
        }
        for group in groups
    )
    status = (
        CostAmountStatus.USAGE_UNKNOWN
        if any_unknown and blocked
        else CostAmountStatus.PARTIALLY_METERED
    )
    return CostAmount(
        status=status,
        minor_units=None,
        currency=groups[0].amount.currency,
        pricing_version="mixed",
        pricing_digest="mixed",
        calculation_method="mixed-pricing-day:not-summed",
    )


def project_day_cost(
    day: date,
    entries: list[UsageLedgerEntry],
    resolve: Callable[[UsageLedgerEntry], PricingTable | None],
) -> DayCost:
    keyed: dict[tuple[str, str], list[UsageLedgerEntry]] = {}
    resolved: dict[tuple[str, str], PricingTable | None] = {}
    for entry in entries:
        pricing = resolve(entry)
        key = group_key(pricing)
        keyed.setdefault(key, []).append(entry)
        resolved[key] = pricing
    groups = tuple(
        PricingGroup(
            pricing=resolved[key],
            amount=_group_amount(items, resolved[key]),
            entry_count=len(items),
        )
        for key, items in sorted(keyed.items())
    )
    any_unknown = any(entry.quantity_status is LedgerQuantityStatus.UNKNOWN for entry in entries)
    return DayCost(
        day=day,
        total=_day_total(groups, any_unknown),
        groups=groups,
        mixed_pricing=len(groups) > 1,
    )


MAX_DAYS = 400


def daily_series(
    entries: Iterable[UsageLedgerEntry],
    resolve: Callable[[UsageLedgerEntry], PricingTable | None],
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[DayCost], bool]:
    """按 UTC 日投影序列；返回 (days, truncated)。无数据日不填充。"""
    buckets = bucket_days(entries)
    days: list[DayCost] = []
    for day in sorted(buckets):
        if date_from is not None and day < date_from:
            continue
        if date_to is not None and day > date_to:
            continue
        days.append(project_day_cost(day, buckets[day], resolve))
    truncated = len(days) > MAX_DAYS
    return days[:MAX_DAYS], truncated
