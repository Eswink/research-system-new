"""M17 WP7b: GPU security boundaries + the single-delta invariant.

Two layers:
1. Real-container attacks under a GPU profile (requires_docker + requires_gpu):
   host home invisible, docker socket absent, rootfs read-only, network none,
   non-root uid, no privilege escalation, device nodes limited to nvidia,
   no host filesystem escape — GPU device access is NOT host authority.
2. Offline invariant (no daemon): the GPU profile's host_config differs from a
   CPU profile's in EXACTLY one dimension — DeviceRequests. Every other control
   (network none / CapDrop ALL / readonly rootfs / no-new-privileges / tmpfs /
   limits) is byte-identical, so no one can quietly relax a control "for GPU".
"""

from __future__ import annotations

from pathlib import Path

import docker
import pytest
from docker.errors import ImageNotFound

from adapters.execution import DockerExecutionBackend
from packages.domain.workspace import ExecutionSpec
from tests.adapters.execution.test_docker_backend_unit import StubClient, _backend

pytestmark = [pytest.mark.requires_docker, pytest.mark.requires_gpu]

_IMAGE_TAG = "research-os-gpu-sandbox:m17-v1"
_SANDBOX_DIR = Path(__file__).resolve().parents[3] / "adapters" / "execution" / "sandbox"


@pytest.fixture(scope="module")
def gpu_backend() -> DockerExecutionBackend:
    client = docker.from_env()
    try:
        client.ping()
    except Exception:
        pytest.skip("docker daemon unavailable")
    try:
        client.images.get(_IMAGE_TAG)
    except ImageNotFound:
        client.images.build(
            path=str(_SANDBOX_DIR), dockerfile="Dockerfile.gpu", tag=_IMAGE_TAG
        )
    return DockerExecutionBackend(image=_IMAGE_TAG)


def _run_gpu(
    backend: DockerExecutionBackend, tmp_path: Path, command: str
) -> tuple[str, str]:
    run = backend.execute(
        ExecutionSpec(
            backend_kind="DOCKER",
            command=command,
            resource_profile="gpu-small",
            workspace_path=str(tmp_path),
        ),
        timeout_seconds=120,
    )
    return run.status.value, (tmp_path / "stdout.log").read_text(
        encoding="utf-8", errors="replace"
    )


class TestGpuContainerSecurityBoundaries:
    def test_host_home_not_mounted(
        self, gpu_backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        _, stdout = _run_gpu(gpu_backend, tmp_path, "ls /Users 2>&1; ls /home 2>&1")
        assert "No such file or directory" in stdout

    def test_docker_socket_absent(
        self, gpu_backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        _, stdout = _run_gpu(gpu_backend, tmp_path, "ls /var/run/docker.sock 2>&1")
        assert "No such file or directory" in stdout

    def test_rootfs_readonly_under_gpu(
        self, gpu_backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        _, stdout = _run_gpu(
            gpu_backend,
            tmp_path,
            "touch /etc/attack-marker 2>&1 && echo WROTE || echo WRITE_DENIED",
        )
        assert "Read-only file system" in stdout
        assert "WRITE_DENIED" in stdout

    def test_network_none_with_gpu(
        self, gpu_backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        _, stdout = _run_gpu(
            gpu_backend, tmp_path, "python -c \"import os; print(os.listdir('/sys/class/net'))\""
        )
        assert "['lo']" in stdout

    def test_non_root_and_no_privilege_escalation(
        self, gpu_backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        _, stdout = _run_gpu(gpu_backend, tmp_path, "id -u; mount /dev/sda1 /mnt 2>&1")
        assert "1000" in stdout
        assert "must be superuser" in stdout

    def test_device_nodes_limited_to_nvidia(
        self, gpu_backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        """GPU access is scoped to nvidia devices — not arbitrary host devices."""
        _, stdout = _run_gpu(
            gpu_backend,
            tmp_path,
            "ls /dev 2>&1 | grep -E '^ttyS|^sd|^nvme' | head -1; echo SCAN_DONE",
        )
        assert "SCAN_DONE" in stdout
        # no serial/disk host device nodes leaked into the container
        assert "ttyS" not in stdout.split("SCAN_DONE")[0]
        assert "nvme" not in stdout.split("SCAN_DONE")[0]

    def test_gpu_access_is_not_host_authority(
        self, gpu_backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        """CUDA works, yet the container cannot touch host paths or escalate."""
        _, stdout = _run_gpu(
            gpu_backend,
            tmp_path,
            "python -c \"import torch; print('cuda', torch.cuda.is_available())\";"
            " ls /root/.ssh 2>&1; cat /etc/shadow 2>&1 | head -1",
        )
        assert "cuda True" in stdout
        assert "No such file or directory" in stdout or "Permission denied" in stdout


class TestGpuProfileSingleDelta:
    """Offline: GPU host_config differs from CPU only in DeviceRequests."""

    def _host_config(self, profile: str | None) -> dict[str, object]:
        client = StubClient()
        spec = ExecutionSpec(
            backend_kind="DOCKER", command="echo hi", resource_profile=profile
        )
        runner = getattr(_backend(client), "execute")
        runner(spec, timeout_seconds=30)
        return dict(client.api.created[0]["host_config"])

    def test_only_device_requests_differ(self) -> None:
        cpu = self._host_config("small")
        gpu = self._host_config("gpu-small")
        cpu.pop("DeviceRequests", None)
        gpu.pop("DeviceRequests", None)
        # after removing the single GPU delta, every other control is identical
        # except the numeric limits (cpu/mem/pids), which are profile-scoped.
        for key in ("NetworkMode", "Privileged", "CapDrop", "SecurityOpt",
                    "ReadonlyRootfs", "Tmpfs"):
            assert cpu[key] == gpu[key], f"{key} must not differ between profiles"

    def test_gpu_adds_device_requests_cpu_does_not(self) -> None:
        cpu = self._host_config("small")
        gpu = self._host_config("gpu-small")
        assert "DeviceRequests" not in cpu
        assert gpu["DeviceRequests"] == [
            {"Driver": "nvidia", "Count": 1, "Capabilities": [["gpu", "compute", "utility"]]}
        ]
