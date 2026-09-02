"""M17 WP3b 离线单元测试：GPU profile 的 host_config delta、契约环境注入、
GPU 事实白名单解析与失败分类（无需 Docker daemon；真实容器行为见
test_gpu_backend_e2e.py，requires_gpu）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adapters.execution.docker_backend import (
    GPU_FACTS_FILE,
    DockerExecutionBackend,
    _gpu_failure_category,
    _parse_gpu_facts,
)
from packages.domain.enums import FailureCategory
from packages.domain.workspace import ExecutionSpec, ExecutionStatus
from tests.adapters.execution.test_docker_backend_unit import StubClient, _backend


def _spec(
    profile: str | None = None, *, workspace_path: str | None = None, **env: str
) -> ExecutionSpec:
    return ExecutionSpec(
        backend_kind="DOCKER",
        command="echo hi",
        resource_profile=profile,
        workspace_path=workspace_path,
        environment=env,
    )


def _run(backend: DockerExecutionBackend, spec: ExecutionSpec) -> Any:
    runner = getattr(backend, "execute")
    return runner(spec, timeout_seconds=30)


def test_gpu_profile_adds_device_requests_and_assert_env(tmp_path: Path) -> None:
    client = StubClient()
    client.api.running_sequence = [True, False]
    _run(_backend(client), _spec("gpu-small", workspace_path=str(tmp_path)))
    created = client.api.created[0]
    host_config = created["host_config"]
    assert host_config["DeviceRequests"] == [
        {"Driver": "nvidia", "Count": 1, "Capabilities": [["gpu", "compute", "utility"]]}
    ]
    env = dict(created["environment"])
    assert env["RESEARCHOS_GPU_ASSERT_DEVICE_COUNT"] == "1"
    assert env["RESEARCHOS_GPU_ASSERT_FRAMEWORK"] == "torch"
    assert "RESEARCHOS_GPU_ASSERT_MIN_VRAM_BYTES" in env
    assert "RESEARCHOS_GPU_ASSERT_MIN_CUDA" in env
    # 唯一 delta：其余安全基线与 CPU profile 完全一致
    assert host_config["NetworkMode"] == "none"
    assert host_config["CapDrop"] == ["ALL"]
    assert host_config["ReadonlyRootfs"] is True
    assert host_config["Privileged"] is False


def test_cpu_profile_has_no_device_requests_or_assert_env(tmp_path: Path) -> None:
    client = StubClient()
    _run(_backend(client), _spec("small", workspace_path=str(tmp_path)))
    created = client.api.created[0]
    assert "DeviceRequests" not in created["host_config"]
    assert not [k for k in created["environment"] if k.startswith("RESEARCHOS_GPU_ASSERT")]


def test_gpu_run_merges_bounded_facts_into_summary(tmp_path: Path) -> None:
    client = StubClient()
    client.api.running_sequence = [True, False]
    facts = {
        "gpu_device_name": "NVIDIA GeForce RTX 4060 Laptop GPU",
        "driver_version": "581.80",
        "cuda_runtime_version": "12.8",
        "framework_version": "2.9.1+cu128",
        "peak_gpu_memory_bytes": 123_456,
        "gpu_elapsed_seconds": 7,
        "cuda_available": True,
    }
    (tmp_path / GPU_FACTS_FILE).write_text(json.dumps(facts), encoding="utf-8")
    run = _run(_backend(client), _spec("gpu-small", workspace_path=str(tmp_path)))
    assert run.status is ExecutionStatus.SUCCEEDED
    summary = run.compute_usage_summary
    assert summary["gpu_device_name"].endswith("RTX 4060 Laptop GPU")
    assert summary["peak_gpu_memory_bytes"] == 123_456
    assert summary["cuda_available"] is True


def test_parse_gpu_facts_whitelists_bounded_keys(tmp_path: Path) -> None:
    payload = {
        "gpu_device_name": "RTX 4060",
        "driver_version": "581.80",
        "cuda_runtime_version": "12.8",
        "framework_version": "2.9.1+cu128",
        "peak_gpu_memory_bytes": 123456,
        "gpu_elapsed_seconds": 7,
        "gpu_oom": False,
        "cuda_available": True,
        "prompt_text": "leak?",
        "gpu_elapsed_seconds_bad": "nope",
    }
    (tmp_path / GPU_FACTS_FILE).write_text(json.dumps(payload), encoding="utf-8")
    facts = _parse_gpu_facts(tmp_path)
    assert facts["gpu_device_name"] == "RTX 4060"
    assert facts["peak_gpu_memory_bytes"] == 123456
    assert facts["cuda_available"] is True
    assert "prompt_text" not in facts
    # 非整数的 gpu_elapsed_seconds 被丢弃（gpu_elapsed_seconds 仍是合法 int）
    malformed = dict(payload, gpu_elapsed_seconds="not-an-int")
    (tmp_path / GPU_FACTS_FILE).write_text(json.dumps(malformed), encoding="utf-8")
    assert "gpu_elapsed_seconds" not in _parse_gpu_facts(tmp_path)


def test_parse_gpu_facts_missing_or_malformed_yields_empty(tmp_path: Path) -> None:
    assert _parse_gpu_facts(tmp_path) == {}
    (tmp_path / GPU_FACTS_FILE).write_text("[]", encoding="utf-8")
    assert _parse_gpu_facts(tmp_path) == {}
    (tmp_path / GPU_FACTS_FILE).write_text("{not json", encoding="utf-8")
    assert _parse_gpu_facts(tmp_path) == {}


def test_gpu_failure_category_oom_beats_unavailable() -> None:
    spec = _spec("gpu-small")
    assert _gpu_failure_category(spec, {"gpu_oom": True}) is FailureCategory.GPU_OOM
    assert _gpu_failure_category(spec, {"cuda_available": False}) is FailureCategory.GPU_UNAVAILABLE
    # 设备在、非 OOM → 不加 GPU 分类（保持 EXECUTION_FAILURE 兜底）
    assert _gpu_failure_category(spec, {"gpu_device_name": "RTX"}) is None


def test_cpu_profile_never_gets_gpu_failure_category() -> None:
    spec = _spec("small")
    assert _gpu_failure_category(spec, {"gpu_oom": True}) is None
    assert _gpu_failure_category(spec, {"cuda_available": False}) is None


def test_failed_gpu_run_with_oom_facts_maps_to_gpu_oom(tmp_path: Path) -> None:
    client = StubClient()
    client.api.running_sequence = [True, False]
    client.api.inspect_final_state = {
        "State": {"Running": False, "ExitCode": 1, "OOMKilled": False}
    }
    (tmp_path / GPU_FACTS_FILE).write_text(
        json.dumps({"gpu_oom": True, "cuda_available": True}), encoding="utf-8"
    )
    run = _run(_backend(client), _spec("gpu-small", workspace_path=str(tmp_path)))
    assert run.status is ExecutionStatus.FAILED
    assert run.failure_category is FailureCategory.GPU_OOM
