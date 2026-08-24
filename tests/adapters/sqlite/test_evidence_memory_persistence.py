"""SqliteEvidenceLedger / SqliteMemoryStore 持久化与契约专项（M12-R1 WP9）。

验证：
- 跨连接重启后 claim/evidence/source/relations/memory 可恢复（生产链证据不丢）；
- close 后调用抛 PermanentPortError（PORTS.md resource cleanup）；
- VERIFIED provenance 不变量在 SQLite 面同样强制（防绕过直写升级）；
- 与 Fake 语义一致：同键冲突拒绝、deny-by-default、重复 commit 拒绝。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
from adapters.sqlite.memory_store import SqliteMemoryStore
from packages.application.ports.errors import InvalidInputError, PermanentPortError
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.memory import MemoryWriteProposal


def _source(origin: str = "experiment:run-1:result.json") -> SourceRecord:
    return SourceRecord(
        origin=origin,
        content_digest="sha256:source-digest",
        trust_label=TrustLabel.GENERATED,
        access_time=Timestamp.now(),
        parser_version="m12-evidence-v1",
    )


def _evidence(evidence_id: str = "evidence:run-1") -> Evidence:
    return Evidence(
        id=evidence_id,
        source_ref="experiment:run-1:result.json",
        content_digest="sha256:source-digest",
        captured_at=Timestamp.now(),
        artifact_id="run-1:experiment_result.json",
        run_id="run-1",
        experiment_run_id="5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a",
        metric_refs=("metric:run-1:baseline_accuracy",),
        image_digest="sha256:image",
        manifest_digest="sha256:manifest",
    )


def _populate(ledger: SqliteEvidenceLedger) -> Claim:
    ledger.register_source(_source())
    ledger.register_evidence(_evidence())
    claim = Claim(
        id="claim:run-1",
        statement="baseline outperforms candidate",
        status=ClaimStatus.PROPOSED,
        author="system:m12",
        evidence_relations=[("evidence:run-1", EvidenceRelationType.SUPPORTS)],
    )
    ledger.register_claim(claim)
    ledger.attach_relation(
        EvidenceRelation(
            claim_id="claim:run-1",
            evidence_id="evidence:run-1",
            relation=EvidenceRelationType.SUPPORTS,
            strength=0.95,
        )
    )
    return claim


class TestSqliteEvidenceLedgerPersistence:
    def test_survives_connection_reopen(self, tmp_path: Path) -> None:
        db = str(tmp_path / "evidence.sqlite")
        ledger = SqliteEvidenceLedger(db)
        _populate(ledger)
        ledger.close()

        reopened = SqliteEvidenceLedger(db)
        claim = reopened.get_claim("claim:run-1")
        assert claim.status is ClaimStatus.PROPOSED
        evidence = reopened.get_evidence("evidence:run-1")
        assert evidence.artifact_id == "run-1:experiment_result.json"
        assert evidence.manifest_digest == "sha256:manifest"
        source = reopened.get_source("experiment:run-1:result.json")
        assert source.trust_label is TrustLabel.GENERATED
        relations = reopened.relations_for_claim("claim:run-1")
        assert len(relations) == 1
        assert relations[0].relation is EvidenceRelationType.SUPPORTS
        assert reopened.claims() == (claim,)
        reopened.close()

    def test_close_then_call_raises(self) -> None:
        ledger = SqliteEvidenceLedger(":memory:")
        ledger.close()
        with pytest.raises(PermanentPortError):
            ledger.claims()

    def test_verified_provenance_invariant_enforced(self) -> None:
        ledger = SqliteEvidenceLedger(":memory:")
        # 直接登记 VERIFIED claim，但 evidence 未登记 → 拒绝（防绕过直写升级）
        ghost = Claim(
            id="claim:ghost",
            statement="unsupported",
            status=ClaimStatus.VERIFIED,
            evidence_relations=[("evidence:missing", EvidenceRelationType.SUPPORTS)],
        )
        with pytest.raises(InvalidInputError, match="unknown evidence"):
            ledger.register_claim(ghost)
        # evidence 登记了但 source 未登记 → 拒绝
        ledger.register_evidence(_evidence("evidence:no-source"))
        broken = Claim(
            id="claim:no-source",
            statement="unsupported",
            status=ClaimStatus.VERIFIED,
            evidence_relations=[("evidence:no-source", EvidenceRelationType.SUPPORTS)],
        )
        with pytest.raises(InvalidInputError, match="not registered"):
            ledger.register_claim(broken)
        # 合法路径：source + evidence + PROPOSED → update 为 VERIFIED 成功
        ledger.register_source(_source())
        ledger.register_evidence(_evidence("evidence:ok"))
        ok = Claim(
            id="claim:ok",
            statement="supported",
            status=ClaimStatus.PROPOSED,
            evidence_relations=[("evidence:ok", EvidenceRelationType.SUPPORTS)],
        )
        ledger.register_claim(ok)
        ledger.update_claim(
            Claim(
                id="claim:ok",
                statement="supported",
                status=ClaimStatus.VERIFIED,
                evidence_relations=[("evidence:ok", EvidenceRelationType.SUPPORTS)],
            )
        )
        assert ledger.get_claim("claim:ok").status is ClaimStatus.VERIFIED

    def test_conflicting_registration_rejected(self) -> None:
        ledger = SqliteEvidenceLedger(":memory:")
        ledger.register_source(_source())
        with pytest.raises(InvalidInputError, match="conflicting"):
            ledger.register_source(
                SourceRecord(
                    origin="experiment:run-1:result.json",
                    content_digest="sha256:different",
                )
            )

    def test_attach_relation_requires_both_sides(self) -> None:
        ledger = SqliteEvidenceLedger(":memory:")
        with pytest.raises(InvalidInputError, match="unknown claim"):
            ledger.attach_relation(
                EvidenceRelation(
                    claim_id="claim:missing",
                    evidence_id="evidence:missing",
                    relation=EvidenceRelationType.SUPPORTS,
                )
            )
        _populate(ledger)
        with pytest.raises(InvalidInputError, match="unknown evidence"):
            ledger.attach_relation(
                EvidenceRelation(
                    claim_id="claim:run-1",
                    evidence_id="evidence:ghost",
                    relation=EvidenceRelationType.REFUTES,
                )
            )


class TestSqliteMemoryStorePersistence:
    def test_survives_connection_reopen(self, tmp_path: Path) -> None:
        db = str(tmp_path / "memory.sqlite")
        store = SqliteMemoryStore(db, allowed_sources=("experiment:run-1:result.json",))
        record = store.commit(
            MemoryWriteProposal(
                id="mem:run-1:negative-result",
                tier=MemoryTier.PROJECT,
                kind=MemoryType.NEGATIVE_RESULT,
                content="candidate did not beat baseline",
                provenance="experiment:run-1:result.json",
                confidence=0.97,
            )
        )
        assert record.id == "mem:run-1:negative-result"
        store.close()

        reopened = SqliteMemoryStore(db, allowed_sources=("experiment:run-1:result.json",))
        got = reopened.get("mem:run-1:negative-result")
        assert got.kind is MemoryType.NEGATIVE_RESULT
        assert got.tier is MemoryTier.PROJECT
        assert got.active is True
        assert len(reopened.query()) == 1
        # tombstone 语义持久化
        tombstone = reopened.deactivate("mem:run-1:negative-result")
        assert tombstone.active is False
        assert reopened.get("mem:run-1:negative-result").active is False
        reopened.delete("mem:run-1:negative-result")
        with pytest.raises(InvalidInputError):
            reopened.get("mem:run-1:negative-result")
        reopened.close()

    def test_deny_by_default_and_duplicate_rejected(self) -> None:
        store = SqliteMemoryStore(":memory:")
        with pytest.raises(InvalidInputError, match="deny by default"):
            store.commit(
                MemoryWriteProposal(
                    id="mem:x",
                    tier=MemoryTier.PROJECT,
                    kind=MemoryType.FACT,
                    content="x",
                    provenance="anything",
                    confidence=0.5,
                )
            )
        store.allow_source("source:ok")
        proposal = MemoryWriteProposal(
            id="mem:x",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="x",
            provenance="source:ok",
            confidence=0.5,
        )
        store.commit(proposal)
        with pytest.raises(InvalidInputError, match="already committed"):
            store.commit(proposal)
        with pytest.raises(InvalidInputError, match="gate rejected"):
            store.commit(
                MemoryWriteProposal(
                    id="mem:y",
                    tier=MemoryTier.PROJECT,
                    kind=MemoryType.FACT,
                    content="y",
                    provenance="source:not-allowed",
                    confidence=0.5,
                )
            )

    def test_close_then_call_raises(self) -> None:
        store = SqliteMemoryStore(":memory:")
        store.close()
        with pytest.raises(PermanentPortError):
            store.query()

    def test_shared_connection_with_evidence_ledger(self) -> None:
        """同一 sqlite3 连接共享事务边界（clean-run 组合根场景）。"""
        connection = sqlite3.connect(":memory:")
        ledger = SqliteEvidenceLedger(connection)
        store = SqliteMemoryStore(connection, allowed_sources=("experiment:run-1:result.json",))
        _populate(ledger)
        store.commit(
            MemoryWriteProposal(
                id="mem:shared",
                tier=MemoryTier.PROJECT,
                kind=MemoryType.NEGATIVE_RESULT,
                content="shared connection commit",
                provenance="experiment:run-1:result.json",
                confidence=0.9,
            )
        )
        assert ledger.get_claim("claim:run-1").id == "claim:run-1"
        assert store.get("mem:shared").content == "shared connection commit"
        ledger.close()
        store.close()
