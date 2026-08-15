"""schema_validity v1.0.0：自研最小结构校验器（无第三方依赖）。

约束：只支持显式子集（object/array/string/number/integer/boolean/null +
properties/required/items）；未知 schema 关键字 fail-closed；NaN/Infinity
拒绝进入 number 判定。为保持单文件行数阈值独立成模块。
"""

from __future__ import annotations

from numbers import Number
from typing import Mapping

from packages.application.evaluation.scorer_types import (
    ScorerContext,
    make_finding,
)
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding

SCHEMA_TYPES = ("object", "array", "string", "number", "integer", "boolean", "null")

_SCHEMA_SCORER_ID = "schema_validity"


def _check_type(value: object, type_name: str) -> bool:
    if type_name == "object":
        return isinstance(value, Mapping)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "null":
        return value is None
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        if isinstance(value, bool):
            return False
        if not isinstance(value, Number):
            return False
        return not (
            isinstance(value, float) and (value != value or value in (float("inf"), float("-inf")))
        )
    return False


def _object_schema_error(
    value: Mapping[object, object], spec: Mapping[str, object], path: str
) -> str | None:
    properties = spec.get("properties", {})
    if not isinstance(properties, Mapping):
        return f"{path}: properties must be a mapping"
    required = spec.get("required", [])
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        return f"{path}: required must be a list of strings"
    missing = [name for name in required if name not in value]
    if missing:
        return f"{path}: missing required keys {missing}"
    for name, child_spec in properties.items():
        if not isinstance(child_spec, Mapping):
            return f"{path}.{name}: schema must be a mapping"
        if name in value:
            error = _schema_error(value[name], child_spec, f"{path}.{name}")
            if error is not None:
                return error
    return None


def _array_schema_error(value: list[object], spec: Mapping[str, object], path: str) -> str | None:
    items_spec = spec.get("items")
    if not isinstance(items_spec, Mapping):
        return f"{path}: items schema must be a mapping"
    for index, item in enumerate(value):
        error = _schema_error(item, items_spec, f"{path}[{index}]")
        if error is not None:
            return error
    return None


def _schema_error(value: object, spec: Mapping[str, object], path: str) -> str | None:
    type_name = spec.get("type")
    if not isinstance(type_name, str) or type_name not in SCHEMA_TYPES:
        return f"{path}: unknown schema type {type_name!r}"
    if not _check_type(value, type_name):
        return f"{path}: expected {type_name}, got {type(value).__name__}"
    if type_name == "object" and isinstance(value, Mapping):
        return _object_schema_error(value, spec, path)
    if type_name == "array" and isinstance(value, list):
        return _array_schema_error(value, spec, path)
    return None


def _schema_validity(ctx: ScorerContext) -> ScorerFinding:
    spec = ctx.case.expected
    if not isinstance(spec, Mapping):
        return make_finding(
            _SCHEMA_SCORER_ID,
            ctx,
            EvalFindingStatus.FAIL,
            "expected must be a schema spec mapping",
        )
    error = _schema_error(ctx.input.actual, spec, "$")
    if error is None:
        return make_finding(_SCHEMA_SCORER_ID, ctx, EvalFindingStatus.PASS, "output matches schema")
    return make_finding(
        _SCHEMA_SCORER_ID,
        ctx,
        EvalFindingStatus.FAIL,
        f"schema violation: {error}",
    )
