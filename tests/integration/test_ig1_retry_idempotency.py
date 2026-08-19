"""IG-1 retry/idempotency: same run_id does not duplicate evidence."""

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
from packages.application.experiments.types import ExperimentExecutionOutcome
from packages.application.run_orchestration.experiment_task import (
    ExperimentTaskDeps,
    execute_experiment_task,
)
from packages.application.run_orchestration.task_executor import SessionSpecContext
from packages.domain.core import ID
from packages.domain.enums import ActivationPolicy, ModelBindingMode, RoleCategory
from packages.domain.experiment_state import ExperimentPlanState
from packages.domain.experiments import ExperimentPlan
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from packages.domain.tasks import ResearchTask, TaskContract
from packages.domain.workspace import Workspace

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="retry",
        hypothesis="test",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _task() -> ResearchTask:
    return ResearchTask(id=ID.generate(), run_id=ID.generate(), contract_id="experiment_execution")


def _contract() -> TaskContract:
    from packages.domain.enums import AcceptanceCriterionType
    from packages.domain.tasks import AcceptanceCriterion

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
            model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        ),
        frozen_manifest_digest="manifest",
    )


def _make_deps(tmp_path: Path) -> tuple[ExperimentTaskDeps, FakeEvidenceLedger, FakeArtifactStore]:
    ledger = FakeEvidenceLedger()
    artifacts = FakeArtifactStore()
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
    cache: dict[str, ExperimentExecutionOutcome | None] = {}
    governed = GovernedExperimentExecutor(
        inner=inner,
        policy=FakePolicyEvaluator(),
        idempotency_check=lambda req: cache.get(req.run_id.value),
    )
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
        provenance_builder=lambda task: ExperimentProvenance(run_id=str(task.run_id.value)),
    )
    return deps, ledger, artifacts


def test_retry_does_not_duplicate_evidence(tmp_path: Path) -> None:
    deps, ledger, artifacts = _make_deps(tmp_path)
    first = execute_experiment_task(deps, _task(), _contract(), _spec_context(), "trace-1")
    assert first.succeeded
    # Populate the idempotency cache with the first outcome.
    assert first.experiment_outcome is not None
    deps.executor._idempotency_check = lambda req: first.experiment_outcome
    second = execute_experiment_task(deps, _task(), _contract(), _spec_context(), "trace-2")
    assert second.succeeded
    # No duplicate canonical evidence/claims.
    assert len(ledger.claims()) == 1
    assert len(ledger.relations_for_claim(ledger.claims()[0].id)) == 2
    assert len([a for a in artifacts.list_refs() if a.id == f"{_RUN_ID.value}:samples.json"]) == 1
