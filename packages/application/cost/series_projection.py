"""跨 run 时序支出投影（G12；纯函数，无 IO）。

诚实语义（与 `daily.py` / `projection.py` 同一口径）：

- 只对**已计价**的天外推：`ACTUAL` / `ESTIMATED` / `ZERO` 且金额非空才进样本；
  `USAGE_UNKNOWN` / `MONETARY_UNAVAILABLE` / `NO_DATA` / `CURRENCY_CONFLICT` /
  `PARTIALLY_METERED` 以及 `mixed_pricing` 的天**一律排除**，并逐日给出原因；
- 不插值、不把缺失当 0（UNKNOWN ≠ 0）；样本跨币种时不给金额（跨币种不求和）；
- 方法与样本量随结果返回：`MEAN_OF_VALUED_DAYS`（已计价日均 × 视野天数），
  注记明确这是"按近期节奏外推"，不是承诺。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from packages.application.cost.amount import CostAmount, CostAmountStatus
from packages.application.cost.daily import DayCost

METHOD_MEAN_OF_VALUED_DAYS = "MEAN_OF_VALUED_DAYS"
MIXED_PRICING_REASON = "MIXED_PRICING"
AMOUNT_MISSING_SUFFIX = ":AMOUNT_MISSING"
MIXED_PRICING_VERSION = "mixed"
NO_VALUED_DAYS_REASON = "NO_VALUED_DAYS: no day in the window has a valued amount"
CURRENCY_CONFLICT_REASON = (
    "CURRENCY_CONFLICT: valued days span multiple currencies; "
    "the series is never summed across them"
)
PROJECTION_NOTE = (
    "projection = mean of the valued daily amounts in the window × horizon; days without a "
    "valued amount are excluded (never interpolated, never treated as 0) and the recent daily "
    "rate is assumed to continue — an extrapolation, not a commitment"
)
MIN_HORIZON_DAYS = 1
MAX_HORIZON_DAYS = 90
VALUED_STATUSES = frozenset({
    CostAmountStatus.ACTUAL,
    CostAmountStatus.ESTIMATED,
    CostAmountStatus.ZERO,
})


@dataclass(frozen=True, slots=True)
class ExcludedDay:
    day: date
    reason: str


@dataclass(frozen=True, slots=True)
class SeriesProjection:
    """已计价日均外推结果；`unavailable_reason` 非空时不给金额。"""

    method: str
    horizon_days: int
    valued_days: int
    excluded_days: tuple[ExcludedDay, ...]
    observed_minor: int | None
    observed_status: str
    currency: str | None
    pricing_version: str | None
    daily_mean_minor: int | None
    projected_minor: int | None
    unavailable_reason: str | None
    note: str = PROJECTION_NOTE


def exclusion_reason(day: DayCost) -> str | None:
    """该日不进样本的原因；None 表示可计价、计入样本。"""
    if day.mixed_pricing:
        return MIXED_PRICING_REASON
    if day.total.status not in VALUED_STATUSES:
        return day.total.status.value
    if day.total.minor_units is None:
        return f"{day.total.status.value}{AMOUNT_MISSING_SUFFIX}"
    return None


def project_series(days: Sequence[DayCost], horizon_days: int) -> SeriesProjection:
    """按已计价日均外推 `horizon_days` 天；排除项逐日返回。"""
    valued: list[CostAmount] = []
    excluded: list[ExcludedDay] = []
    for day in days:
        reason = exclusion_reason(day)
        if reason is None:
            valued.append(day.total)
        else:
            excluded.append(ExcludedDay(day=day.day, reason=reason))
    return _project(valued, tuple(excluded), horizon_days)


def _project(
    valued: list[CostAmount],
    excluded: tuple[ExcludedDay, ...],
    horizon_days: int,
) -> SeriesProjection:
    currencies = {amount.currency for amount in valued}
    if not valued:
        return _unavailable(excluded, horizon_days, NO_VALUED_DAYS_REASON)
    if len(currencies) > 1:
        return _unavailable(
            excluded,
            horizon_days,
            CURRENCY_CONFLICT_REASON,
            status=CostAmountStatus.CURRENCY_CONFLICT,
        )
    total = sum(amount.minor_units or 0 for amount in valued)
    return SeriesProjection(
        method=METHOD_MEAN_OF_VALUED_DAYS,
        horizon_days=horizon_days,
        valued_days=len(valued),
        excluded_days=excluded,
        observed_minor=total,
        observed_status=_observed_status(valued),
        currency=next(iter(currencies)),
        pricing_version=_pricing_version(valued),
        daily_mean_minor=round(total / len(valued)),
        projected_minor=round(total * horizon_days / len(valued)),
        unavailable_reason=None,
    )


def _unavailable(
    excluded: tuple[ExcludedDay, ...],
    horizon_days: int,
    reason: str,
    *,
    status: CostAmountStatus = CostAmountStatus.NO_DATA,
) -> SeriesProjection:
    return SeriesProjection(
        method=METHOD_MEAN_OF_VALUED_DAYS,
        horizon_days=horizon_days,
        valued_days=0,
        excluded_days=excluded,
        observed_minor=None,
        observed_status=status.value,
        currency=None,
        pricing_version=None,
        daily_mean_minor=None,
        projected_minor=None,
        unavailable_reason=reason,
    )


def _observed_status(valued: Sequence[CostAmount]) -> str:
    """全部为实测才敢标 ACTUAL；混入估计值即为 ESTIMATED。"""
    if all(amount.status is CostAmountStatus.ACTUAL for amount in valued):
        return CostAmountStatus.ACTUAL.value
    return CostAmountStatus.ESTIMATED.value


def _pricing_version(valued: Sequence[CostAmount]) -> str:
    versions = {amount.pricing_version for amount in valued}
    if len(versions) == 1:
        return next(iter(versions))
    return MIXED_PRICING_VERSION


__all__ = [
    "AMOUNT_MISSING_SUFFIX",
    "CURRENCY_CONFLICT_REASON",
    "MAX_HORIZON_DAYS",
    "METHOD_MEAN_OF_VALUED_DAYS",
    "MIN_HORIZON_DAYS",
    "MIXED_PRICING_REASON",
    "NO_VALUED_DAYS_REASON",
    "PROJECTION_NOTE",
    "ExcludedDay",
    "SeriesProjection",
    "exclusion_reason",
    "project_series",
]
