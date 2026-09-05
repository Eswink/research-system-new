"""Deliverable-from-state 测试 fixtures（M12-R1 WP3）。

标识与生产链一致（experiment_run_id 派生 / claim:...:result / evidence:
artifact id / source origin = artifact id）。
"""

from __future__ import annotations

import json
from decimal import Decimal

from adapters.fakes import (
    FakeArtifactStore,
    FakeBudgetLedger,
    FakeEvidenceLedger,
    FakeMemoryStore,
)
from packages.application.deliverable.builder import DeliverableInputs
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.application.experiments.metric_extraction import semantic_metrics_digest
from packages.application.m12_reference.clean_run_stages import experiment_run_id_of
from packages.domain.artifacts import Artifact
from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.core import ID, Digest, Timestamp, Version
from packages.domain.enums import MemoryTier, MemoryType, TrustLabel
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalReport
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
EXPERIMENT_RUN_ID = experiment_run_id_of(RUN_ID)
CLAIM_ID = f"claim:{EXPERIMENT_RUN_ID}:result"
EVIDENCE_ID = f"evidence:{EXPERIMENT_RUN_ID}:experiment_result.json"
MEMORY_ID = f"mem:{RUN_ID}:negative-result"
ARTIFACT_ID = f"{EXPERIMENT_RUN_ID}:experiment_result.json"
SOURCE_ORIGIN = ARTIFACT_ID


def artifact_content() -> bytes:
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


def populate(
    **flags: bool,
) -> tuple[DeliverableInputs, FakeArtifactStore, FakeEvidenceLedger, FakeBudgetLedger]:
    with_artifact = flags.get("with_artifact", True)
    with_claim = flags.get("with_claim", True)
    with_memory = flags.get("with_memory", True)
    with_budget = flags.get("with_budget", True)
    with_eval = flags.get("with_eval", True)
    with_audit = flags.get("with_audit", True)
    artifacts = _artifacts(with_artifact)
    ledger = _ledger(with_claim)
    memory = _memory(with_memory)
    budget = _budget(with_budget)
    manifest = _manifest()
    audit = _audit(with_audit)
    eval_report = _eval_report(with_eval)
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


def _artifacts(with_artifact: bool) -> FakeArtifactStore:
    store = FakeArtifactStore()
    if not with_artifact:
        return store
    content = artifact_content()
    store.put(
        Artifact(
            id=ARTIFACT_ID,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/json",
        ),
        content,
    )
    return store


def _ledger(with_claim: bool) -> FakeEvidenceLedger:
    ledger = FakeEvidenceLedger()
    if not with_claim:
        return ledger
    ledger.register_source(
        SourceRecord(
            origin=SOURCE_ORIGIN,
            content_digest=str(Digest.of_bytes(artifact_content())),
            trust_label=TrustLabel.GENERATED,
        )
    )
    ledger.register_evidence(
        Evidence(
            id=EVIDENCE_ID,
            source_ref=SOURCE_ORIGIN,
            content_digest=str(Digest.of_bytes(artifact_content())),
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
    return ledger


def _memory(with_memory: bool) -> FakeMemoryStore:
    memory = FakeMemoryStore(allowed_sources=(SOURCE_ORIGIN,))
    if not with_memory:
        return memory
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
    return memory


def _budget(with_budget: bool) -> FakeBudgetLedger:
    budget = FakeBudgetLedger()
    if not with_budget:
        return budget
    budget.record_usage(
        UsageLedgerEntry(
            run_id=RUN_ID,
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
            run_id=RUN_ID,
            entry_id=f"usage:{RUN_ID}:tool:literature_search",
            resource_type=ResourceType.TOOL_REQUESTS,
            quantity=2,
            unit="requests",
            cost_status=LedgerCostStatus.UNKNOWN,
            source="m12:tool_plane",
            occurred_at=Timestamp.now().value,
        )
    )
    return budget


def _manifest() -> RunManifest:
    return RunManifest(
        run_id=RUN_ID,
        project_id="project-1",
        protocol_version=Version("0.4.0"),
        protocol_digest=Digest.of_bytes(b"protocol"),
        compiled_plan_digest=Digest.of_bytes(b"plan"),
        fallback_audit={"mode": "none"},
        evaluation_dataset_digest="sha256:dataset",
    )


def _audit(with_audit: bool) -> ReproducibilityAudit | None:
    if not with_audit:
        return None
    metrics = json.loads(artifact_content())["metrics"]
    return ReproducibilityAudit(
        audit_id=ID("8b3c4d5e-6f7a-4b5c-9d0e-1f2a3b4c5d6e"),
        experiment_run_id=ID(EXPERIMENT_RUN_ID),
        input_digest=Digest.of_bytes(b"input"),
        command="python experiment.py",
        seed=7,
        environment_digest=Digest.of_bytes(b"env"),
        image_digest="sha256:image",
        workspace_snapshot_before="sha256:before",
        workspace_snapshot_after="sha256:after",
        output_artifact_digests=(str(Digest.of_bytes(artifact_content())),),
        metrics_digest=semantic_metrics_digest(metrics),
        semantic_metrics_digest=semantic_metrics_digest(metrics),
    ).with_audit_digest()


def _eval_report(with_eval: bool) -> EvalReport | None:
    if not with_eval:
        return None
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
    return outcome.report


__all__ = [
    "ARTIFACT_ID",
    "CLAIM_ID",
    "EVIDENCE_ID",
    "EXPERIMENT_RUN_ID",
    "MEMORY_ID",
    "RUN_ID",
    "SOURCE_ORIGIN",
    "artifact_content",
    "populate",
]
