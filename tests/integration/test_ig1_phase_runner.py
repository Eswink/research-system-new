"""IG-1 phase-runner experiment + memory promotion integration (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.fakes import (
    FakeAgentRuntime,
    FakeArtifactStore,
    FakeEvidenceLedger,
    FakeExecutionBackend,
    FakeMemoryStore,
    FakePolicyEvaluator,
    FakeWorkflowEngine,
    FakeWorkspaceBackend,
)
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
    ExperimentProvenance,
    GovernedExperimentExecutor,
)
from packages.application.memory.gate import MemoryGateDeps
from packages.application.run_orchestration.experiment_task import (
    ExperimentTaskDeps,
    execute_experiment_task,
)
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
    execute_phases,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.core import ID
from packages.domain.enums import (
    AcceptanceCriterionType,
    ActivationPolicy,
    ArtifactState,
    ModelBindingMode,
    RoleCategory,
)
from packages.domain.evidence import ClaimStatus
from packages.domain.experiment_state import ExperimentPlanState
from packages.domain.experiments import ExperimentPlan
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.run_state import ResearchRunState
from packages.domain.tasks import (
    AcceptanceCriterion,
    ExperimentExecutionSpec,
    ResearchTask,
    TaskContract,
)
from packages.domain.workspace import Workspace
from services.api.demo import DECLARED_INPUTS as DECLARED_INPUT_IDS
from tests.e2e.scenario import seed_run_inputs

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="phase-runner",
        hypothesis="test",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _task() -> ResearchTask:
    return ResearchTask(id=ID.generate(), run_id=ID.generate(), contract_id="experiment_execution")


def _contract() -> TaskContract:
    return TaskContract(
        id="experiment_execution",
        version="1",
        purpose="test",
        # GOAL-011 EC-03：派发判据是**声明**（`contract.experiment is not None`），不是合约 id。
        # 本用例驱动的是实验缝 ⇒ 合约必须自己声明；不声明则按会话语义派发（另一条判据钉住）。
        experiment=ExperimentExecutionSpec(
            script="run.py",
            image="research-os-sandbox:m9-test",
            command="python run.py",
        ),
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS,
                artifact="samples.json",
            ),
            AcceptanceCriterion(
                type=AcceptanceCriterionType.EVIDENCE_COVERAGE,
                minimum_sources=1,
            ),
        ],
    )


def _spec_context() -> SessionSpecContext:
    return SessionSpecContext(
        role=RoleDefinition(
            id="experiment_engineer",
            role_type="experiment_engineer",
            category=RoleCategory.EXPERIMENT,
            activation_default=ActivationPolicy.ALWAYS,
        ),
        agent=AgentSpec(
            id="agent-1",
            role="experiment_engineer",
            model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        ),
        frozen_manifest_digest="manifest-digest",
        # GOAL-010 EC-02：experiment 任务的「非自身来源」同样是**声明的输入制品**——
        # 它自己的 experiment artifact 属于自产，覆盖判据不认；没有这条声明，
        # `EVIDENCE_COVERAGE: 1` 会如实判拒（本用例的合约就声明了它）。
        declared_input_artifacts=tuple(DECLARED_INPUT_IDS),
    )


def _make_memory_gate(
    ledger: FakeEvidenceLedger,
) -> tuple[FakeMemoryStore, MemoryGateDeps]:
    store = FakeMemoryStore(
        allowed_sources=(
            f"{_RUN_ID.value}:experiment_result.json",
            f"{_RUN_ID.value}:samples.json",
        )
    )
    gate = MemoryGateDeps(
        store=store,
        policy=FakePolicyEvaluator(),
        ledger=ledger,
        allowed_sources=frozenset({
            f"{_RUN_ID.value}:experiment_result.json",
            f"{_RUN_ID.value}:samples.json",
        }),
        actor="system:ig1",
    )
    return store, gate


def _make_experiment_deps(
    tmp_path: Path,
    artifacts: FakeArtifactStore,
    ledger: FakeEvidenceLedger,
) -> ExperimentTaskDeps:
    workspaces = FakeWorkspaceBackend()
    workspaces.create_workspace(Workspace(id="ws-a", name="ws-a"))
    (tmp_path / "samples.json").write_bytes(b"[1,2,3]")
    (tmp_path / "experiment_result.json").write_text(
        json.dumps({
            "experiment_run_id": str(_RUN_ID.value),
            "status": "SUCCEEDED",
            "artifact_refs": ["samples.json"],
            "metrics": {"mean": 0.5},
        }),
        encoding="utf-8",
    )
    inner = ExperimentExecutor(
        execution=FakeExecutionBackend(),
        workspaces=workspaces,
        artifacts=artifacts,
        workspace_dir=lambda lease: tmp_path,
    )
    governed = GovernedExperimentExecutor(inner=inner, policy=FakePolicyEvaluator())
    return ExperimentTaskDeps(
        executor=governed,
        artifacts=artifacts,
        ledger=ledger,
        request_builder=lambda task, contract, spec: ExperimentExecutionRequest(
            plan=_plan(),
            run_id=_RUN_ID,
            command="python run.py",
            workspace=Workspace(id="ws-a", name="ws-a"),
            agent_session_id=f"session-{task.id.value[:8]}",
            seed=42,
        ),
        provenance_builder=lambda task: ExperimentProvenance(
            run_id=str(task.run_id.value),
            manifest_digest="manifest-digest",
        ),
    )


def _make_phase_deps(
    tmp_path: Path,
) -> tuple[
    PhaseRunnerDeps,
    FakeArtifactStore,
    FakeEvidenceLedger,
    FakeMemoryStore,
    PhaseContext,
]:
    artifacts = FakeArtifactStore()
    seed_run_inputs(artifacts)  # GOAL-010 EC-02：协议声明的输入须在库（同生产组合根）
    ledger = FakeEvidenceLedger()
    memory_store, memory_gate = _make_memory_gate(ledger)
    exp_deps = _make_experiment_deps(tmp_path, artifacts, ledger)
    task = _task()
    contract = _contract()
    spec = _spec_context()
    deps = PhaseRunnerDeps(
        workflow=FakeWorkflowEngine(),
        runtime=FakeAgentRuntime(),
        artifacts=artifacts,
        ledger=ledger,
        memory_gate=memory_gate,
        experiment_task=lambda t, c, s, trace: execute_experiment_task(exp_deps, t, c, s, trace),
    )
    ctx = PhaseContext(
        command=None,
        resolve_sessions=lambda: ((task, contract, spec),),
        frozen_manifest_digest="manifest-digest",
        trace_id="trace-ig1",
        run_id=str(task.run_id.value),
    )
    return deps, artifacts, ledger, memory_store, ctx


def test_phase_runner_experiment_promotes_claim_and_memory(tmp_path: Path) -> None:
    deps, artifacts, ledger, memory_store, ctx = _make_phase_deps(tmp_path)
    outcome = execute_phases(deps, ctx)
    assert outcome.state == ResearchRunState.State.SUCCEEDED
    assert len(outcome.tasks) == 1
    assert outcome.tasks[0].verdict == "PASS"
    claims = ledger.claims()
    assert claims
    assert all(claim.status is ClaimStatus.VERIFIED for claim in claims)
    assert memory_store.query()
    artifact = next(a for a in artifacts.list_refs() if a.id == f"{_RUN_ID.value}:samples.json")
    assert artifact.state in (ArtifactState.VERIFIED, ArtifactState.ACTIVE)
