"""M15 PricingTable:版本化定价快照(纯 Domain-adjacent 应用层类型)。

- 厂商价格永远不进入 Domain、不硬编码进仓库(BUDGET_QUOTA.md);
- `pricing_digest()` 对内容确定性(canonical JSON),价格表任何变更产生新
  digest → 投影历史不可被后续改价改写;
- `unpriced` 构造:零价格条目 → 每个维度 MONETARY_UNAVAILABLE(默认姿态)。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any

from packages.domain.serialization import canonical_json_bytes


class PriceDimension(StrEnum):
    MODEL = "model"
    TOOL = "tool"
    EXPERIMENT = "experiment"
    EVALUATION = "evaluation"


CALCULATION_METHOD = "unit_price_minor_per_unit"


@dataclass(frozen=True, slots=True)
class PriceEntry:
    """dimension+resource_key → 每 unit 的 minor 单位单价(整数,无浮点)。"""

    dimension: PriceDimension
    resource_key: str
    unit: str
    unit_price_minor: int

    def __post_init__(self) -> None:
        if not self.resource_key:
            raise ValueError("price resource_key must not be empty")
        if not self.unit:
            raise ValueError("price unit must not be empty")
        if self.unit_price_minor < 0:
            raise ValueError("unit_price_minor must be non-negative")


@dataclass(frozen=True, slots=True)
class PricingTable:
    """一次定价快照;digest 参与投影盖章(version + digest 一起)。"""

    version: str
    currency: str
    effective_from: str
    calculation_method: str = CALCULATION_METHOD
    prices: tuple[PriceEntry, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("pricing version must not be empty")
        if len(self.currency) != 3 or not self.currency.isupper() or not self.currency.isalpha():
            raise ValueError("pricing currency must be an ISO-4217 alpha-3 code")
        if self.calculation_method != CALCULATION_METHOD:
            raise ValueError(f"unsupported calculation_method: {self.calculation_method}")
        seen: set[tuple[PriceDimension, str]] = set()
        for entry in self.prices:
            key = (entry.dimension, entry.resource_key)
            if key in seen:
                raise ValueError(f"duplicate price entry for {key}")
            seen.add(key)

    def pricing_digest(self) -> str:
        """确定性内容摘要(canonical JSON over prices + metadata)。"""
        payload = {
            "version": self.version,
            "currency": self.currency,
            "effective_from": self.effective_from,
            "calculation_method": self.calculation_method,
            "prices": [
                {
                    "dimension": entry.dimension.value,
                    "resource_key": entry.resource_key,
                    "unit": entry.unit,
                    "unit_price_minor": entry.unit_price_minor,
                }
                for entry in self.prices
            ],
        }
        return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()

    def price_for(self, dimension: PriceDimension, resource_key: str) -> PriceEntry | None:
        """未配置价格 → None(调用方必须落到 MONETARY_UNAVAILABLE,不得记 0)。"""
        for entry in self.prices:
            if entry.dimension is dimension and entry.resource_key == resource_key:
                return entry
        return None

    def unit_ratio(self, entry: PriceEntry) -> Decimal:
        return Decimal(entry.unit_price_minor)


def unpriced_table() -> PricingTable:
    """出厂默认:零价格条目(unpriced_v1)。"""
    return PricingTable(
        version="unpriced_v1",
        currency="USD",
        effective_from="1970-01-01",
        prices=(),
    )


def pricing_table_from_dict(data: dict[str, Any]) -> PricingTable:
    """schema 校验后的 dict → PricingTable(loader 调用;格式错误抛 ValueError)。"""
    prices = tuple(
        PriceEntry(
            dimension=PriceDimension(item["dimension"]),
            resource_key=item["resource_key"],
            unit=item["unit"],
            unit_price_minor=item["unit_price_minor"],
        )
        for item in data.get("prices", [])
    )
    return PricingTable(
        version=str(data["version"]),
        currency=str(data["currency"]),
        effective_from=str(data["effective_from"]),
        calculation_method=str(data.get("calculation_method", CALCULATION_METHOD)),
        prices=prices,
    )


__all__ = [
    "CALCULATION_METHOD",
    "PriceDimension",
    "PriceEntry",
    "PricingTable",
    "pricing_table_from_dict",
    "unpriced_table",
]
