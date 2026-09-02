"""M11 确定性 scorer 注册表（纯函数，无 Port 依赖，无副作用）。

来源（权威）：docs/roadmap/MILESTONES.md M11（deterministic-first）、
docs/architecture/EVALUATION.md（Deterministic gates 优先于 LLM judgment）。
约束：
- 每个 scorer 版本化、可追溯、可复现，失败给出结构化 ScorerFinding；
- scorer 不得修改被评对象（纯函数、frozen 输入）；
- malformed 输入 → FAIL finding（不抛异常）；scorer 内部错误由 runner
  统一转换为 INFRA_ERROR；
- 确定性可验证的问题不得交给 Reviewer。
schema_validity 实现见 schema_scorer.py（独立模块以保持行数阈值）。
"""

from __future__ import annotations

import hashlib
from decimal import Decimal, InvalidOperation
from numbers import Number
from typing import Mapping

from packages.application.evaluation.schema_scorer import _schema_validity
from packages.application.evaluation.scorer_types import (
    V1,
    ScorerContext,
    ScorerFn,
    ScorerRegistration,
    make_finding,
)
from packages.application.evaluation.scorers_m17_gpu import _gpu_compute_device
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding


def _exact_match(ctx: ScorerContext) -> ScorerFinding:
    if ctx.case.expected is None:
        return make_finding(
            "exact_match", ctx, EvalFindingStatus.INFRA_ERROR, "case has no expected oracle"
        )
    if ctx.input.actual == ctx.case.expected:
        return make_finding("exact_match", ctx, EvalFindingStatus.PASS, "output equals expected")
    return make_finding(
        "exact_match",
        ctx,
        EvalFindingStatus.FAIL,
        f"output {ctx.input.actual!r} != expected {ctx.case.expected!r}",
    )


def _digest_match(ctx: ScorerContext) -> ScorerFinding:
    spec = ctx.case.expected
    if not isinstance(spec, Mapping) or spec.get("algorithm") != "sha256":
        return make_finding(
            "digest_match",
            ctx,
            EvalFindingStatus.FAIL,
            "expected must be {'algorithm': 'sha256', 'hex': ...}",
        )
    hex_expected = spec.get("hex")
    if not isinstance(hex_expected, str) or len(hex_expected) != 64:
        return make_finding(
            "digest_match",
            ctx,
            EvalFindingStatus.FAIL,
            "expected digest hex must be 64 characters",
        )
    actual = ctx.input.actual
    if isinstance(actual, str):
        payload = actual.encode("utf-8")
    elif isinstance(actual, bytes):
        payload = actual
    else:
        return make_finding(
            "digest_match",
            ctx,
            EvalFindingStatus.FAIL,
            f"actual must be str or bytes, got {type(actual).__name__}",
        )
    hex_actual = hashlib.sha256(payload).hexdigest()
    if hex_actual == hex_expected:
        return make_finding("digest_match", ctx, EvalFindingStatus.PASS, "digest matches")
    return make_finding(
        "digest_match",
        ctx,
        EvalFindingStatus.FAIL,
        f"sha256 mismatch: got {hex_actual}",
    )


def _lookup_path(value: object, path: str) -> bool:
    current: object = value
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return False
        current = current[part]
    return True


def _required_fields(ctx: ScorerContext) -> ScorerFinding:
    spec = ctx.case.expected
    if not isinstance(spec, list) or not all(isinstance(item, str) for item in spec):
        return make_finding(
            "required_fields",
            ctx,
            EvalFindingStatus.FAIL,
            "expected must be a list of dotted paths",
        )
    if not isinstance(ctx.input.actual, Mapping):
        return make_finding(
            "required_fields",
            ctx,
            EvalFindingStatus.FAIL,
            "actual output is not a mapping",
        )
    missing = [path for path in spec if not _lookup_path(ctx.input.actual, path)]
    if missing:
        return make_finding(
            "required_fields",
            ctx,
            EvalFindingStatus.FAIL,
            f"missing required fields: {', '.join(missing)}",
        )
    return make_finding(
        "required_fields", ctx, EvalFindingStatus.PASS, "all required fields present"
    )


def _to_decimal(value: object) -> Decimal | None:
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, Number):
            return Decimal(str(value))
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _numeric_tolerance(ctx: ScorerContext) -> ScorerFinding:
    spec = ctx.case.expected
    if not isinstance(spec, Mapping):
        return make_finding(
            "numeric_tolerance",
            ctx,
            EvalFindingStatus.FAIL,
            "expected must be {'value': number, 'tolerance': number}",
        )
    expected_value = _to_decimal(spec.get("value"))
    tolerance = _to_decimal(spec.get("tolerance"))
    actual = _to_decimal(ctx.input.actual)
    if expected_value is None or tolerance is None or tolerance < 0:
        return make_finding(
            "numeric_tolerance",
            ctx,
            EvalFindingStatus.FAIL,
            f"invalid expected spec: {spec!r}",
        )
    if actual is None:
        return make_finding(
            "numeric_tolerance",
            ctx,
            EvalFindingStatus.FAIL,
            f"actual is not numeric: {ctx.input.actual!r}",
        )
    diff = abs(actual - expected_value)
    if diff <= tolerance:
        return make_finding(
            "numeric_tolerance",
            ctx,
            EvalFindingStatus.PASS,
            f"|actual - expected| = {diff} <= {tolerance}",
            value=str(diff),
        )
    return make_finding(
        "numeric_tolerance",
        ctx,
        EvalFindingStatus.FAIL,
        f"|actual - expected| = {diff} > {tolerance}",
        value=str(diff),
    )


def _invariant(ctx: ScorerContext) -> ScorerFinding:
    spec = ctx.case.expected
    if not isinstance(spec, Mapping):
        return make_finding(
            "invariant",
            ctx,
            EvalFindingStatus.FAIL,
            "expected must be {'predicate_id': str, 'params': {...}}",
        )
    predicate_id = spec.get("predicate_id")
    if not isinstance(predicate_id, str):
        return make_finding(
            "invariant", ctx, EvalFindingStatus.FAIL, "predicate_id must be a string"
        )
    predicate = ctx.predicates.get(predicate_id)
    if predicate is None:
        return make_finding(
            "invariant",
            ctx,
            EvalFindingStatus.INFRA_ERROR,
            f"predicate {predicate_id!r} not registered",
        )
    params = spec.get("params", {})
    if not isinstance(params, Mapping):
        return make_finding("invariant", ctx, EvalFindingStatus.FAIL, "params must be a mapping")
    if predicate(ctx.input.actual, dict(params)):
        return make_finding(
            "invariant", ctx, EvalFindingStatus.PASS, f"invariant {predicate_id} holds"
        )
    return make_finding(
        "invariant", ctx, EvalFindingStatus.FAIL, f"invariant {predicate_id} violated"
    )


def _evidence_source_distinct(ctx: ScorerContext) -> ScorerFinding:
    spec = ctx.case.expected
    minimum = 1
    if spec is not None:
        if not isinstance(spec, Mapping) or not isinstance(spec.get("minimum"), int):
            return make_finding(
                "evidence_source_distinct",
                ctx,
                EvalFindingStatus.FAIL,
                "expected must be {'minimum': int}",
            )
        minimum = int(spec["minimum"])
    distinct = {identity for identity in ctx.input.evidence_sources.values() if identity}
    count = len(distinct)
    if count >= minimum:
        return make_finding(
            "evidence_source_distinct",
            ctx,
            EvalFindingStatus.PASS,
            f"{count} >= {minimum} distinct sources",
            value=count,
        )
    return make_finding(
        "evidence_source_distinct",
        ctx,
        EvalFindingStatus.FAIL,
        f"{count} < {minimum} distinct sources",
        value=count,
    )


REGISTRY: tuple[ScorerRegistration, ...] = (
    ScorerRegistration("exact_match", V1, _exact_match),
    ScorerRegistration("digest_match", V1, _digest_match),
    ScorerRegistration("required_fields", V1, _required_fields),
    ScorerRegistration("numeric_tolerance", V1, _numeric_tolerance),
    ScorerRegistration("invariant", V1, _invariant),
    ScorerRegistration("evidence_source_distinct", V1, _evidence_source_distinct),
    ScorerRegistration("schema_validity", V1, _schema_validity),
    # M17: GPU evidence-layer no-fallback discriminator
    ScorerRegistration("gpu_compute_device", V1, _gpu_compute_device),
)

_SCORERS: dict[tuple[str, str], ScorerFn] = {
    (item.scorer_id, item.version.text): item.fn for item in REGISTRY
}


def resolve_scorer(scorer_id: str, version: str) -> ScorerFn:
    """按 id+version 解析 scorer；未知组合 fail-closed。"""

    fn = _SCORERS.get((scorer_id, version))
    if fn is None:
        raise KeyError(f"unknown scorer: {scorer_id}@{version}")
    return fn


def versioned_scorer_ids() -> tuple[str, ...]:
    """全部已注册 scorer 的稳定标识（供 CI 门禁校验）。"""

    return tuple(f"{item.scorer_id}@{item.version.text}" for item in REGISTRY)
