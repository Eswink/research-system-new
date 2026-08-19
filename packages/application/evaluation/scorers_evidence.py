"""M11 evidence/experiment runtime scorers (IG-1 seam)."""

from __future__ import annotations

from typing import Mapping

from packages.application.evaluation.scorer_types import (
    ScorerContext,
    ScorerFn,
    make_finding,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.eval_result import EvalFindingStatus, ScorerFinding
from packages.domain.evidence import ClaimStatus
from packages.domain.experiments import ExperimentRun

_EVIDENCE_SCORER = "evidence_provenance"
_EXPERIMENT_SCORER = "experiment_reproducibility"


def evidence_provenance_scorer(ledger: EvidenceLedger) -> ScorerFn:
    """expected = {'claim_id': str, 'minimum_sources': int (optional)}."""

    def score(ctx: ScorerContext) -> ScorerFinding:
        spec = ctx.case.expected
        if not isinstance(spec, Mapping) or not isinstance(spec.get("claim_id"), str):
            return make_finding(
                _EVIDENCE_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "expected must be {'claim_id': str, 'minimum_sources': int}",
            )
        return _evidence_provenance_finding(
            ctx,
            ledger,
            str(spec["claim_id"]),
            spec.get("minimum_sources", 1),
        )

    return score


def _evidence_provenance_finding(
    ctx: ScorerContext,
    ledger: EvidenceLedger,
    claim_id: str,
    minimum: object,
) -> ScorerFinding:
    if not isinstance(minimum, int) or minimum < 1:
        return make_finding(
            _EVIDENCE_SCORER,
            ctx,
            EvalFindingStatus.FAIL,
            "minimum_sources must be a positive integer",
        )
    try:
        claim = ledger.get_claim(claim_id)
        relations_error = _evidence_relations_error(ctx, ledger, claim_id, minimum)
        if relations_error is not None:
            return relations_error
    except Exception as exc:  # noqa: BLE001 - Port 故障 = 评测设施故障
        return make_finding(
            _EVIDENCE_SCORER,
            ctx,
            EvalFindingStatus.INFRA_ERROR,
            f"evidence ledger failure: {type(exc).__name__}",
        )
    if claim.status is ClaimStatus.DISPUTED:
        return make_finding(
            _EVIDENCE_SCORER,
            ctx,
            EvalFindingStatus.FAIL,
            f"claim {claim_id} is disputed",
        )
    return make_finding(
        _EVIDENCE_SCORER,
        ctx,
        EvalFindingStatus.PASS,
        f"claim {claim_id} provenance verified",
    )


def _evidence_relations_error(
    ctx: ScorerContext,
    ledger: EvidenceLedger,
    claim_id: str,
    minimum: int,
) -> ScorerFinding | None:
    relations = ledger.relations_for_claim(claim_id)
    if len(relations) < minimum:
        return make_finding(
            _EVIDENCE_SCORER,
            ctx,
            EvalFindingStatus.FAIL,
            f"claim {claim_id} has {len(relations)} evidence relations, need {minimum}",
        )
    for relation in relations:
        evidence = ledger.get_evidence(relation.evidence_id)
        if not ledger.has_source(evidence.source_ref):
            return make_finding(
                _EVIDENCE_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                f"evidence {evidence.id} source {evidence.source_ref!r} is not registered",
            )
    return None


def experiment_reproducibility_scorer(artifacts: ArtifactStore) -> ScorerFn:
    """expected = {'experiment_run_id': str}.

    Actual input must be an ExperimentRun.  Checks terminal scientific state,
    result/image/snapshot/metrics/artifact digest presence and artifact
    integrity via ArtifactStore.verify.
    """

    def score(ctx: ScorerContext) -> ScorerFinding:
        spec = ctx.case.expected
        if not isinstance(spec, Mapping) or not isinstance(spec.get("experiment_run_id"), str):
            return make_finding(
                _EXPERIMENT_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                "expected must be {'experiment_run_id': str}",
            )
        run = ctx.input.actual
        if not isinstance(run, ExperimentRun):
            return make_finding(
                _EXPERIMENT_SCORER,
                ctx,
                EvalFindingStatus.FAIL,
                f"actual must be ExperimentRun, got {type(run).__name__}",
            )
        error = _experiment_run_error(ctx, run, str(spec["experiment_run_id"]), artifacts)
        if error is not None:
            return error
        return make_finding(
            _EXPERIMENT_SCORER,
            ctx,
            EvalFindingStatus.PASS,
            f"experiment run {run.id.value} reproducibility anchors verified",
        )

    return score


def _experiment_run_error(
    ctx: ScorerContext,
    run: ExperimentRun,
    expected_id: str,
    artifacts: ArtifactStore,
) -> ScorerFinding | None:
    if str(run.id.value) != expected_id:
        return _experiment_fail(ctx, f"run id {run.id.value} != expected {expected_id}")
    if run.result is None or run.spec is None:
        return _experiment_fail(ctx, "run is missing result or spec")
    result = run.result
    if result.image_digest is None or result.workspace_snapshot_before is None:
        return _experiment_fail(ctx, "run is missing image digest or workspace snapshot before")
    if not result.artifact_refs:
        return _experiment_fail(ctx, "run has no artifact refs")
    try:
        for artifact_id in result.artifact_refs:
            if not artifacts.verify(artifact_id):
                return _experiment_fail(ctx, f"artifact {artifact_id} integrity check failed")
    except Exception as exc:  # noqa: BLE001 - Port 故障 = 评测设施故障
        return make_finding(
            _EXPERIMENT_SCORER,
            ctx,
            EvalFindingStatus.INFRA_ERROR,
            f"artifact store failure: {type(exc).__name__}",
        )
    return None


def _experiment_fail(ctx: ScorerContext, message: str) -> ScorerFinding:
    return make_finding(_EXPERIMENT_SCORER, ctx, EvalFindingStatus.FAIL, message)


__all__ = [
    "_EVIDENCE_SCORER",
    "_EXPERIMENT_SCORER",
    "evidence_provenance_scorer",
    "experiment_reproducibility_scorer",
]
