"""DockerExecutionBackend 容器 E2E 与故障注入（requires_docker）。

验证 M9 DoD 容器面：创建/挂载/执行/timeout（kill）/失败/OOM/镜像缺失/
清理/网络禁用/host_config 资源边界断言。无 Docker daemon 时整体 skip；
镜像缺失时从仓库 Dockerfile 构建（CI 也显式 build）。

本机（Windows + Docker Desktop linux 容器）与 GitHub ubuntu runner 均可运行。
"""

from __future__ import annotations

import base64
import json
import threading
import time
from pathlib import Path
from typing import Any

import docker
import pytest
from docker.errors import ImageNotFound

from adapters.execution import DockerExecutionBackend
from packages.application.ports.errors import PermanentPortError
from packages.domain.enums import FailureCategory
from packages.domain.workspace import ExecutionRun, ExecutionSpec, ExecutionStatus

pytestmark = [pytest.mark.requires_docker, pytest.mark.timing_sensitive]

IMAGE_TAG = "research-os-sandbox:m9-test"
CONTAINER_FILTER = {"name": "research-os-exec"}

_SANDBOX_DIR = Path(__file__).resolve().parents[3] / "adapters" / "execution" / "sandbox"
_SMALL_MEMORY = 512 * 1024 * 1024


def _ping_with_retry(client: docker.DockerClient, attempts: int = 3) -> bool:
    """Transient daemon unresponsiveness (PART B W-04) — bounded ping retry
    before skipping; a genuinely down daemon still skips after the attempts."""
    for _ in range(attempts):
        try:
            client.ping()
            return True
        except Exception:  # noqa: BLE001 - daemon may still be starting
            time.sleep(0.5)
    return False


@pytest.fixture(scope="module")
def sandbox_image() -> str:
    client = docker.from_env()
    if not _ping_with_retry(client):
        pytest.skip("docker daemon unavailable")
    try:
        client.images.get(IMAGE_TAG)
    except ImageNotFound:
        client.images.build(path=str(_SANDBOX_DIR), tag=IMAGE_TAG)
    return IMAGE_TAG


@pytest.fixture()
def backend(sandbox_image: str) -> DockerExecutionBackend:
    return DockerExecutionBackend(image=sandbox_image)


def _spec(command: str, workspace_path: Path, **overrides: Any) -> ExecutionSpec:
    return ExecutionSpec(
        backend_kind="sandbox",
        command=command,
        workspace_path=str(workspace_path),
        **overrides,
    )


def _no_residual_containers() -> None:
    client = docker.from_env()
    remaining = client.containers.list(filters=CONTAINER_FILTER)
    assert remaining == [], f"residual containers: {[c.name for c in remaining]}"


def _write_result_python(metrics: dict[str, object], status: str = "SUCCEEDED") -> str:
    """构造容器内写 result.json 的命令；payload 经 base64 传递避免 shell 引号层。"""
    payload = json.dumps({"status": status, "metrics": metrics})
    encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    return (
        f'python -c "import base64; '
        f"from pathlib import Path; "
        f"Path('result.json').write_text(base64.b64decode('{encoded}').decode())\""
    )


class TestContainerLifecycle:
    def test_create_mount_execute_cleanup(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        command = _write_result_python({"n": 42}) + "; echo hello-container"
        run = backend.execute(_spec(command, tmp_path), timeout_seconds=60)
        assert run.status is ExecutionStatus.SUCCEEDED
        assert run.exit_code == 0
        assert run.completed_at is not None
        result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
        assert result == {"status": "SUCCEEDED", "metrics": {"n": 42}}
        assert "image_digest" in run.compute_usage_summary
        _no_residual_containers()

    def test_stdout_digest_matches_actual_output(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        run = backend.execute(_spec("echo deterministic-out", tmp_path), timeout_seconds=60)
        assert run.stdout_digest is not None
        expected = _sha256(b"deterministic-out\n")
        assert run.stdout_digest.hex_value == expected

    def test_deterministic_rerun_same_digest(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        first = backend.execute(_spec("echo reproducible", tmp_path), timeout_seconds=60)
        second = backend.execute(_spec("echo reproducible", tmp_path), timeout_seconds=60)
        assert first.stdout_digest == second.stdout_digest
        assert (
            first.compute_usage_summary["image_digest"]
            == second.compute_usage_summary["image_digest"]
        )

    def test_pinned_image_reference_is_consumed_and_recorded(
        self, sandbox_image: str, tmp_path: Path
    ) -> None:
        """`name@sha256:<digest>` pinned reference 可被消费且 digest 被记录。

        生产 composition 注入 pinned reference 的消费路径验证；digest 从
        fixture 镜像运行时解析，不硬编码环境值。
        """
        client = docker.from_env()
        expected = client.images.get(sandbox_image).id
        pinned = DockerExecutionBackend(image=f"research-os-sandbox@{expected}")
        run = pinned.execute(_spec("echo pinned-ref", tmp_path), timeout_seconds=60)
        assert run.status is ExecutionStatus.SUCCEEDED
        recorded = run.compute_usage_summary["image_digest"]
        assert recorded == expected


class TestFaultInjection:
    def test_timeout_kills_container_and_returns_timed_out(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        run = backend.execute(_spec("sleep 60", tmp_path), timeout_seconds=2)
        assert run.status is ExecutionStatus.TIMED_OUT
        assert run.completed_at is not None
        elapsed = run.compute_usage_summary["elapsed_seconds"]
        assert isinstance(elapsed, float) and elapsed < 10
        _no_residual_containers()

    def test_nonzero_exit_is_failed_with_category(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        run = backend.execute(_spec("exit 3", tmp_path), timeout_seconds=60)
        assert run.status is ExecutionStatus.FAILED
        assert run.failure_category is FailureCategory.EXECUTION_FAILURE
        assert run.exit_code == 3

    def test_oom_is_failed(self, backend: DockerExecutionBackend, tmp_path: Path) -> None:
        command = "python -c \"data = bytearray(1 << 30); data[:] = b'x' * (1 << 30)\""
        run = backend.execute(
            _spec(command, tmp_path, resource_profile="small"),
            timeout_seconds=60,
        )
        assert run.status is ExecutionStatus.FAILED
        assert run.compute_usage_summary["oom_killed"] is True

    def test_missing_image_is_permanent_configuration(self, tmp_path: Path) -> None:
        missing = DockerExecutionBackend(image="research-os-sandbox:does-not-exist")
        with pytest.raises(PermanentPortError) as exc_info:
            missing.execute(_spec("true", tmp_path), timeout_seconds=30)
        assert exc_info.value.failure_category is FailureCategory.CONFIGURATION
        _no_residual_containers()


class TestSandboxBoundaries:
    def test_network_is_disabled(self, backend: DockerExecutionBackend, tmp_path: Path) -> None:
        command = (
            'python -c "import socket; s = socket.socket(); '
            "s.settimeout(3); s.connect(('1.1.1.1', 53))\""
        )
        run = backend.execute(_spec(command, tmp_path), timeout_seconds=30)
        assert run.status is ExecutionStatus.FAILED
        assert run.stderr_digest is not None

    def test_pids_limit_blocks_fork_bomb(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        command = (
            'python -c "import os\n'
            "n = 0\n"
            "while True:\n"
            "    try:\n"
            "        os.fork()\n"
            "        n += 1\n"
            "    except OSError:\n"
            "        print('forked', n)\n"
            '        break"'
        )
        run = backend.execute(
            _spec(command, tmp_path, resource_profile="small"),
            timeout_seconds=30,
        )
        assert run.status is ExecutionStatus.SUCCEEDED
        assert run.stdout_digest is not None

    def test_host_config_boundaries_during_run(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        results: dict[str, ExecutionRun] = {}

        def run() -> None:
            results["run"] = backend.execute(
                _spec("sleep 5", tmp_path, resource_profile="small"),
                timeout_seconds=30,
            )

        thread = threading.Thread(target=run)
        thread.start()
        try:
            time.sleep(2.0)
            client = docker.from_env()
            containers = client.containers.list(filters=CONTAINER_FILTER)
            assert containers, "container should be running during execute"
            host_config = containers[0].attrs["HostConfig"]
            assert host_config["NetworkMode"] == "none"
            assert host_config["Privileged"] is False
            assert host_config["CapDrop"] == ["ALL"]
            assert host_config["SecurityOpt"] == ["no-new-privileges"]
            assert host_config["ReadonlyRootfs"] is True
            assert "/tmp" in host_config.get("Tmpfs", {})
            assert host_config["PidsLimit"] == 256
            assert host_config["Memory"] == _SMALL_MEMORY
            assert host_config["NanoCpus"] == 1_000_000_000
            binds = containers[0].attrs["Mounts"]
            assert binds and binds[0]["Destination"] == "/workspace"
            assert binds[0]["Source"] == str(tmp_path)
        finally:
            thread.join(timeout=60)
        run_result = results.get("run")
        assert run_result is not None
        assert run_result.status is ExecutionStatus.SUCCEEDED
        _no_residual_containers()


def _sha256(payload: bytes) -> str:
    import hashlib

    return hashlib.sha256(payload).hexdigest()
