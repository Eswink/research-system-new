"""M15 WP3a 定价冻结回归(BLOCKER-6)。

Run A 冻结 v1 并持久化快照；随后当前价表变成 v2。重读 Run A 的成本投影
必须仍按 v1 计价。这个测试刻意不比较两个临时 CostAmount，而是经过
Run → PricingSnapshotStore → resolve_run_pricing 的真实历史读取路径。
"""

from __future__ import annotations

from datetime import datetime, timezone

from adapters.sqlite.pricing_snapshot_store import SqlitePricingSnapshotStore
from packages.application.cost.pricing import PriceDimension, PriceEntry, PricingTable
from packages.application.cost.projection import (
    CostAmountStatus,
    project_entry_cost,
    resolve_run_pricing,
)
from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.core import ID
from packages.domain.run import ResearchRun

_NOW = datetime(2026, 8, 30, tzinfo=timezone.utc)


def _table(version: str, price: int) -> PricingTable:
    return PricingTable(
        version=version,
        currency="USD",
        effective_from="2026-08-30",
        prices=(
            PriceEntry(
                dimension=PriceDimension.MODEL,
                resource_key="relay-model",
                unit="tokens",
                unit_price_minor=price,
            ),
        ),
    )


def _entry() -> UsageLedgerEntry:
    return UsageLedgerEntry(
        entry_id="usage:run-a:model",
        resource_type=ResourceType.MODEL_TOKENS,
        quantity=100,
        unit="tokens",
        cost_status=LedgerCostStatus.UNKNOWN,
        source="test",
        occurred_at=_NOW,
        model_id="relay-model",
    )


def test_price_change_cannot_mutate_persisted_run_a_projection() -> None:
    store = SqlitePricingSnapshotStore(":memory:")
    v1 = _table("v1", 2)
    store.put(v1)
    run_a = ResearchRun(
        id=ID.generate(),
        project_id="project",
        protocol_id="protocol",
        pricing_version=v1.version,
        pricing_digest=v1.pricing_digest(),
    )

    # The live table changes after Run A was frozen; only v2 describes new runs.
    v2 = _table("v2", 9)
    store.put(v2)

    historical = resolve_run_pricing(run_a, store, current=v2)
    amount = project_entry_cost(_entry(), historical.pricing)
    assert historical.frozen is True
    assert historical.degraded_reason is None
    assert historical.pricing_version == "v1"
    assert amount.status is CostAmountStatus.ESTIMATED
    assert amount.minor_units == 200
    assert amount.pricing_version == "v1"
    assert amount.pricing_digest == v1.pricing_digest()


def test_legacy_run_is_explicitly_unfrozen_and_never_uses_current_table() -> None:
    resolution = resolve_run_pricing(
        ResearchRun(id=ID.generate(), project_id="project", protocol_id="protocol"),
        SqlitePricingSnapshotStore(":memory:"),
        current=_table("v2", 9),
    )
    amount = project_entry_cost(_entry(), resolution.pricing)
    assert resolution.frozen is False
    assert resolution.degraded_reason == "pricing not frozen for this run"
    assert amount.status is CostAmountStatus.MONETARY_UNAVAILABLE
    assert amount.minor_units is None


def test_missing_frozen_snapshot_is_explicitly_degraded_not_repriced() -> None:
    missing = ResearchRun(
        id=ID.generate(),
        project_id="project",
        protocol_id="protocol",
        pricing_version="v1",
        pricing_digest="a" * 64,
    )
    resolution = resolve_run_pricing(missing, SqlitePricingSnapshotStore(":memory:"))
    assert resolution.frozen is True
    assert resolution.pricing is None
    assert resolution.degraded_reason is not None
    assert "missing from store" in resolution.degraded_reason
