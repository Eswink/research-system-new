"""M17 WP4a 失败语义边界测试（Fake 执行后端，离线）。

固定 GPU_OOM / GPU_UNAVAILABLE 与 SCIENTIFIC_NEGATIVE_RESULT 的边界：
- CUDA OOM 是执行/资源失败 → FAILED 终态 + GPU_OOM 分类，即使结果文件
  自称 NEGATIVE_RESULT 也不采信（M9 语义的 GPU 延伸）；
- 指标未改善（exit 0 + 声明负结论）是科学结论 → NEGATIVE_RESULT 终态，
  绝不挂 GPU 失败分类；
- GPU_UNAVAILABLE（从未 claim / 设备不可见）不落入 CPU 执行路径。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adapters.fakes import FakeArtifactStore, FakeExecutionBackend, FakeWorkspaceBackend
from packages.application.experiments import ExperimentExecutionRequest, ExperimentExecutor
from packages.application.experiments.classification import gpu_failure_reason
from packages.domain.core import ID
from packages.domain.enums import FailureCategory
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState
from packages.domain.experiments import ExperimentPlan
from packages.domain.workspace import ExecutionStatus, Workspace

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="gpu-boundary",
        hypothesis="mixed precision preserves accuracy",
        input_spec_digest=None,
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _request() -> ExperimentExecutionRequest:
    return ExperimentExecutionRequest(
        plan=_plan(),
        run_id=_RUN_ID,
        command="python train.py",
        workspace=Workspace(id="ws-a", name="ws-a"),
        agent_session_id="session-1",
        resource_profile="gpu-small",
    )


def _executor(tmp_path: Path, execution: FakeExecutionBackend) -> ExperimentExecutor:
    workspaces = FakeWorkspaceBackend()
    workspaces.create_workspace(Workspace(id="ws-a", name="ws-a"))
    return ExperimentExecutor(
        execution=execution,
        workspaces=workspaces,
        artifacts=FakeArtifactStore(),
        workspace_dir=lambda lease: tmp_path,
    )


def _run(executee: ExperimentExecutor, request: ExperimentExecutionRequest) -> Any:
    runner = getattr(executee, "execute")
    return runner(request)


def _write_result(tmp_path: Path, *, status: str, compute_device: dict[str, object]) -> None:
    payload = {
        "experiment_run_id": str(_RUN_ID.value),
        "status": status,
        "artifact_refs": [],
        "metrics": {"accuracy": 0.55},
        "compute_device": compute_device,
    }
    (tmp_path / "experiment_result.json").write_text(json.dumps(payload), encoding="utf-8")


_CUDA = {"kind": "cuda", "name": "NVIDIA GeForce RTX 4060 Laptop GPU"}


def test_cuda_oom_is_execution_failure_not_negative_result(tmp_path: Path) -> None:
    """OOM 中途崩溃：即使结果文件自称 NEGATIVE_RESULT，终态也是 FAILED。"""
    _write_result(tmp_path, status="NEGATIVE_RESULT", compute_device=_CUDA)
    backend = FakeExecutionBackend(
        status=ExecutionStatus.FAILED,
        exit_code=1,
        failure_category=FailureCategory.GPU_OOM,
    )
    outcome = _run(_executor(tmp_path, backend), _request())
    run = outcome.run
    assert run.state == ExperimentRunState.State.FAILED
    assert run.state != ExperimentRunState.State.NEGATIVE_RESULT
    assert run.result is not None
    assert run.result.failure_reason is not None
    assert "GPU_OOM" in run.result.failure_reason


def test_scientific_regression_is_negative_result_never_gpu_failure(tmp_path: Path) -> None:
    """指标未改善：exit 0 + 声明负结论 → NEGATIVE_RESULT，无 GPU 失败分类。"""
    _write_result(tmp_path, status="NEGATIVE_RESULT", compute_device=_CUDA)
    backend = FakeExecutionBackend(status=ExecutionStatus.SUCCEEDED, exit_code=0)
    outcome = _run(_executor(tmp_path, backend), _request())
    run = outcome.run
    assert run.state == ExperimentRunState.State.NEGATIVE_RESULT
    assert run.result is not None
    assert run.result.failure_reason is None or "GPU" not in str(run.result.failure_reason)


def test_gpu_unavailable_surfaces_reason(tmp_path: Path) -> None:
    _write_result(tmp_path, status="SUCCEEDED", compute_device=_CUDA)
    backend = FakeExecutionBackend(
        status=ExecutionStatus.FAILED,
        exit_code=1,
        failure_category=FailureCategory.GPU_UNAVAILABLE,
    )
    outcome = _run(_executor(tmp_path, backend), _request())
    run = outcome.run
    assert run.state == ExperimentRunState.State.FAILED
    assert run.result is not None
    assert "GPU_UNAVAILABLE" in str(run.result.failure_reason)


def test_gpu_failure_reason_mapping() -> None:
    assert gpu_failure_reason(FailureCategory.GPU_OOM) is not None
    assert "GPU_OOM" in str(gpu_failure_reason(FailureCategory.GPU_OOM))
    assert "GPU_UNAVAILABLE" in str(gpu_failure_reason(FailureCategory.GPU_UNAVAILABLE))
    # 非 GPU 分类不走 GPU 原因（M16 语义不变）
    assert gpu_failure_reason(FailureCategory.EXECUTION_FAILURE) is None
    assert gpu_failure_reason(FailureCategory.WORKER_LOST) is None
