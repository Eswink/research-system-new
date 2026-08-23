"""M12 真实证据链 E2E（requires_docker）：容器产物 → SQLite 准入 → Claim → Memory。

M12-R1 WP2：真实链必须成为
Docker Execution → persisted Experiment Artifact → ArtifactStore →
EvidenceAdmission → EvidenceLedger(Sqlite) → Claim → Memory。

验证（全部基于真实运行事实，无合成常量）：
- 真实容器产出 experiment_result.json 并 spill 到 SqliteArtifactStore；
- evidence_admission.register_experiment_evidence 以真实 ExperimentRun 登记
  Source/Evidence/Claim（artifact digest / image_digest / snapshots / metrics
  全部来自运行结果）；
- verify_claim（gate: 独立 reviewer）升级 PROPOSED → VERIFIED；
- governed memory（NEGATIVE_RESULT，provenance=真实 source origin）经 gate 入账；
- 重启 SqliteEvidenceLedger 后 claim 仍 VERIFIED（持久化不丢）。
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import docker
import pytest
from docker.errors import ImageNotFound

from adapters.execution import DockerExecutionBackend
from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
from adapters.sqlite.memory_store import SqliteMemoryStore
from adapters.workspace import FileWorkspaceBackend
from packages.application.evidence.m12_chain import (
    MemoryProposalInput,
    propose_and_commit_memory,
    verify_claim,
)
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
    register_experiment_evidence,
)
from packages.application.experiments.evidence_admission import ExperimentProvenance
from packages.application.memory.gate import MemoryGateDeps
from packages.domain.core import ID
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.evidence import ClaimStatus
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState
from packages.domain.experiments import ExperimentPlan
from packages.domain.workspace import Workspace

pytestmark = pytest.mark.requires_docker

IMAGE_TAG = "research-os-sandbox:m9-test"
_SANDBOX_DIR = Path(__file__).resolve().parents[3] / "adapters" / "execution" / "sandbox"
_EXPERIMENT_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "examples"
    / "experiments"
    / "m12_reference_classification.py"
)

_PLAN_ID = ID("5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a")
_WORKSPACE = Workspace(id="ws-m12-admission", name="ws-m12-admission")
RUN_ID = "12121212-2222-4333-8444-555555555555"
EXPERIMENT_RUN_ID = "5a1c6a8e-9b2d-4f3a-8c5e-2b2c3d4e5f6a"
CLAIM_STATEMENT = (
    "baseline tfidf+linear_softmax (0.745) outperforms candidate "
    "hash_embedding+linear_softmax (0.28) on the low-resource subset"
)


@pytest.fixture(scope="module")
def image() -> str:
    client = docker.from_env()
    try:
        client.ping()
    except Exception:
        pytest.skip("docker daemon unavailable")
    try:
        client.images.get(IMAGE_TAG)
    except ImageNotFound:
        client.images.build(path=str(_SANDBOX_DIR), tag=IMAGE_TAG)
    return IMAGE_TAG


@pytest.fixture()
def harness(
    tmp_path: Path, image: str
) -> tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore, Path]:
    workspaces = FileWorkspaceBackend(tmp_path / "workspaces")
    workspaces.create_workspace(_WORKSPACE)
    artifacts = SqliteArtifactStore(blob_dir=tmp_path / "blobs")
    db_path = tmp_path / "state.sqlite"
    executor = ExperimentExecutor(
        execution=DockerExecutionBackend(image=image),
        workspaces=workspaces,
        artifacts=artifacts,
        workspace_dir=lambda lease: workspaces.workspace_dir(lease),
    )
    return executor, workspaces, artifacts, db_path


def _prepare(
    workspaces: FileWorkspaceBackend,
    run_id: ID,
) -> ExperimentExecutionRequest:
    session_id = f"session-{run_id.value[:8]}"
    lease = workspaces.acquire_lease(_WORKSPACE, session_id)
    workspace_dir = workspaces.workspace_dir(lease)
    script = _EXPERIMENT_SCRIPT.read_text(encoding="utf-8")
    script = script.replace("M12-REFERENCE-RUN", str(run_id.value))
    (workspace_dir / "experiment.py").write_text(script, encoding="utf-8")
    plan = ExperimentPlan(
        id=_PLAN_ID,
        name="m12-reference-classification",
        hypothesis="hash-embedding+linear classifier beats tfidf on low-resource subset",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)
    return ExperimentExecutionRequest(
        plan=plan,
        run_id=run_id,
        command="python experiment.py",
        workspace=_WORKSPACE,
        agent_session_id=session_id,
        seed=7,
        resource_profile="small",
        timeout_seconds=180,
    )


class TestM12RealEvidenceChain:
    def test_container_to_verified_claim_to_memory(
        self,
        harness: tuple[ExperimentExecutor, FileWorkspaceBackend, SqliteArtifactStore, Path],
    ) -> None:
        executor, workspaces, artifacts, db_path = harness
        connection = sqlite3.connect(str(db_path))
        outcome = executor.execute(_prepare(workspaces, ID(EXPERIMENT_RUN_ID)))
        assert outcome.run.state == ExperimentRunState.State.SUCCEEDED

        # --- 1. 真实 artifact 已在 SqliteArtifactStore ---
        artifact_id = f"{EXPERIMENT_RUN_ID}:experiment_result.json"
        payload = json.loads(artifacts.get(artifact_id).decode("utf-8"))
        assert payload["status"] == "SUCCEEDED"
        assert payload["metrics"]["baseline_accuracy"] == 0.745
        assert artifacts.verify(artifact_id)

        # --- 2. 正式准入：ExperimentRun → Source/Evidence/Claim ---
        ledger = SqliteEvidenceLedger(connection)
        result = register_experiment_evidence(
            ledger,
            outcome.run,
            artifacts,
            provenance=ExperimentProvenance(
                run_id=RUN_ID,
                manifest_digest="sha256:m12-manifest-frozen",
                tool_refs=("literature_search",),
            ),
            claim_statement=CLAIM_STATEMENT,
        )
        claim = result.claim
        assert claim.status is ClaimStatus.PROPOSED
        assert len(result.evidence) >= 1
        evidence = next(
            item for item in result.evidence if item.artifact_id == artifact_id
        )
        # 全部来自真实运行事实（非合成快照）
        assert evidence.artifact_id == artifact_id
        assert evidence.experiment_run_id == EXPERIMENT_RUN_ID
        assert evidence.run_id == RUN_ID
        assert evidence.image_digest == outcome.run.result.image_digest
        assert evidence.manifest_digest == "sha256:m12-manifest-frozen"
        assert ledger.get_source(evidence.source_ref).content_digest == str(
            evidence.content_digest
        )

        # --- 3. 独立 reviewer 升级 VERIFIED（agent 自证拒绝已由契约覆盖） ---
        verified = verify_claim(
            ledger,
            ledger.get_claim(claim.id),
            reviewer="gate:independent-acceptance",
            verdict="PASS",
        )
        assert verified.status is ClaimStatus.VERIFIED

        # --- 4. governed memory（真实 provenance） ---
        store = SqliteMemoryStore(connection, allowed_sources=(evidence.source_ref,))
        memory_deps = MemoryGateDeps(
            store=store,
            ledger=ledger,
            allowed_sources=frozenset({evidence.source_ref}),
            actor="system:m12",
        )
        memory_id = propose_and_commit_memory(
            memory_deps,
            input=MemoryProposalInput(
                memory_id=f"mem:{RUN_ID}:negative-result",
                content=(
                    "hash-embedding+linear_softmax candidate (0.28) did not beat "
                    "tfidf baseline (0.745) on low-resource 20-class subset"
                ),
                provenance=evidence.source_ref,
                kind=MemoryType.NEGATIVE_RESULT,
                tier=MemoryTier.PROJECT,
                confidence=0.97,
                curator_approved=True,
            ),
        )
        assert memory_id == f"mem:{RUN_ID}:negative-result"
        assert store.get(memory_id).provenance == evidence.source_ref

        # --- 5. 持久化不丢：重开 ledger 连接后 claim 仍 VERIFIED ---
        ledger.close()
        reopened = SqliteEvidenceLedger(sqlite3.connect(str(db_path)))
        assert reopened.get_claim(claim.id).status is ClaimStatus.VERIFIED
        relations = reopened.relations_for_claim(claim.id)
        assert len(relations) >= 1
        assert {relation.evidence_id for relation in relations} >= {
            evidence.id
        }
        reopened.close()