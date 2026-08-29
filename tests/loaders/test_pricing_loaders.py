"""PricingTable loader + pricing digest 测试(M15 WP2)。"""

from __future__ import annotations

import pytest

from adapters.contracts.pricing_loaders import load_pricing_table
from packages.application.cost.pricing import (
    PriceDimension,
    PriceEntry,
    PricingTable,
    pricing_table_from_dict,
    unpriced_table,
)


def test_shipped_pricing_yaml_is_unpriced_v1() -> None:
    table = load_pricing_table("examples/config/pricing.yaml")
    assert table.version == "unpriced_v1"
    assert table.prices == ()
    assert table.currency == "USD"


def test_unpriced_table_every_dimension_has_no_price() -> None:
    table = unpriced_table()
    for dimension in PriceDimension:
        assert table.price_for(dimension, "anything") is None


def test_pricing_digest_is_deterministic_and_content_sensitive() -> None:
    empty = unpriced_table()
    assert empty.pricing_digest() == unpriced_table().pricing_digest()
    priced = pricing_table_from_dict({
        "version": "v2",
        "currency": "USD",
        "effective_from": "2026-08-29",
        "prices": [
            {
                "dimension": "model",
                "resource_key": "relay-model",
                "unit": "tokens",
                "unit_price_minor": 3,
            }
        ],
    })
    assert priced.pricing_digest() != empty.pricing_digest()
    again = pricing_table_from_dict({
        "version": "v2",
        "currency": "USD",
        "effective_from": "2026-08-29",
        "prices": [
            {
                "dimension": "model",
                "resource_key": "relay-model",
                "unit": "tokens",
                "unit_price_minor": 3,
            }
        ],
    })
    assert priced.pricing_digest() == again.pricing_digest()
    assert priced.price_for(PriceDimension.MODEL, "relay-model") is not None


def test_duplicate_price_entries_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate price entry"):
        PricingTable(
            version="v2",
            currency="USD",
            effective_from="2026-08-29",
            prices=(
                _entry("model", "m", 3),
                _entry("model", "m", 5),
            ),
        )


def test_invalid_currency_rejected() -> None:
    with pytest.raises(ValueError, match="currency"):
        PricingTable(version="v2", currency="usd", effective_from="2026-08-29")


def _entry(dimension: str, key: str, minor: int) -> PriceEntry:
    return PriceEntry(
        dimension=PriceDimension(dimension), resource_key=key, unit="tokens", unit_price_minor=minor
    )
