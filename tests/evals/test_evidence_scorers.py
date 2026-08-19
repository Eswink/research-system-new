"""M11 evidence-aware runtime scorer tests (IG-1 seam)."""

from __future__ import annotations

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.evaluation.scorer_types import ScorerContext, ScorerInput
from packages.application.evaluation.scorers_runtime import (
    evidence_provenance_scorer,
    experiment_reproducibility_scorer,
)
from packages.domain.core import ID, Digest, Timestamp, Version
from packages.domain.enums import ArtifactState, TrustLabel
from packages.domain.eval_result import EvalFindingStatus
from packages.domain.eval_spec import EvalCase, EvalScope
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.experiment_state import ExperimentRunState
from packages.domain.experiments import (
    ExperimentRun,
    ExperimentRunResult,
    ExperimentRunSpec,
)
from packages.domain.serialization import digest_of


def _case(case_id: str, expected: object) -> EvalCase:
    return EvalCase(
        id=case_id,
        version=Version("1.0.0"),
        scope=EvalScope.INTEGRATION,
        input_ref=f"input://{case_id}",
        expected=expected,
        scorer_refs=(),
    )


def _context(case: EvalCase, actual: object) -> ScorerContext:
    return ScorerContext(case=case, input=ScorerInput(actual=actual))


def _ledger_with_claim() -> FakeEvidenceLedger:
    ledger = FakeEvidenceLedger()
    ledger.register_source(
        SourceRecord(
            origin="artifact:1",
            content_digest="sha256:" + "0" * 64,
            trust_label=TrustLabel.GENERATED,
            access_time=Timestamp.now(),
        )
    )
    ledger.register_evidence(
        Evidence(
            id="evidence:1",
            source_ref="artifact:1",
            content_digest="sha256:" + "0" * 64,
            artifact_id="artifact:1",
        )
    )
    ledger.register_claim(
        Claim(
            id="claim:1",
            statement="test claim",
            status=ClaimStatus.PROPOSED,
            evidence_relations=[("evidence:1", EvidenceRelationType.SUPPORTS)],
        )
    )
    ledger.attach_relation(EvidenceRelation("claim:1", "evidence:1", EvidenceRelationType.SUPPORTS))
    return ledger


def test_evidence_provenance_scorer_pass() -> None:
    ledger = _ledger_with_claim()
    scorer = evidence_provenance_scorer(ledger)
    finding = scorer(_context(_case("e1", {"claim_id": "claim:1"}), {}))
    assert finding.status is EvalFindingStatus.PASS


def test_evidence_provenance_scorer_missing_source_is_fail() -> None:
    ledger = _ledger_with_claim()
    # Remove source to simulate provenance break.
    ledger._sources.clear()  # noqa: SLF001
    scorer = evidence_provenance_scorer(ledger)
    finding = scorer(_context(_case("e2", {"claim_id": "claim:1"}), {}))
    assert finding.status is EvalFindingStatus.FAIL


def test_evidence_provenance_scorer_ledger_failure_is_infra() -> None:
    class BrokenLedger(FakeEvidenceLedger):
        def get_claim(self, claim_id: str) -> Claim:
            raise RuntimeError("down")

    scorer = evidence_provenance_scorer(BrokenLedger())
    finding = scorer(_context(_case("e3", {"claim_id": "claim:1"}), {}))
    assert finding.status is EvalFindingStatus.INFRA_ERROR


def test_experiment_reproducibility_scorer_pass() -> None:
    store = FakeArtifactStore()
    content = b"data"
    artifact_id = "run:1:result"
    from packages.domain.artifacts import Artifact

    artifact = Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="application/json",
        state=ArtifactState.STAGED,
    )
    store.put(artifact, content)
    store.mark(artifact_id, ArtifactState.VERIFIED)
    run = ExperimentRun(
        id=ID("11111111-2222-4333-8444-555555555555"),
        plan_id=ID("22222222-2222-4333-8444-555555555555"),
        spec=ExperimentRunSpec(
            input_digest=digest_of({"x": 1}),
            command="python run.py",
            environment_digest=digest_of({}),
            seed=1,
        ),
        result=ExperimentRunResult(
            execution_run_id="exec-1",
            image_digest="sha256:" + "0" * 64,
            workspace_snapshot_before="snap-before",
            workspace_snapshot_after="snap-after",
            metrics=(),
            artifact_refs=(artifact_id,),
        ),
        state=ExperimentRunState.State.SUCCEEDED,
    )
    scorer = experiment_reproducibility_scorer(store)
    case = _case("x1", {"experiment_run_id": str(run.id.value)})
    finding = scorer(_context(case, run))
    assert finding.status is EvalFindingStatus.PASS
