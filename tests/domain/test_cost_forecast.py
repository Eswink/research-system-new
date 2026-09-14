"""成本预测视图域测试（PLAN-20260914-046 WP-A/WP-B）。

纯函数投影的诚实边界：
- 只计本 run 作用域的预留（`run:<id>`），其他 run/phase 预留不混入；
- 预留存在但尚无 usage → NO_DATA（与"已测量为零"区分），remaining None；
- 消耗超出预留 → remaining 为负（如实呈现，不截断为 0）；
- 时长类资源（Decimal quantity）保持小数口径；
- 金额：ACTUAL/ESTIMATED/PARTIALLY_METERED 三态 + 跨币种冲突 + UNKNOWN。
- 预留/消耗单位不同（如 tokens vs seconds）不聚合到同一行。
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from packages.domain.budget import (
    BudgetReservation,
    LedgerCostStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.cost_forecast import (
    ForecastCostStatus,
    ForecastLineStatus,
    ReservationAttribution,
    build_cost_forecast,
)

_AT = datetime(2026, 9, 14, tzinfo=UTC)
_RUN = "run-1"


def _reservation(
    *,
    ref_run: str = _RUN,
    resource_type: ResourceType = ResourceType.MODEL_TOKENS,
    quantity: int = 1000,
    unit: str = "tokens",
    suffix: str = "a",
) -> BudgetReservation:
    return BudgetReservation(
        id=f"budget:{ref_run}:{resource_type.value}:{suffix}",
        scope=f"run:{ref_run}",
        resource_type=resource_type,
        quantity=quantity,
        unit=unit,
    )


def _entry(  # noqa: PLR0913 - 账本条目构造器，参数即字段
    quantity: int | Decimal = 100,
    *,
    resource_type: ResourceType = ResourceType.MODEL_TOKENS,
    unit: str = "tokens",
    currency: str = "USD",
    estimated: int | None = 100,
    actual: int | None = None,
    run_id: str | None = _RUN,
) -> UsageLedgerEntry:
    return UsageLedgerEntry(
        entry_id=f"e-{quantity}-{unit}-{currency}",
        resource_type=resource_type,
        quantity=quantity,
        unit=unit,
        cost_status=LedgerCostStatus.KNOWN,
        source="test",
        occurred_at=_AT,
        estimated_cost_minor=estimated,
        actual_cost_minor=actual,
        currency=currency,
        run_id=run_id,
    )


def test_other_run_reservations_are_rejected_as_caller_error() -> None:
    """归属由调用方决定：把别的 run 的预留传进来是调用方错误，必须报错。"""
    with pytest.raises(ValueError):
        build_cost_forecast(
            _RUN,
            (_reservation(), _reservation(ref_run="run-2", quantity=9999)),
            (),
        )


def test_reserved_without_usage_is_no_data_and_keeps_reserved() -> None:
    view = build_cost_forecast(_RUN, (_reservation(),), ())
    line = view.lines[0]
    assert (line.reserved, line.consumed, line.remaining) == (1000, None, None)
    assert line.data_status is ForecastLineStatus.NO_DATA
    assert view.cost_status is ForecastCostStatus.NO_DATA
    assert view.consumed_cost_minor is None


def test_over_consumption_yields_negative_remaining() -> None:
    view = build_cost_forecast(_RUN, (_reservation(quantity=100),), (_entry(250),))
    assert view.lines[0].remaining == -150


def test_units_are_not_merged() -> None:
    view = build_cost_forecast(
        _RUN,
        (_reservation(), _reservation(unit="seconds", quantity=60, suffix="b")),
        (_entry(100), _entry(30, unit="seconds")),
    )
    assert [(line.unit, line.remaining) for line in view.lines] == [
        ("seconds", 30),
        ("tokens", 900),
    ]


def test_fractional_quantity_keeps_decimal_precision() -> None:
    view = build_cost_forecast(
        _RUN,
        (_reservation(resource_type=ResourceType.GPU_TIME, unit="seconds", quantity=10),),
        (
            _entry(
                Decimal("2.5"),
                resource_type=ResourceType.GPU_TIME,
                unit="seconds",
            ),
        ),
    )
    assert view.lines[0].remaining == Decimal("7.5")


def test_actual_and_estimated_mix_is_partially_metered() -> None:
    view = build_cost_forecast(
        _RUN,
        (),
        (_entry(10, actual=500), _entry(20, estimated=300)),
    )
    assert view.cost_status is ForecastCostStatus.PARTIALLY_METERED
    assert view.consumed_cost_minor == 800


def test_unknown_cost_entry_blocks_the_total() -> None:
    unknown = UsageLedgerEntry(
        entry_id="e-unknown",
        resource_type=ResourceType.MODEL_TOKENS,
        quantity=10,
        unit="tokens",
        cost_status=LedgerCostStatus.UNKNOWN,
        source="test",
        occurred_at=_AT,
        run_id=_RUN,
    )
    view = build_cost_forecast(_RUN, (), (_entry(10), unknown))
    assert view.cost_status is ForecastCostStatus.MONETARY_UNAVAILABLE
    assert view.consumed_cost_minor is None
    assert view.unknown_cost_entries == 1


def test_currency_conflict_is_reported_not_summed() -> None:
    view = build_cost_forecast(_RUN, (), (_entry(10, currency="USD"), _entry(10, currency="EUR")))
    assert view.cost_status is ForecastCostStatus.CURRENCY_CONFLICT
    assert view.consumed_cost_minor is None
    assert view.currency is None


def test_scope_note_states_reserved_only_boundary() -> None:
    view = build_cost_forecast(_RUN, (), ())
    assert view.forecast_scope == "RESERVED_ONLY"
    assert "not extrapolated" in view.scope_note


def test_attribution_defaults_and_flag_propagate() -> None:
    view = build_cost_forecast(
        _RUN,
        (),
        (),
        attribution=ReservationAttribution.NONE,
        unattributed_reserved=3,
    )
    assert view.attribution is ReservationAttribution.NONE
    assert view.unattributed_reserved == 3


def test_phase_scoped_reservations_are_allowed_when_ref_attributed() -> None:
    """正式 preflight 预留作用域是 phase:<id>；ref 解析成功时它们属于本 run。"""
    phase_scoped = BudgetReservation(
        id="budget:execution:wall_clock",
        scope="phase:execution",
        resource_type=ResourceType.WALL_CLOCK,
        quantity=120,
        unit="seconds",
    )
    view = build_cost_forecast(
        _RUN,
        (phase_scoped,),
        (),
        attribution=ReservationAttribution.RESERVATION_REF,
    )
    assert [(line.resource_type.value, line.reserved) for line in view.lines] == [
        ("WALL_CLOCK", 120)
    ]
