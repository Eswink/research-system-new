"""Experiment task dispatcher tests (IG-1 orchestration seam)."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.fakes import (
    FakeArtifactStore,
    FakeEvidenceLedger,
    FakeExecutionBackend,
    FakePolicyEvaluator,
    FakeWorkspaceBackend,
)
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
    ExperimentProvenance,
    GovernedExperimentExecutor,
)
from packages.application.run_orchestration.experiment_task import (
    ExperimentTaskDeps,
    execute_experiment_task,
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
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, TaskContract
from packages.domain.workspace import ExecutionStatus, Workspace

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="task-dispatch",
        hypothesis="test",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _task() -> ResearchTask:
    return ResearchTask(id=ID.generate(), run_id=ID.generate())


def _contract() -> TaskContract:
    return TaskContract(
        id="experiment_execution",
        version="1",
        purpose="test",
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS,
                artifact="samples.json",
            )
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
            model_binding=AgentBinding(
                mode=ModelBindingMode.EXPLICIT_MODEL,
                value="model-1",
            ),
        ),
        frozen_manifest_digest="manifest-digest",
    )


def _make_inner(
    tmp_path: Path,
    artifacts: FakeArtifactStore,
    *,
    status: str,
    artifact_refs: tuple[str, ...],
    execution_status: ExecutionStatus | None = None,
) -> ExperimentExecutor:
    workspaces = FakeWorkspaceBackend()
    workspaces.create_workspace(Workspace(id="ws-a", name="ws-a"))
    if "samples.json" in artifact_refs:
        (tmp_path / "samples.json").write_bytes(b"[1,2,3]")
    (tmp_path / "experiment_result.json").write_text(
        json.dumps({
            "experiment_run_id": str(_RUN_ID.value),
            "status": status,
            "artifact_refs": list(artifact_refs),
            "metrics": {"mean": 0.5} if status == "SUCCEEDED" else {"effect": 0.0},
        }),
        encoding="utf-8",
    )
    execution_backend = (
        FakeExecutionBackend(status=execution_status)
        if execution_status is not None
        else FakeExecutionBackend()
    )
    return ExperimentExecutor(
        execution=execution_backend,
        workspaces=workspaces,
        artifacts=artifacts,
        workspace_dir=lambda lease: tmp_path,
    )


def _make_deps(
    tmp_path: Path,
    *,
    status: str = "SUCCEEDED",
    artifact_refs: tuple[str, ...] = ("samples.json",),
    execution_status: ExecutionStatus | None = None,
) -> tuple[ExperimentTaskDeps, FakeEvidenceLedger, FakeArtifactStore]:
    ledger = FakeEvidenceLedger()
    artifacts = FakeArtifactStore()
    inner = _make_inner(
        tmp_path,
        artifacts,
        status=status,
        artifact_refs=artifact_refs,
        execution_status=execution_status,
    )
    governed = GovernedExperimentExecutor(inner=inner, policy=FakePolicyEvaluator())
    deps = ExperimentTaskDeps(
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
            manifest_digest=_spec_context().frozen_manifest_digest,
        ),
    )
    return deps, ledger, artifacts


def test_experiment_task_dispatches_and_admits_evidence(tmp_path: Path) -> None:
    deps, ledger, artifacts = _make_deps(tmp_path)
    result = execute_experiment_task(deps, _task(), _contract(), _spec_context(), "trace-1")

    assert result.succeeded
    assert result.experiment_outcome is not None
    assert result.experiment_admission is not None
    claims = ledger.claims()
    assert claims
    assert all(claim.status is ClaimStatus.PROPOSED for claim in claims)
    relation = ledger.relations_for_claim(claims[0].id)[0]
    ev = ledger.get_evidence(relation.evidence_id)
    assert ev.experiment_run_id == str(_RUN_ID.value)
    artifact = next(a for a in artifacts.list_refs() if a.id == f"{_RUN_ID.value}:samples.json")
    assert artifact.state in (ArtifactState.VERIFIED, ArtifactState.ACTIVE)


def test_negative_result_is_success_and_admitted(tmp_path: Path) -> None:
    deps, ledger, _ = _make_deps(
        tmp_path,
        status="NEGATIVE_RESULT",
        artifact_refs=(),
    )
    result = execute_experiment_task(deps, _task(), _contract(), _spec_context(), "trace-neg")

    assert result.succeeded
    assert result.experiment_outcome is not None
    assert result.experiment_outcome.run.state == "NEGATIVE_RESULT"
    assert result.experiment_admission is not None
    assert ledger.claims()


def test_cancelled_experiment_does_not_admit_evidence(tmp_path: Path) -> None:
    deps, ledger, _ = _make_deps(
        tmp_path,
        status="SUCCEEDED",
        artifact_refs=(),
        execution_status=ExecutionStatus.CANCELLED,
    )
    result = execute_experiment_task(deps, _task(), _contract(), _spec_context(), "trace-cancel")

    assert not result.succeeded
    assert result.experiment_outcome is not None
    assert result.experiment_outcome.run.state == "CANCELLED"
    assert ledger.claims() == ()
