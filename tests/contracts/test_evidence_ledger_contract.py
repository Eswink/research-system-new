"""EvidenceLedger 契约测试：登记/查询/引用完整性语义。"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from adapters.fakes import FakeEvidenceLedger
from packages.application.ports.errors import InvalidInputError
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


def _claim(claim_id: str = "claim-1") -> Claim:
    return Claim(
        id=claim_id,
        statement="a measurable statement",
        status=ClaimStatus.PROPOSED,
        evidence_relations=[("ev-1", EvidenceRelationType.SUPPORTS)],
    )


def _relation() -> EvidenceRelation:
    return EvidenceRelation(
        claim_id="claim-1",
        evidence_id="ev-1",
        relation=EvidenceRelationType.SUPPORTS,
        strength=0.9,
    )


class TestEvidenceLedgerContract:
    def test_register_and_get_roundtrip(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_source(_source())
        ledger.register_evidence(_evidence())
        ledger.register_claim(_claim())
        assert ledger.get_source("task:demo:artifact") == _source()
        assert ledger.get_evidence("ev-1") == _evidence()
        assert ledger.get_claim("claim-1") == _claim()
        assert ledger.has_source("task:demo:artifact") is True
        assert ledger.has_source("missing:source") is False

    def test_idempotent_re_registration_allowed(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_source(_source())
        ledger.register_source(_source())
        assert ledger.get_source("task:demo:artifact") == _source()

    def test_conflicting_re_registration_rejected(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_evidence(_evidence())
        conflicting = replace(_evidence(), content_digest="sha256:cc")
        with pytest.raises(InvalidInputError, match="conflicting"):
            ledger.register_evidence(conflicting)

    def test_unknown_lookups_rejected(self) -> None:
        ledger = FakeEvidenceLedger()
        with pytest.raises(InvalidInputError):
            ledger.get_source("missing:source")
        with pytest.raises(InvalidInputError):
            ledger.get_evidence("missing-ev")
        with pytest.raises(InvalidInputError):
            ledger.get_claim("missing-claim")

    def test_attach_relation_and_query(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_evidence(_evidence())
        ledger.register_claim(_claim())
        ledger.attach_relation(_relation())
        relations = ledger.relations_for_claim("claim-1")
        assert relations == (_relation(),)

    def test_attach_relation_duplicate_dedupes(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_evidence(_evidence())
        ledger.register_claim(_claim())
        ledger.attach_relation(_relation())
        ledger.attach_relation(_relation())
        assert len(ledger.relations_for_claim("claim-1")) == 1

    def test_attach_relation_requires_known_claim_and_evidence(self) -> None:
        ledger = FakeEvidenceLedger()
        with pytest.raises(InvalidInputError):
            ledger.attach_relation(_relation())
        ledger.register_claim(_claim())
        with pytest.raises(InvalidInputError):
            ledger.attach_relation(_relation())

    def test_update_claim_transitions_status(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_source(_source())
        ledger.register_evidence(_evidence())
        ledger.register_claim(_claim())
        verified = replace(_claim(), status=ClaimStatus.VERIFIED)
        ledger.update_claim(verified)
        assert ledger.get_claim("claim-1").status is ClaimStatus.VERIFIED

    def test_update_claim_to_verified_requires_registered_evidence(self) -> None:
        """VERIFIED 的 provenance 不变量在登记面强制：ghost evidence 拒绝。"""
        ledger = FakeEvidenceLedger()
        ledger.register_claim(_claim())
        verified = replace(_claim(), status=ClaimStatus.VERIFIED)
        with pytest.raises(InvalidInputError, match="unknown evidence"):
            ledger.update_claim(verified)

    def test_register_verified_claim_requires_registered_evidence_and_source(self) -> None:
        ledger = FakeEvidenceLedger()
        verified = replace(_claim(), status=ClaimStatus.VERIFIED)
        with pytest.raises(InvalidInputError, match="unknown evidence"):
            ledger.register_claim(verified)
        ledger.register_evidence(_evidence())
        with pytest.raises(InvalidInputError, match="not registered"):
            ledger.register_claim(verified)
        ledger.register_source(_source())
        ledger.register_claim(verified)
        assert ledger.get_claim("claim-1").status is ClaimStatus.VERIFIED

    def test_update_unknown_claim_rejected(self) -> None:
        ledger = FakeEvidenceLedger()
        with pytest.raises(InvalidInputError):
            ledger.update_claim(_claim())

    def test_claims_snapshot(self) -> None:
        ledger = FakeEvidenceLedger()
        ledger.register_claim(_claim("claim-a"))
        ledger.register_claim(_claim("claim-b"))
        assert {claim.id for claim in ledger.claims()} == {"claim-a", "claim-b"}
