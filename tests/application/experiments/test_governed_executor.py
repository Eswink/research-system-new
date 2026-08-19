"""GovernedExperimentExecutor tests (IG-1 policy/credential/budget/cancel seam)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.fakes import (
    FakeArtifactStore,
    FakeExecutionBackend,
    FakePolicyEvaluator,
    FakeWorkspaceBackend,
)
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
    GovernedExperimentExecutor,
)
from packages.application.ports.errors import PermanentPortError, PortCancelledError
from packages.domain.core import ID
from packages.domain.enums import PolicyDecision
from packages.domain.experiment_state import ExperimentPlanState
from packages.domain.experiments import ExperimentPlan
from packages.domain.workspace import Workspace

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="governed",
        hypothesis="test",
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _request(tmp_path: Path) -> ExperimentExecutionRequest:
    return ExperimentExecutionRequest(
        plan=_plan(),
        run_id=_RUN_ID,
        command="python run.py",
        workspace=Workspace(id="ws-a", name="ws-a"),
        agent_session_id="session-1",
        seed=42,
        environment={"SAFE": "1"},
    )


def _inner(tmp_path: Path) -> ExperimentExecutor:
    workspaces = FakeWorkspaceBackend()
    workspaces.create_workspace(Workspace(id="ws-a", name="ws-a"))
    (tmp_path / "experiment_result.json").write_text(
        json.dumps({
            "experiment_run_id": str(_RUN_ID.value),
            "status": "SUCCEEDED",
            "artifact_refs": [],
            "metrics": {"n": 1},
        }),
        encoding="utf-8",
    )
    return ExperimentExecutor(
        execution=FakeExecutionBackend(),
        workspaces=workspaces,
        artifacts=FakeArtifactStore(),
        workspace_dir=lambda lease: tmp_path,
    )


def test_policy_deny_blocks_before_execution(tmp_path: Path) -> None:
    policy = FakePolicyEvaluator()
    policy.set_decision("code.execute", PolicyDecision.DENY)
    inner = _inner(tmp_path)
    governed = GovernedExperimentExecutor(inner=inner, policy=policy)
    with pytest.raises(PermanentPortError, match="policy denied"):
        governed.execute(_request(tmp_path))
    assert inner._execution.method_calls("execute") == 0  # type: ignore[attr-defined]


def test_approval_required_blocks_before_execution(tmp_path: Path) -> None:
    policy = FakePolicyEvaluator()
    policy.set_decision("code.execute", PolicyDecision.REQUIRE_APPROVAL)
    governed = GovernedExperimentExecutor(inner=_inner(tmp_path), policy=policy)
    with pytest.raises(PermanentPortError, match="requires approval"):
        governed.execute(_request(tmp_path))


def test_budget_and_credential_gates_are_called(tmp_path: Path) -> None:
    calls: list[str] = []
    governed = GovernedExperimentExecutor(
        inner=_inner(tmp_path),
        policy=FakePolicyEvaluator(),
        budget_check=lambda: calls.append("budget"),
        credential_check=lambda: calls.append("credential"),
    )
    governed.execute(_request(tmp_path))
    assert calls == ["budget", "credential"]


def test_cancellation_blocks_before_execution(tmp_path: Path) -> None:
    governed = GovernedExperimentExecutor(
        inner=_inner(tmp_path),
        policy=FakePolicyEvaluator(),
        cancellation_check=lambda: True,
    )
    with pytest.raises(PortCancelledError):
        governed.execute(_request(tmp_path))


def test_usage_recorder_called_on_success(tmp_path: Path) -> None:
    recorded: list[str] = []
    governed = GovernedExperimentExecutor(
        inner=_inner(tmp_path),
        policy=FakePolicyEvaluator(),
        usage_recorder=lambda outcome: recorded.append(outcome.run.state),
    )
    governed.execute(_request(tmp_path))
    assert recorded == ["SUCCEEDED"]


def test_idempotency_check_returns_existing_without_execution(tmp_path: Path) -> None:
    inner = _inner(tmp_path)
    existing = inner.execute(_request(tmp_path))
    calls: list[str] = []
    governed = GovernedExperimentExecutor(
        inner=inner,
        policy=FakePolicyEvaluator(),
        idempotency_check=lambda req: existing,
        usage_recorder=lambda outcome: calls.append("recorded"),
    )
    outcome = governed.execute(_request(tmp_path))
    assert outcome == existing
    assert calls == []  # duplicate path skips usage recording
