"""M17 WP3b Real GPU Smoke（requires_docker + requires_gpu）。

真实 NVIDIA GPU 上的 DockerExecutionBackend 冒烟：真实设备可见性、CUDA
初始化、真实 compute（GEMM）、stdout/stderr 落盘、workspace Artifact、
timeout 清理、GPU 下的 network none。隐藏 GPU（清空设备可见性环境变量）
时同一 workload 必须 FAIL/GPU_UNAVAILABLE——无静默 CPU fallback（第 3/4
层防线的执行面证据；调度层负向在 test_gpu_dispatch.py）。

无 Docker daemon 或无 pinned GPU 镜像时整体 skip；镜像缺失时按
Dockerfile.gpu（基座按 digest pin）构建。
"""

from __future__ import annotations

import json
from pathlib import Path

import docker
import pytest
from docker.errors import ImageNotFound

from adapters.execution import DockerExecutionBackend
from packages.domain.enums import FailureCategory
from packages.domain.workspace import ExecutionSpec, ExecutionStatus

pytestmark = [pytest.mark.requires_docker, pytest.mark.requires_gpu]

IMAGE_TAG = "research-os-gpu-sandbox:m17-v1"
CONTAINER_FILTER = {"name": "research-os-exec"}


def _repo_root() -> Path:
    """tests/adapters/execution/x.py → 仓库根（向上找到 pyproject.toml）。"""
    root = Path(__file__).resolve()
    while not root.joinpath("pyproject.toml").exists():
        root = root.parent
    return root


def _sandbox_dir() -> Path:
    return _repo_root().joinpath("adapters", "execution", "sandbox")

# GPU 实验入口的公共形状（WP6a 研究实验同款断言/记账逻辑）：
# 强制设备断言 → 只在 cuda:0 上真实计算 → 写 gpu_runtime_facts.json +
# experiment_result.json（compute_device 进证据链）。任何断言失败 = FAIL，
# 绝不降级 CPU。
_GPU_SMOKE_SCRIPT = '''
import json, os, subprocess, sys
from pathlib import Path

def write_facts(facts):
    Path("gpu_runtime_facts.json").write_text(json.dumps(facts), encoding="utf-8")

def main():
    import torch
    assert_count = int(os.environ.get("RESEARCHOS_GPU_ASSERT_DEVICE_COUNT", "1"))
    min_vram = int(os.environ.get("RESEARCHOS_GPU_ASSERT_MIN_VRAM_BYTES", "0"))
    min_cuda = os.environ.get("RESEARCHOS_GPU_ASSERT_MIN_CUDA", "")
    if torch.cuda.device_count() < assert_count:
        write_facts({"cuda_available": torch.cuda.is_available()})
        sys.exit(1)
    props = torch.cuda.get_device_properties(0)
    total_vram = int(props.total_memory)
    cuda = torch.version.cuda or ""
    if not torch.cuda.is_available() or total_vram < min_vram or cuda < min_cuda:
        write_facts({"cuda_available": False, "gpu_device_name": props.name})
        sys.exit(1)
    x = torch.ones(128, 128, device="cuda:0", dtype=torch.float32)
    y = x @ x
    torch.cuda.synchronize()
    sm = subprocess.run(
        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
        capture_output=True, text=True, timeout=30)
    write_facts({
        "cuda_available": True,
        "gpu_device_name": props.name,
        "driver_version": sm.stdout.strip() if sm.returncode == 0 else "unknown",
        "cuda_runtime_version": cuda,
        "framework_version": torch.__version__,
        "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated()),
        "gpu_elapsed_seconds": 0,
    })
    result = {
        "status": "SUCCEEDED",
        "metrics": {"gemm_checksum": float(y.sum().item())},
        "compute_device": {
            "kind": "cuda",
            "name": props.name,
            "total_vram_bytes": total_vram,
            "cuda_runtime_version": cuda,
        },
    }
    Path("experiment_result.json").write_text(json.dumps(result), encoding="utf-8")
    print("gpu smoke ok")

main()
'''


@pytest.fixture(scope="module")
def gpu_image() -> str:
    client = docker.from_env()
    try:
        client.ping()
    except Exception:
        pytest.skip("docker daemon unavailable")
    try:
        client.images.get(IMAGE_TAG)
    except ImageNotFound:
        client.images.build(
            path=str(_sandbox_dir()), dockerfile="Dockerfile.gpu", tag=IMAGE_TAG
        )
    return IMAGE_TAG


@pytest.fixture()
def gpu_backend(gpu_image: str) -> DockerExecutionBackend:
    return DockerExecutionBackend(image=gpu_image)


def _gpu_spec(tmp_path: Path, script: str, **env: str) -> ExecutionSpec:
    workspace = tmp_path.joinpath("ws")
    workspace.mkdir(exist_ok=True)
    workspace.joinpath("gpu_smoke.py").write_text(script, encoding="utf-8")
    return ExecutionSpec(
        backend_kind="DOCKER",
        command="python /workspace/gpu_smoke.py",
        resource_profile="gpu-small",
        workspace_path=str(workspace),
        environment=env,
    )


def _run(backend: DockerExecutionBackend, spec: ExecutionSpec, **kw: object) -> object:
    runner = getattr(backend, "execute")
    return runner(spec, **kw)


def _no_leftover_containers() -> None:
    client = docker.from_env()
    leftovers = client.api.containers(filters=CONTAINER_FILTER)
    assert not leftovers


def test_real_gpu_smoke_succeeds_and_reports_facts(
    tmp_path: Path, gpu_backend: DockerExecutionBackend
) -> None:
    spec = _gpu_spec(tmp_path, _GPU_SMOKE_SCRIPT)
    run = _run(gpu_backend, spec, timeout_seconds=600)
    assert run.status is ExecutionStatus.SUCCEEDED
    summary = run.compute_usage_summary
    assert summary["cuda_available"] is True
    device_name = str(summary["gpu_device_name"])
    assert "NVIDIA" in device_name.upper() or "GEFORCE" in device_name.upper()
    assert str(summary["cuda_runtime_version"]).startswith("12.")
    assert int(summary["peak_gpu_memory_bytes"]) > 0
    workspace = Path(str(spec.workspace_path))
    result = json.loads(workspace.joinpath("experiment_result.json").read_text(encoding="utf-8"))
    assert result["compute_device"]["kind"] == "cuda"
    assert result["metrics"]["gemm_checksum"] == 128.0**3  # 真实 GEMM 精确结果
    assert workspace.joinpath("stdout.log").exists()
    assert workspace.joinpath("stderr.log").exists()
    _no_leftover_containers()


def test_hidden_gpu_must_fail_not_fallback(
    tmp_path: Path, gpu_backend: DockerExecutionBackend
) -> None:
    """清空设备可见性环境变量 → 必须 FAIL/GPU_UNAVAILABLE，绝不 CPU 执行。"""
    spec = _gpu_spec(tmp_path, _GPU_SMOKE_SCRIPT, CUDA_VISIBLE_DEVICES="")
    run = _run(gpu_backend, spec, timeout_seconds=600)
    assert run.status is ExecutionStatus.FAILED
    assert run.failure_category is FailureCategory.GPU_UNAVAILABLE
    workspace = Path(str(spec.workspace_path))
    facts = json.loads(workspace.joinpath("gpu_runtime_facts.json").read_text(encoding="utf-8"))
    assert facts["cuda_available"] is False
    # 没有 experiment_result.json —— 没有 CPU 上的计算发生
    assert not workspace.joinpath("experiment_result.json").exists()
    _no_leftover_containers()


def test_gpu_profile_timeout_kills_and_cleans(
    tmp_path: Path, gpu_backend: DockerExecutionBackend
) -> None:
    spec = _gpu_spec(tmp_path, "import time; time.sleep(300)")
    run = _run(gpu_backend, spec, timeout_seconds=6)
    assert run.status is ExecutionStatus.TIMED_OUT
    _no_leftover_containers()


def test_gpu_profile_keeps_network_none(
    tmp_path: Path, gpu_backend: DockerExecutionBackend
) -> None:
    workspace = tmp_path.joinpath("ws")
    workspace.mkdir(exist_ok=True)
    spec = ExecutionSpec(
        backend_kind="DOCKER",
        command="python -c \"import os; assert os.listdir('/sys/class/net') == ['lo']; print('net none ok')\"",
        resource_profile="gpu-small",
        workspace_path=str(workspace),
    )
    run = _run(gpu_backend, spec, timeout_seconds=120)
    assert run.status is ExecutionStatus.SUCCEEDED
    _no_leftover_containers()
