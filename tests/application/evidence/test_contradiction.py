"""冲突证据检测测试：REFUTES → DISPUTED，旧证据保留，事件审计。

覆盖 M10 DoD“同一 Claim 冲突证据检测测试”。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from adapters.fakes import FakeEventPublisher, FakeEvidenceLedger
from packages.application.evidence.contradiction import (
    register_evidence_with_contradiction_check,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.enums import TrustLabel
from packages.domain.events import EventType
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)

NOW = datetime(2026, 8, 15, 10, 0, 0, tzinfo=timezone.utc)


def _source(origin: str = "task:demo:artifact") -> SourceRecord:
    return SourceRecord(
        origin=origin,
        content_digest="sha256:aa",
        trust_label=TrustLabel.GENERATED,
        access_time=Timestamp(NOW),
    )


def _evidence(evidence_id: str = "ev-1") -> Evidence:
    return Evidence(
        id=evidence_id,
        source_ref="task:demo:artifact",
        content_digest="sha256:bb",
        captured_at=Timestamp(NOW),
        artifact_id="artifact-1",
    )


def _verified_claim(claim_id: str = "claim-1") -> Claim:
    return Claim(
        id=claim_id,
        statement="a measurable statement",
        status=ClaimStatus.VERIFIED,
        evidence_relations=[("ev-1", EvidenceRelationType.SUPPORTS)],
    )


def _refutes_relation(claim_id: str = "claim-1", evidence_id: str = "ev-2") -> EvidenceRelation:
    return EvidenceRelation(
        claim_id=claim_id,
        evidence_id=evidence_id,
        relation=EvidenceRelationType.REFUTES,
        strength=0.9,
    )


def _seeded_ledger(claim_status: ClaimStatus = ClaimStatus.VERIFIED) -> FakeEvidenceLedger:
    ledger = FakeEvidenceLedger()
    ledger.register_source(_source())
    ledger.register_evidence(_evidence("ev-1"))
    ledger.register_claim(replace(_verified_claim(), status=claim_status))
    ledger.attach_relation(
        EvidenceRelation(
            claim_id="claim-1",
            evidence_id="ev-1",
            relation=EvidenceRelationType.SUPPORTS,
        )
    )
    return ledger


class TestContradictionDetection:
    def test_refutes_verified_claim_becomes_disputed(self) -> None:
        ledger = _seeded_ledger()
        ledger.register_evidence(_evidence("ev-2"))
        outcome = register_evidence_with_contradiction_check(
            ledger, _evidence("ev-2"), _refutes_relation()
        )
        assert outcome.disputed is True
        assert outcome.claim.status is ClaimStatus.DISPUTED
        assert ledger.get_claim("claim-1").status is ClaimStatus.DISPUTED

    def test_refutes_proposed_claim_becomes_disputed(self) -> None:
        ledger = _seeded_ledger(ClaimStatus.PROPOSED)
        ledger.register_evidence(_evidence("ev-2"))
        outcome = register_evidence_with_contradiction_check(
            ledger, _evidence("ev-2"), _refutes_relation()
        )
        assert outcome.disputed is True

    def test_old_evidence_and_relations_preserved(self) -> None:
        ledger = _seeded_ledger()
        ledger.register_evidence(_evidence("ev-2"))
        register_evidence_with_contradiction_check(ledger, _evidence("ev-2"), _refutes_relation())
        # 旧支持证据与 relation 全部保留（矛盾不覆盖历史）
        assert ledger.get_evidence("ev-1") == _evidence("ev-1")
        relations = ledger.relations_for_claim("claim-1")
        assert {(relation.evidence_id, relation.relation) for relation in relations} == {
            ("ev-1", EvidenceRelationType.SUPPORTS),
            ("ev-2", EvidenceRelationType.REFUTES),
        }

    def test_supports_does_not_dispute(self) -> None:
        ledger = _seeded_ledger()
        ledger.register_evidence(_evidence("ev-2"))
        supports = EvidenceRelation(
            claim_id="claim-1",
            evidence_id="ev-2",
            relation=EvidenceRelationType.SUPPORTS,
        )
        outcome = register_evidence_with_contradiction_check(ledger, _evidence("ev-2"), supports)
        assert outcome.disputed is False
        assert ledger.get_claim("claim-1").status is ClaimStatus.VERIFIED

    def test_refutes_already_disputed_claim_stays_disputed(self) -> None:
        ledger = _seeded_ledger(ClaimStatus.DISPUTED)
        ledger.register_evidence(_evidence("ev-2"))
        outcome = register_evidence_with_contradiction_check(
            ledger, _evidence("ev-2"), _refutes_relation()
        )
        assert outcome.disputed is False
        assert ledger.get_claim("claim-1").status is ClaimStatus.DISPUTED


class TestContradictionAudit:
    def test_dispute_publishes_claim_disputed_event(self) -> None:
        publisher = FakeEventPublisher()
        ledger = _seeded_ledger()
        ledger.register_evidence(_evidence("ev-2"))
        register_evidence_with_contradiction_check(
            ledger,
            _evidence("ev-2"),
            _refutes_relation(),
            publisher=publisher,
            actor="gate:reviewer",
        )
        events = [
            envelope
            for envelope in publisher.published
            if envelope.event_type is EventType.CLAIM_DISPUTED
        ]
        assert len(events) == 1
        payload = events[0].payload
        assert payload["claim_id"] == "claim-1"
        assert payload["evidence_id"] == "ev-2"
        assert payload["relation"] == "REFUTES"
        assert events[0].actor == "gate:reviewer"
        assert events[0].scope == "claim:claim-1"

    def test_no_event_when_publisher_absent(self) -> None:
        ledger = _seeded_ledger()
        ledger.register_evidence(_evidence("ev-2"))
        outcome = register_evidence_with_contradiction_check(
            ledger, _evidence("ev-2"), _refutes_relation()
        )
        assert outcome.disputed is True


class TestContradictionProvenanceGate:
    """REFUTES 会改变 Claim 的 epistemic 状态，evidence 来源必须已登记。"""

    def test_refutes_with_unregistered_source_rejected(self) -> None:
        ledger = _seeded_ledger()
        ghost = Evidence(
            id="ev-ghost",
            source_ref="source:never-registered",
            content_digest="sha256:cc",
        )
        with pytest.raises(InvalidInputError, match="cannot refute"):
            register_evidence_with_contradiction_check(
                ledger,
                ghost,
                EvidenceRelation(
                    claim_id="claim-1",
                    evidence_id="ev-ghost",
                    relation=EvidenceRelationType.REFUTES,
                ),
            )
        # claim 状态未被 ghost evidence 改变
        assert ledger.get_claim("claim-1").status is ClaimStatus.VERIFIED
        # ghost evidence 的 relation 未挂上
        assert ledger.relations_for_claim("claim-1") == (
            EvidenceRelation(
                claim_id="claim-1",
                evidence_id="ev-1",
                relation=EvidenceRelationType.SUPPORTS,
            ),
        )
