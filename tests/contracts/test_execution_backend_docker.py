"""ExecutionBackend contract suite 真实容器实现（requires_docker）。

与 tests/contracts/test_ports_regressions.py 的 TestExecutionBackendContract
同语义断言，但以 DockerExecutionBackend（真实容器）执行：
- SUCCEEDED 必须携带 completed_at/started_at/exit_code==0（P0 回归 R-001）；
- timeout → TIMED_OUT（携带 completed_at，状态化而非异常，M5 D2）；
- FAILED 必须携带 failure_category；
- close 后拒绝（resource cleanup 语义）；
- stdout/stderr digest 与真实输出一致（内容寻址）。

Docker 不可用或镜像无法构建时 skip（离线 CI 环境由 Fake 覆盖同语义）。
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import docker
import pytest
from docker.errors import ImageNotFound

from adapters.execution import DockerExecutionBackend
from packages.application.ports.errors import PermanentPortError
from packages.domain.enums import FailureCategory
from packages.domain.workspace import ExecutionSpec, ExecutionStatus

pytestmark = pytest.mark.requires_docker

IMAGE_TAG = "research-os-sandbox:m9-test"
_SANDBOX_DIR = Path(__file__).resolve().parents[2] / "adapters" / "execution" / "sandbox"


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


def _spec(command: str, workspace_path: Path) -> ExecutionSpec:
    return ExecutionSpec(
        backend_kind="sandbox",
        command=command,
        workspace_path=str(workspace_path),
    )


def _write_result(metrics: dict[str, object]) -> str:
    payload = json.dumps(metrics)
    encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    return (
        f'python -c "import base64; '
        f"open('result.json','w').write(base64.b64decode('{encoded}').decode())\""
    )


class TestExecutionBackendContractDocker:
    def test_happy_path_returns_valid_run(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        run = backend.execute(_spec(_write_result({"n": 1}), tmp_path), timeout_seconds=60)
        assert run.status is ExecutionStatus.SUCCEEDED
        assert run.completed_at is not None
        assert run.started_at is not None
        assert run.exit_code == 0
        assert json.loads((tmp_path / "result.json").read_text(encoding="utf-8")) == {"n": 1}

    def test_timed_out_run_is_valid(self, backend: DockerExecutionBackend, tmp_path: Path) -> None:
        run = backend.execute(_spec("sleep 60", tmp_path), timeout_seconds=2)
        assert run.status is ExecutionStatus.TIMED_OUT
        assert run.completed_at is not None

    def test_failed_run_carries_failure_category(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        run = backend.execute(_spec("exit 7", tmp_path), timeout_seconds=60)
        assert run.status is ExecutionStatus.FAILED
        assert run.failure_category is FailureCategory.EXECUTION_FAILURE

    def test_close_then_calls_are_rejected(self, tmp_path: Path) -> None:
        """close 语义用独立实例验证，避免污染 module fixture。"""
        isolated = DockerExecutionBackend(image=IMAGE_TAG)
        isolated.close()
        with pytest.raises(PermanentPortError):
            isolated.execute(_spec("true", tmp_path))

    def test_stdout_digest_matches_content(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        run = backend.execute(_spec("echo contract-stdout", tmp_path), timeout_seconds=60)
        assert run.stdout_digest is not None
        assert run.stdout_digest.hex_value == hashlib.sha256(b"contract-stdout\n").hexdigest()

    def test_image_digest_recorded_in_summary(
        self, backend: DockerExecutionBackend, tmp_path: Path
    ) -> None:
        run = backend.execute(_spec("true", tmp_path), timeout_seconds=60)
        digest = run.compute_usage_summary["image_digest"]
        assert isinstance(digest, str) and digest.startswith("sha256:")
