"""DockerExecutionBackend 离线单元测试（无需 Docker daemon）。

用 Stub 客户端按脚本验证：host_config 安全边界、timeout deadline 逻辑、
错误映射、close 语义、profile 解析。真实容器行为由
test_docker_backend_e2e.py（requires_docker）覆盖。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from docker.errors import APIError, ImageNotFound

from adapters.execution import DockerExecutionBackend, resolve_resource_profile
from adapters.execution.docker_backend import _map_docker_error
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    TransientPortError,
)
from packages.domain.enums import FailureCategory
from packages.domain.workspace import ExecutionSpec, ExecutionStatus

_EXPECTED_DIGEST_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class StubApi:
    """记录调用的 docker API stub（create/start/inspect/kill/logs/remove）。"""

    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []
        self.started: list[str] = []
        self.killed: list[str] = []
        self.removed: list[str] = []
        self.inspect_calls = 0
        self.inspect_image_result: dict[str, Any] = {"Id": "sha256:" + "ab" * 32}
        self.inspect_final_state: dict[str, Any] = {
            "State": {"Running": False, "ExitCode": 0, "OOMKilled": False}
        }
        self.running_sequence: list[bool] = [False]
        self.logs_stdout = b""
        self.logs_stderr = b""
        self.image_error: Exception | None = None
        self.api_error: Exception | None = None

    def inspect_image(self, image: str) -> dict[str, Any]:
        if self.image_error is not None:
            raise self.image_error
        return self.inspect_image_result

    def create_container(self, **kwargs: Any) -> dict[str, Any]:
        if self.api_error is not None:
            raise self.api_error
        self.created.append(kwargs)
        return {"Id": "cid-1"}

    def start(self, container: str) -> None:
        if self.api_error is not None:
            raise self.api_error
        self.started.append(container)

    def kill(self, container: str) -> None:
        self.killed.append(container)

    def inspect_container(self, container: str) -> dict[str, Any]:
        self.inspect_calls += 1
        running = self.running_sequence[min(self.inspect_calls, len(self.running_sequence)) - 1]
        if running:
            return {"State": {"Running": True, "ExitCode": 0, "OOMKilled": False}}
        return self.inspect_final_state

    def logs(self, container: str, stdout: bool, stderr: bool) -> bytes:
        return self.logs_stdout if stdout else self.logs_stderr

    def remove_container(self, container: str, force: bool) -> None:
        self.removed.append(container)


class StubClient:
    def __init__(self) -> None:
        self.api = StubApi()
        self.closed = False

    def close(self) -> None:
        self.closed = True


def _backend(client: StubClient | None = None) -> DockerExecutionBackend:
    return DockerExecutionBackend(image="research-os-sandbox:test", client=client or StubClient())


def _spec(**overrides: Any) -> ExecutionSpec:
    fields = {"backend_kind": "sandbox", "command": "echo hi", **overrides}
    return ExecutionSpec(**fields)


class TestHappyPath:
    def test_succeeded_run_and_security_boundaries(self, tmp_path: Path) -> None:
        client = StubClient()
        client.api.running_sequence = [True, False]
        backend = _backend(client)
        run = backend.execute(
            _spec(workspace_path=str(tmp_path), resource_profile="small"),
            timeout_seconds=60,
        )
        assert run.status is ExecutionStatus.SUCCEEDED
        assert run.completed_at is not None
        assert run.exit_code == 0
        assert run.failure_category is None
        assert run.stdout_digest is not None
        assert run.stderr_digest is not None
        assert run.compute_usage_summary["image_digest"] == "sha256:" + "ab" * 32
        host_config = client.api.created[0]["host_config"]
        assert host_config["Binds"] == [f"{tmp_path}:/workspace"]
        assert host_config["NetworkMode"] == "none"
        assert host_config["Privileged"] is False
        assert host_config["CapDrop"] == ["ALL"]
        assert host_config["SecurityOpt"] == ["no-new-privileges"]
        assert host_config["ReadonlyRootfs"] is True
        assert host_config["Tmpfs"] == {"/tmp": "rw,noexec,nosuid,size=64m,mode=1777"}
        assert host_config["NanoCpus"] == 1_000_000_000
        assert host_config["Memory"] == 512 * 1024 * 1024
        assert host_config["PidsLimit"] == 256
        assert client.api.removed == ["cid-1"]

    def test_stdout_stderr_digests(self, tmp_path: Path) -> None:
        client = StubClient()
        client.api.logs_stdout = b"hello\n"
        client.api.logs_stderr = b"warn\n"
        run = _backend(client).execute(_spec(workspace_path=str(tmp_path)))
        assert run.stdout_digest is not None
        assert run.stderr_digest is not None
        assert str(run.stdout_digest) != str(run.stderr_digest)

    def test_empty_stdout_digest_is_sha256_of_empty(self, tmp_path: Path) -> None:
        run = _backend().execute(_spec(workspace_path=str(tmp_path)))
        assert run.stdout_digest is not None
        assert run.stdout_digest.hex_value == _EXPECTED_DIGEST_SHA


class TestFailureMapping:
    def test_nonzero_exit_is_failed(self, tmp_path: Path) -> None:
        client = StubClient()
        client.api.inspect_final_state = {
            "State": {"Running": False, "ExitCode": 3, "OOMKilled": False}
        }
        run = _backend(client).execute(_spec(workspace_path=str(tmp_path)))
        assert run.status is ExecutionStatus.FAILED
        assert run.failure_category is FailureCategory.EXECUTION_FAILURE
        assert run.exit_code == 3

    def test_oom_is_failed(self, tmp_path: Path) -> None:
        client = StubClient()
        client.api.inspect_final_state = {
            "State": {"Running": False, "ExitCode": 137, "OOMKilled": True}
        }
        run = _backend(client).execute(_spec(workspace_path=str(tmp_path)))
        assert run.status is ExecutionStatus.FAILED
        assert run.compute_usage_summary["oom_killed"] is True

    def test_timeout_kills_and_returns_timed_out(self, tmp_path: Path) -> None:
        client = StubClient()
        client.api.running_sequence = [True]
        run = _backend(client).execute(_spec(workspace_path=str(tmp_path)), timeout_seconds=1)
        assert run.status is ExecutionStatus.TIMED_OUT
        assert client.api.killed == ["cid-1"]
        assert client.api.removed == ["cid-1"]
        assert client.api.inspect_calls >= 1

    def test_container_exit_before_deadline_succeeds(self, tmp_path: Path) -> None:
        client = StubClient()
        client.api.running_sequence = [True, True, False]
        run = _backend(client).execute(_spec(workspace_path=str(tmp_path)), timeout_seconds=30)
        assert run.status is ExecutionStatus.SUCCEEDED
        assert client.api.killed == []

    def test_missing_image_is_permanent_configuration(self, tmp_path: Path) -> None:
        client = StubClient()
        client.api.image_error = ImageNotFound("missing")
        with pytest.raises(PermanentPortError) as exc_info:
            _backend(client).execute(_spec(workspace_path=str(tmp_path)))
        assert exc_info.value.failure_category is FailureCategory.CONFIGURATION
        assert client.api.removed == []

    def test_daemon_error_is_transient(self, tmp_path: Path) -> None:
        client = StubClient()
        client.api.api_error = APIError("daemon down", response=None)
        with pytest.raises(TransientPortError):
            _backend(client).execute(_spec(workspace_path=str(tmp_path)))
        assert client.api.removed == []

    def test_mapping_covers_image_and_api_errors(self) -> None:
        permanent = _map_docker_error(ImageNotFound("missing"))
        transient = _map_docker_error(APIError("500", response=None))
        assert isinstance(permanent, PermanentPortError)
        assert isinstance(transient, TransientPortError)


class TestInputValidation:
    def test_empty_command_rejected_at_domain(self) -> None:
        """空 command 被 ExecutionSpec 域不变量拒绝（backend 双保险）。"""
        with pytest.raises(ValueError):
            ExecutionSpec(backend_kind="sandbox", command="")

    def test_unknown_resource_profile_rejected(self) -> None:
        with pytest.raises(InvalidInputError):
            _backend().execute(_spec(resource_profile="nope"))

    def test_close_then_execute_rejected(self) -> None:
        client = StubClient()
        backend = _backend(client)
        backend.close()
        with pytest.raises(PermanentPortError):
            backend.execute(_spec())
        assert client.closed is False

    def test_injected_client_not_closed_on_close(self) -> None:
        client = StubClient()
        backend = _backend(client)
        backend.close()
        assert client.closed is False


class TestProfiles:
    def test_default_profile(self) -> None:
        limits = resolve_resource_profile(None)
        assert limits.memory_bytes == 2 * 1024 * 1024 * 1024

    def test_known_profiles_are_deterministic(self) -> None:
        assert resolve_resource_profile("small") == resolve_resource_profile("small")
        assert resolve_resource_profile("large").cpu_nanos == 4_000_000_000

    def test_unknown_profile_rejected(self) -> None:
        with pytest.raises(InvalidInputError):
            resolve_resource_profile("missing")
