"""ExperimentRun -> Evidence/Claim admission (IG-1 seam).

M9 produces ExperimentRun + ArtifactStore content; M10 owns EvidenceLedger.
This module is the formal admission path that converts a terminal scientific
ExperimentRun into SourceRecord/Evidence/Claim with full structured provenance.

It is not allowed to convert ToolResult directly into trusted Evidence.  The
only accepted path is: terminal ExperimentRun + verified Artifacts + registered
SourceRecord -> Evidence -> Claim.
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.domain.artifacts import Artifact
from packages.domain.core import Timestamp
from packages.domain.enums import ArtifactState, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.experiments import ExperimentRun, ExperimentRunResult


@dataclass(frozen=True, slots=True)
class ExperimentProvenance:
    """Additional cross-stage provenance for an ExperimentRun evidence set."""

    run_id: str | None = None
    manifest_digest: str | None = None
    tool_refs: tuple[str, ...] = ()
    skill_refs: tuple[str, ...] = ()
    model_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExperimentEvidenceResult:
    """Admission result: the merged Claim and its Evidence references."""

    claim: Claim
    evidence: tuple[Evidence, ...]
    artifact_ids: tuple[str, ...]


def register_experiment_evidence(
    ledger: EvidenceLedger,
    run: ExperimentRun,
    artifacts: ArtifactStore,
    *,
    provenance: ExperimentProvenance | None = None,
    claim_statement: str | None = None,
) -> ExperimentEvidenceResult:
    """Register Evidence/Claim for a terminal scientific ExperimentRun.

    Only SUCCEEDED and NEGATIVE_RESULT runs are scientific outcomes eligible
    for evidence admission.  Execution failures, timeouts and cancellations
    do not become Evidence.
    """
    if run.state not in (
        ExperimentRunState.State.SUCCEEDED,
        ExperimentRunState.State.NEGATIVE_RESULT,
    ):
        raise ValueError(f"cannot admit evidence for non-scientific run state {run.state}")
    if run.result is None or run.spec is None:
        raise ValueError("terminal scientific run must carry spec and result")

    p = provenance or ExperimentProvenance()
    evidences = _admit_artifact_evidences(ledger, run, artifacts, p)
    if not evidences:
        raise ValueError("experiment run has no artifact refs to admit as evidence")
    claim = _register_claim_for_evidences(ledger, run, evidences, claim_statement=claim_statement)
    return ExperimentEvidenceResult(
        claim=claim,
        evidence=tuple(evidences),
        artifact_ids=tuple(run.result.artifact_refs),
    )


def _admit_artifact_evidences(
    ledger: EvidenceLedger,
    run: ExperimentRun,
    artifacts: ArtifactStore,
    p: ExperimentProvenance,
) -> list[Evidence]:
    assert run.result is not None
    result = run.result
    by_id = {artifact.id: artifact for artifact in artifacts.list_refs()}
    evidences: list[Evidence] = []
    for artifact_id in result.artifact_refs:
        artifact = by_id.get(artifact_id)
        if artifact is None:
            raise ValueError(f"artifact {artifact_id!r} missing from artifact store")
        _ensure_verified(artifacts, artifact)
        evidence = _evidence_for_artifact(run, result, artifact, p)
        ledger.register_source(
            SourceRecord(
                origin=evidence.source_ref,
                content_digest=str(artifact.digest),
                trust_label=TrustLabel.GENERATED,
                access_time=Timestamp.now(),
            )
        )
        ledger.register_evidence(evidence)
        evidences.append(evidence)
    return evidences


def _register_claim_for_evidences(
    ledger: EvidenceLedger,
    run: ExperimentRun,
    evidences: list[Evidence],
    *,
    claim_statement: str | None = None,
) -> Claim:
    assert run.spec is not None
    claim_id = f"claim:{run.id.value}:result"
    claim = Claim(
        id=claim_id,
        statement=claim_statement or f"ExperimentRun {run.id.value} produced artifacts and metrics",
        status=ClaimStatus.PROPOSED,
        author=run.spec.command,
        evidence_relations=[(ev.id, EvidenceRelationType.SUPPORTS) for ev in evidences],
    )
    ledger.register_claim(claim)
    for evidence in evidences:
        ledger.attach_relation(
            EvidenceRelation(
                claim_id=claim.id,
                evidence_id=evidence.id,
                relation=EvidenceRelationType.SUPPORTS,
            )
        )
    return claim


def _ensure_verified(artifacts: ArtifactStore, artifact: Artifact) -> None:
    if artifact.state in (ArtifactState.VERIFIED, ArtifactState.ACTIVE):
        return
    if artifact.state is not ArtifactState.STAGED:
        raise ValueError(
            f"artifact {artifact.id!r} is in state {artifact.state.value}, "
            "cannot be admitted as evidence"
        )
    artifacts.mark(artifact.id, ArtifactState.VERIFIED)


def _evidence_for_artifact(
    run: ExperimentRun,
    result: ExperimentRunResult,
    artifact: Artifact,
    p: ExperimentProvenance,
) -> Evidence:
    assert run.spec is not None
    metric_refs = tuple(f"metric:{run.id.value}:{metric.metric.name}" for metric in result.metrics)
    return Evidence(
        id=f"evidence:{artifact.id}",
        source_ref=artifact.id,
        content_digest=str(artifact.digest),
        extracted_by=f"experiment:{run.id.value}",
        captured_at=Timestamp.now(),
        artifact_id=artifact.id,
        run_id=p.run_id,
        experiment_run_id=str(run.id.value),
        metric_refs=metric_refs,
        workspace_snapshot_before=result.workspace_snapshot_before,
        workspace_snapshot_after=result.workspace_snapshot_after,
        image_digest=result.image_digest,
        environment_digest=(
            str(run.spec.environment_digest) if run.spec.environment_digest else None
        ),
        tool_refs=p.tool_refs,
        skill_refs=p.skill_refs,
        model_refs=p.model_refs,
        manifest_digest=p.manifest_digest,
    )
