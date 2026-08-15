"""DockerExecutionBackend：真实隔离容器执行（M9 Real Experiment Runtime）。

职责：把 ExecutionSpec 执行为一次性容器 run，返回归一化 ExecutionRun
（M5 决策 D2 同步语义）。每个 execute 创建容器 → start → wait（带 deadline）
→ 采集 stdout/stderr digest → 强制清理（force remove）。timeout 产生
ExecutionStatus.TIMED_OUT 而不是异常；compute usage 以摘要返回，不记账。

安全边界（AGENTS.md §9 / WORKSPACE_RUNTIME.md §6，运行时 host_config 施加）：
- 仅 bind-mount spec.workspace_path（或临时目录）到 spec.workdir；
- 网络 none、非 privileged、capability 全 drop、no-new-privileges；
- readonly rootfs + /tmp tmpfs（noexec/nosuid/size 64m）；
- CPU/memory/pids 限额来自 profiles.resolve_resource_profile；
- 不挂 Docker socket / host shell / home，不枚举 secret，环境变量由
  调用方（application use case）白名单构造后经 spec.environment 传入。

非职责：不管理文件布局与 Lease（WorkspaceBackend）；不记账（BudgetLedger）。

image 供应链：构造参数 image 必须可 pin（tag@digest 或本地构建镜像名）；
每次 execute 通过 inspect_image 解析实际 image digest，并写入
ExecutionRun.compute_usage_summary["image_digest"] 供 ReproducibilityAudit。
"""

from __future__ import annotations

import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import docker
from docker.errors import APIError, DockerException, ImageNotFound

from adapters.execution.profiles import ResourceLimits, resolve_resource_profile
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortError,
    TransientPortError,
)
from packages.application.ports.execution_backend import ExecutionBackend
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import FailureCategory
from packages.domain.workspace import ExecutionRun, ExecutionSpec, ExecutionStatus

CONTAINER_NAME_PREFIX = "research-os-exec"
# 镜像引用分界：
# - DEFAULT_IMAGE：本地开发默认（可变 tag，仅开发工作流，`docker build -t`
#   可覆盖）；不是生产 pin。
# - 测试/CI：`research-os-sandbox:m9-test` 构建 tag（fixture 缺失时自动 build，
#   CI container-quality job 显式 build）。
# - 生产 composition（M12/M14 落地）：必须注入 `name@sha256:<digest>` 形式的
#   pinned reference；每次 execute 仍解析实际 image digest 写入
#   compute_usage_summary["image_digest"]，供 ReproducibilityAudit 漂移检测。
DEFAULT_IMAGE = "research-os-sandbox:m9-sandbox-v1"
STDOUT_LOG = "stdout.log"
STDERR_LOG = "stderr.log"
_WAIT_STEP_SECONDS = 0.5
_TMPFS_MOUNT = "/tmp"
_TMPFS_OPTS = "rw,noexec,nosuid,size=64m,mode=1777"


def _resolve_workspace_dir(workspace_path: str | None) -> Path:
    """执行工作目录：未提供时创建隔离临时目录；容器内非 root 用户需可写。"""
    path = (
        Path(workspace_path).resolve()
        if workspace_path
        else Path(tempfile.mkdtemp(prefix="research-os-exec-"))
    )
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o777)
    except OSError:
        pass
    return path


def _final_status(timed_out: bool, exit_code: int) -> ExecutionStatus:
    if timed_out:
        return ExecutionStatus.TIMED_OUT
    if exit_code == 0:
        return ExecutionStatus.SUCCEEDED
    return ExecutionStatus.FAILED


def _map_docker_error(exc: Exception) -> PortError:
    if isinstance(exc, ImageNotFound):
        return PermanentPortError(
            "execution image not found",
            failure_category=FailureCategory.CONFIGURATION,
        )
    if isinstance(exc, APIError):
        if exc.status_code is not None and exc.status_code < 500:
            return PermanentPortError(
                "docker API rejected request",
                failure_category=FailureCategory.CONFIGURATION,
            )
        return TransientPortError(
            "docker API unavailable",
            failure_category=FailureCategory.WORKSPACE_FAILURE,
        )
    return TransientPortError(
        "docker daemon unavailable",
        failure_category=FailureCategory.WORKSPACE_FAILURE,
    )


class DockerExecutionBackend(ExecutionBackend):
    """一次性容器执行后端；线程不安全（同步语义，M5 D2）。"""

    def __init__(
        self,
        *,
        image: str = DEFAULT_IMAGE,
        client: docker.DockerClient | None = None,
    ) -> None:
        self._image = image
        self._owns_client = client is None
        self._client = client or docker.from_env()
        self._closed = False
        self._image_digest: str | None = None

    @property
    def image_digest(self) -> str | None:
        """最近一次 execute 解析到的实际 image digest（供审计使用）。"""
        return self._image_digest

    def execute(
        self,
        spec: ExecutionSpec,
        timeout_seconds: int | None = None,
    ) -> ExecutionRun:
        self._ensure_open()
        if not spec.command:
            raise InvalidInputError("execution command must not be empty")
        limits = resolve_resource_profile(spec.resource_profile)
        workspace = _resolve_workspace_dir(spec.workspace_path)
        container_id: str | None = None
        started = Timestamp.now()
        started_mono = time.monotonic()
        try:
            self._image_digest = self._resolve_image_digest()
            container_id = self._create_container(spec, limits, workspace)
            self._api.start(container_id)
            timed_out = self._wait(container_id, timeout_seconds)
            if timed_out:
                self._api.kill(container_id)
            state = self._api.inspect_container(container_id)
            exit_code = int((state.get("State") or {}).get("ExitCode") or 0)
            oom_killed = bool((state.get("State") or {}).get("OOMKilled"))
            stdout, stderr = self._collect_logs(container_id)
            self._write_workspace_logs(workspace, stdout, stderr)
            status = _final_status(timed_out, exit_code)
            return ExecutionRun(
                run_id=f"exec-{uuid.uuid4().hex}",
                spec=spec,
                status=status,
                started_at=started,
                completed_at=Timestamp.now(),
                exit_code=exit_code,
                failure_category=(
                    FailureCategory.EXECUTION_FAILURE if status is ExecutionStatus.FAILED else None
                ),
                stdout_digest=Digest.of_bytes(stdout),
                stderr_digest=Digest.of_bytes(stderr),
                compute_usage_summary={
                    "exit_code": exit_code,
                    "oom_killed": oom_killed,
                    "elapsed_seconds": round(time.monotonic() - started_mono, 3),
                    "image_digest": self._image_digest,
                },
            )
        except (APIError, DockerException) as exc:
            raise _map_docker_error(exc) from exc
        finally:
            if container_id is not None:
                self._remove_container(container_id)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._owns_client:
            self._client.close()

    @property
    def _api(self) -> Any:
        return self._client.api

    def _ensure_open(self) -> None:
        if self._closed:
            raise PermanentPortError(
                "execution backend is closed",
                failure_category=FailureCategory.CONFIGURATION,
            )

    def _resolve_image_digest(self) -> str:
        info = self._api.inspect_image(self._image)
        return str(info.get("Id") or "")

    def _create_container(
        self,
        spec: ExecutionSpec,
        limits: ResourceLimits,
        workspace: Path,
    ) -> str:
        host_config = {
            "Binds": [f"{workspace}:{spec.workdir}"],
            "NetworkMode": "none",
            "Privileged": False,
            "CapDrop": ["ALL"],
            "SecurityOpt": ["no-new-privileges"],
            "ReadonlyRootfs": True,
            "Tmpfs": {_TMPFS_MOUNT: _TMPFS_OPTS},
            "NanoCpus": limits.cpu_nanos,
            "Memory": limits.memory_bytes,
            "PidsLimit": limits.pids_limit,
        }
        container = self._api.create_container(
            image=self._image,
            command=["/bin/sh", "-c", spec.command],
            host_config=host_config,
            environment=dict(spec.environment),
            working_dir=spec.workdir,
            name=f"{CONTAINER_NAME_PREFIX}-{uuid.uuid4().hex[:12]}",
            detach=True,
        )
        return str(container.get("Id") or "")

    def _wait(self, container_id: str, timeout_seconds: int | None) -> bool:
        """轮询容器 Running 状态直到退出；越过 deadline 返回 True（timed_out）。

        不用 docker-py `wait(timeout=)`：其超时异常在 Windows npipe 与 Linux
        unix socket 上类型不一致（ConnectionError vs ReadTimeout），轮询
        inspect 跨平台确定。
        """
        deadline = time.monotonic() + timeout_seconds if timeout_seconds is not None else None
        while True:
            state = self._api.inspect_container(container_id)
            if not bool((state.get("State") or {}).get("Running")):
                return False
            if deadline is None:
                time.sleep(_WAIT_STEP_SECONDS)
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return True
            time.sleep(min(remaining, _WAIT_STEP_SECONDS))

    def _collect_logs(self, container_id: str) -> tuple[bytes, bytes]:
        stdout = self._api.logs(container_id, stdout=True, stderr=False)
        stderr = self._api.logs(container_id, stdout=False, stderr=True)
        return bytes(stdout), bytes(stderr)

    def _write_workspace_logs(self, workspace: Path, stdout: bytes, stderr: bytes) -> None:
        """执行输出契约：stdout/stderr 全文写入挂载工作区根目录。

        实验 use case（packages/application/experiments）据此把日志作为
        内容寻址 Artifact 落库，且文件进入 post-snapshot 构成可复现性
        绑定（WORKSPACE_RUNTIME.md §8）。
        """
        (workspace / STDOUT_LOG).write_bytes(stdout)
        (workspace / STDERR_LOG).write_bytes(stderr)

    def _remove_container(self, container_id: str) -> None:
        try:
            self._api.remove_container(container_id, force=True)
        except (APIError, DockerException):
            pass
