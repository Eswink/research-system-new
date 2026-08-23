"""M12 independent ground truth scorers（M12-R1 WP5）。

消除自证循环：候选值不再与 expected 常量同源，而是由 scorer 从正式
持久状态独立验证：

- metric_correctness：从 ArtifactStore 的 experiment_result.json 独立
  重算/读取 metric，与报告自报值比对——不信报告自报值；
- direction_improvement：按 claim 语义校验 baseline vs candidate 方向，
  不固定"越高越好"；方向反转必 FAIL；
- citation_source：Claim 引用的 Evidence 必须已登记 Source 且属于当前
  run_id（wrong source id 必 FAIL）；
- unsupported_claim：无 SUPPORTS 支撑的 Claim 必 FAIL。

Port 异常一律转为 INFRA_ERROR（设施故障不得判为被评对象质量失败）。
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Mapping

from packages.application.evaluation.scorer_types import (
    ScorerContext,
    ScorerFn,
    make_finding,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding
from packages.domain.evidence import EvidenceRelationType

_METRIC_SCORER = "metric_correctness"
_DIRECTION_SCORER = "direction_improvement"
_CITATION_SCORER = "citation_source"
_UNSUPPORTED_SCORER = "unsupported_claim"


def _to_decimal(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _read_artifact_json(artifacts: ArtifactStore, artifact_id: str) -> dict[str, object] | None:
    """读 artifact 内容并解析 JSON；任何失败返回 None（由调用方转 INFRA）。"""
    content = artifacts.get(artifact_id)
    parsed = json.loads(content.decode("utf-8"))
    if not isinstance(parsed, dict):
        return None
    return parsed


def metric_correctness_scorer(artifacts: ArtifactStore) -> ScorerFn:
    """expected = {'artifact_id': str, 'metric': str}。

    actual = 报告自报 metric 值（数字/字符串）。scorer 从 artifact JSON
    独立读取同一 metric 并比对；差异超 tolerance（默认 0.001）→ FAIL。
    """

    def score(ctx: ScorerContext) -> ScorerFinding:
        spec = ctx.case.expected
        if not isinstance(spec, Mapping):
            return make_finding(
                _METRIC_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "expected must be {'artifact_id': str, 'metric': str}",
            )
        artifact_id = spec.get("artifact_id")
        metric_path = spec.get("metric")
        if not isinstance(artifact_id, str) or not isinstance(metric_path, str):
            return make_finding(
                _METRIC_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "artifact_id and metric must be strings",
            )
        try:
            payload = _read_artifact_json(artifacts, artifact_id)
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
        ground_truth = _lookup(payload, metric_path)
        if ground_truth is None:
            return make_finding(
                _METRIC_SCORER,
                ctx,
                EvalFindingStatus.INFRA_ERROR,
                f"metric {metric_path} not found in artifact",
            )
        tolerance = _to_decimal(spec.get("tolerance", "0.001"))
        reported = _to_decimal(ctx.input.actual)
        expected = _to_decimal(ground_truth)
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

    return score


def direction_improvement_scorer() -> ScorerFn:
    """expected = {'baseline_metric': str, 'candidate_metric': str,
    'claim_direction': 'baseline_better' | 'candidate_better'}。

    actual = 报告 metrics dict。按 claim 语义判断方向；
    与 claim 声明的方向相反 → FAIL（不固定"越高越好"）。
    """

    def score(ctx: ScorerContext) -> ScorerFinding:
        spec = ctx.case.expected
        if not isinstance(spec, Mapping):
            return make_finding(
                _DIRECTION_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "expected must declare baseline/candidate metrics and claim_direction",
            )
        baseline_path = spec.get("baseline_metric")
        candidate_path = spec.get("candidate_metric")
        direction = spec.get("claim_direction")
        if not isinstance(baseline_path, str) or not isinstance(candidate_path, str):
            return make_finding(
                _DIRECTION_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "baseline_metric and candidate_metric must be dotted paths",
            )
        if direction not in ("baseline_better", "candidate_better"):
            return make_finding(
                _DIRECTION_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "claim_direction must be 'baseline_better' or 'candidate_better'",
            )
        actual = ctx.input.actual
        if not isinstance(actual, Mapping):
            return make_finding(
                _DIRECTION_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "actual must be a metrics mapping",
            )
        baseline = _to_decimal(_lookup(actual, baseline_path))
        candidate = _to_decimal(_lookup(actual, candidate_path))
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
            f"direction contradicts claim ({baseline} vs {candidate}); "
            f"expected {direction}",
        )

    return score


def citation_source_scorer(ledger: EvidenceLedger, run_id: str) -> ScorerFn:
    """expected = {'claim_id': str}。

    校验 Claim 每条 relation 的 Evidence：source 已登记且 evidence.run_id
    属于当前 run（wrong source id / 跨 run 引用必 FAIL）。
    """

    def score(ctx: ScorerContext) -> ScorerFinding:
        spec = ctx.case.expected
        if not isinstance(spec, Mapping) or not isinstance(spec.get("claim_id"), str):
            return make_finding(
                _CITATION_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "expected must be {'claim_id': str}",
            )
        claim_id = str(spec["claim_id"])
        try:
            relations = ledger.relations_for_claim(claim_id)
        except Exception as exc:  # noqa: BLE001 - Port 故障 = 评测设施故障
            return make_finding(
                _CITATION_SCORER,
                ctx,
                EvalFindingStatus.INFRA_ERROR,
                f"evidence ledger failure: {type(exc).__name__}: {exc}",
            )
        if not relations:
            return make_finding(
                _CITATION_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                f"claim {claim_id} has no evidence relations",
            )
        for relation in relations:
            evidence = ledger.get_evidence(relation.evidence_id)
            if evidence.run_id != run_id:
                return make_finding(
                    _CITATION_SCORER,
                    ctx,
                    EvalFindingStatus.FAIL,
                    f"evidence {evidence.id} belongs to run {evidence.run_id}, "
                    f"not current run {run_id}",
                )
            if not ledger.has_source(evidence.source_ref):
                return make_finding(
                    _CITATION_SCORER,
                    ctx,
                    EvalFindingStatus.FAIL,
                    f"evidence {evidence.id} source {evidence.source_ref} is not registered",
                )
        return make_finding(
            _CITATION_SCORER,
            ctx,
            EvalFindingStatus.PASS,
            f"claim {claim_id} citations verified in run {run_id}",
        )

    return score


def unsupported_claim_scorer(ledger: EvidenceLedger) -> ScorerFn:
    """expected = {'claim_id': str}。

    无 SUPPORTS/CORROBORATES 支撑（仅 REFUTES 或零 relation）的 Claim
    必 FAIL——unsupported claim 不得通过。
    """

    def score(ctx: ScorerContext) -> ScorerFinding:
        spec = ctx.case.expected
        if not isinstance(spec, Mapping) or not isinstance(spec.get("claim_id"), str):
            return make_finding(
                _UNSUPPORTED_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "expected must be {'claim_id': str}",
            )
        claim_id = str(spec["claim_id"])
        try:
            relations = ledger.relations_for_claim(claim_id)
        except Exception as exc:  # noqa: BLE001 - Port 故障 = 评测设施故障
            return make_finding(
                _UNSUPPORTED_SCORER,
                ctx,
                EvalFindingStatus.INFRA_ERROR,
                f"evidence ledger failure: {type(exc).__name__}: {exc}",
            )
        supporting = [
            relation
            for relation in relations
            if relation.relation
            in (EvidenceRelationType.SUPPORTS, EvidenceRelationType.CORROBORATES)
        ]
        if supporting:
            return make_finding(
                _UNSUPPORTED_SCORER,
                ctx,
                EvalFindingStatus.PASS,
                f"claim {claim_id} has {len(supporting)} supporting relations",
            )
        return make_finding(
            _UNSUPPORTED_SCORER,
            ctx,
            EvalFindingStatus.FAIL,
            f"claim {claim_id} has no supporting evidence",
        )

    return score


def _lookup(mapping: Mapping[str, object], path: str) -> object | None:
    current: object = mapping
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


M12_TRUTH_SCORER_IDS = (
    _METRIC_SCORER,
    _DIRECTION_SCORER,
    _CITATION_SCORER,
    _UNSUPPORTED_SCORER,
)

__all__ = [
    "M12_TRUTH_SCORER_IDS",
    "citation_source_scorer",
    "direction_improvement_scorer",
    "metric_correctness_scorer",
    "unsupported_claim_scorer",
]