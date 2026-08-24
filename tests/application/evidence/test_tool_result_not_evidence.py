"""ToolResult != Evidence：工具结果必须经正式准入进入 Evidence 链（M12-R1 WP2）。

验证：
- ToolResultRecord 不能直接注册为 Evidence（必须经 SourceRecord 登记前置）；
- register_tool_evidence 成功路径：spill 产物 → SourceRecord(GENERATED) → Evidence；
- 未 spill / 内容篡改 / 非成功状态拒绝（provenance 前置 + 内容寻址）；
- 工具证据绑定 run_id / manifest_digest / tool_refs（provenance 完整）。
"""

from __future__ import annotations

import json

import pytest

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.evidence.tool_evidence import (
    ToolEvidenceInput,
    register_tool_evidence,
    source_origin_for,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.tool_plane.results import spill_large_result
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ToolResultStatus, TrustLabel
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.tools import ToolCallRecord, ToolResultRecord

RUN_ID = "12121212-2222-4333-8444-555555555555"
MANIFEST_DIGEST = "sha256:manifest-frozen"
TASK_ID = "task-m12-discovery"
OPERATION_KEY = "literature-search-1"


def _call() -> ToolCallRecord:
    return ToolCallRecord(
        task_id=TASK_ID,
        attempt=1,
        operation_key=OPERATION_KEY,
        tool_id="literature_search",
        capability="literature.search",
        argument_digest=Digest.of_bytes(b'{"query": "tfidf text classification"}'),
    )


def _payload() -> bytes:
    return json.dumps(
        {"count": 754, "ids": ["38234567", "38234568", "38234569"], "query": "tfidf"},
        sort_keys=True,
    ).encode("utf-8")


def _spilled() -> tuple[ToolResultRecord, FakeArtifactStore]:
    store = FakeArtifactStore()
    outcome = spill_large_result(store, _call(), _payload(), threshold_bytes=1)
    assert outcome.spilled and outcome.artifact_ref is not None
    return outcome.record, store


class TestToolResultIsNotEvidence:
    def test_tool_result_cannot_reach_verified_claim_without_ingestion(self) -> None:
        """绕过正式 ingestion 直写 Evidence 无法升级 VERIFIED（无 bypass）。

        底层 register_evidence 是内部 API（登记面宽松）；provenance 不变量
        在升级面强制：直写 Evidence（source 未登记）的 claim 无法 VERIFIED。
        """
        ledger = FakeEvidenceLedger()
        record, _ = _spilled()
        ledger.register_evidence(
            Evidence(
                id=f"evidence:{RUN_ID}:direct",
                source_ref=f"tool:literature_search:{TASK_ID}:{OPERATION_KEY}",
                content_digest=str(record.output_digest),
                captured_at=Timestamp.now(),
                run_id=RUN_ID,
            )
        )
        ghost = Claim(
            id=f"claim:{RUN_ID}:direct",
            statement="unsupported tool claim",
            status=ClaimStatus.PROPOSED,
            evidence_relations=[(f"evidence:{RUN_ID}:direct", EvidenceRelationType.SUPPORTS)],
        )
        ledger.register_claim(ghost)
        # 升级 VERIFIED：evidence 的 source 未登记 → 拒绝
        with pytest.raises(InvalidInputError, match="not registered"):
            ledger.update_claim(
                Claim(
                    id=f"claim:{RUN_ID}:direct",
                    statement="unsupported tool claim",
                    status=ClaimStatus.VERIFIED,
                    evidence_relations=[
                        (f"evidence:{RUN_ID}:direct", EvidenceRelationType.SUPPORTS)
                    ],
                )
            )

    def test_register_tool_evidence_full_path(self) -> None:
        ledger = FakeEvidenceLedger()
        record, store = _spilled()
        source, evidence = register_tool_evidence(
            ledger,
            store,
            input=ToolEvidenceInput(
                result=record,
                run_id=RUN_ID,
                manifest_digest=MANIFEST_DIGEST,
                tool_refs=("literature_search",),
            ),
        )
        assert source.origin == source_origin_for(record)
        assert source.trust_label is TrustLabel.GENERATED
        assert source.content_digest == str(record.output_digest)
        assert evidence.artifact_id == f"tool-result:{TASK_ID}:{OPERATION_KEY}:literature_search"
        assert evidence.run_id == RUN_ID
        assert evidence.manifest_digest == MANIFEST_DIGEST
        assert evidence.tool_refs == ("literature_search",)
        # ledger 侧可追溯
        assert ledger.has_source(source.origin)
        assert ledger.get_evidence(evidence.id) == evidence

    def test_register_requires_spilled_artifact(self) -> None:
        """未 spill 的结果（无 artifact 内容）拒绝——无内容可采信。"""
        ledger = FakeEvidenceLedger()
        store = FakeArtifactStore()
        record = ToolResultRecord(
            task_id=TASK_ID,
            attempt=1,
            operation_key=OPERATION_KEY,
            tool_id="literature_search",
            status=ToolResultStatus.SUCCEEDED,
            output_digest=Digest.of_bytes(_payload()),
            recorded_at=Timestamp.now(),
        )
        with pytest.raises(Exception, match="unknown artifact"):
            register_tool_evidence(
                ledger,
                store,
                input=ToolEvidenceInput(result=record, run_id=RUN_ID),
            )

    def test_register_rejects_tampered_content(self) -> None:
        ledger = FakeEvidenceLedger()
        record, store = _spilled()
        # 篡改已 spill 的 artifact 内容（digest 不匹配）
        artifact_id = f"tool-result:{TASK_ID}:{OPERATION_KEY}:literature_search"
        tampered = b"tampered"
        store.put(
            Artifact(
                id=artifact_id,
                digest=Digest.of_bytes(tampered),
                size_bytes=len(tampered),
                media_type="application/json",
            ),
            tampered,
        )
        with pytest.raises(ValueError, match="digest mismatch"):
            register_tool_evidence(
                ledger,
                store,
                input=ToolEvidenceInput(result=record, run_id=RUN_ID),
            )

    def test_register_rejects_non_success_status(self) -> None:
        ledger = FakeEvidenceLedger()
        _, store = _spilled()
        failed = ToolResultRecord(
            task_id=TASK_ID,
            attempt=1,
            operation_key=OPERATION_KEY,
            tool_id="literature_search",
            status=ToolResultStatus.FAILED,
            failure_category=None,
            error_message_redacted="ncbi rate limited",
            recorded_at=Timestamp.now(),
        )
        with pytest.raises(ValueError, match="status FAILED"):
            register_tool_evidence(
                ledger,
                store,
                input=ToolEvidenceInput(result=failed, run_id=RUN_ID),
            )

    def test_source_registration_conflict_detected(self) -> None:
        """同 origin 重复登记内容不一致 → 拒绝（防静默漂移）。"""
        ledger = FakeEvidenceLedger()
        record, store = _spilled()
        register_tool_evidence(
            ledger,
            store,
            input=ToolEvidenceInput(result=record, run_id=RUN_ID),
        )
        with pytest.raises(InvalidInputError, match="conflicting"):
            ledger.register_source(
                SourceRecord(
                    origin=source_origin_for(record),
                    content_digest="sha256:different",
                )
            )
