"""Claim -> Governed Memory promotion tests (IG-1 seam)."""

from __future__ import annotations

from adapters.fakes import FakeEvidenceLedger, FakeMemoryStore, FakePolicyEvaluator
from packages.application.memory.gate import MemoryGateDeps
from packages.application.run_orchestration.memory_promotion import (
    MemoryPromotionContext,
    promote_memory_from_registration,
)
from packages.application.run_orchestration.result_handler import ResultRegistration
from packages.domain.core import Timestamp
from packages.domain.enums import TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)


def _ledger_and_registration() -> tuple[FakeEvidenceLedger, ResultRegistration]:
    ledger = FakeEvidenceLedger()
    artifact_id = "artifact:1"
    source = SourceRecord(
        origin=artifact_id,
        content_digest="sha256:" + "0" * 64,
        trust_label=TrustLabel.GENERATED,
        access_time=Timestamp.now(),
    )
    evidence = Evidence(
        id="evidence:1",
        source_ref=artifact_id,
        content_digest="sha256:" + "0" * 64,
        artifact_id=artifact_id,
    )
    claim = Claim(
        id="claim:1",
        statement="verified claim",
        status=ClaimStatus.PROPOSED,
        evidence_relations=[("evidence:1", EvidenceRelationType.SUPPORTS)],
    )
    ledger.register_source(source)
    ledger.register_evidence(evidence)
    ledger.register_claim(claim)
    ledger.attach_relation(EvidenceRelation("claim:1", "evidence:1", EvidenceRelationType.SUPPORTS))
    # promote to verified
    ledger.update_claim(
        Claim(
            id=claim.id,
            statement=claim.statement,
            status=ClaimStatus.VERIFIED,
            author=claim.author,
            evidence_relations=claim.evidence_relations,
        )
    )
    registration = ResultRegistration(
        artifacts=(),
        evidence=(evidence,),
        claims=(claim,),
    )
    return ledger, registration


def test_memory_promotion_commits_via_gate() -> None:
    ledger, registration = _ledger_and_registration()
    store = FakeMemoryStore(allowed_sources=("artifact:1",))
    gate = MemoryGateDeps(
        store=store,
        policy=FakePolicyEvaluator(),
        ledger=ledger,
        allowed_sources=frozenset({"artifact:1"}),
        actor="system:ig1",
    )
    ctx = MemoryPromotionContext(memory_gate=gate)
    records = promote_memory_from_registration(ctx, registration)
    assert len(records) == 1
    assert records[0].provenance == "artifact:1"
    assert records[0].active is True
    assert store.get(records[0].id).content == "Claim claim:1: verified claim"


def test_memory_promotion_skips_non_verified() -> None:
    ledger, registration = _ledger_and_registration()
    # Downgrade the claim to PROPOSED in ledger after registration was built.
    from packages.domain.evidence import Claim

    ledger.update_claim(
        Claim(
            id="claim:1",
            statement="verified claim",
            status=ClaimStatus.PROPOSED,
            evidence_relations=[("evidence:1", EvidenceRelationType.SUPPORTS)],
        )
    )
    store = FakeMemoryStore(allowed_sources=("artifact:1",))
    gate = MemoryGateDeps(
        store=store,
        policy=FakePolicyEvaluator(),
        ledger=ledger,
        allowed_sources=frozenset({"artifact:1"}),
        actor="system:ig1",
    )
    records = promote_memory_from_registration(
        MemoryPromotionContext(memory_gate=gate), registration
    )
    assert records == ()
