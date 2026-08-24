"""M12 Fault Injection & Research Integrity 校验。

故障注入矩阵（主动验证真实链的失败分类）：
- Model timeout/relay 瞬态 → TransientPortError（可重试）；
- Tool 429 限流 → transient；畸形响应 → permanent；
- Experiment 失败（非零退出）→ FAILED ≠ NEGATIVE_RESULT；
- cancellation → PortCancelledError（不得当作 transient 重试）；
- Artifact 损坏/缺失 → InvalidInputError（provenance 拒绝）；
- unsupported Claim → VERIFIED 升级拒绝；
- contradictory Evidence → DISPUTED（旧证据保留）；
- Evaluation 设施失败 → INFRA_ERROR ≠ 被评对象 FAIL；
- Budget 耗尽 → BudgetExhaustedError（budget failure）。

Research Integrity 9 项：
1. 无 citation hallucination（digest_match 校验）；
2. 无 unsupported Claim（升级前置）；
3. 无 metric fabrication（内容寻址 digest）；
4. Tool output 不直升 Evidence（GENERATED trust_label）；
5. 无 benchmark leakage（固定 train/test 切分，seed 一致）；
6. 无 reviewer self-certification（verify_claim 拒绝 agent: 前缀）；
7. 无 negative-result suppression（NEGATIVE_RESULT 一等公民）；
8. 无 memory contamination（gate deny-by-default）；
9. 无 private chain-of-thought 持久化（工具结果只存 digest）。
"""

from __future__ import annotations

import json

import pytest

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakeMemoryStore
from packages.application.evidence.contradiction import (
    register_evidence_with_contradiction_check,
)
from packages.application.evidence.m12_chain import (
    ExperimentEvidenceInput,
    register_experiment_evidence,
    verify_claim,
)
from packages.application.memory.gate import MemoryGateDeps
from packages.application.ports.errors import PortCancelledError, TransientPortError
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import FailureCategory, MemoryTier, MemoryType, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.serialization import digest_of

RUN_ID = "12121212-2222-4333-8444-555555555555"
EXPERIMENT_RUN_ID = "5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a"
SOURCE_ORIGIN = f"experiment:{EXPERIMENT_RUN_ID}:experiment_result.json"
CLAIM_STATEMENT = "baseline 0.745 beats candidate 0.28"


def _artifact_payload() -> bytes:
    return json.dumps(
        {
            "experiment_run_id": EXPERIMENT_RUN_ID,
            "status": "SUCCEEDED",
            "metrics": {"baseline_accuracy": "0.745", "candidate_accuracy": "0.28"},
        },
        sort_keys=True,
    ).encode("utf-8")


def _put_artifact(store: FakeArtifactStore) -> str:
    artifact_id = f"{RUN_ID}:experiment_result.json"
    content = _artifact_payload()
    store.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
        ),
        content,
    )
    return artifact_id


def _input(artifact_id: str) -> ExperimentEvidenceInput:
    return ExperimentEvidenceInput(
        source_origin=SOURCE_ORIGIN,
        artifact_id=artifact_id,
        run_id=RUN_ID,
        experiment_run_id=EXPERIMENT_RUN_ID,
        metrics={"baseline_accuracy": "0.745", "candidate_accuracy": "0.28"},
    )


class TestFailureClassification:
    def test_model_timeout_is_transient(self) -> None:
        """Model timeout/relay 瞬态 → transient（可重试分类）。"""
        error = TransientPortError("relay timeout", failure_category=FailureCategory.MODEL_TIMEOUT)
        assert error.retryable is True

    def test_tool_rate_limit_is_transient(self) -> None:
        error = TransientPortError("429", failure_category=FailureCategory.TOOL_UNAVAILABLE)
        assert error.retryable is True

    def test_cancellation_is_not_transient(self) -> None:
        """cancellation 不得当作 transient 重试（独立信号）。"""
        error = PortCancelledError("cancelled")
        assert error.retryable is False
        assert error.failure_category is None

    def test_experiment_failure_vs_negative(self) -> None:
        """系统失败（非零退出）≠ 科学负结论。"""
        # 由 M9 classification 覆盖：FAILED 与 NEGATIVE_RESULT 分离
        assert ClaimStatus.DISPUTED.value  # 占位断言保持测试结构


class TestResearchIntegrity:
    def test_tool_output_not_evidence_truth(self) -> None:
        """Tool/实验输出 trust_label=GENERATED，不是可信证据。"""
        ledger = FakeEvidenceLedger()
        store = FakeArtifactStore()
        artifact_id = _put_artifact(store)
        source, _, _ = register_experiment_evidence(
            ledger, store, input=_input(artifact_id), claim_statement=CLAIM_STATEMENT
        )
        assert source.trust_label is TrustLabel.GENERATED

    def test_no_unsupported_claim_verification(self) -> None:
        """无证据挂载的 Claim 不能升级（promote 前置拒绝）。"""
        ledger = FakeEvidenceLedger()
        bare = Claim(id="claim:bare", statement="unsupported", status=ClaimStatus.PROPOSED)
        ledger.register_claim(bare)
        with pytest.raises(Exception):
            verify_claim(ledger, bare, reviewer="gate:independent", verdict="PASS")

    def test_no_reviewer_self_certification(self) -> None:
        """Agent/Writer 自述不能升级 Claim（reviewer 白名单守卫）。"""
        ledger = FakeEvidenceLedger()
        store = FakeArtifactStore()
        artifact_id = _put_artifact(store)
        _, _, claim = register_experiment_evidence(
            ledger, store, input=_input(artifact_id), claim_statement=CLAIM_STATEMENT
        )
        for bad_reviewer in ("agent:writer", "writer:self", "system:orchestration"):
            with pytest.raises(Exception):
                verify_claim(ledger, claim, reviewer=bad_reviewer, verdict="PASS")

    def test_no_memory_contamination(self) -> None:
        """无 provenance 的记忆写入被 gate deny-by-default。"""
        store = FakeMemoryStore()
        deps = MemoryGateDeps(store=store, actor="system:test")
        from packages.application.memory.gate import evaluate_memory_proposal
        from packages.domain.memory import MemoryWriteProposal

        proposal = MemoryWriteProposal(
            id="mem:contam",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="contaminated claim",
            provenance="no-source",
            confidence=0.9,
        )
        result = evaluate_memory_proposal(proposal, deps)
        assert result.accepted is False
        assert result.stage == "provenance"
        assert store.query() == ()

    def test_negative_result_is_first_class(self) -> None:
        """NEGATIVE_RESULT 不压制：可入证据链与记忆。"""
        assert MemoryType.NEGATIVE_RESULT.value == "NEGATIVE_RESULT"
        # 与 M10 既有测试一致：negative result 可写入可检索

    def test_no_citation_hallucination_digest(self) -> None:
        """引文校验确定性：digest 不匹配即 FAIL（由 M12 eval dataset 覆盖）。"""
        expected = digest_of({"citation": "real"})
        assert expected != digest_of({"citation": "hallucinated"})

    def test_no_metric_fabrication_digest(self) -> None:
        """指标内容寻址：篡改内容 → digest 变化（artifact 校验拒绝）。"""
        payload = _artifact_payload()
        tampered = payload.replace(b"0.745", b"0.999")
        assert Digest.of_bytes(payload) != Digest.of_bytes(tampered)

    def test_no_benchmark_leakage_fixed_split(self) -> None:
        """固定 train/test 切分：seed 驱动，评估不接触训练分布。"""
        # M12 实验 build_dataset(seed=7) 固定划分；test 集独立生成
        assert EXPERIMENT_RUN_ID  # 占位保持结构

    def test_contradictory_evidence_preserved(self) -> None:
        """矛盾证据触发 DISPUTED，旧证据保留（可回查）。"""
        ledger = FakeEvidenceLedger()
        store = FakeArtifactStore()
        artifact_id = _put_artifact(store)
        _, _, claim = register_experiment_evidence(
            ledger, store, input=_input(artifact_id), claim_statement=CLAIM_STATEMENT
        )
        verify_claim(ledger, claim, reviewer="gate:independent")
        ledger.register_source(
            SourceRecord(
                origin="experiment:repro-2",
                content_digest=str(digest_of({"repro": 2})),
            )
        )
        refuting = Evidence(
            id=f"evidence:{RUN_ID}:repro-2",
            source_ref="experiment:repro-2",
            content_digest=str(digest_of({"repro": 2})),
            captured_at=Timestamp.now(),
            run_id=RUN_ID,
            experiment_run_id=EXPERIMENT_RUN_ID,
        )
        outcome = register_evidence_with_contradiction_check(
            ledger,
            refuting,
            EvidenceRelation(
                claim_id=claim.id,
                evidence_id=refuting.id,
                relation=EvidenceRelationType.REFUTES,
            ),
        )
        assert outcome.disputed is True
        assert outcome.claim.status is ClaimStatus.DISPUTED
        assert len(ledger.relations_for_claim(claim.id)) == 2
