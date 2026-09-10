"""成本日序列投影测试（PLAN-20260910-037 WP-D）。

不变量：按 UTC 日分桶；同定价表才求和；混合定价天不静默合计；
UNKNOWN 计量保持五状态；窗口过滤；truncated 上限。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from packages.application.cost.amount import CostAmountStatus
from packages.application.cost.daily import MAX_DAYS, daily_series
from packages.application.cost.pricing import PriceDimension, PriceEntry, PricingTable
from packages.domain.budget import (
    LedgerCostStatus,
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)

_NOW = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(day_offset: int, minor: int, **overrides: object) -> UsageLedgerEntry:
    base: dict[str, object] = {
        "entry_id": f"u-{day_offset}-{minor}",
        "resource_type": ResourceType.MODEL_TOKENS,
        "quantity": Decimal(1000),
        "unit": "tokens",
        "cost_status": LedgerCostStatus.KNOWN,
        "source": "model_gateway",
        "occurred_at": _NOW + timedelta(days=day_offset),
        "estimated_cost_minor": minor,
        "currency": "USD",
        "run_id": "r-1",
        "model_id": "model-x",
    }
    base.update(overrides)
    return UsageLedgerEntry(**base)  # type: ignore[arg-type]


def _table(version: str, unit_price: int = 1) -> PricingTable:
    return PricingTable(
        version=version,
        currency="USD",
        effective_from="2026-01-01",
        prices=(
            PriceEntry(
                dimension=PriceDimension.MODEL,
                resource_key="model-x",
                unit="tokens",
                unit_price_minor=unit_price,
            ),
        ),
    )


def test_groups_days_and_sums_within_one_pricing_table() -> None:
    entries = [_entry(0, 100), _entry(0, 250), _entry(1, 50)]
    days, truncated = daily_series(entries, lambda _e: _table("v1"))
    assert truncated is False
    assert [d.day.isoformat() for d in days] == ["2026-09-01", "2026-09-02"]
    first = days[0]
    assert first.total.minor_units == 350
    assert first.total.status is CostAmountStatus.ESTIMATED
    assert first.mixed_pricing is False


def test_mixed_pricing_day_is_not_silently_summed() -> None:
    tables = {"a": _table("v1"), "b": _table("v2")}
    entries = [_entry(0, 100, run_id="a"), _entry(0, 200, run_id="b")]
    days, _ = daily_series(entries, lambda e: tables[str(e.run_id)], _NOW.date(), None)
    day = days[0]
    assert day.mixed_pricing is True
    assert day.total.minor_units is None
    assert day.total.status is CostAmountStatus.PARTIALLY_METERED
    assert [g.pricing.version if g.pricing else "?" for g in day.groups] == ["v1", "v2"]


def test_usage_unknown_entry_never_collapses_in_day_total() -> None:
    unknown = _entry(
        0,
        0,
        entry_id="u-unknown",
        cost_status=LedgerCostStatus.UNKNOWN,
        estimated_cost_minor=None,
        quantity_status=LedgerQuantityStatus.UNKNOWN,
        unavailable_reason="meter unavailable",
    )
    days, _ = daily_series([_entry(0, 100), unknown], lambda _e: _table("v1"))
    day = days[0]
    if day.total.status is CostAmountStatus.PARTIALLY_METERED:
        # 部分计量：仅呈现已计量小计，绝不把 UNKNOWN 当 0
        assert day.total.minor_units == 100
    else:
        assert day.total.status is CostAmountStatus.USAGE_UNKNOWN
        assert day.total.minor_units is None


def test_date_window_filters_days() -> None:
    entries = [_entry(0, 100), _entry(5, 200)]
    days, _ = daily_series(entries, lambda _e: None, _NOW.date(), _NOW.date())
    assert [d.day.day for d in days] == [1]


def test_truncation_reports_without_fabricating() -> None:
    entries = [_entry(i, 10, entry_id=f"u-trunc-{i}") for i in range(MAX_DAYS + 10)]
    days, truncated = daily_series(entries, lambda _e: None)
    assert truncated is True
    assert len(days) == MAX_DAYS


def test_empty_ledger_produces_no_days_never_zero_fill() -> None:
    days, truncated = daily_series([], lambda _e: None)
    assert days == []
    assert truncated is False
