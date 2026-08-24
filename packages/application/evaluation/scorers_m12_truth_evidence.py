"""M12 evidence-backed ground truth scorers（M12-R1 WP5）。

与 scorers_m12_truth.py 拆分（保持模块规模阈值）：本模块承载依赖
EvidenceLedger 的 scorer：
- citation_source：Claim 引用的 Evidence 必须已登记 Source 且属于当前
  run_id（wrong source id 必 FAIL）；
- unsupported_claim：无 SUPPORTS 支撑的 Claim 必 FAIL；
- evidence_artifact：Evidence 登记的内容 digest 必须与 ArtifactStore
  当前内容一致（artifact 被替换/篡改必 FAIL）。

Port 异常一律转为 INFRA_ERROR（设施故障不得判为被评对象质量失败）。
工厂只返回模块级 score 函数（函数体 ≤ 50 行）。
"""

from __future__ import annotations

from typing import Mapping

from packages.application.evaluation.scorer_types import (
    ScorerContext,
    ScorerFn,
    make_finding,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.core import Digest
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding
from packages.domain.evidence import EvidenceRelationType

_CITATION_SCORER = "citation_source"
_UNSUPPORTED_SCORER = "unsupported_claim"
_EVIDENCE_ARTIFACT_SCORER = "evidence_artifact"


def citation_source_scorer(ledger: EvidenceLedger, run_id: str) -> ScorerFn:
    """expected = {'claim_id': str}；校验 Evidence run_id/source 登记。"""
    return lambda ctx: _citation_score(ctx, ledger, run_id)


def _citation_score(ctx: ScorerContext, ledger: EvidenceLedger, run_id: str) -> ScorerFinding:
    claim_id = _expected_claim_id(ctx)
    if claim_id is None:
        return _fail(_CITATION_SCORER, ctx, "expected must be {'claim_id': str}")
    try:
        relations = ledger.relations_for_claim(claim_id)
    except Exception as exc:  # noqa: BLE001 - Port 故障 = 评测设施故障
        return _infra(
            _CITATION_SCORER, ctx, f"evidence ledger failure: {type(exc).__name__}: {exc}"
        )
    if not relations:
        return _fail(_CITATION_SCORER, ctx, f"claim {claim_id} has no evidence relations")
    for relation in relations:
        evidence = ledger.get_evidence(relation.evidence_id)
        if evidence.run_id != run_id:
            return _fail(
                _CITATION_SCORER,
                ctx,
                f"evidence {evidence.id} belongs to run {evidence.run_id}, "
                f"not current run {run_id}",
            )
        if not ledger.has_source(evidence.source_ref):
            return _fail(
                _CITATION_SCORER,
                ctx,
                f"evidence {evidence.id} source {evidence.source_ref} is not registered",
            )
    return make_finding(
        _CITATION_SCORER,
        ctx,
        EvalFindingStatus.PASS,
        f"claim {claim_id} citations verified in run {run_id}",
    )


def unsupported_claim_scorer(ledger: EvidenceLedger) -> ScorerFn:
    """expected = {'claim_id': str}；无 SUPPORTS/CORROBORATES 必 FAIL。"""
    return lambda ctx: _unsupported_score(ctx, ledger)


def _unsupported_score(ctx: ScorerContext, ledger: EvidenceLedger) -> ScorerFinding:
    claim_id = _expected_claim_id(ctx)
    if claim_id is None:
        return _fail(_UNSUPPORTED_SCORER, ctx, "expected must be {'claim_id': str}")
    try:
        relations = ledger.relations_for_claim(claim_id)
    except Exception as exc:  # noqa: BLE001 - Port 故障 = 评测设施故障
        return _infra(
            _UNSUPPORTED_SCORER, ctx, f"evidence ledger failure: {type(exc).__name__}: {exc}"
        )
    supporting = [
        relation
        for relation in relations
        if relation.relation in (EvidenceRelationType.SUPPORTS, EvidenceRelationType.CORROBORATES)
    ]
    if supporting:
        return make_finding(
            _UNSUPPORTED_SCORER,
            ctx,
            EvalFindingStatus.PASS,
            f"claim {claim_id} has {len(supporting)} supporting relations",
        )
    return _fail(_UNSUPPORTED_SCORER, ctx, f"claim {claim_id} has no supporting evidence")


def evidence_artifact_scorer(ledger: EvidenceLedger, artifacts: ArtifactStore) -> ScorerFn:
    """expected = {'claim_id': str}；Evidence 引用 artifact 内容 digest 一致性。"""
    return lambda ctx: _evidence_artifact_score(ctx, ledger, artifacts)


def _evidence_artifact_score(
    ctx: ScorerContext, ledger: EvidenceLedger, artifacts: ArtifactStore
) -> ScorerFinding:
    claim_id = _expected_claim_id(ctx)
    if claim_id is None:
        return _fail(_EVIDENCE_ARTIFACT_SCORER, ctx, "expected must be {'claim_id': str}")
    try:
        relations = ledger.relations_for_claim(claim_id)
    except Exception as exc:  # noqa: BLE001 - Port 故障 = 评测设施故障
        return _infra(
            _EVIDENCE_ARTIFACT_SCORER, ctx, f"evidence ledger failure: {type(exc).__name__}: {exc}"
        )
    for relation in relations:
        if relation.relation not in (
            EvidenceRelationType.SUPPORTS,
            EvidenceRelationType.CORROBORATES,
        ):
            continue
        evidence = ledger.get_evidence(relation.evidence_id)
        if not evidence.artifact_id:
            continue
        actual_digest = _artifact_digest(artifacts, evidence.artifact_id)
        if actual_digest is None:
            return _infra(
                _EVIDENCE_ARTIFACT_SCORER,
                ctx,
                f"artifact {evidence.artifact_id} unavailable",
            )
        if actual_digest != evidence.content_digest:
            return _fail(
                _EVIDENCE_ARTIFACT_SCORER,
                ctx,
                f"artifact {evidence.artifact_id} digest {actual_digest} "
                f"!= evidence content digest {evidence.content_digest}",
            )
    return make_finding(
        _EVIDENCE_ARTIFACT_SCORER,
        ctx,
        EvalFindingStatus.PASS,
        f"claim {claim_id} artifacts match evidence digests",
    )


def _expected_claim_id(ctx: ScorerContext) -> str | None:
    spec = ctx.case.expected
    if not isinstance(spec, Mapping) or not isinstance(spec.get("claim_id"), str):
        return None
    return str(spec["claim_id"])


def _artifact_digest(artifacts: ArtifactStore, artifact_id: str) -> str | None:
    """当前 artifact 内容 digest；存储故障返回 None（调用方转 INFRA）。"""
    try:
        content = artifacts.get(artifact_id)
    except Exception:  # noqa: BLE001 - Port 故障 = 评测设施故障
        return None
    return str(Digest.of_bytes(content))


def _fail(scorer_id: str, ctx: ScorerContext, message: str) -> ScorerFinding:
    return make_finding(scorer_id, ctx, EvalFindingStatus.FAIL, message)


def _infra(scorer_id: str, ctx: ScorerContext, message: str) -> ScorerFinding:
    return make_finding(scorer_id, ctx, EvalFindingStatus.INFRA_ERROR, message)


EVIDENCE_TRUTH_SCORER_IDS = (
    _CITATION_SCORER,
    _UNSUPPORTED_SCORER,
    _EVIDENCE_ARTIFACT_SCORER,
)

__all__ = [
    "EVIDENCE_TRUTH_SCORER_IDS",
    "citation_source_scorer",
    "evidence_artifact_scorer",
    "unsupported_claim_scorer",
]
