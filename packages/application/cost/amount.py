"""M15 CostAmount 值对象与投影戳记（金额/盖章语义）。

从 projection.py 拆出以遵守 300 行上限；CostAmount 不可变且随投影金额
携带 pricing 快照章（version/digest/effective_from/calculation_method）——
价格表后续变更产生新版本，不能改写历史投影。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from packages.application.cost.pricing import CALCULATION_METHOD, PricingTable, unpriced_table


class CostAmountStatus(StrEnum):
    ACTUAL = "ACTUAL"  # 实测金额(entry.actual_cost_minor)
    ESTIMATED = "ESTIMATED"  # 估计金额(entry.estimated_cost_minor 或 定价表计算)
    MONETARY_UNAVAILABLE = "MONETARY_UNAVAILABLE"  # 未配置价格/单位不匹配 → 不可计价
    USAGE_UNKNOWN = "USAGE_UNKNOWN"  # quantity_status=UNKNOWN → 绝不解释为 0
    ZERO = "ZERO"  # quantity 已知为 0 → 显式零
    NO_DATA = "NO_DATA"  # 没有任何 usage entry → 与"已测量为零"严格区分
    CURRENCY_CONFLICT = "CURRENCY_CONFLICT"  # 跨币种,不做隐式换算
    # 同一分组既有可计价金额又有 UNKNOWN / 未定价事实：保留可计价小计，
    # 同时明确总额不完整，不能把未知一票否决成无任何信息。
    PARTIALLY_METERED = "PARTIALLY_METERED"


@dataclass(frozen=True, slots=True)
class CostAmount:
    """一次投影金额;status 完备,不可变,盖章 pricing 快照。

    `effective_from` 与 `calculation_method` 随金额一起返回:复审指出它们此前
    只活在被加载的价表里,读者无法判断这笔钱是按哪套规则、哪个生效时间算的。
    """

    status: CostAmountStatus
    minor_units: int | None
    currency: str
    pricing_version: str
    pricing_digest: str
    effective_from: str = ""
    calculation_method: str = CALCULATION_METHOD


@dataclass(frozen=True, slots=True)
class _PricingStamp:
    """投影盖章:版本、摘要、币种、生效时间、计算方法。"""

    version: str
    digest: str
    currency: str
    effective_from: str
    calculation_method: str


def _stamp_of(pricing: PricingTable | None) -> _PricingStamp:
    table = pricing if pricing is not None else unpriced_table()
    return _PricingStamp(
        version=table.version,
        digest=table.pricing_digest(),
        currency=table.currency,
        effective_from=table.effective_from,
        calculation_method=table.calculation_method,
    )


def _amount(
    status: CostAmountStatus,
    minor_units: int | None,
    stamp: _PricingStamp,
    *,
    currency: str | None = None,
) -> CostAmount:
    return CostAmount(
        status=status,
        minor_units=minor_units,
        currency=currency or stamp.currency,
        pricing_version=stamp.version,
        pricing_digest=stamp.digest,
        effective_from=stamp.effective_from,
        calculation_method=stamp.calculation_method,
    )


__all__ = [
    "CostAmount",
    "CostAmountStatus",
    "_PricingStamp",
    "_amount",
    "_stamp_of",
]
