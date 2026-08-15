"""Negative result 记忆用例（M10 DoD）：failed/null 结果是一等研究事实。

验证：SCIENTIFIC_NEGATIVE_RESULT 场景经 gate 写入 NEGATIVE_RESULT 记忆、
可查询、可与 REFUTES claim 关联（contradiction 链路），且不被删除。
"""

from __future__ import annotations

from adapters.fakes import (
    FakeEvidenceLedger,
    FakeMemoryStore,
    FakePolicyEvaluator,
)
from packages.application.evidence.contradiction import (
    register_evidence_with_contradiction_check,
)
from packages.application.memory.gate import MemoryGateDeps, commit_memory
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


def _ledger() -> FakeEvidenceLedger:
    ledger = FakeEvidenceLedger()
    ledger.register_source(
        SourceRecord(
            origin="experiment:exp-1:run",
            content_digest="sha256:neg",
            trust_label=TrustLabel.VERIFIED_SOURCE,
        )
    )
    ledger.register_evidence(
        Evidence(
            id="evidence:exp-1:null",
            source_ref="experiment:exp-1:run",
            content_digest="sha256:null",
            artifact_id="artifact:exp-1:metrics",
        )
    )
    ledger.register_claim(
        Claim(
            id="claim:hypothesis-1",
            statement="treatment improves outcome",
            status=ClaimStatus.PROPOSED,
            evidence_relations=[("evidence:exp-1:null", EvidenceRelationType.REFUTES)],
        )
    )
    return ledger


def _negative_proposal() -> MemoryWriteProposal:
    return MemoryWriteProposal(
        id="mem:neg-1",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.NEGATIVE_RESULT,
        content="treatment shows no significant effect (p=0.62)",
        provenance="experiment:exp-1:run",
        confidence=0.97,
    )


class TestNegativeResultMemory:
    def test_negative_result_written_through_gate_and_queryable(self) -> None:
        store = FakeMemoryStore()
        store.allow_source("experiment:exp-1:run")
        ledger = _ledger()
        deps = MemoryGateDeps(
            store=store,
            policy=FakePolicyEvaluator(),
            ledger=ledger,
        )
        result = commit_memory(_negative_proposal(), deps, curator_approved=True)
        assert result.accepted is True
        records = store.query(MemoryTier.PROJECT)
        assert len(records) == 1
        assert records[0].kind is MemoryType.NEGATIVE_RESULT
        assert records[0].active is True
        # negative result 检索：不被 canonical 丢弃
        assert store.get("mem:neg-1").content.startswith("treatment")

    def test_negative_result_contradicts_claim_via_refutes_relation(self) -> None:
        ledger = _ledger()
        outcome = register_evidence_with_contradiction_check(
            ledger,
            ledger.get_evidence("evidence:exp-1:null"),
            EvidenceRelation(
                claim_id="claim:hypothesis-1",
                evidence_id="evidence:exp-1:null",
                relation=EvidenceRelationType.REFUTES,
            ),
        )
        assert outcome.disputed is True
        assert ledger.get_claim("claim:hypothesis-1").status is ClaimStatus.DISPUTED
        # 旧 relation 保留（矛盾可回查）
        relations = ledger.relations_for_claim("claim:hypothesis-1")
        assert any(relation.relation is EvidenceRelationType.REFUTES for relation in relations)

    def test_negative_result_survives_lifecycle_inspection(self) -> None:
        """NEGATIVE_RESULT 记忆参与 deactivate（tombstone）而非静默消失。"""
        store = FakeMemoryStore()
        store.allow_source("experiment:exp-1:run")
        ledger = _ledger()
        deps = MemoryGateDeps(store=store, ledger=ledger)
        commit_memory(_negative_proposal(), deps, curator_approved=True)
        tombstone = store.deactivate("mem:neg-1")
        assert tombstone.active is False
        preserved = store.get("mem:neg-1")
        assert preserved.kind is MemoryType.NEGATIVE_RESULT
        assert preserved.active is False
