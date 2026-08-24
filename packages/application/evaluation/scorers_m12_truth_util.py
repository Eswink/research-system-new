"""M12 independent ground truth scorers 共享工具（M12-R1 WP5）。

纯函数：Decimal 解析 / artifact JSON 读取 / dotted-path 查找。
scorers_m12_truth 拆分出的工具模块（保持模块规模阈值）。
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Mapping

from packages.application.ports.artifact_store import ArtifactStore


def to_decimal(value: object) -> Decimal | None:
    """把任意值转为 Decimal；非数值/非法返回 None（不抛异常）。"""
    try:
        if isinstance(value, bool):
            return None
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def read_artifact_json(artifacts: ArtifactStore, artifact_id: str) -> dict[str, object] | None:
    """读 artifact 内容并解析 JSON；非 JSON 对象返回 None（调用方转 INFRA）。"""
    content = artifacts.get(artifact_id)
    parsed = json.loads(content.decode("utf-8"))
    if not isinstance(parsed, dict):
        return None
    return parsed


def lookup(mapping: Mapping[str, object], path: str) -> object | None:
    """dotted-path 查找；任一层缺失返回 None。"""
    current: object = mapping
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


__all__ = ["lookup", "read_artifact_json", "to_decimal"]
