"""Worker-side GPU probe (M17 WP1): real facts from a real CUDA container.

The worker discovers its GPU by RUNNING the pinned GPU sandbox image with
DeviceRequests — the exact execution path a GPU job will take — and reading
structured facts from inside (torch device properties + a real GEMM kernel).
No `nvidia-smi` text parsing as truth, no caching, no guessing: any failure
returns `None` and the worker registers CPU-only (never declares `gpu`).

This is freshness layer 1 (startup probe) and layer 3 (re-probe) input;
layer 2 is the gateway TTL gate, layer 4 the in-container contract assert.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import docker
from docker.errors import DockerException

from packages.domain.core import Timestamp
from packages.domain.workers import (
    MAX_GPU_DEVICE_COUNT,
    WorkerGpuObservation,
    gpu_probe_digest,
)

GPU_SANDBOX_IMAGE_DEFAULT = "research-os-gpu-sandbox:m17-v1"
_PROBE_MOUNT = "/researchos-probe"
# 真实 CUDA kernel 校验和：ones(64,64) @ ones(64,64) 总和 = 64**3。
_GEMM_EXPECTED = 64.0**3

# 在 pinned GPU 容器内执行的探针：只读 introspection + 一次微小确定性
# GEMM（证明 compute 子系统可用，排除「设备可枚举但 kernel 不能跑」）。
# 输出单行 JSON；任何失败以非零退出（worker 侧 fail-closed → 不声明 gpu）。
_PROBE_SCRIPT = f"""
import json, subprocess, sys
sm = subprocess.run(
    ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
    capture_output=True, text=True, timeout=60,
)
if sm.returncode != 0:
    sys.exit(3)
import torch
if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
    sys.exit(4)
props = torch.cuda.get_device_properties(0)
x = torch.ones(64, 64, device="cuda:0", dtype=torch.float32)
y = x @ x
torch.cuda.synchronize()
print(json.dumps({{
    "device_name": props.name,
    "device_count": int(torch.cuda.device_count()),
    "driver_version": sm.stdout.strip(),
    "cuda_runtime_version": torch.version.cuda,
    "total_vram_bytes": int(props.total_memory),
    "torch_version": torch.__version__,
    "gemm_checksum": float(y.sum().item()),
    "gemm_expected": {_GEMM_EXPECTED!r},
}}, sort_keys=True))
"""


@dataclass(frozen=True, slots=True)
class GpuProbeConfig:
    """探测参数；image 必须是已按 digest pin 的 GPU sandbox 镜像。"""

    image: str = GPU_SANDBOX_IMAGE_DEFAULT
    probe_timeout_seconds: float = 300.0


def _parse_facts(stdout: bytes) -> dict[str, Any] | None:
    """取 stdout 最后一行 JSON；缺失/畸形 → None。"""
    lines = [ln for ln in stdout.decode("utf-8", "replace").splitlines() if ln.strip()]
    if not lines:
        return None
    try:
        facts: Any = json.loads(lines[-1])
    except json.JSONDecodeError:
        return None
    if not isinstance(facts, dict):
        return None
    required = {
        "device_name",
        "device_count",
        "driver_version",
        "cuda_runtime_version",
        "total_vram_bytes",
        "torch_version",
        "gemm_checksum",
        "gemm_expected",
    }
    if not required <= set(facts):
        return None
    return facts


def _observation_from_facts(facts: dict[str, Any]) -> WorkerGpuObservation | None:
    """结构化事实 → 有界观测；断言失败（含 GEMM 校验）→ None。"""
    count = int(facts["device_count"])
    vram = int(facts["total_vram_bytes"])
    if count < 1 or count > MAX_GPU_DEVICE_COUNT or vram <= 0:
        return None
    if abs(float(facts["gemm_checksum"]) - float(facts["gemm_expected"])) > 1e-6:
        return None  # 设备在但 compute 不工作：不声明 gpu
    framework = f"torch-{facts['torch_version']}"
    return WorkerGpuObservation(
        device_name=str(facts["device_name"]),
        device_count=count,
        driver_version=str(facts["driver_version"]),
        cuda_runtime_version=str(facts["cuda_runtime_version"]),
        total_vram_bytes=vram,
        framework=framework,
        probed_at=Timestamp.now(),
        probe_digest=gpu_probe_digest(
            device_name=str(facts["device_name"]),
            device_count=count,
            driver_version=str(facts["driver_version"]),
            cuda_runtime_version=str(facts["cuda_runtime_version"]),
            total_vram_bytes=vram,
            framework=framework,
        ),
    )


def probe_gpu(
    config: GpuProbeConfig,
    *,
    client: docker.DockerClient | None = None,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> WorkerGpuObservation | None:
    """运行真实 GPU 探测容器；任何失败 → None（不声明 gpu）。"""
    owns = client is None
    docker_client = client or docker.from_env()
    scratch = Path(tempfile.mkdtemp(prefix="researchos-gpu-probe-"))
    cid: str | None = None
    try:
        script = scratch / "gpu_probe.py"
        script.write_text(_PROBE_SCRIPT, encoding="utf-8")
        cid = _run_probe_container(docker_client, config, scratch, sleep, monotonic)
        if cid is None:
            return None
        facts = _collect(docker_client, cid)
        if facts is None:
            return None
        return _observation_from_facts(facts)
    except (DockerException, OSError, ValueError):
        return None
    finally:
        if cid is not None:
            try:
                docker_client.api.remove_container(cid, force=True)
            except (DockerException, OSError):
                pass
        # SI-1 W1: probe scratch was never removed — a long-lived worker
        # accumulated one temp dir per probe. Safe after container removal.
        shutil.rmtree(scratch, ignore_errors=True)
        if owns:
            docker_client.close()


def _sweep_stale_containers(client: docker.DockerClient, image: str) -> None:
    """SI-1 W2: remove stopped containers of the pinned image left behind by a
    hard-killed worker (probe + exec leftovers). Running containers are never
    touched, so no live compute is lost; a stopped container holds nothing."""
    try:
        for cont in client.api.list_containers(all=True, filters={"image": image}):
            if not bool((cont.get("State") or {}).get("Running")):
                try:
                    client.api.remove_container(cont["Id"], force=True)
                except (DockerException, OSError):
                    pass
    except (DockerException, OSError):
        pass


def _collect(client: docker.DockerClient, cid: str) -> dict[str, Any] | None:
    return _parse_facts(bytes(client.api.logs(cid, stdout=True, stderr=False)))


def _run_probe_container(
    client: docker.DockerClient,
    config: GpuProbeConfig,
    scratch: Path,
    sleep: Callable[[float], None],
    monotonic: Callable[[], float],
) -> str | None:
    """与执行路径同构的容器：完整安全基线 + DeviceRequests（WP0 T4 形式）。"""
    _sweep_stale_containers(client, config.image)
    host_config = {
        "Binds": [f"{scratch}:{_PROBE_MOUNT}:ro"],
        "NetworkMode": "none",
        "Privileged": False,
        "CapDrop": ["ALL"],
        "SecurityOpt": ["no-new-privileges"],
        "ReadonlyRootfs": True,
        "Tmpfs": {"/tmp": "rw,noexec,nosuid,size=64m,mode=1777"},
        "PidsLimit": 512,
        "DeviceRequests": [
            {"Driver": "nvidia", "Count": 1, "Capabilities": [["gpu", "compute", "utility"]]}
        ],
    }
    container = client.api.create_container(
        image=config.image,
        command=["python", f"{_PROBE_MOUNT}/gpu_probe.py"],
        host_config=host_config,
        detach=True,
    )
    cid = str(container.get("Id") or "")
    client.api.start(cid)
    deadline = monotonic() + config.probe_timeout_seconds
    while monotonic() < deadline:
        state = client.api.inspect_container(cid).get("State") or {}
        running = bool(state.get("Running"))
        exit_code = state.get("ExitCode")
        # ExitCode 0 is falsy: never fold it through `or` (0 != unknown here).
        if not running and exit_code is not None and int(exit_code) == 0:
            return cid
        if not running and exit_code is not None:
            return None
        sleep(0.5)
    client.api.kill(cid)
    return None
