"""ExperimentExecutor 测试（Fake 执行后端，离线）。

覆盖：lease→执行→artifact→metric→状态分类全链；NEGATIVE_RESULT 语义
（exit 0 + 声明负结论 ≠ 执行失败）；timeout/执行失败分类；输出契约
违约（缺 result.json）；artifact ref 越界拒绝。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.fakes import (
    FakeArtifactStore,
    FakeExecutionBackend,
    FakeWorkspaceBackend,
)
from packages.application.experiments import (
    ExperimentExecutionRequest,
    ExperimentExecutor,
)
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID
from packages.domain.enums import FailureCategory
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState
from packages.domain.experiments import ExperimentPlan
from packages.domain.serialization import digest_of
from packages.domain.workspace import ExecutionStatus, Workspace

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="sort-benchmark",
        hypothesis="merge sort outperforms bubble sort",
        input_spec_digest=None,
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _request(**overrides: object) -> ExperimentExecutionRequest:
    fields: dict[str, object] = {
        "plan": _plan(),
        "run_id": _RUN_ID,
        "command": "python run.py",
        "workspace": Workspace(id="ws-a", name="ws-a"),
        "agent_session_id": "session-1",
        "seed": 42,
        "resource_profile": "small",
        **overrides,
    }
    return ExperimentExecutionRequest(**fields)  # type: ignore[arg-type]


def _executor(tmp_path: Path, execution: FakeExecutionBackend) -> ExperimentExecutor:
    workspaces = FakeWorkspaceBackend()
    workspaces.create_workspace(Workspace(id="ws-a", name="ws-a"))
    return ExperimentExecutor(
        execution=execution,
        workspaces=workspaces,
        artifacts=FakeArtifactStore(),
        workspace_dir=lambda lease: tmp_path,
    )


def _write_result(
    tmp_path: Path,
    *,
    status: str = "SUCCEEDED",
    metrics: dict[str, object] | None = None,
    refs: list[str] | None = None,
) -> None:
    (tmp_path / "experiment_result.json").write_text(
        json.dumps({
            "experiment_run_id": str(_RUN_ID.value),
            "status": status,
            "artifact_refs": refs or [],
            "metrics": metrics if metrics is not None else {"n": 42},
        }),
        encoding="utf-8",
    )


class TestSuccessfulExecution:
    def test_succeeded_run_produces_metrics_and_artifacts(self, tmp_path: Path) -> None:
        _write_result(tmp_path)
        executor = _executor(tmp_path, FakeExecutionBackend())
        outcome = executor.execute(_request())
        run = outcome.run
        assert run.state == ExperimentRunState.State.SUCCEEDED
        assert run.is_terminal
        assert run.result is not None
        assert run.result.metrics[0].metric.name == "n"
        assert run.result.workspace_snapshot_before is not None
        assert run.result.workspace_snapshot_after is not None
        assert outcome.result_artifact_id == f"{_RUN_ID.value}:experiment_result.json"

    def test_negative_result_is_not_execution_failure(self, tmp_path: Path) -> None:
        _write_result(tmp_path, status="NEGATIVE_RESULT", metrics={"effect": 0.0})
        outcome = _executor(tmp_path, FakeExecutionBackend()).execute(_request())
        assert outcome.run.state == ExperimentRunState.State.NEGATIVE_RESULT
        assert outcome.run.result is not None
        assert outcome.run.result.failure_reason == "declared scientific outcome: NEGATIVE_RESULT"

    def test_declared_failed_with_exit_zero_is_negative_result(self, tmp_path: Path) -> None:
        _write_result(tmp_path, status="FAILED", metrics={"p": 0.42})
        outcome = _executor(tmp_path, FakeExecutionBackend()).execute(_request())
        assert outcome.run.state == ExperimentRunState.State.NEGATIVE_RESULT

    def test_referenced_artifacts_are_stored(self, tmp_path: Path) -> None:
        (tmp_path / "chart.png").write_bytes(b"png-bytes")
        _write_result(tmp_path, refs=["chart.png"])
        outcome = _executor(tmp_path, FakeExecutionBackend()).execute(_request())
        run = outcome.run
        assert run.result is not None
        assert f"{_RUN_ID.value}:chart.png" in run.result.artifact_refs


class TestExecutionFailures:
    def test_failed_execution_overrides_declared_negative(self, tmp_path: Path) -> None:
        """非零退出即使输出自称 NEGATIVE_RESULT 也不采信（DoD 语义）。"""
        _write_result(tmp_path, status="NEGATIVE_RESULT")
        executor = _executor(
            tmp_path,
            FakeExecutionBackend(
                status=ExecutionStatus.FAILED,
                exit_code=3,
                failure_category=FailureCategory.EXECUTION_FAILURE,
            ),
        )
        outcome = executor.execute(_request())
        assert outcome.run.state == ExperimentRunState.State.FAILED
        assert outcome.run.result is not None
        assert outcome.run.result.metrics == ()
        assert outcome.run.result.failure_reason == "execution failed"

    def test_timed_out_execution(self, tmp_path: Path) -> None:
        executor = _executor(
            tmp_path,
            FakeExecutionBackend(duration_seconds=30),
        )
        outcome = executor.execute(_request(timeout_seconds=10))
        assert outcome.run.state == ExperimentRunState.State.TIMED_OUT
        assert outcome.run.result is not None
        assert outcome.run.result.failure_reason == "execution timed out"

    def test_missing_result_file_is_contract_violation(self, tmp_path: Path) -> None:
        outcome = _executor(tmp_path, FakeExecutionBackend()).execute(_request())
        assert outcome.run.state == ExperimentRunState.State.FAILED
        assert outcome.run.result is not None
        assert "missing experiment_result.json" in (outcome.run.result.failure_reason or "")


class TestInputValidation:
    def test_artifact_ref_escape_rejected(self, tmp_path: Path) -> None:
        _write_result(tmp_path, refs=["../escape.txt"])
        with pytest.raises(Exception) as exc_info:
            _executor(tmp_path, FakeExecutionBackend()).execute(_request())
        assert "escapes workspace" in str(exc_info.value)

    def test_missing_artifact_ref_rejected(self, tmp_path: Path) -> None:
        _write_result(tmp_path, refs=["missing.png"])
        with pytest.raises(Exception) as exc_info:
            _executor(tmp_path, FakeExecutionBackend()).execute(_request())
        assert "missing" in str(exc_info.value)

    def test_input_digest_changes_with_seed(self, tmp_path: Path) -> None:
        _write_result(tmp_path)
        executor = _executor(tmp_path, FakeExecutionBackend())
        first = executor.execute(_request(seed=1))
        second = executor.execute(_request(seed=2))
        assert first.run.spec is not None and second.run.spec is not None
        assert first.run.spec.input_digest != second.run.spec.input_digest

    def test_input_digest_stable_for_same_request(self, tmp_path: Path) -> None:
        _write_result(tmp_path)
        executor = _executor(tmp_path, FakeExecutionBackend())
        first = executor.execute(_request())
        second = executor.execute(_request())
        assert first.run.spec is not None and second.run.spec is not None
        assert first.run.spec.input_digest == second.run.spec.input_digest


class TestPlanGate:
    def test_draft_plan_rejected(self, tmp_path: Path) -> None:
        """生命周期门禁：未 PREREGISTER 的计划不得执行。"""
        _write_result(tmp_path)
        plan = ExperimentPlan(id=_PLAN_ID, name="sort-benchmark")
        with pytest.raises(InvalidInputError) as exc_info:
            _executor(tmp_path, FakeExecutionBackend()).execute(_request(plan=plan))
        assert "PREREGISTERED" in str(exc_info.value)

    def test_archived_plan_rejected(self, tmp_path: Path) -> None:
        _write_result(tmp_path)
        plan = _plan().transition(ExperimentPlanState.Transition.ARCHIVE)
        with pytest.raises(InvalidInputError):
            _executor(tmp_path, FakeExecutionBackend()).execute(_request(plan=plan))


class TestRunSpecBindings:
    def test_spec_binds_command_and_environment_digest(self, tmp_path: Path) -> None:
        """run spec 绑定原始 command 与 env digest（可复现性锚点）。"""
        _write_result(tmp_path)
        outcome = _executor(tmp_path, FakeExecutionBackend()).execute(
            _request(environment={"PYTHONHASHSEED": "0"})
        )
        spec = outcome.run.spec
        assert spec is not None
        assert spec.command == "python run.py"
        assert spec.environment_digest == digest_of({"PYTHONHASHSEED": "0"})

    def test_spec_binds_empty_environment_digest(self, tmp_path: Path) -> None:
        """空环境也必须产生 digest（None 会让审计锚点缺失）。"""
        _write_result(tmp_path)
        outcome = _executor(tmp_path, FakeExecutionBackend()).execute(_request())
        assert outcome.run.spec is not None
        assert outcome.run.spec.environment_digest is not None
