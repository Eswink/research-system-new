"""Root test configuration: environment-probe skips for environment-dependent suites.

`requires_docker` / `requires_gpu` 标记的用例只有在真实环境可用时才执行；缺失时
诚实 skip（skip 计数在 pytest 输出中可见），而不是以环境错误 fail。CI 上可用
`RESEARCHOS_REQUIRE_DOCKER=1` / `RESEARCHOS_REQUIRE_GPU=1` 把「本该跳过」重新变成
硬失败（fail-closed）。PostgreSQL 的守卫沿用 `tests/postgres/conftest.py`。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_DOCKER_SKIP_REASON = (
    "no Linux-capable docker daemon available — requires_docker tests skipped "
    "(set RESEARCHOS_REQUIRE_DOCKER=1 to fail instead)"
)
_GPU_SKIP_REASON = (
    "no NVIDIA GPU device detected — requires_gpu tests skipped "
    "(set RESEARCHOS_REQUIRE_GPU=1 to fail instead)"
)


def _env_requires(name: str) -> bool:
    return os.environ.get(name) == "1"


def _docker_available() -> bool:
    """A *Linux-capable* daemon is required: every requires_docker suite runs
    Linux sandbox images. A Windows-container daemon (default on windows-latest)
    pings fine but cannot run them, so it must skip rather than fail."""
    try:
        import docker
    except ImportError:
        return False
    client = None
    try:
        client = docker.from_env(timeout=3)
        client.ping()
        info = client.info()
        return str(info.get("OSType", "")).lower() == "linux"
    except Exception:  # noqa: BLE001 - any daemon/transport failure means "no docker"
        return False
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:  # noqa: BLE001 - close is best-effort cleanup
                pass


def _gpu_available() -> bool:
    # Linux 设备节点是权威信号；Windows/macOS 回退到 nvidia-smi 存在性探测。
    if Path("/dev/nvidiactl").exists() or Path("/dev/nvidia0").exists():
        return True
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return False
    try:
        probe = subprocess.run(
            [nvidia_smi, "-L"],
            capture_output=True,
            timeout=15,
            check=False,
        )
    except Exception:  # noqa: BLE001 - a broken/blocked nvidia-smi means "no gpu"
        return False
    return probe.returncode == 0 and b"GPU" in probe.stdout


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    need_docker = any(item.get_closest_marker("requires_docker") for item in items)
    need_gpu = any(item.get_closest_marker("requires_gpu") for item in items)
    docker_ok = _docker_available() if need_docker else True
    gpu_ok = _gpu_available() if need_gpu else True
    require_docker = _env_requires("RESEARCHOS_REQUIRE_DOCKER") or _docker_is_the_point(config)
    require_gpu = _env_requires("RESEARCHOS_REQUIRE_GPU")
    for item in items:
        if item.get_closest_marker("requires_docker") and not docker_ok and not require_docker:
            item.add_marker(pytest.mark.skip(reason=_DOCKER_SKIP_REASON))
        elif item.get_closest_marker("requires_gpu") and not gpu_ok and not require_gpu:
            item.add_marker(pytest.mark.skip(reason=_GPU_SKIP_REASON))


def _docker_is_the_point(config: pytest.Config) -> bool:
    """`pytest -m requires_docker` 是专门的容器门禁作业：此时 daemon 缺失必须
    硬失败（fail-closed），而不是把整轮 skip 成 vacuous pass（避免削弱门禁）。"""
    markexpr = (getattr(config.option, "markexpr", "") or "").replace(" ", "")
    return markexpr == "requires_docker"
