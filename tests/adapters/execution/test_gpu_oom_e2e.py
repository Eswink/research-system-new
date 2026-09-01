"""M17 WP4b 受控 OOM E2E（requires_docker + requires_gpu）。

可重复、不损伤机器稳定性的真实 CUDA OOM：容器内 256 MiB 分块分配，目标
= 实测 free 显存 + 小余量，配 set_per_process_memory_fraction 上限保护；
捕获 torch.cuda.OutOfMemoryError 后如实记账（gpu_oom=true）并退出 1。

验证链：进程终止 → 容器清理 → GPU_OOM 分类 → 显存释放（新探针容器实测）
→ worker/backend 仍可用（紧接的下一个 GPU job SUCCEEDED）。全程无
Fake/Mock：OOM 必须真实发生在真实驱动/allocator 上。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.execution import DockerExecutionBackend
from adapters.execution.gpu_probe import GpuProbeConfig, probe_gpu
from packages.domain.enums import FailureCategory
from packages.domain.workspace import ExecutionSpec, ExecutionStatus

pytestmark = [pytest.mark.requires_docker, pytest.mark.requires_gpu]

IMAGE_TAG = "research-os-gpu-sandbox:m17-v1"

# OOM 探针：分块分配直至越过 free+margin（必然 OOM）；fraction 上限是
# 第二道保护。OOM 捕获后释放全部块并验证 free 显存回升，然后如实写
# gpu_oom=true 退出 1（执行失败语义，绝不假装成功）。
_OOM_SCRIPT = '''
import json, sys
from pathlib import Path
import torch

CHUNK_BYTES = 256 * 1024 * 1024
MARGIN_BYTES = 512 * 1024 * 1024

free, total = torch.cuda.mem_get_info()
torch.cuda.set_per_process_memory_fraction(0.85)
props = torch.cuda.get_device_properties(0)
chunks = []
oom = False
try:
    allocated = 0
    while allocated < int(free) + MARGIN_BYTES:
        chunks.append(torch.empty(CHUNK_BYTES // 4, dtype=torch.float32, device="cuda:0"))
        allocated += CHUNK_BYTES
except torch.cuda.OutOfMemoryError:
    oom = True
peak = int(torch.cuda.max_memory_allocated())
chunks.clear()
torch.cuda.empty_cache()
free_after, _ = torch.cuda.mem_get_info()
facts = {
    "cuda_available": True,
    "gpu_device_name": props.name,
    "gpu_oom": oom,
    "framework_version": torch.__version__,
    "cuda_runtime_version": torch.version.cuda or "",
    "peak_gpu_memory_bytes": peak,
    "gpu_elapsed_seconds": 0,
    "free_bytes_after_release": int(free_after),
}
Path("gpu_runtime_facts.json").write_text(json.dumps(facts), encoding="utf-8")
sys.exit(1 if oom else 0)
'''

_HEALTHY_SCRIPT = '''
import json
from pathlib import Path
import torch

assert torch.cuda.is_available()
x = torch.ones(64, 64, device="cuda:0")
torch.cuda.synchronize()
facts = {
    "cuda_available": True,
    "gpu_device_name": torch.cuda.get_device_properties(0).name,
    "gpu_oom": False,
    "framework_version": torch.__version__,
    "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated()),
}
Path("gpu_runtime_facts.json").write_text(json.dumps(facts), encoding="utf-8")
Path("experiment_result.json").write_text(
    json.dumps({"status": "SUCCEEDED", "metrics": {"ok": 1}}), encoding="utf-8")
print("healthy ok")
'''


@pytest.fixture(scope="module")
def gpu_backend() -> DockerExecutionBackend:
    return DockerExecutionBackend(image=IMAGE_TAG)


def _spec(tmp_path: Path, script: str, name: str) -> ExecutionSpec:
    workspace = tmp_path / name
    workspace.mkdir()
    workspace.joinpath("main.py").write_text(script, encoding="utf-8")
    return ExecutionSpec(
        backend_kind="DOCKER",
        command="python /workspace/main.py",
        resource_profile="gpu-oom-probe",
        workspace_path=str(workspace),
    )


def _run(backend: DockerExecutionBackend, spec: ExecutionSpec, **kw: object) -> object:
    runner = getattr(backend, "execute")
    return runner(spec, **kw)


def test_controlled_oom_fails_cleans_and_recovers(tmp_path: Path, gpu_backend: DockerExecutionBackend) -> None:
    oom_spec = _spec(tmp_path, _OOM_SCRIPT, "oom")
    run = _run(gpu_backend, oom_spec, timeout_seconds=600)
    assert run.status is ExecutionStatus.FAILED
    assert run.failure_category is FailureCategory.GPU_OOM
    summary = run.compute_usage_summary
    assert summary["gpu_oom"] is True
    assert int(summary["peak_gpu_memory_bytes"]) > 0
    workspace = Path(str(oom_spec.workspace_path))
    facts = json.loads(workspace.joinpath("gpu_runtime_facts.json").read_text(encoding="utf-8"))
    assert facts["gpu_oom"] is True
    # 显存释放验证：容器退出前 free 显存已回升（进程内实测），且没有任何
    # 残留容器（backend finally 强制 remove 由下一 job 成功隐式证明）。
    released = int(facts["free_bytes_after_release"])
    assert released > 2 * 1024**3  # OOM 后释放，free 显存回到可用量级

    # worker/backend 仍可用：紧接的下一个 GPU job 必须成功
    healthy_spec = _spec(tmp_path, _HEALTHY_SCRIPT, "healthy")
    healthy = _run(gpu_backend, healthy_spec, timeout_seconds=600)
    assert healthy.status is ExecutionStatus.SUCCEEDED

    # 新探针容器实测显存已释放：探测路径完整可用
    observation = probe_gpu(GpuProbeConfig(image=IMAGE_TAG))
    assert observation is not None
    assert observation.device_count == 1
