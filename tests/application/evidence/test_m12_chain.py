"""M12 Evidence Chain E2E：实验产物 → Source → Evidence → Claim → Memory。

验证 M10 治理链在真实产物上的完整路径：
- artifact 内容寻址校验（篡改拒绝）；
- Source trust_label=GENERATED（非可信，ToolResult 不直升 Evidence）；
- Evidence 绑定 artifact/run/experiment_run/image/snapshot/metrics（N003 闭合）；
- Claim PROPOSED → VERIFIED（VerificationBasis gate 前置，Agent 自述不能升级）；
- REFUTES 冲突 → DISPUTED（旧证据保留，provenance 前置）；
- Memory gate：无 provenance 拒绝、无 curator 拒绝、curator 通过三类路径；
- NEGATIVE_RESULT 记忆可入账（科学负结论为一等事实）。
"""

from __future__ import annotations

import pytest

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.evidence.m12_chain import (
    ContradictionInput,
    ExperimentEvidenceInput,
    MemoryProposalInput,
    propose_and_commit_memory,
    register_contradicting_evidence,
    register_experiment_evidence,
    summarize_evidence_chain,
    verify_claim,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.evidence import ClaimStatus, EvidenceRelationType, SourceRecord
from packages.domain.serialization import digest_of
from tests.application.evidence.m12_chain_fixtures import (
    CLAIM_STATEMENT,
    EXPERIMENT_RUN_ID,
    RUN_ID,
    SOURCE_ORIGIN,
    evidence_input,
    memory_deps,
    put_artifact,
)


class TestSourceEvidenceClaim:
    def test_full_chain_to_verified(self) -> None:
        ledger = FakeEvidenceLedger()
        store = FakeArtifactStore()
        input_ = evidence_input(artifact_id=put_artifact(store))
        source, evidence, claim = register_experiment_evidence(
            ledger, store, input=input_, claim_statement=CLAIM_STATEMENT
        )
        assert source.trust_label.value == "GENERATED"
        assert evidence.artifact_id == input_.artifact_id
        assert evidence.experiment_run_id == EXPERIMENT_RUN_ID
        assert evidence.image_digest is not None
        assert evidence.workspace_snapshot_before is not None
        assert evidence.workspace_snapshot_after is not None
        assert claim.status is ClaimStatus.PROPOSED
        verified = verify_claim(ledger, claim, reviewer="gate:acceptance", verdict="PASS")
        assert verified.status is ClaimStatus.VERIFIED
        summary = summarize_evidence_chain(ledger, RUN_ID)
        assert summary["claim_status"] == "VERIFIED"
        evidence_ids = summary["evidence_ids"]
        assert isinstance(evidence_ids, tuple) and len(evidence_ids) == 1

    def test_artifact_tampering_rejected(self) -> None:
        ledger = FakeEvidenceLedger()
        store = FakeArtifactStore()
        artifact_id = put_artifact(store)
        # 篡改 artifact 内容（digest 不匹配）
        store.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(b"tampered"),
                size_bytes=8,
                media_type="application/json",
            ),
            b"tampered",
        )
        with pytest.raises(Exception):
            register_experiment_evidence(
                ledger,
                store,
                input=evidence_input(artifact_id=artifact_id),
                claim_statement=CLAIM_STATEMENT,
            )

    def test_experiment_run_id_mismatch_rejected(self) -> None:
        ledger = FakeEvidenceLedger()
        store = FakeArtifactStore()
        artifact_id = put_artifact(store)
        mismatched = ExperimentEvidenceInput(
            source_origin=SOURCE_ORIGIN,
            artifact_id=artifact_id,
            run_id=RUN_ID,
            experiment_run_id="99999999-2222-4333-8444-555555555555",
        )
        with pytest.raises(Exception):
            register_experiment_evidence(
                ledger, store, input=mismatched, claim_statement=CLAIM_STATEMENT
            )

    def test_agent_self_report_cannot_verify(self) -> None:
        ledger = FakeEvidenceLedger()
        store = FakeArtifactStore()
        input_ = evidence_input(artifact_id=put_artifact(store))
        _, _, claim = register_experiment_evidence(
            ledger, store, input=input_, claim_statement=CLAIM_STATEMENT
        )
        with pytest.raises(Exception):
            verify_claim(ledger, claim, reviewer="agent:self", verdict="PASS")


class TestContradiction:
    def test_refutes_disputes_verified_claim(self) -> None:
        ledger = FakeEvidenceLedger()
        store = FakeArtifactStore()
        input_ = evidence_input(artifact_id=put_artifact(store))
        _, _, claim = register_experiment_evidence(
            ledger, store, input=input_, claim_statement=CLAIM_STATEMENT
        )
        verify_claim(ledger, claim, reviewer="gate:acceptance")
        disputed = register_contradicting_evidence(
            ledger,
            input=ContradictionInput(
                source_origin=f"experiment:{EXPERIMENT_RUN_ID}:repro-2",
                evidence_id=f"evidence:{RUN_ID}:repro-2",
                claim=ledger.get_claim(f"claim:{RUN_ID}"),
                content_digest=str(digest_of({"repro": 2})),
                run_id=RUN_ID,
                experiment_run_id=EXPERIMENT_RUN_ID,
            ),
        )
        assert disputed.status is ClaimStatus.DISPUTED
        # 旧证据保留
        relations = ledger.relations_for_claim(disputed.id)
        assert len(relations) == 2

    def test_refutes_requires_registered_source(self) -> None:
        ledger = FakeEvidenceLedger()
        store = FakeArtifactStore()
        input_ = evidence_input(artifact_id=put_artifact(store))
        _, _, claim = register_experiment_evidence(
            ledger, store, input=input_, claim_statement=CLAIM_STATEMENT
        )
        # 直接调用底层 contradiction use case：REFUTES 的 evidence source
        # 未在 ledger 登记 → 拒绝（provenance 前置）
        from packages.application.evidence.contradiction import (
            register_evidence_with_contradiction_check,
        )
        from packages.domain.core import Timestamp
        from packages.domain.evidence import Evidence, EvidenceRelation

        ghost = Evidence(
            id=f"evidence:{RUN_ID}:ghost",
            source_ref="unregistered-origin",
            content_digest=str(digest_of({"x": 1})),
            captured_at=Timestamp.now(),
            run_id=RUN_ID,
            experiment_run_id=EXPERIMENT_RUN_ID,
        )
        with pytest.raises(Exception):
            register_evidence_with_contradiction_check(
                ledger,
                ghost,
                EvidenceRelation(
                    claim_id=claim.id,
                    evidence_id=ghost.id,
                    relation=EvidenceRelationType.REFUTES,
                ),
            )


class TestGovernedMemory:
    def test_no_provenance_rejected(self) -> None:
        deps, store, _ = memory_deps()
        memory_id = propose_and_commit_memory(
            deps,
            input=MemoryProposalInput(
                memory_id="mem:no-provenance",
                content="baseline wins",
                provenance="unregistered-origin",
            ),
        )
        assert memory_id is None
        assert store.query() == ()

    def test_project_tier_requires_curator(self) -> None:
        deps, store, ledger = memory_deps()
        ledger.register_source(
            SourceRecord(
                origin="experiment:exp:artifact",
                content_digest=str(digest_of({"x": 1})),
            )
        )
        store.allow_source("experiment:exp:artifact")
        memory_id = propose_and_commit_memory(
            deps,
            input=MemoryProposalInput(
                memory_id="mem:no-curator",
                content="baseline wins",
                provenance="experiment:exp:artifact",
            ),
        )
        assert memory_id is None
        assert store.query() == ()

    def test_curator_approved_commits(self) -> None:
        deps, store, ledger = memory_deps()
        ledger.register_source(
            SourceRecord(
                origin="experiment:exp:artifact",
                content_digest=str(digest_of({"x": 1})),
            )
        )
        store.allow_source("experiment:exp:artifact")
        memory_id = propose_and_commit_memory(
            deps,
            input=MemoryProposalInput(
                memory_id="mem:committed",
                content="baseline tfidf beats hash-embedding on low-resource subset",
                provenance="experiment:exp:artifact",
                kind=MemoryType.FACT,
                tier=MemoryTier.PROJECT,
                curator_approved=True,
            ),
        )
        assert memory_id == "mem:committed"
        assert len(store.query()) == 1

    def test_negative_result_memory_is_first_class(self) -> None:
        deps, store, ledger = memory_deps()
        ledger.register_source(
            SourceRecord(
                origin="experiment:exp:negative",
                content_digest=str(digest_of({"effect": 2})),
            )
        )
        store.allow_source("experiment:exp:negative")
        memory_id = propose_and_commit_memory(
            deps,
            input=MemoryProposalInput(
                memory_id="mem:negative",
                content="hash-embedding candidate did not improve over tfidf baseline",
                provenance="experiment:exp:negative",
                kind=MemoryType.NEGATIVE_RESULT,
                tier=MemoryTier.PROJECT,
                confidence=0.97,
                curator_approved=True,
            ),
        )
        assert memory_id == "mem:negative"
        record = store.get("mem:negative")
        assert record.kind is MemoryType.NEGATIVE_RESULT
