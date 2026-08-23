"""Deliverable from persisted state（M12-R1 WP3）。

验证：
- 报告事实全部来自持久状态（artifact digest 重算 / claim / memory / budget /
  eval / audit），无代码内常量；
- 空/缺失状态 → DeliverableBuildError（不静默降级）；
- 篡改 artifact 内容 → digest 不一致，报告反映真实状态；
- 基于同一 run_id 两次重建报告一致（确定性 render）；
- budget 段只读 ledger entries，不虚构 reservation 一致性。
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from adapters.fakes import (
    FakeArtifactStore,
    FakeBudgetLedger,
    FakeEvidenceLedger,
    FakeMemoryStore,
)
from packages.application.deliverable.builder import (
    DeliverableBuildError,
    DeliverableInputs,
    build_deliverable,
)
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.application.experiments.metric_extraction import semantic_metrics_digest
from packages.domain.artifacts import Artifact
from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.core import ID, Digest, Timestamp, Version
from packages.domain.enums import MemoryTier, MemoryType, TrustLabel
from packages.domain.eval_gate import GateConfig
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)
from packages.domain.manifest import RunManifest
from packages.domain.memory import MemoryWriteProposal
from packages.domain.reproducibility import ReproducibilityAudit

RUN_ID = "12121212-2222-4333-8444-555555555555"
EXPERIMENT_RUN_ID = "5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a"
CLAIM_ID = f"claim:{RUN_ID}"
EVIDENCE_ID = f"evidence:{RUN_ID}:{EXPERIMENT_RUN_ID}"
MEMORY_ID = f"mem:{RUN_ID}:negative-result"
ARTIFACT_ID = f"{RUN_ID}:experiment_result.json"
SOURCE_ORIGIN = f"experiment:{EXPERIMENT_RUN_ID}:experiment_result.json"


def _artifact_content() -> bytes:
    return json.dumps(
        {
            "experiment_run_id": EXPERIMENT_RUN_ID,
            "status": "SUCCEEDED",
            "metrics": {
                "baseline_accuracy": "0.745",
                "candidate_accuracy": "0.28",
                "n_train": 500,
                "n_test": 200,
                "baseline_feature_time_s": 0.42,
            },
            "seed": 7,
        },
        sort_keys=True,
    ).encode("utf-8")


def _populate(
    **flags: bool,
) -> tuple[DeliverableInputs, FakeArtifactStore, FakeEvidenceLedger, FakeBudgetLedger]:
    with_artifact = flags.get("with_artifact", True)
    with_claim = flags.get("with_claim", True)
    with_memory = flags.get("with_memory", True)
    with_budget = flags.get("with_budget", True)
    with_eval = flags.get("with_eval", True)
    with_audit = flags.get("with_audit", True)
    artifacts = FakeArtifactStore()
    if with_artifact:
        content = _artifact_content()
        artifacts.put(
            Artifact(
                id=ARTIFACT_ID,
                digest=Digest.of_bytes(content),
                size_bytes=len(content),
                media_type="application/json",
            ),
            content,
        )
    ledger = FakeEvidenceLedger()
    if with_claim:
        ledger.register_source(
            SourceRecord(
                origin=SOURCE_ORIGIN,
                content_digest=str(Digest.of_bytes(_artifact_content())),
                trust_label=TrustLabel.GENERATED,
            )
        )
        ledger.register_evidence(
            Evidence(
                id=EVIDENCE_ID,
                source_ref=SOURCE_ORIGIN,
                content_digest=str(Digest.of_bytes(_artifact_content())),
                artifact_id=ARTIFACT_ID,
                run_id=RUN_ID,
                experiment_run_id=EXPERIMENT_RUN_ID,
            )
        )
        ledger.register_claim(
            Claim(
                id=CLAIM_ID,
                statement="baseline outperforms candidate",
                status=ClaimStatus.VERIFIED,
                evidence_relations=[(EVIDENCE_ID, EvidenceRelationType.SUPPORTS)],
            )
        )
        ledger.attach_relation(
            EvidenceRelation(
                claim_id=CLAIM_ID,
                evidence_id=EVIDENCE_ID,
                relation=EvidenceRelationType.SUPPORTS,
            )
        )
    memory = FakeMemoryStore(allowed_sources=(SOURCE_ORIGIN,))
    if with_memory:
        memory.commit(
            MemoryWriteProposal(
                id=MEMORY_ID,
                tier=MemoryTier.PROJECT,
                kind=MemoryType.NEGATIVE_RESULT,
                content="candidate did not beat baseline",
                provenance=SOURCE_ORIGIN,
                confidence=0.97,
            )
        )
    budget = FakeBudgetLedger()
    if with_budget:
        budget.record_usage(
            UsageLedgerEntry(
                entry_id=f"usage:{RUN_ID}:model:research_alpha",
                resource_type=ResourceType.MODEL_TOKENS,
                quantity=2000,
                unit="tokens",
                cost_status=LedgerCostStatus.UNKNOWN,
                source="m12:model_relay",
                occurred_at=Timestamp.now().value,
            )
        )
        budget.record_usage(
            UsageLedgerEntry(
                entry_id=f"usage:{RUN_ID}:tool:literature_search",
                resource_type=ResourceType.TOOL_REQUESTS,
                quantity=2,
                unit="requests",
                cost_status=LedgerCostStatus.UNKNOWN,
                source="m12:tool_plane",
                occurred_at=Timestamp.now().value,
            )
        )
    manifest = RunManifest(
        run_id=RUN_ID,
        project_id="project-1",
        protocol_version=Version("0.4.0"),
        protocol_digest=Digest.of_bytes(b"protocol"),
        compiled_plan_digest=Digest.of_bytes(b"plan"),
        fallback_audit={"mode": "none"},
        evaluation_dataset_digest="sha256:dataset",
    )
    audit = None
    if with_audit:
        metrics = json.loads(_artifact_content())["metrics"]
        audit = ReproducibilityAudit(
            audit_id=ID("8b3c4d5e-6f7a-4b5c-9d0e-1f2a3b4c5d6e"),
            experiment_run_id=ID(EXPERIMENT_RUN_ID),
            input_digest=Digest.of_bytes(b"input"),
            command="python experiment.py",
            seed=7,
            environment_digest=Digest.of_bytes(b"env"),
            image_digest="sha256:image",
            workspace_snapshot_before="sha256:before",
            workspace_snapshot_after="sha256:after",
            output_artifact_digests=(str(Digest.of_bytes(_artifact_content())),),
            metrics_digest=semantic_metrics_digest(metrics),
            semantic_metrics_digest=semantic_metrics_digest(metrics),
        ).with_audit_digest()
    eval_report = None
    if with_eval:
        from adapters.contracts.eval_loaders import load_eval_dataset

        dataset = load_eval_dataset("examples/eval/datasets/m12_research_v1.yaml")
        outcome = run_evaluation(
            RunRequest(
                dataset=dataset,
                config=GateConfig(
                    id="m12-independent-gate",
                    version=Version("1.0.0"),
                    min_pass_ratio=Decimal("0.8"),
                ),
                mode="OFFLINE_FAKE",
                system_version="0.4.0",
                inputs={},
            )
        )
        eval_report = outcome.report
    inputs = DeliverableInputs(
        run_id=RUN_ID,
        manifest=manifest,
        artifacts=artifacts,
        ledger=ledger,
        memory=memory,
        budget=budget,
        audit=audit,
        eval_report=eval_report,
        objective="Compare baseline vs candidate on low-resource subset",
    )
    return inputs, artifacts, ledger, budget


class TestDeliverableFromState:
    def test_full_report_from_persisted_state(self) -> None:
        inputs, _, _, _ = _populate()
        report = build_deliverable(inputs)
        # artifact digest 由内容重算（非常量）
        assert report["experiment"]["artifact_digest"] == str(
            Digest.of_bytes(_artifact_content())
        )
        assert report["experiment"]["metrics"]["baseline_accuracy"] == "0.745"
        assert report["evidence_chain"]["claim_status"] == "VERIFIED"
        assert report["evidence_chain"]["evidence_ids"] == (EVIDENCE_ID,)
        assert report["evidence_chain"]["evidence_sources"][EVIDENCE_ID].startswith(
            "experiment:"
        )
        assert report["memory"]["memory_id"] == MEMORY_ID
        assert report["budget"]["total_model_tokens"] == 2000
        assert report["budget"]["tool_requests"] == 2
        assert report["evaluation"]["dataset"] == "m12_research_v1"
        assert report["reproduction"]["semantic_metrics_digest"] is not None
        assert report["protocol"]["manifest_digest"] == str(inputs.manifest.digest())

    def test_missing_artifact_fails(self) -> None:
        inputs, _, _, _ = _populate(with_artifact=False)
        with pytest.raises(DeliverableBuildError):
            build_deliverable(inputs)

    def test_missing_claim_fails(self) -> None:
        inputs, _, _, _ = _populate(with_claim=False)
        with pytest.raises(DeliverableBuildError):
            build_deliverable(inputs)

    def test_missing_memory_fails(self) -> None:
        inputs, _, _, _ = _populate(with_memory=False)
        with pytest.raises(DeliverableBuildError):
            build_deliverable(inputs)

    def test_missing_eval_report_fails(self) -> None:
        inputs, _, _, _ = _populate(with_eval=False)
        with pytest.raises(DeliverableBuildError):
            build_deliverable(inputs)

    def test_missing_audit_fails(self) -> None:
        inputs, _, _, _ = _populate(with_audit=False)
        with pytest.raises(DeliverableBuildError):
            build_deliverable(inputs)

    def test_deterministic_rebuild_from_same_state(self) -> None:
        first_inputs, _, _, _ = _populate()
        second_inputs, _, _, _ = _populate()
        first = build_deliverable(first_inputs)
        second = build_deliverable(second_inputs)
        assert first == second

    def test_tampered_artifact_changes_digest(self) -> None:
        inputs, artifacts, _, _ = _populate()
        tampered = b'{"status": "SUCCEEDED", "metrics": {"baseline_accuracy": "0.999"}}'
        artifacts.put(
            Artifact(
                id=ARTIFACT_ID,
                digest=Digest.of_bytes(tampered),
                size_bytes=len(tampered),
                media_type="application/json",
            ),
            tampered,
        )
        report = build_deliverable(inputs)
        assert report["experiment"]["artifact_digest"] == str(Digest.of_bytes(tampered))
        assert report["experiment"]["metrics"]["baseline_accuracy"] == "0.999"

    def test_budget_from_ledger_not_constants(self) -> None:
        inputs, _, _, budget = _populate()
        report = build_deliverable(inputs)
        snapshot = budget.snapshot()
        assert report["budget"]["entries"] == len(snapshot.entries)
        # 无 reservation → 不虚构一致结论
        assert report["budget"]["reservations"] == 0