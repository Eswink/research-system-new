"""DockerExecutionBackend 容器安全边界攻击测试（requires_docker）。

主动攻击并断言默认 deny 全部生效（AGENTS.md §9 / WORKSPACE_RUNTIME.md §6）：
- host home 不可见；
- Docker socket 不存在；
- rootfs 只读；
- 运行时包安装被网络禁用阻断；
- 容器内非 root（uid 1000），提权挂载被拒。

容器本身不是完整安全 Sandbox（进程级隔离），本测试只断言 M9 范围内
声明的边界；系统级强化隔离属后续 Milestone（M9_DOCKER_QUALIFICATION §3）。
"""

from __future__ import annotations

from pathlib import Path

import docker
import pytest
from docker.errors import ImageNotFound

from adapters.execution import DockerExecutionBackend
from packages.domain.workspace import ExecutionSpec

pytestmark = pytest.mark.requires_docker

IMAGE_TAG = "research-os-sandbox:m9-test"
_SANDBOX_DIR = Path(__file__).resolve().parents[3] / "adapters" / "execution" / "sandbox"


@pytest.fixture(scope="module")
def backend() -> DockerExecutionBackend:
    client = docker.from_env()
    try:
        client.ping()
    except Exception:
        pytest.skip("docker daemon unavailable")
    try:
        client.images.get(IMAGE_TAG)
    except ImageNotFound:
        client.images.build(path=str(_SANDBOX_DIR), tag=IMAGE_TAG)
    return DockerExecutionBackend(image=IMAGE_TAG)


def _run(backend: DockerExecutionBackend, tmp_path: Path, command: str) -> tuple[str, str]:
    run = backend.execute(
        ExecutionSpec(backend_kind="sandbox", command=command, workspace_path=str(tmp_path)),
        timeout_seconds=60,
    )
    return run.status.value, (tmp_path / "stdout.log").read_text(encoding="utf-8", errors="replace")


class TestContainerSecurityBoundaries:
    def test_host_home_is_not_mounted(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        status, stdout = _run(backend, tmp_path, "ls -la /Users 2>&1; ls /home 2>&1")
        assert "No such file or directory" in stdout

    def test_docker_socket_is_absent(self, backend: DockerExecutionBackend, tmp_path: Path) -> None:
        status, stdout = _run(backend, tmp_path, "ls /var/run/docker.sock 2>&1")
        assert "No such file or directory" in stdout

    def test_rootfs_is_readonly(self, backend: DockerExecutionBackend, tmp_path: Path) -> None:
        status, stdout = _run(
            backend,
            tmp_path,
            "touch /etc/attack-marker 2>&1 && echo WROTE || echo WRITE_DENIED",
        )
        assert "Read-only file system" in stdout
        assert "WRITE_DENIED" in stdout

    def test_runtime_package_install_is_blocked_by_network_none(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        status, stdout = _run(backend, tmp_path, "pip install requests 2>&1 | tail -2")
        assert "No matching distribution found" in stdout

    def test_non_root_user_and_no_privilege_escalation(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        status, stdout = _run(backend, tmp_path, "id -u; mount /dev/sda1 /mnt 2>&1")
        assert "1000" in stdout
        assert "must be superuser" in stdout
