"""M12 evidence chain 测试 fixtures（与 test_m12_chain.py 拆分保持规模阈值）。"""

from __future__ import annotations

import json

from adapters.fakes import FakeArtifactStore, FakeEvidenceLedger, FakeMemoryStore
from packages.application.evidence.m12_chain import ExperimentEvidenceInput
from packages.application.memory.gate import MemoryGateDeps
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest

RUN_ID = "12121212-2222-4333-8444-555555555555"
EXPERIMENT_RUN_ID = "5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a"
SOURCE_ORIGIN = f"experiment:{EXPERIMENT_RUN_ID}:experiment_result.json"
CLAIM_STATEMENT = (
    "baseline tfidf+linear_softmax (0.745) outperforms candidate "
    "hash_embedding+linear_softmax (0.28) on the low-resource subset"
)


def artifact_payload(run_id: str = RUN_ID) -> bytes:
    return json.dumps(
        {
            "experiment_run_id": EXPERIMENT_RUN_ID,
            "status": "SUCCEEDED",
            "metrics": {
                "baseline_accuracy": 0.745,
                "candidate_accuracy": 0.28,
            },
        },
        sort_keys=True,
    ).encode("utf-8")


def put_artifact(store: FakeArtifactStore, *, run_id: str = RUN_ID) -> str:
    artifact_id = f"{run_id}:experiment_result.json"
    content = artifact_payload(run_id)
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


def evidence_input(run_id: str = RUN_ID, artifact_id: str | None = None) -> ExperimentEvidenceInput:
    store = FakeArtifactStore()
    return ExperimentEvidenceInput(
        source_origin=SOURCE_ORIGIN,
        artifact_id=artifact_id or put_artifact(store, run_id=run_id),
        run_id=run_id,
        experiment_run_id=EXPERIMENT_RUN_ID,
        image_digest="sha256:" + "ab" * 32,
        workspace_snapshot_before="sha256:" + "cd" * 32,
        workspace_snapshot_after="sha256:" + "ef" * 32,
        metrics={"baseline_accuracy": 0.745, "candidate_accuracy": 0.28},
    )


def memory_deps(
    *,
    allowed_sources: set[str] | None = None,
    with_ledger: FakeEvidenceLedger | None = None,
) -> tuple[MemoryGateDeps, FakeMemoryStore, FakeEvidenceLedger]:
    store = FakeMemoryStore()
    for source in sorted(allowed_sources or set()):
        store.allow_source(source)
    ledger = with_ledger or FakeEvidenceLedger()
    deps = MemoryGateDeps(
        store=store,
        ledger=ledger,
        allowed_sources=frozenset(allowed_sources or set()),
        actor="system:test",
    )
    return deps, store, ledger


__all__ = [
    "CLAIM_STATEMENT",
    "EXPERIMENT_RUN_ID",
    "RUN_ID",
    "SOURCE_ORIGIN",
    "artifact_payload",
    "evidence_input",
    "memory_deps",
    "put_artifact",
]
