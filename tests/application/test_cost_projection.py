"""M15 cost projection 对账测试(DoD 9-12)。

- 五状态完备:unknown 绝不折叠为 0;未定价绝不伪造 0;
- pricing version/digest 盖章;历史稳定性(改价不改写历史投影);
- retry/failure/cancel/re-evaluation/重复回放不 under/double-count、不伪造;
- 确定性 scorer 不产生 model 成本。
"""

from __future__ import annotations

from datetime import datetime, timezone

from adapters.sqlite.budget_ledger import SqliteBudgetLedger
from packages.application.cost.aggregation import summary_lines, total_cost
from packages.application.cost.pricing import (
    PriceDimension,
    PriceEntry,
    PricingTable,
    pricing_table_from_dict,
    unpriced_table,
)
from packages.application.cost.projection import (
    CostAmountStatus,
    project_dimensions,
    project_entry_cost,
)
from packages.domain.budget import (
    LedgerCostStatus,
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)

_UTC = timezone.utc
_NOW = datetime(2026, 8, 29, 12, 0, 0, tzinfo=_UTC)


def _entry(**overrides: object) -> UsageLedgerEntry:
    base: dict[str, object] = {
        "entry_id": "entry-1",
        "resource_type": ResourceType.MODEL_TOKENS,
        "quantity": 100,
        "unit": "tokens",
        "cost_status": LedgerCostStatus.KNOWN,
        "estimated_cost_minor": 7,
        "source": "llm",
        "occurred_at": _NOW,
        "model_id": "relay-model",
    }
    base.update(overrides)
    return UsageLedgerEntry(**base)  # type: ignore[arg-type]


def _priced_table(minor: int = 2) -> PricingTable:
    return PricingTable(
        version="v1",
        currency="USD",
        effective_from="2026-08-29",
        prices=(
            PriceEntry(
                dimension=PriceDimension.MODEL,
                resource_key="relay-model",
                unit="tokens",
                unit_price_minor=minor,
            ),
        ),
    )


def test_usage_unknown_never_collapses_to_zero() -> None:
    amount = project_entry_cost(
        _entry(
            quantity=0,
            quantity_status=LedgerQuantityStatus.UNKNOWN,
            unavailable_reason="streaming carried no usage chunk",
        ),
        _priced_table(),
    )
    assert amount.status is CostAmountStatus.USAGE_UNKNOWN
    assert amount.minor_units is None


def test_unpriced_model_is_monetary_unavailable_not_zero() -> None:
    amount = project_entry_cost(_entry(), unpriced_table())
    assert amount.status is CostAmountStatus.MONETARY_UNAVAILABLE
    assert amount.minor_units is None


def test_known_zero_quantity_is_explicit_zero() -> None:
    amount = project_entry_cost(_entry(quantity=0), _priced_table())
    assert amount.status is CostAmountStatus.ZERO
    assert amount.minor_units == 0


def test_priced_estimate_and_actual_precedence() -> None:
    estimated = project_entry_cost(
        _entry(cost_status=LedgerCostStatus.UNKNOWN, estimated_cost_minor=None),
        _priced_table(minor=3),
    )
    assert estimated.status is CostAmountStatus.ESTIMATED
    assert estimated.minor_units == 300  # 100 tokens × 3 minor
    actual = project_entry_cost(_entry(actual_cost_minor=55), _priced_table(minor=3))
    assert actual.status is CostAmountStatus.ACTUAL
    assert actual.minor_units == 55


def test_projection_is_stamped_with_pricing_version_and_digest() -> None:
    amount = project_entry_cost(_entry(), _priced_table())
    table = _priced_table()
    assert amount.pricing_version == table.version
    assert amount.pricing_digest == table.pricing_digest()


def test_price_change_cannot_mutate_historical_projection() -> None:
    v1 = project_entry_cost(
        _entry(cost_status=LedgerCostStatus.UNKNOWN, estimated_cost_minor=None),
        _priced_table(minor=2),
    )
    v2_table = pricing_table_from_dict({
        "version": "v2",
        "currency": "USD",
        "effective_from": "2026-09-01",
        "prices": [
            {
                "dimension": "model",
                "resource_key": "relay-model",
                "unit": "tokens",
                "unit_price_minor": 9,
            }
        ],
    })
    v2 = project_entry_cost(
        _entry(cost_status=LedgerCostStatus.UNKNOWN, estimated_cost_minor=None),
        v2_table,
    )
    assert v2.minor_units == 900
    assert v1.minor_units == 200
    assert v1.pricing_version == "v1" and v1.pricing_digest == _priced_table().pricing_digest()
    assert v2.pricing_version == "v2" and v2.pricing_digest != v1.pricing_digest


def test_retry_appends_without_double_counting_success() -> None:
    """retry:attempt 作用域条目按次计;同一 attempt 的重复回放被 ledger 去重。"""
    ledger = SqliteBudgetLedger(":memory:")
    unmeasured = {
        "cost_status": LedgerCostStatus.UNKNOWN,
        "estimated_cost_minor": None,
    }
    first = _entry(entry_id="usage:run:turns", quantity=10, **unmeasured)
    replayed = _entry(entry_id="usage:run:turns", quantity=10, **unmeasured)
    second_attempt = _entry(entry_id="usage:run:turns:attempt-2", quantity=15, **unmeasured)
    ledger.record_usage(first)
    import pytest

    from packages.application.ports.errors import InvalidInputError

    with pytest.raises(InvalidInputError):
        ledger.record_usage(replayed)  # 同 entry_id 被 ledger 拒绝(不 double-count)
    ledger.record_usage(second_attempt)  # 新 attempt 追加(不碰撞)
    entries = ledger.snapshot().entries
    assert len(entries) == 2
    dimensions = project_dimensions(entries, _priced_table())
    assert dimensions[0].entry_count == 2
    assert dimensions[0].amount.minor_units == 25 * 2


def test_failure_and_cancellation_never_undercount_to_zero() -> None:
    entries = (
        _entry(
            entry_id="e-known",
            quantity=50,
        ),
        _entry(
            entry_id="e-failed",
            quantity=0,
            quantity_status=LedgerQuantityStatus.UNKNOWN,
            unavailable_reason="attempt outcome not fully observable",
            model_id="relay-model",
        ),
    )
    total = total_cost(entries, _priced_table())
    assert total.status is CostAmountStatus.USAGE_UNKNOWN
    assert total.minor_units is None


def test_re_evaluation_appends_scoped_entry() -> None:
    ledger = SqliteBudgetLedger(":memory:")
    ledger.record_usage(
        _entry(entry_id="usage:run:eval:r1", resource_type=ResourceType.MODEL_REQUESTS, quantity=4)
    )
    ledger.record_usage(
        _entry(
            entry_id="usage:run:eval:r1:attempt-2",
            resource_type=ResourceType.MODEL_REQUESTS,
            quantity=4,
        )
    )
    assert len(ledger.snapshot().entries) == 2
    total = total_cost(tuple(ledger.snapshot().entries), unpriced_table())
    assert total.status is CostAmountStatus.MONETARY_UNAVAILABLE


def test_deterministic_scorers_produce_no_model_cost() -> None:
    """无 model_id 的 MODEL_REQUESTS 条目归 unknown key;无定价 → 不可计价,非 0。"""
    entry = _entry(
        entry_id="eval-1",
        resource_type=ResourceType.MODEL_REQUESTS,
        quantity=6,
        model_id=None,
    )
    amount = project_entry_cost(entry, _priced_table())
    assert amount.status is CostAmountStatus.MONETARY_UNAVAILABLE
    assert amount.minor_units is None


def test_summary_lines_are_deterministic() -> None:
    entries = (_entry(quantity=10),)
    assert summary_lines(entries, _priced_table()) == summary_lines(entries, _priced_table())
    assert summary_lines(entries, _priced_table())[0].startswith("model/relay-model: ESTIMATED")
