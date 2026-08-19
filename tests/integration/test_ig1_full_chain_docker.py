"""IG-1 full real chain: MCP Tool -> policy -> Docker Experiment -> Evidence -> Eval -> Memory."""

from __future__ import annotations

import sys
from pathlib import Path

import docker
import pytest
from docker.errors import ImageNotFound

from adapters.execution import DockerExecutionBackend
from adapters.fakes import FakeEvidenceLedger, FakeMemoryStore, FakePolicyEvaluator
from adapters.mcp import McpConnectionSpec, McpToolProvider
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
    GovernedExperimentExecutor,
    register_experiment_evidence,
)
from packages.application.experiments.types import ExperimentExecutionOutcome
from packages.application.memory.gate import MemoryGateDeps, commit_memory
from packages.application.tool_plane import execute_tool_call
from packages.application.tool_plane.results import fetch_spilled_result
from packages.domain.core import ID, Digest, Version
from packages.domain.enums import (
    EffectClass,
    MemoryTier,
    MemoryType,
    ProviderType,
    QualityGateVerdict,
    TrustLevel,
)
from packages.domain.eval_gate import GateConfig
from packages.domain.eval_spec import EvalCase, EvalDataset, EvalScope, ScorerRef
from packages.domain.experiment_state import ExperimentPlanState
from packages.domain.experiments import ExperimentPlan
from packages.domain.memory import MemoryWriteProposal
from packages.domain.tools import ToolCallRecord, ToolProviderSpec
from packages.domain.workspace import Workspace

pytestmark = pytest.mark.requires_docker

IMAGE_TAG = "research-os-sandbox:m9-test"
_SANDBOX_DIR = Path(__file__).resolve().parents[2] / "adapters" / "execution" / "sandbox"
_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("bbbbbbbb-2222-4333-8444-555555555555")
_WORKSPACE = Workspace(id="ws-full", name="ws-full")

_PROVIDER = ToolProviderSpec(
    id="mcp-full",
    kind=ProviderType.MCP,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["tool.big"],
    effect_class=EffectClass.READ_ONLY,
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


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="ig1-full",
        hypothesis="tool input reaches experiment",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _tool_call() -> ToolCallRecord:
    return ToolCallRecord(
        task_id="task-tool",
        attempt=1,
        operation_key="op-big",
        tool_id="big_tool",
        capability="tool.big",
        argument_digest=Digest.of_bytes(b"{}"),
    )


def _run_tool_and_prepare_workspace(
    artifacts: SqliteArtifactStore, workspaces: FileWorkspaceBackend
) -> None:
    provider = McpToolProvider(
        McpConnectionSpec(
            transport="stdio",
            command=(sys.executable, "-B", "-m", "tests.mcp_server.run_stdio", "big"),
            timeout_seconds=30.0,
        ),
        artifact_store=artifacts,
        spill_threshold_bytes=1024,
    )
    result = execute_tool_call(
        provider,
        _PROVIDER,
        _tool_call(),
        FakePolicyEvaluator(),
        actor="agent-ig1",
    )
    assert result.result is not None
    payload = fetch_spilled_result(artifacts, result.result)
    assert payload is not None
    lease = workspaces.acquire_lease(_WORKSPACE, "session-tool")
    workspace_dir = workspaces.workspace_dir(lease)
    (workspace_dir / "samples.txt").write_bytes(payload)


def _experiment_script() -> str:
    return """import json, pathlib
data = pathlib.Path('samples.txt').read_bytes()
open('result.json', 'w').write(json.dumps({'bytes': len(data)}))
payload = {'experiment_run_id': 'RUN_ID', 'status': 'SUCCEEDED',
           'artifact_refs': ['result.json'],
           'metrics': {'bytes': len(data)}}
open('experiment_result.json', 'w').write(json.dumps(payload))
print('bytes=', len(data))
"""


def _execute_experiment(
    tmp_path: Path, image: str
) -> tuple[ExperimentExecutionOutcome, SqliteArtifactStore]:
    workspaces = FileWorkspaceBackend(tmp_path / "workspaces")
    workspaces.create_workspace(_WORKSPACE)
    artifacts = SqliteArtifactStore(blob_dir=tmp_path / "blobs")
    _run_tool_and_prepare_workspace(artifacts, workspaces)
    lease = workspaces.acquire_lease(_WORKSPACE, "session-exp")
    workspace_dir = workspaces.workspace_dir(lease)
    (workspace_dir / "experiment.py").write_text(
        _experiment_script().replace("RUN_ID", str(_RUN_ID.value)),
        encoding="utf-8",
    )
    inner = ExperimentExecutor(
        execution=DockerExecutionBackend(image=image),
        workspaces=workspaces,
        artifacts=artifacts,
        workspace_dir=lambda lease: workspaces.workspace_dir(lease),
    )
    governed = GovernedExperimentExecutor(
        inner=inner,
        policy=FakePolicyEvaluator(),
        budget_check=lambda: None,
        credential_check=lambda: None,
    )
    outcome = governed.execute(
        ExperimentExecutionRequest(
            plan=_plan(),
            run_id=_RUN_ID,
            command="python experiment.py",
            workspace=_WORKSPACE,
            agent_session_id="session-exp",
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
) -> None:
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
        id="ig1-full",
        version=Version("1.0.0"),
        cases=(evidence_case, experiment_case),
    )
    report = run_evaluation(
        RunRequest(
            dataset=dataset,
            config=GateConfig(id="ig1-full", version=Version("1.0.0")),
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


def _commit_memory(ledger: FakeEvidenceLedger, source: str) -> FakeMemoryStore:
    store = FakeMemoryStore(allowed_sources=(source,))
    gate = MemoryGateDeps(
        store=store,
        policy=FakePolicyEvaluator(),
        ledger=ledger,
        allowed_sources=frozenset({source}),
        actor="system:ig1",
    )
    result = commit_memory(
        MemoryWriteProposal(
            id="memory:ig1-full",
            tier=MemoryTier.RUN,
            kind=MemoryType.FACT,
            content=f"Claim {source}: full chain completed",
            provenance=source,
            confidence=0.9,
            scope="run",
            proposed_by="system:ig1",
        ),
        gate,
    )
    assert result.accepted
    return store


def test_full_real_chain(tmp_path: Path, image: str) -> None:
    outcome, artifacts = _execute_experiment(tmp_path, image)
    assert outcome.run.state == "SUCCEEDED"

    ledger = FakeEvidenceLedger()
    admission = register_experiment_evidence(
        ledger,
        outcome.run,
        artifacts,
        provenance=ExperimentProvenance(
            run_id="run-ig1-full",
            manifest_digest="sha256:" + "0" * 64,
            tool_refs=("big_tool@1.0.0",),
        ),
    )
    assert admission.evidence
    _run_eval(outcome, artifacts, ledger, admission.claim.id)
    store = _commit_memory(ledger, admission.evidence[0].source_ref)
    assert store.query()
