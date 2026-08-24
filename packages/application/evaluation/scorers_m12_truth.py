"""M12 independent ground truth scorers（M12-R1 WP5）。

消除自证循环：候选值不再与 expected 常量同源，而是由 scorer 从正式
持久状态独立验证：

- metric_correctness：从 ArtifactStore 的 experiment_result.json 独立
  重算/读取 metric，与报告自报值比对——不信报告自报值；
- direction_improvement：按 claim 语义校验 baseline vs candidate 方向，
  不固定"越高越好"；方向反转必 FAIL。

Evidence-backed scorer（citation_source / unsupported_claim /
evidence_artifact）见 scorers_m12_truth_evidence.py（模块规模阈值拆分）。

Port 异常一律转为 INFRA_ERROR（设施故障不得判为被评对象质量失败）。
"""

from __future__ import annotations

from typing import Mapping

from packages.application.evaluation.scorer_types import (
    ScorerContext,
    ScorerFn,
    make_finding,
)
from packages.application.evaluation.scorers_m12_truth_util import (
    lookup,
    read_artifact_json,
    to_decimal,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding

_METRIC_SCORER = "metric_correctness"
_DIRECTION_SCORER = "direction_improvement"


def metric_correctness_scorer(artifacts: ArtifactStore) -> ScorerFn:
    """expected = {'artifact_id': str, 'metric': str}。

    actual = 报告自报 metric 值（数字/字符串）。scorer 从 artifact JSON
    独立读取同一 metric 并比对；差异超 tolerance（默认 0.001）→ FAIL。
    """

    def score(ctx: ScorerContext) -> ScorerFinding:
        spec = _metric_spec(ctx)
        if spec is None:
            return make_finding(
                _METRIC_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "expected must be {'artifact_id': str, 'metric': str}",
            )
        artifact_id, metric_path = spec
        try:
            payload = read_artifact_json(artifacts, artifact_id)
        except Exception as exc:  # noqa: BLE001 - Port 故障 = 评测设施故障
            return make_finding(
                _METRIC_SCORER,
                ctx,
                EvalFindingStatus.INFRA_ERROR,
                f"artifact store failure: {type(exc).__name__}: {exc}",
            )
        if payload is None:
            return make_finding(
                _METRIC_SCORER,
                ctx,
                EvalFindingStatus.INFRA_ERROR,
                "experiment artifact is not a JSON object",
            )
        ground_truth = lookup(payload, metric_path)
        if ground_truth is None:
            return make_finding(
                _METRIC_SCORER,
                ctx,
                EvalFindingStatus.INFRA_ERROR,
                f"metric {metric_path} not found in artifact",
            )
        return _compare_metric(ctx, ground_truth)

    return score


def _metric_spec(ctx: ScorerContext) -> tuple[str, str] | None:
    """提取 artifact_id/metric 路径；结构非法返回 None。"""
    spec = ctx.case.expected
    if not isinstance(spec, Mapping):
        return None
    artifact_id = spec.get("artifact_id")
    metric_path = spec.get("metric")
    if not isinstance(artifact_id, str) or not isinstance(metric_path, str):
        return None
    return artifact_id, metric_path


def _compare_metric(ctx: ScorerContext, ground_truth: object) -> ScorerFinding:
    """报告自报值与 artifact 独立重算值比对（tolerance 默认 0.001）。"""
    spec = ctx.case.expected
    tolerance = to_decimal(spec.get("tolerance", "0.001")) if isinstance(spec, Mapping) else None
    reported = to_decimal(ctx.input.actual)
    expected = to_decimal(ground_truth)
    if reported is None or expected is None or tolerance is None:
        return make_finding(
            _METRIC_SCORER,
            ctx,
            EvalFindingStatus.INFRA_ERROR,
            "metric values must be numeric",
        )
    diff = abs(reported - expected)
    if diff <= tolerance:
        return make_finding(
            _METRIC_SCORER,
            ctx,
            EvalFindingStatus.PASS,
            f"reported {reported} matches artifact {expected} (|diff|={diff})",
            value=str(diff),
        )
    return make_finding(
        _METRIC_SCORER,
        ctx,
        EvalFindingStatus.FAIL,
        f"reported {reported} != artifact ground truth {expected} (|diff|={diff})",
        value=str(diff),
    )


def direction_improvement_scorer() -> ScorerFn:
    """expected = {'baseline_metric': str, 'candidate_metric': str,
    'claim_direction': 'baseline_better' | 'candidate_better'}。

    actual = 报告 metrics dict。按 claim 语义判断方向；
    与 claim 声明的方向相反 → FAIL（不固定"越高越好"）。
    """
    return _direction_score


def _direction_score(ctx: ScorerContext) -> ScorerFinding:
    """方向校验实现（模块级；工厂只做绑定，函数体 ≤ 50 行）。"""
    spec = ctx.case.expected
    if not isinstance(spec, Mapping):
        return _direction_fail(
            ctx,
            "expected must declare baseline/candidate metrics and claim_direction",
        )
    baseline_path = spec.get("baseline_metric")
    candidate_path = spec.get("candidate_metric")
    direction = spec.get("claim_direction")
    if not isinstance(baseline_path, str) or not isinstance(candidate_path, str):
        return _direction_fail(ctx, "baseline_metric and candidate_metric must be dotted paths")
    if direction not in ("baseline_better", "candidate_better"):
        return _direction_fail(
            ctx,
            "claim_direction must be 'baseline_better' or 'candidate_better'",
        )
    actual = ctx.input.actual
    if not isinstance(actual, Mapping):
        return _direction_fail(ctx, "actual must be a metrics mapping")
    baseline = to_decimal(lookup(actual, baseline_path))
    candidate = to_decimal(lookup(actual, candidate_path))
    if baseline is None or candidate is None:
        return make_finding(
            _DIRECTION_SCORER,
            ctx,
            EvalFindingStatus.INFRA_ERROR,
            "baseline/candidate metric missing or non-numeric",
        )
    baseline_wins = baseline > candidate
    matches = baseline_wins if direction == "baseline_better" else (not baseline_wins)
    if matches:
        return make_finding(
            _DIRECTION_SCORER,
            ctx,
            EvalFindingStatus.PASS,
            f"direction matches claim ({baseline} vs {candidate})",
        )
    return make_finding(
        _DIRECTION_SCORER,
        ctx,
        EvalFindingStatus.FAIL,
        f"direction contradicts claim ({baseline} vs {candidate}); expected {direction}",
    )


def _direction_fail(ctx: ScorerContext, message: str) -> ScorerFinding:
    return make_finding(_DIRECTION_SCORER, ctx, EvalFindingStatus.FAIL, message)


M12_TRUTH_SCORER_IDS = (_METRIC_SCORER, _DIRECTION_SCORER)

__all__ = ["M12_TRUTH_SCORER_IDS", "direction_improvement_scorer", "metric_correctness_scorer"]
