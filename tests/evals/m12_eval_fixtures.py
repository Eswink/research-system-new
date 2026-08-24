"""M12 evaluation 测试共享 fixtures（M12-R1 WP5 对抗回归）。

标识必须与生产链一致（M12-R1 修正）：
- claim id = f"claim:{EXPERIMENT_RUN_ID}:result"；
- artifact id = f"{EXPERIMENT_RUN_ID}:experiment_result.json"；
- evidence id = f"evidence:{EXPERIMENT_RUN_ID}:experiment_result.json"；
- source origin = artifact id（evidence_admission.source_ref = artifact.id）。

EXPERIMENT_RUN_ID 由 experiment_run_id_of(RUN_ID) 确定性派生，
与 clean_run 生产链完全一致。
"""

from __future__ import annotations

import json
from decimal import Decimal

from adapters.contracts.eval_loaders import load_eval_dataset
from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.application.evaluation.scorer_types import ScorerFn
from packages.application.evaluation.scorers_m12_truth import (
    direction_improvement_scorer,
    metric_correctness_scorer,
)
from packages.application.evaluation.scorers_m12_truth_evidence import (
    citation_source_scorer,
    evidence_artifact_scorer,
    unsupported_claim_scorer,
)
from packages.application.m12_reference.clean_run_stages import (
    CLAIM_STATEMENT,
    experiment_run_id_of,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Version
from packages.domain.enums import TrustLabel
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_result import EvalReport
from packages.domain.eval_spec import EvalDataset
from packages.domain.evidence import (
    Claim,
    ClaimStatus,
    Evidence,
    EvidenceRelation,
    EvidenceRelationType,
    SourceRecord,
)

DATASET_PATH = "examples/eval/datasets/m12_research_v1.yaml"
SYSTEM_VERSION = "0.4.0"
RUN_ID = "12121212-2222-4333-8444-555555555555"
EXPERIMENT_RUN_ID = experiment_run_id_of(RUN_ID)
ARTIFACT_ID = f"{EXPERIMENT_RUN_ID}:experiment_result.json"
CLAIM_ID = f"claim:{EXPERIMENT_RUN_ID}:result"
EVIDENCE_ID = f"evidence:{EXPERIMENT_RUN_ID}:experiment_result.json"
SOURCE_ORIGIN = ARTIFACT_ID


def artifact_content(baseline: str = "0.745") -> bytes:
    return json.dumps(
        {
            "experiment_run_id": EXPERIMENT_RUN_ID,
            "status": "SUCCEEDED",
            "metrics": {
                "baseline_accuracy": baseline,
                "candidate_accuracy": "0.28",
                "n_train": 500,
                "n_test": 200,
            },
            "seed": 7,
        },
        sort_keys=True,
    ).encode("utf-8")


def make_artifacts(content: bytes | None = None) -> FakeArtifactStore:
    store = FakeArtifactStore()
    content = content or artifact_content()
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


def make_ledger(
    *,
    with_claim: bool = True,
    evidence_run_id: str = RUN_ID,
    relation: EvidenceRelationType = EvidenceRelationType.SUPPORTS,
    claim_status: ClaimStatus = ClaimStatus.PROPOSED,
    claim_statement: str = CLAIM_STATEMENT,
) -> FakeEvidenceLedger:
    ledger = FakeEvidenceLedger()
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
            run_id=evidence_run_id,
            experiment_run_id=EXPERIMENT_RUN_ID,
        )
    )
    if with_claim:
        ledger.register_claim(
            Claim(
                id=CLAIM_ID,
                statement=claim_statement,
                status=claim_status,
                evidence_relations=[(EVIDENCE_ID, relation)],
            )
        )
        ledger.attach_relation(
            EvidenceRelation(
                claim_id=CLAIM_ID,
                evidence_id=EVIDENCE_ID,
                relation=relation,
            )
        )
    return ledger


def dataset() -> EvalDataset:
    return load_eval_dataset(DATASET_PATH)


def gate() -> GateConfig:
    return GateConfig(
        id="m12-independent-gate",
        version=Version("1.0.0"),
        min_pass_ratio=Decimal("0.8"),
    )


def base_inputs() -> dict[str, object]:
    return {
        "input://m12/task_completion": {"status": "SUCCEEDED"},
        "input://m12/evidence_support": {"sources": 2},
        "input://m12/experimental_validity": {
            "status": "SUCCEEDED",
            "hypothesis": ("hash-embedding+linear classifier beats tfidf on low-resource subset"),
            "metrics": {
                "baseline_accuracy": "0.745",
                "candidate_accuracy": "0.28",
                "n_train": 500,
                "n_test": 200,
            },
            "seed": 7,
        },
        "input://m12/result_correctness": "0.745",
        "input://m12/reproducibility": {
            "audit_status": "PASS",
            "image_digest": "sha256:" + "ab" * 32,
            "workspace_snapshot_before": "sha256:" + "cd" * 32,
            "workspace_snapshot_after": "sha256:" + "ef" * 32,
            "metrics_digest": "sha256:" + "12" * 32,
        },
        "input://m12/claim_calibration": {
            "claim_id": CLAIM_ID,
            "claim_status": "VERIFIED",
        },
        "input://m12/citation_correctness": CLAIM_STATEMENT,
        "input://m12/unsupported_conclusion": {"unsupported_claims": []},
        "input://m12/deliverable_quality": {
            "claim_id": CLAIM_ID,
            "evidence_ids": [EVIDENCE_ID],
            "metrics": {"baseline_accuracy": "0.745", "candidate_accuracy": "0.28"},
        },
        "input://m12/evidence_artifact": {"claim_id": CLAIM_ID},
        "input://m12/cost_efficiency": {
            "model_tokens": 0,
            "tool_requests": 1,
            "experiment_runs": 2,
            "evaluation_runs": 1,
        },
    }


def evidence_map() -> dict[str, dict[str, str]]:
    return {
        "input://m12/evidence_support": {
            SOURCE_ORIGIN: "sha256:" + "ab" * 32,
            f"experiment:{EXPERIMENT_RUN_ID}:repro-2": "sha256:" + "cd" * 32,
        }
    }


def runtime_scorers(
    artifacts: FakeArtifactStore, ledger: FakeEvidenceLedger
) -> dict[tuple[str, str], ScorerFn]:
    return {
        ("metric_correctness", "1.0.0"): metric_correctness_scorer(artifacts),
        ("direction_improvement", "1.0.0"): direction_improvement_scorer(),
        ("citation_source", "1.0.0"): citation_source_scorer(ledger, RUN_ID),
        ("unsupported_claim", "1.0.0"): unsupported_claim_scorer(ledger),
        ("evidence_artifact", "1.0.0"): evidence_artifact_scorer(ledger, artifacts),
    }


def run(
    inputs: dict[str, object],
    *,
    artifacts: FakeArtifactStore | None = None,
    ledger: FakeEvidenceLedger | None = None,
    with_evidence_map: bool = True,
) -> EvalReport:
    artifacts = artifacts or make_artifacts()
    ledger = ledger or make_ledger()
    outcome = run_evaluation(
        RunRequest(
            dataset=dataset(),
            config=gate(),
            mode="OFFLINE_FAKE",
            system_version=SYSTEM_VERSION,
            inputs=inputs,
            evidence=evidence_map() if with_evidence_map else {},
            runtime_scorers=runtime_scorers(artifacts, ledger),
        )
    )
    return outcome.report


__all__ = [
    "ARTIFACT_ID",
    "CLAIM_ID",
    "CLAIM_STATEMENT",
    "DATASET_PATH",
    "EVIDENCE_ID",
    "EXPERIMENT_RUN_ID",
    "RUN_ID",
    "SOURCE_ORIGIN",
    "SYSTEM_VERSION",
    "artifact_content",
    "base_inputs",
    "dataset",
    "evidence_map",
    "gate",
    "make_artifacts",
    "make_ledger",
    "run",
    "runtime_scorers",
]
