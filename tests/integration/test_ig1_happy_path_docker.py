"""IG-1 real Docker integrated chain (requires_docker).

MCP/Tool policy is not re-exercised here; this is the real experiment side of
the chain: DockerExecutionBackend -> ExperimentRun -> Artifact -> Evidence ->
M11 evaluation -> Governed Memory.
"""

from __future__ import annotations

from pathlib import Path

import docker
import pytest
from docker.errors import ImageNotFound

from adapters.execution import DockerExecutionBackend
from adapters.fakes import FakeEvidenceLedger, FakeMemoryStore, FakePolicyEvaluator
from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.workspace import FileWorkspaceBackend
from packages.application.evaluation.runner import RunRequest, run_evaluation
from packages.application.evaluation.scorers_evidence import (
    evidence_provenance_scorer,
    experiment_reproducibility_scorer,
)
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
    ExperimentProvenance,
    register_experiment_evidence,
)
from packages.application.experiments.types import ExperimentExecutionOutcome
from packages.application.memory.gate import MemoryGateDeps, commit_memory
from packages.domain.core import ID, Version
from packages.domain.enums import MemoryTier, MemoryType, QualityGateVerdict
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_spec import EvalCase, EvalDataset, EvalScope, ScorerRef
from packages.domain.experiment_state import ExperimentPlanState
from packages.domain.experiments import ExperimentPlan
from packages.domain.memory import MemoryWriteProposal
from packages.domain.workspace import Workspace

pytestmark = pytest.mark.requires_docker

IMAGE_TAG = "research-os-sandbox:m9-test"
_SANDBOX_DIR = Path(__file__).resolve().parents[2] / "adapters" / "execution" / "sandbox"
_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("aaaaaaaa-2222-4333-8444-555555555555")
_WORKSPACE = Workspace(id="ws-ig1", name="ws-ig1")

_SCRIPT = """import json, random
rng = random.Random(42)
samples = [rng.random() for _ in range(5)]
mean = sum(samples) / len(samples)
payload = {'experiment_run_id': 'RUN_ID', 'status': 'SUCCEEDED',
           'artifact_refs': ['samples.json'],
           'metrics': {'mean': mean, 'n_samples': len(samples)}}
open('samples.json', 'w').write(json.dumps(samples))
open('experiment_result.json', 'w').write(json.dumps(payload))
print('mean=', mean)
"""


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


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="ig1-docker",
        hypothesis="fixed seed produces fixed output",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _execute_experiment(
    tmp_path: Path, image: str
) -> tuple[ExperimentExecutionOutcome, SqliteArtifactStore]:
    workspaces = FileWorkspaceBackend(tmp_path / "workspaces")
    workspaces.create_workspace(_WORKSPACE)
    artifacts = SqliteArtifactStore(blob_dir=tmp_path / "blobs")
    executor = ExperimentExecutor(
        execution=DockerExecutionBackend(image=image),
        workspaces=workspaces,
        artifacts=artifacts,
        workspace_dir=lambda lease: workspaces.workspace_dir(lease),
    )
    session_id = "session-ig1"
    lease = workspaces.acquire_lease(_WORKSPACE, session_id)
    workspace_dir = workspaces.workspace_dir(lease)
    (workspace_dir / "experiment.py").write_text(
        _SCRIPT.replace("RUN_ID", str(_RUN_ID.value)), encoding="utf-8"
    )
    outcome = executor.execute(
        ExperimentExecutionRequest(
            plan=_plan(),
            run_id=_RUN_ID,
            command="python experiment.py",
            workspace=_WORKSPACE,
            agent_session_id=session_id,
            seed=42,
            timeout_seconds=60,
        )
    )
    return outcome, artifacts


def _run_eval(
    outcome: ExperimentExecutionOutcome,
    artifacts: SqliteArtifactStore,
    ledger: FakeEvidenceLedger,
    claim_id: str,
) -> object:
    evidence_case = EvalCase(
        id="evidence",
        version=Version("1.0.0"),
        scope=EvalScope.INTEGRATION,
        input_ref="input://evidence",
        expected={"claim_id": claim_id, "minimum_sources": 1},
        scorer_refs=(ScorerRef("evidence_provenance", Version("1.0.0")),),
    )
    experiment_case = EvalCase(
        id="experiment",
        version=Version("1.0.0"),
        scope=EvalScope.INTEGRATION,
        input_ref="input://experiment",
        expected={"experiment_run_id": str(_RUN_ID.value)},
        scorer_refs=(ScorerRef("experiment_reproducibility", Version("1.0.0")),),
    )
    dataset = EvalDataset(
        id="ig1-docker",
        version=Version("1.0.0"),
        cases=(evidence_case, experiment_case),
    )
    report = run_evaluation(
        RunRequest(
            dataset=dataset,
            config=GateConfig(id="ig1", version=Version("1.0.0")),
            mode="OFFLINE_FAKE",
            system_version="0.4.0",
            inputs={
                "input://evidence": {},
                "input://experiment": outcome.run,
            },
            runtime_scorers={
                ("evidence_provenance", "1.0.0"): evidence_provenance_scorer(ledger),
                ("experiment_reproducibility", "1.0.0"): experiment_reproducibility_scorer(
                    artifacts
                ),
            },
        )
    ).report
    assert report.gate_verdict is QualityGateVerdict.PASS
    return report


def _commit_memory(ledger: FakeEvidenceLedger, source: str) -> FakeMemoryStore:
    memory_store = FakeMemoryStore(allowed_sources=(source,))
    memory_gate = MemoryGateDeps(
        store=memory_store,
        policy=FakePolicyEvaluator(),
        ledger=ledger,
        allowed_sources=frozenset({source}),
        actor="system:ig1",
    )
    result = commit_memory(
        MemoryWriteProposal(
            id="memory:ig1-docker",
            tier=MemoryTier.RUN,
            kind=MemoryType.FACT,
            content=f"Claim {source}: docker chain completed",
            provenance=source,
            confidence=0.9,
            scope="run",
            proposed_by="system:ig1",
        ),
        memory_gate,
    )
    assert result.accepted
    return memory_store


def test_real_docker_experiment_to_evidence_to_eval_to_memory(tmp_path: Path, image: str) -> None:
    outcome, artifacts = _execute_experiment(tmp_path, image)
    assert outcome.run.state == "SUCCEEDED"

    ledger = FakeEvidenceLedger()
    admission = register_experiment_evidence(
        ledger,
        outcome.run,
        artifacts,
        provenance=ExperimentProvenance(
            run_id="run-ig1",
            manifest_digest="sha256:" + "0" * 64,
        ),
    )
    assert admission.evidence
    _run_eval(outcome, artifacts, ledger, admission.claim.id)
    memory_store = _commit_memory(ledger, admission.evidence[0].source_ref)
    assert memory_store.query()
