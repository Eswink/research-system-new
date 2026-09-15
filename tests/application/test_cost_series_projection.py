"""跨 run 时序支出投影测试（G12 / GOAL-20260915-002 EC-02）。

不变量：只对已计价的天外推；其余逐日给出排除原因（不插值、不当 0）；
样本跨币种不给金额；`observed_status` 只在全为实测时才是 ACTUAL；
投影 = 已计价日均 × 视野天数（整数分，不引入浮点漂移）。
"""

from __future__ import annotations

from datetime import date

from packages.application.cost.amount import CostAmount, CostAmountStatus
from packages.application.cost.daily import DayCost
from packages.application.cost.series_projection import (
    CURRENCY_CONFLICT_REASON,
    METHOD_MEAN_OF_VALUED_DAYS,
    MIXED_PRICING_REASON,
    NO_VALUED_DAYS_REASON,
    project_series,
)

_DAY = date(2026, 9, 1)


def _amount(
    status: CostAmountStatus,
    minor: int | None,
    *,
    currency: str = "USD",
    version: str = "v1",
) -> CostAmount:
    return CostAmount(
        status=status,
        minor_units=minor,
        currency=currency,
        pricing_version=version,
        pricing_digest=f"digest-{version}",
    )


def _day(
    offset: int,
    amount: CostAmount,
    *,
    mixed: bool = False,
) -> DayCost:
    return DayCost(
        day=date(2026, 9, 1 + offset),
        total=amount,
        groups=(),
        mixed_pricing=mixed,
    )


def test_projects_mean_of_valued_days_over_horizon() -> None:
    days = [
        _day(0, _amount(CostAmountStatus.ACTUAL, 1000)),
        _day(1, _amount(CostAmountStatus.ACTUAL, 3000)),
    ]

    projection = project_series(days, horizon_days=7)

    assert projection.method == METHOD_MEAN_OF_VALUED_DAYS
    assert projection.valued_days == 2
    assert projection.excluded_days == ()
    assert projection.observed_minor == 4000
    assert projection.observed_status == "ACTUAL"
    assert projection.daily_mean_minor == 2000
    assert projection.projected_minor == 14000
    assert projection.currency == "USD"
    assert projection.unavailable_reason is None


def test_unvalued_days_are_excluded_with_reason_and_never_zero() -> None:
    days = [
        _day(0, _amount(CostAmountStatus.ACTUAL, 1000)),
        _day(1, _amount(CostAmountStatus.USAGE_UNKNOWN, None)),
        _day(2, _amount(CostAmountStatus.MONETARY_UNAVAILABLE, None)),
        _day(3, _amount(CostAmountStatus.PARTIALLY_METERED, None)),
        _day(4, _amount(CostAmountStatus.ACTUAL, 500), mixed=True),
    ]

    projection = project_series(days, horizon_days=10)

    assert projection.valued_days == 1
    assert projection.observed_minor == 1000
    assert projection.projected_minor == 10000
    assert [(item.day.day, item.reason) for item in projection.excluded_days] == [
        (2, "USAGE_UNKNOWN"),
        (3, "MONETARY_UNAVAILABLE"),
        (4, "PARTIALLY_METERED"),
        (5, MIXED_PRICING_REASON),
    ]


def test_zero_day_counts_as_explicit_zero_not_missing() -> None:
    days = [
        _day(0, _amount(CostAmountStatus.ZERO, 0)),
        _day(1, _amount(CostAmountStatus.ACTUAL, 600)),
    ]

    projection = project_series(days, horizon_days=2)

    assert projection.valued_days == 2
    assert projection.observed_minor == 600
    assert projection.projected_minor == 600


def test_multi_currency_sample_refuses_to_sum() -> None:
    days = [
        _day(0, _amount(CostAmountStatus.ACTUAL, 1000, currency="USD")),
        _day(1, _amount(CostAmountStatus.ACTUAL, 1000, currency="JPY")),
    ]

    projection = project_series(days, horizon_days=3)

    assert projection.observed_minor is None
    assert projection.projected_minor is None
    assert projection.observed_status == "CURRENCY_CONFLICT"
    assert projection.unavailable_reason == CURRENCY_CONFLICT_REASON


def test_no_valued_day_yields_no_amount() -> None:
    projection = project_series(
        [_day(0, _amount(CostAmountStatus.USAGE_UNKNOWN, None))], horizon_days=5
    )

    assert projection.valued_days == 0
    assert projection.projected_minor is None
    assert projection.observed_status == "NO_DATA"
    assert projection.unavailable_reason == NO_VALUED_DAYS_REASON
    assert len(projection.excluded_days) == 1

    empty = project_series([], horizon_days=5)
    assert empty.valued_days == 0
    assert empty.unavailable_reason == NO_VALUED_DAYS_REASON


def test_estimated_sample_is_not_labelled_actual_and_mixed_pricing_version_is_marked() -> None:
    days = [
        _day(0, _amount(CostAmountStatus.ESTIMATED, 1000, version="v1")),
        _day(1, _amount(CostAmountStatus.ESTIMATED, 1000, version="v2")),
    ]

    projection = project_series(days, horizon_days=1)

    assert projection.observed_status == "ESTIMATED"
    assert projection.pricing_version == "mixed"
    assert projection.projected_minor == 1000

    single = project_series([days[0]], horizon_days=1)
    assert single.pricing_version == "v1"


def test_valued_status_without_amount_is_excluded_not_summed() -> None:
    days = [_day(0, _amount(CostAmountStatus.ESTIMATED, None))]

    projection = project_series(days, horizon_days=1)

    assert projection.valued_days == 0
    assert projection.excluded_days[0].reason == "ESTIMATED:AMOUNT_MISSING"
