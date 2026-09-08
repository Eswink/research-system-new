"""从内存 YAML 文本加载 ProtocolDefinition（不经文件系统）。

与 adapters.contracts.protocol_loaders.load_protocol 同一 Schema 与
mapping→Domain 转换；草稿修订（不可变文本）经此进入编译链
（PLAN-20260908-033：已保存修订能进入现有运行链）。
"""

from __future__ import annotations

from typing import Any

import jsonschema  # type: ignore[import-untyped]
import yaml

from adapters.contracts.base import load_json_schema
from adapters.contracts.protocol_loaders import _phase_from_mapping
from packages.domain.core import Version
from packages.domain.protocols import ProtocolDefinition


def load_protocol_from_text(text: str) -> ProtocolDefinition:
    """解析 + Schema 校验 + Domain 构造；失败抛 ContractLoadError 语义的 ValueError。"""
    try:
        data: Any = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid protocol YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("protocol must be a mapping")
    schema = load_json_schema("protocol.schema.json")
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(data),
        key=lambda item: list(item.path),
    )
    if errors:
        rendered = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:5])
        raise ValueError(f"protocol schema invalid: {rendered}")
    try:
        phases = [_phase_from_mapping(item) for item in data["phases"]]
        return ProtocolDefinition(
            id=data["id"],
            version=Version(str(data["version"])),
            phases=phases,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"cannot build protocol from draft revision: {exc}") from exc
