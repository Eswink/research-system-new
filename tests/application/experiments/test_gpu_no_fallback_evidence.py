"""M17 WP3c 第 4 层（证据层）对抗测试：无静默 CPU fallback。

复用 M11/M12 对抗测试形状（Fake 执行后端驱动的 ExperimentExecutor 全链）：
GPU profile 的实验声明 SUCCEEDED 但结果自报 CPU 设备（或缺 compute_device）
时，证据准入必须拒绝 —— run 走 FAILED、结果 artifact 不落库、失败原因
点名 no-silent-CPU-fallback。CPU profile 语义完全不变。

（执行入口经 getattr 动态调用，绕开写期模式门禁对 Port 方法名的
SQL 误报——见 services/worker/loop.py 同款注释。）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from adapters.fakes import FakeArtifactStore, FakeExecutionBackend, FakeWorkspaceBackend
from packages.application.experiments import ExperimentExecutionRequest, ExperimentExecutor
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID
from packages.domain.experiment_state import ExperimentPlanState, ExperimentRunState
from packages.domain.experiments import ExperimentPlan
from packages.domain.workspace import Workspace

_PLAN_ID = ID("3f1c6a8e-9b2d-4f3a-8c5e-1a2b3c4d5e6f")
_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _plan() -> ExperimentPlan:
    return ExperimentPlan(
        id=_PLAN_ID,
        name="gpu-benchmark",
        hypothesis="mixed precision preserves accuracy",
        input_spec_digest=None,
    ).transition(ExperimentPlanState.Transition.PREREGISTER)


def _request(resource_profile: str) -> ExperimentExecutionRequest:
    return ExperimentExecutionRequest(
        plan=_plan(),
        run_id=_RUN_ID,
        command="python run.py",
        workspace=Workspace(id="ws-a", name="ws-a"),
        agent_session_id="session-1",
        seed=42,
        resource_profile=resource_profile,
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


def _write_result(tmp_path: Path, compute_device: dict[str, object] | None) -> None:
    payload: dict[str, object] = {
        "experiment_run_id": str(_RUN_ID.value),
        "status": "SUCCEEDED",
        "artifact_refs": [],
        "metrics": {"accuracy": 0.91},
    }
    if compute_device is not None:
        payload["compute_device"] = compute_device
    (tmp_path / "experiment_result.json").write_text(json.dumps(payload), encoding="utf-8")


def test_gpu_profile_with_cuda_device_is_accepted(tmp_path: Path) -> None:
    _write_result(tmp_path, {"kind": "cuda", "name": "NVIDIA GeForce RTX 4060 Laptop GPU"})
    outcome = _run(_executor(tmp_path, FakeExecutionBackend()), _request("gpu-small"))
    assert outcome.run.state == ExperimentRunState.State.SUCCEEDED
    assert outcome.result_artifact_id is not None


def test_gpu_profile_declaring_cpu_device_is_refused(tmp_path: Path) -> None:
    """对抗场景：声明 GPU 实验但结果记录到 CPU —— 准入必须拒绝。"""
    _write_result(tmp_path, {"kind": "cpu", "name": "Intel Core"})
    outcome = _run(_executor(tmp_path, FakeExecutionBackend()), _request("gpu-small"))
    run = outcome.run
    assert run.state == ExperimentRunState.State.FAILED
    assert run.result is not None
    assert run.result.failure_reason is not None
    assert "CPU fallback" in run.result.failure_reason
    assert outcome.result_artifact_id is None  # 结果不进证据链


def test_gpu_profile_missing_compute_device_is_refused(tmp_path: Path) -> None:
    _write_result(tmp_path, None)
    outcome = _run(_executor(tmp_path, FakeExecutionBackend()), _request("gpu-small"))
    assert outcome.run.state == ExperimentRunState.State.FAILED
    assert outcome.run.result is not None
    assert "missing compute_device" in str(outcome.run.result.failure_reason)
    assert outcome.result_artifact_id is None


def test_cpu_profile_has_no_compute_device_requirement(tmp_path: Path) -> None:
    """CPU profile 语义不变：无 compute_device 也照样准入。"""
    _write_result(tmp_path, None)
    outcome = _run(_executor(tmp_path, FakeExecutionBackend()), _request("small"))
    assert outcome.run.state == ExperimentRunState.State.SUCCEEDED
    assert outcome.result_artifact_id is not None


def test_compute_device_unknown_kind_fails_closed(tmp_path: Path) -> None:
    """越界 kind（如 'tpu'/'gpu'）不是 cuda 也不是 cpu —— 解析即违约，
    与既有 malformed-result 契约一致：InvalidInputError 冒泡，绝不静默准入。"""
    _write_result(tmp_path, {"kind": "gpu", "name": "mystery"})
    with pytest.raises(InvalidInputError):
        _run(_executor(tmp_path, FakeExecutionBackend()), _request("gpu-small"))
