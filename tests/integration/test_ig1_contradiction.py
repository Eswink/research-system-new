"""IG-1 contradiction chain: M10 contradiction + M11 observation."""

from __future__ import annotations

from adapters.fakes import FakeEvidenceLedger
from packages.application.evaluation.scorer_types import ScorerContext, ScorerInput
from packages.application.evaluation.scorers_runtime import evidence_provenance_scorer
from packages.application.evidence.contradiction import (
    register_evidence_with_contradiction_check,
)
from packages.domain.core import Timestamp, Version
from packages.domain.enums import TrustLabel
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

_DIGEST = "sha256:" + "0" * 64


def _case(case_id: str) -> EvalCase:
    return EvalCase(
        id=case_id,
        version=Version("1.0.0"),
        scope=EvalScope.INTEGRATION,
        input_ref=f"input://{case_id}",
        expected={"claim_id": "claim:1", "minimum_sources": 1},
        scorer_refs=(),
    )


def _register_source(ledger: FakeEvidenceLedger, origin: str) -> None:
    ledger.register_source(
        SourceRecord(
            origin=origin,
            content_digest=_DIGEST,
            trust_label=TrustLabel.GENERATED,
            access_time=Timestamp.now(),
        )
    )


def _evidence(evidence_id: str, origin: str) -> Evidence:
    return Evidence(
        id=evidence_id,
        source_ref=origin,
        content_digest=_DIGEST,
        artifact_id=origin,
    )


def _ledger_with_support() -> FakeEvidenceLedger:
    ledger = FakeEvidenceLedger()
    _register_source(ledger, "artifact:a")
    ledger.register_evidence(_evidence("evidence:a", "artifact:a"))
    claim = Claim(
        id="claim:1",
        statement="C",
        status=ClaimStatus.PROPOSED,
        evidence_relations=[("evidence:a", EvidenceRelationType.SUPPORTS)],
    )
    ledger.register_claim(claim)
    ledger.attach_relation(EvidenceRelation("claim:1", "evidence:a", EvidenceRelationType.SUPPORTS))
    return ledger


def test_contradiction_preserves_both_evidences_and_is_observable_by_eval() -> None:
    ledger = _ledger_with_support()
    _register_source(ledger, "artifact:b")
    outcome = register_evidence_with_contradiction_check(
        ledger,
        _evidence("evidence:b", "artifact:b"),
        EvidenceRelation("claim:1", "evidence:b", EvidenceRelationType.REFUTES),
    )

    assert outcome.disputed is True
    assert outcome.claim.status is ClaimStatus.DISPUTED
    assert ledger.get_evidence("evidence:a")
    assert ledger.get_evidence("evidence:b")
    relations = ledger.relations_for_claim("claim:1")
    assert len(relations) == 2
    assert {r.relation for r in relations} == {
        EvidenceRelationType.SUPPORTS,
        EvidenceRelationType.REFUTES,
    }

    scorer = evidence_provenance_scorer(ledger)
    ctx = ScorerContext(case=_case("c1"), input=ScorerInput(actual={}))
    finding = scorer(ctx)
    assert finding.status is EvalFindingStatus.FAIL
    assert "disputed" in finding.detail
