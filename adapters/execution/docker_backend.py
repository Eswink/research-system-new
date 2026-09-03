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
image 供应链：image 必须可 pin；每次 execute 解析实际 digest 写入
ExecutionRun.compute_usage_summary["image_digest"] 供 ReproducibilityAudit。
"""

from __future__ import annotations

import json
import tempfile
import time
import uuid
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import docker
from docker.errors import APIError, DockerException, ImageNotFound

from adapters.execution.profiles import (
    ResourceLimits,
    is_gpu_profile,
    resolve_gpu_requirements,
    resolve_resource_profile,
)
from packages.application.observability.scope import operation
from packages.application.observability.signals import OperationOutcome, OperationScope
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortError,
    TransientPortError,
)
from packages.application.ports.execution_backend import ExecutionBackend
from packages.application.ports.telemetry_sink import TelemetrySink
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
# M17 GPU 契约文件：GPU profile 执行时，容器内实验入口把自己的设备事实
# （设备名/驱动/CUDA/框架/峰值显存/是否 OOM）写入 workspace 根目录的该文件；
# 执行后端解析其中有界子集并入 compute_usage_summary（不新增第二真相源，
# 仍走 ExecutionRun → compute_usage_summary 单一通道）。
GPU_FACTS_FILE = "gpu_runtime_facts.json"
_GPU_FACT_KEYS = {
    "gpu_device_name": str,
    "driver_version": str,
    "cuda_runtime_version": str,
    "framework_version": str,
    "peak_gpu_memory_bytes": int,
    # PA-1 W3: allow fractional seconds from the in-container timer
    # (measured below in _SECONDS_FACT_KEYS; contract still rejects bool).
    "gpu_elapsed_seconds": (int, float),
}
_SECONDS_FACT_KEYS = frozenset({"gpu_elapsed_seconds"})
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


def _final_status(timed_out: bool, exit_code: int, cancelled: bool = False) -> ExecutionStatus:
    if cancelled:
        return ExecutionStatus.CANCELLED
    if timed_out:
        return ExecutionStatus.TIMED_OUT
    if exit_code == 0:
        return ExecutionStatus.SUCCEEDED
    return ExecutionStatus.FAILED


def _build_run(  # noqa: PLR0913 - ExecutionRun 字段映射，参数对象会降低可读性
    spec: ExecutionSpec,
    started: Timestamp,
    started_mono: float,
    *,
    status: ExecutionStatus,
    exit_code: int,
    oom_killed: bool,
    stdout: bytes,
    stderr: bytes,
    image_digest: str | None,
    extra_summary: dict[str, object] | None = None,
    failure_category: FailureCategory | None = None,
) -> ExecutionRun:
    summary: dict[str, object] = {
        "exit_code": exit_code,
        "oom_killed": oom_killed,
        "elapsed_seconds": round(time.monotonic() - started_mono, 3),
        "image_digest": image_digest,
    }
    if extra_summary:
        summary.update(extra_summary)
    if failure_category is None and status is ExecutionStatus.FAILED:
        failure_category = FailureCategory.EXECUTION_FAILURE
    return ExecutionRun(
        run_id=f"exec-{uuid.uuid4().hex}",
        spec=spec,
        status=status,
        started_at=started,
        completed_at=Timestamp.now(),
        exit_code=exit_code,
        failure_category=failure_category,
        stdout_digest=Digest.of_bytes(stdout),
        stderr_digest=Digest.of_bytes(stderr),
        compute_usage_summary=summary,
    )


def _gpu_failure_category(spec: ExecutionSpec, facts: dict[str, object]) -> FailureCategory | None:
    """GPU profile 失败的细分类（WP4a）：OOM 优先于设备不可用。

    依据只来自容器内实验自己报告的 gpu_runtime_facts.json（受控字段），
    不猜 stderr 文本。非 GPU profile 永远返回 None。
    """
    if not is_gpu_profile(spec.resource_profile):
        return None
    if facts.get("gpu_oom") is True:
        return FailureCategory.GPU_OOM
    if facts.get("cuda_available") is False or facts.get("gpu_device_name") is None:
        return FailureCategory.GPU_UNAVAILABLE
    return None


def _parse_gpu_facts(workspace: Path) -> dict[str, object]:
    """读取容器内报告的 GPU 事实（有界白名单子集；缺失/畸形 → 空 dict）。"""
    try:
        raw = json.loads((workspace / GPU_FACTS_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    facts: dict[str, object] = {}
    for key, expected in _GPU_FACT_KEYS.items():
        value = raw.get(key)
        kinds = expected if isinstance(expected, tuple) else (expected,)
        if isinstance(value, kinds) and not isinstance(value, bool):
            # PA-1 W3: one-decimal sub-second honesty as Decimal (canonical-
            # safe); integral values stay ints; bools stay out.
            if key in _SECONDS_FACT_KEYS:
                rounded = round(Decimal(str(value)), 1)
                facts[key] = int(rounded) if rounded == rounded.to_integral_value() else rounded
            else:
                facts[key] = value
    # 显式布尔：只有容器内确实报告了才携带
    for key in ("gpu_oom", "cuda_available"):
        if isinstance(raw.get(key), bool):
            facts[key] = raw[key]
    return facts


def _gpu_assert_environment(spec: ExecutionSpec) -> dict[str, str]:
    """把 GPU profile 的执行期契约注入容器环境（WP3c 第 3 层断言输入）。"""
    requirements = resolve_gpu_requirements(spec.resource_profile or "")
    return {
        "RESEARCHOS_GPU_ASSERT_DEVICE_COUNT": str(requirements.device_count),
        "RESEARCHOS_GPU_ASSERT_MIN_VRAM_BYTES": str(requirements.min_total_vram_bytes),
        "RESEARCHOS_GPU_ASSERT_MIN_CUDA": requirements.min_cuda_runtime_version,
        "RESEARCHOS_GPU_ASSERT_FRAMEWORK": requirements.framework,
    }


def _map_docker_error(exc: Exception, *, gpu_profile: bool = False) -> PortError:
    """Docker 异常 → PortError；GPU profile 下创建期失败分类为 GPU_UNAVAILABLE。

    M17 第 2 层无静默 CPU fallback 防线：DeviceRequests 无法满足（无 nvidia
    runtime / 设备不可见）是 GPU 基础设施失败，绝不降级为 CPU 重试。
    """
    category = None
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
        category = (
            FailureCategory.GPU_UNAVAILABLE if gpu_profile else FailureCategory.WORKSPACE_FAILURE
        )
        return TransientPortError("docker API unavailable", failure_category=category)
    category = FailureCategory.GPU_UNAVAILABLE if gpu_profile else FailureCategory.WORKSPACE_FAILURE
    return TransientPortError("docker daemon unavailable", failure_category=category)


class DockerExecutionBackend(ExecutionBackend):
    """一次性容器执行后端;线程不安全(同步语义,M5 D2)。"""

    def __init__(
        self,
        *,
        image: str = DEFAULT_IMAGE,
        client: docker.DockerClient | None = None,
        telemetry: TelemetrySink | None = None,
    ) -> None:
        self._image = image
        self._owns_client = client is None
        self._client = client or docker.from_env()
        self._closed = False
        self._image_digest: str | None = None
        self._telemetry = telemetry

    @property
    def image_digest(self) -> str | None:
        """最近一次 execute 解析到的 image digest(供审计)。"""
        return self._image_digest

    def execute(
        self,
        spec: ExecutionSpec,
        timeout_seconds: int | None = None,
        *,
        cancelled: Callable[[], bool] | None = None,
    ) -> ExecutionRun:
        with operation(
            self._telemetry,
            scope=OperationScope.EXPERIMENT_RUN,
            name="experiment.execute",
            attributes={"resource_type": spec.backend_kind},
        ) as op:
            try:
                run = self._execute_impl(spec, timeout_seconds, cancelled)
            except PortError as exc:
                category = exc.failure_category or FailureCategory.EXECUTION_FAILURE
                op.set_outcome(OperationOutcome.FAILED, category.value)
                raise
            extras: dict[str, object] = {"resource_type": spec.backend_kind}
            if run.exit_code is not None:
                extras["exit_code"] = run.exit_code
            if self._image_digest:
                extras["image_digest"] = self._image_digest
            if run.compute_usage_summary.get("oom_killed"):
                extras["oom_killed"] = True
            op.set_outcome(OperationOutcome.OK, extra=extras)
            return run

    def _execute_impl(
        self,
        spec: ExecutionSpec,
        timeout_seconds: int | None,
        cancelled: Callable[[], bool] | None = None,
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
            timed_out, was_cancelled = self._wait(container_id, timeout_seconds, cancelled)
            if timed_out or was_cancelled:
                self._api.kill(container_id)
            state = self._api.inspect_container(container_id)
            exit_code = int((state.get("State") or {}).get("ExitCode") or 0)
            oom_killed = bool((state.get("State") or {}).get("OOMKilled"))
            stdout, stderr = self._collect_logs(container_id)
            self._write_workspace_logs(workspace, stdout, stderr)
            status = _final_status(timed_out, exit_code, was_cancelled)
            gpu_facts = _parse_gpu_facts(workspace) if is_gpu_profile(spec.resource_profile) else {}
            return _build_run(
                spec,
                started,
                started_mono,
                status=status,
                exit_code=exit_code,
                oom_killed=oom_killed,
                stdout=stdout,
                stderr=stderr,
                image_digest=self._image_digest,
                extra_summary=gpu_facts or None,
                failure_category=(
                    _gpu_failure_category(spec, gpu_facts)
                    if status is ExecutionStatus.FAILED
                    else None
                ),
            )
        except (APIError, DockerException) as exc:
            raise _map_docker_error(exc, gpu_profile=is_gpu_profile(spec.resource_profile)) from exc
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
        # M17 WP3b: DeviceRequests is the ONLY GPU delta (WP0 T2/T4 evidence).
        # Everything else — network none, CapDrop ALL, readonly rootfs,
        # no-new-privileges, tmpfs, limits — stays identical to CPU profiles
        # (asserted by the WP7b security suite).
        if is_gpu_profile(spec.resource_profile):
            host_config["DeviceRequests"] = [
                {"Driver": "nvidia", "Count": 1, "Capabilities": [["gpu", "compute", "utility"]]}
            ]
        environment = dict(spec.environment)
        if is_gpu_profile(spec.resource_profile):
            environment.update(_gpu_assert_environment(spec))
        container = self._api.create_container(
            image=self._image,
            command=["/bin/sh", "-c", spec.command],
            host_config=host_config,
            environment=environment,
            working_dir=spec.workdir,
            name=f"{CONTAINER_NAME_PREFIX}-{uuid.uuid4().hex[:12]}",
            detach=True,
        )
        return str(container.get("Id") or "")

    def _wait(
        self,
        container_id: str,
        timeout_seconds: int | None,
        cancelled: Callable[[], bool] | None = None,
    ) -> tuple[bool, bool]:
        """轮询容器 Running 状态直到退出；返回 (timed_out, cancelled)。

        不用 docker-py `wait(timeout=)`：其超时异常在 Windows npipe 与 Linux
        unix socket 上类型不一致（ConnectionError vs ReadTimeout），轮询
        inspect 跨平台确定。`cancelled` 探针每轮调用一次（协作式取消，M16）。
        """
        deadline = time.monotonic() + timeout_seconds if timeout_seconds is not None else None
        while True:
            state = self._api.inspect_container(container_id)
            if not bool((state.get("State") or {}).get("Running")):
                return False, False
            if cancelled is not None and cancelled():
                return False, True
            if deadline is None:
                time.sleep(_WAIT_STEP_SECONDS)
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return True, False
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
