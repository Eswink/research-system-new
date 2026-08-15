"""Provenance 测试套件：VERIFIED Claim 必须追溯合法登记的证据来源。

覆盖：升级前置（gate PASS、evidence 可解析、source 已登记）、
Agent 输出不得自行升级、GENERATED 来源的登记语义。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.evidence.verification import (
    VerificationBasis,
    promote_claim_to_verified,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.run_orchestration.result_handler import (
    RegistrationDeps,
    register_session_result,
)
from packages.domain.core import Timestamp
from packages.domain.enums import TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelationType,
    SourceRecord,
)
from tests.contracts.fixtures import research_task, task_contract

NOW = datetime(2026, 8, 15, 10, 0, 0, tzinfo=timezone.utc)


def _source(origin: str = "task:demo:artifact") -> SourceRecord:
    return SourceRecord(
        origin=origin,
        content_digest="sha256:aa",
        trust_label=TrustLabel.GENERATED,
        access_time=Timestamp(NOW),
    )


def _evidence(evidence_id: str = "ev-1", source_ref: str = "task:demo:artifact") -> Evidence:
    return Evidence(
        id=evidence_id,
        source_ref=source_ref,
        content_digest="sha256:bb",
        captured_at=Timestamp(NOW),
        artifact_id="artifact-1",
    )


def _proposed_claim(claim_id: str = "claim-1") -> Claim:
    return Claim(
        id=claim_id,
        statement="a measurable statement",
        status=ClaimStatus.PROPOSED,
        evidence_relations=[("ev-1", EvidenceRelationType.SUPPORTS)],
    )


def _basis(verdict: str = "PASS") -> VerificationBasis:
    return VerificationBasis(verdict=verdict, reviewer="gate:agent-a")


class TestClaimPromotionGate:
    def test_promotion_requires_passing_verdict(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_source(_source())
        ledger.register_evidence(_evidence())
        ledger.register_claim(_proposed_claim())
        with pytest.raises(InvalidInputError, match="passing gate verdict"):
            promote_claim_to_verified(ledger, _proposed_claim(), basis=_basis("REJECT"))

    def test_promotion_requires_registered_evidence(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_claim(_proposed_claim())
        with pytest.raises(InvalidInputError, match="unknown evidence"):
            promote_claim_to_verified(ledger, _proposed_claim(), basis=_basis())

    def test_promotion_requires_registered_source(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_evidence(_evidence())
        ledger.register_claim(_proposed_claim())
        with pytest.raises(InvalidInputError, match="not registered"):
            promote_claim_to_verified(ledger, _proposed_claim(), basis=_basis())

    def test_promotion_succeeds_with_full_provenance(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_source(_source())
        ledger.register_evidence(_evidence())
        ledger.register_claim(_proposed_claim())
        verified = promote_claim_to_verified(ledger, _proposed_claim(), basis=_basis())
        assert verified.status is ClaimStatus.VERIFIED
        assert ledger.get_claim("claim-1").status is ClaimStatus.VERIFIED

    def test_promotion_from_non_proposed_rejected(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_source(_source())
        ledger.register_evidence(_evidence())
        disputed = replace(_proposed_claim(), status=ClaimStatus.DISPUTED)
        ledger.register_claim(disputed)
        with pytest.raises(InvalidInputError, match="cannot be verified"):
            promote_claim_to_verified(ledger, disputed, basis=_basis())

    def test_agent_assertion_alone_cannot_verify(self) -> None:
        """无 gate 依据 + 无登记证据时，Agent 自述不能升级 Claim。"""
        ledger = FakeEvidenceLedger()
        claim = _proposed_claim()
        ledger.register_claim(claim)
        with pytest.raises(InvalidInputError):
            promote_claim_to_verified(ledger, claim, basis=_basis())


class TestSessionResultRegistration:
    def test_registration_records_generated_source_and_relation(self) -> None:
        store = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        task = research_task()
        registration = register_session_result(
            RegistrationDeps(store=store, agent_id="agent-a", ledger=ledger),
            task,
            task_contract(),
            {"report": {"value": 1}},
        )
        assert registration.evidence_source_count == 1
        evidence = registration.evidence[0]
        assert ledger.has_source(evidence.source_ref)
        registered_source = ledger.get_source(evidence.source_ref)
        assert registered_source.trust_label is TrustLabel.GENERATED
        claim_id = f"claim:{task.id.value}:result"
        claim = ledger.get_claim(claim_id)
        assert claim.status is ClaimStatus.PROPOSED
        relations = ledger.relations_for_claim(claim_id)
        assert len(relations) == 1
        assert relations[0].evidence_id == evidence.id

    def test_registration_merges_multiple_evidences_into_one_claim(self) -> None:
        store = FakeArtifactStore()
        ledger = FakeEvidenceLedger()
        task = research_task()
        registration = register_session_result(
            RegistrationDeps(store=store, agent_id="agent-a", ledger=ledger),
            task,
            task_contract(),
            {"report": {"a": 1}, "metrics": {"b": 2}},
        )
        assert registration.evidence_source_count == 2
        claim_id = f"claim:{task.id.value}:result"
        claim = ledger.get_claim(claim_id)
        assert len(claim.evidence_relations) == 2
        assert len(ledger.relations_for_claim(claim_id)) == 2

    def test_registration_without_ledger_skips_provenance(self) -> None:
        store = FakeArtifactStore()
        registration = register_session_result(
            RegistrationDeps(store=store, agent_id="agent-a"),
            research_task(),
            task_contract(),
            {"report": {"value": 1}},
        )
        assert registration.evidence_source_count == 1
