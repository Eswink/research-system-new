"""PricingTable 文件加载器（adapter 边界：文件 I/O 与 JSON Schema 校验）。

遵循 adapters/contracts/base.py 基建：UTF-8 读取、jsonschema Draft202012
校验、ContractLoadError 错误模型；类型构造委托
`packages.application.cost.pricing.pricing_table_from_dict`。
"""

from __future__ import annotations

from adapters.contracts.base import (
    ContractLoadError,
    load_json_schema,
    load_yaml,
    validate_instance,
)
from packages.application.cost.pricing import PricingTable, pricing_table_from_dict

_PRICING_SCHEMA = "pricing-table.schema.json"


def load_pricing_table(relative_path: str) -> PricingTable:
    """加载并校验一个 pricing 表文件，构造版本化 PricingTable。"""
    data = load_yaml(relative_path)
    validate_instance(load_json_schema(_PRICING_SCHEMA), data, relative_path)
    if not isinstance(data, dict):
        raise ContractLoadError(f"{relative_path} must be a mapping")
    try:
        return pricing_table_from_dict(data)
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractLoadError(f"invalid pricing table at {relative_path}: {exc}") from exc
