"""Worker 域：生命周期状态机 + 注册值对象（M16 / ADR-0027；M17 GPU 观测）。

状态集合与迁移表来自 M16 计划 §3（Distributed Execution Plane）。
Worker 是 untrusted 执行方：本模块只表达 Control Plane 侧观察到的
worker 生命周期事实，不表达 worker 本地资源。

`WorkerRegistration` 是**有界字段**（基本身份 + 能力声明 + 可选 GPU 观测），
不是硬件清单。M17 增补 `WorkerGpuObservation`：一次真实探测产出的
**有界观测事实**（单卡、观测性质），不含任何 provider SDK 类型；
`nvidia-smi` 原文/完整硬件清单不进 canonical state。所有边界 fail closed：
超限即拒绝构造（注册入口在 gateway 层同样拒绝）。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from packages.domain.core import Timestamp
from packages.domain.state_base import InvalidTransitionError

# 有界字段上限（M16 计划 §3：注册值对象必须有界，防恶意/畸形输入）
MAX_WORKER_ID_LENGTH = 128
MAX_VERSION_LENGTH = 64
MAX_PLATFORM_LENGTH = 64
MAX_CAPABILITIES = 32
MAX_CAPABILITY_LENGTH = 64
MAX_BACKEND_KINDS = 8
MAX_CONCURRENCY = 64
PARTITION_COUNT = 16

# M17 GPU 观测有界字段（观测事实，非硬件清单）
GPU_CAPABILITY = "gpu"  # 调度键唯一 token（ADR-0029：单 token，无数值匹配）
MAX_GPU_DEVICE_NAME_LENGTH = 128
MAX_GPU_VERSION_LENGTH = 64
MAX_GPU_FRAMEWORK_LENGTH = 64
MAX_PROBE_DIGEST_LENGTH = 128
MAX_GPU_DEVICE_COUNT = 64
# 健全性封顶（256 TiB）：只防畸形输入，不是任何规格宣称
MAX_GPU_VRAM_BYTES = 2**48
_GPU_OBSERVATION_FIELDS = (
    "device_name",
    "device_count",
    "driver_version",
    "cuda_runtime_version",
    "total_vram_bytes",
    "framework",
)


class WorkerState:
    """Worker 生命周期状态机。

    `register()` 是生命周期创建（新 generation，state=REGISTERING），
    不走迁移表；迁移表描述单个注册世代内的状态演化。
    OFFLINE 为干净下线终态；LOST 可经重新注册进入新世代。
    """

    class State:
        REGISTERING = "REGISTERING"
        READY = "READY"
        BUSY = "BUSY"
        DRAINING = "DRAINING"
        OFFLINE = "OFFLINE"
        LOST = "LOST"

    class Transition:
        HANDSHAKE_OK = "HANDSHAKE_OK"
        HANDSHAKE_REJECTED = "HANDSHAKE_REJECTED"
        CLAIM = "CLAIM"
        JOB_SETTLED = "JOB_SETTLED"
        DRAIN_REQUESTED = "DRAIN_REQUESTED"
        OWNED_WORK_SETTLED = "OWNED_WORK_SETTLED"
        HEARTBEAT_EXPIRED = "HEARTBEAT_EXPIRED"
        RE_REGISTER = "RE_REGISTER"

    # fmt: off
    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.REGISTERING, Transition.HANDSHAKE_OK): State.READY,
        # 握手拒绝：该世代直接下线（不进入调度），由重新注册开新世代
        (State.REGISTERING, Transition.HANDSHAKE_REJECTED): State.OFFLINE,
        (State.READY, Transition.CLAIM): State.BUSY,
        (State.BUSY, Transition.JOB_SETTLED): State.READY,
        (State.READY, Transition.DRAIN_REQUESTED): State.DRAINING,
        (State.BUSY, Transition.DRAIN_REQUESTED): State.DRAINING,
        (State.DRAINING, Transition.OWNED_WORK_SETTLED): State.OFFLINE,
        (State.READY, Transition.HEARTBEAT_EXPIRED): State.LOST,
        (State.BUSY, Transition.HEARTBEAT_EXPIRED): State.LOST,
        (State.DRAINING, Transition.HEARTBEAT_EXPIRED): State.LOST,
        (State.LOST, Transition.RE_REGISTER): State.REGISTERING,
    }
    # fmt: on

    @staticmethod
    def initial() -> str:
        return WorkerState.State.REGISTERING

    @staticmethod
    def terminal() -> frozenset[str]:
        return frozenset({WorkerState.State.OFFLINE})

    @staticmethod
    def schedulable() -> frozenset[str]:
        """可被 claim 的状态集合（DRAINING/LOST/OFFLINE/REGISTERING 不可）。"""
        return frozenset({WorkerState.State.READY})

    @staticmethod
    def transition(current: str, event: str) -> str:
        try:
            return WorkerState._TRANSITIONS[(current, event)]
        except KeyError:
            raise InvalidTransitionError(current, event) from None


def compute_partition(run_id: str, partition_count: int = PARTITION_COUNT) -> int:
    """Stable partition bucket for run affinity (M16 §7).

    `sha256(run_id)` first 4 bytes mod partition_count. This is a routing hint
    only — never an ownership authority (that stays the `leases` row).
    """
    if not run_id:
        raise ValueError("run_id must not be empty")
    if partition_count < 1:
        raise ValueError("partition_count must be >= 1")
    digest = hashlib.sha256(run_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % partition_count


def _check_bounded_text(value: str, *, field: str, max_length: int) -> None:
    if not value or len(value) > max_length:
        raise ValueError(f"{field} must be non-empty and <= {max_length} chars")


def gpu_probe_digest(  # noqa: PLR0913 - 观测字段是封闭集合，参数对象反而失真
    *,
    device_name: str,
    device_count: int,
    driver_version: str,
    cuda_runtime_version: str,
    total_vram_bytes: int,
    framework: str,
) -> str:
    """观测内容 digest（sha256 前 16 hex）：变化检测键，非身份/非秘密。

    worker 重探时比较新旧 digest：变化 → re-register（freshness 第 3 层）。
    """
    payload = json.dumps(
        {
            "cuda_runtime_version": cuda_runtime_version,
            "device_count": device_count,
            "device_name": device_name,
            "driver_version": driver_version,
            "framework": framework,
            "total_vram_bytes": total_vram_bytes,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class WorkerGpuObservation:
    """一次真实 GPU 探测的有界观测事实（M17；单卡个人规模）。

    纯数据：不含 provider SDK 类型、不执行任何 I/O。`probed_at` 是探测方
    （worker 侧）时钟的观测记录，仅作信息展示——**freshness 判定一律用
    服务端记录的 `gpu_observed_at`**（M16 时钟权威规则不破）。
    """

    device_name: str
    device_count: int
    driver_version: str
    cuda_runtime_version: str
    total_vram_bytes: int
    framework: str
    probed_at: Timestamp
    probe_digest: str

    def __post_init__(self) -> None:
        _check_bounded_text(
            self.device_name, field="device_name", max_length=MAX_GPU_DEVICE_NAME_LENGTH
        )
        if not 1 <= self.device_count <= MAX_GPU_DEVICE_COUNT:
            raise ValueError(f"device_count must be in [1, {MAX_GPU_DEVICE_COUNT}]")
        _check_bounded_text(
            self.driver_version, field="driver_version", max_length=MAX_GPU_VERSION_LENGTH
        )
        _check_bounded_text(
            self.cuda_runtime_version,
            field="cuda_runtime_version",
            max_length=MAX_GPU_VERSION_LENGTH,
        )
        if not 1 <= self.total_vram_bytes <= MAX_GPU_VRAM_BYTES:
            raise ValueError(f"total_vram_bytes must be in [1, {MAX_GPU_VRAM_BYTES}]")
        _check_bounded_text(
            self.framework, field="framework", max_length=MAX_GPU_FRAMEWORK_LENGTH
        )
        _check_bounded_text(
            self.probe_digest, field="probe_digest", max_length=MAX_PROBE_DIGEST_LENGTH
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "device_name": self.device_name,
            "device_count": self.device_count,
            "driver_version": self.driver_version,
            "cuda_runtime_version": self.cuda_runtime_version,
            "total_vram_bytes": self.total_vram_bytes,
            "framework": self.framework,
            "probed_at": self.probed_at.value.isoformat(),
            "probe_digest": self.probe_digest,
        }

    @classmethod
    def from_json_dict(cls, data: Any) -> WorkerGpuObservation:
        """fail-closed 解码：缺字段/类型错/越界一律 ValueError。"""
        if not isinstance(data, dict):
            raise ValueError("gpu observation must be a JSON object")
        try:
            return cls(
                device_name=str(data["device_name"]),
                device_count=int(data["device_count"]),
                driver_version=str(data["driver_version"]),
                cuda_runtime_version=str(data["cuda_runtime_version"]),
                total_vram_bytes=int(data["total_vram_bytes"]),
                framework=str(data["framework"]),
                probed_at=Timestamp(datetime.fromisoformat(str(data["probed_at"]))),
                probe_digest=str(data["probe_digest"]),
            )
        except KeyError as exc:
            raise ValueError(f"gpu observation missing field: {exc}") from exc
        except (TypeError, ValueError) as exc:
            if "gpu observation" in str(exc):
                raise
            raise ValueError(f"invalid gpu observation: {exc}") from exc


def _check_bounded_set(
    values: frozenset[str], *, field: str, max_items: int, max_item_length: int
) -> None:
    if len(values) > max_items:
        raise ValueError(f"{field} must contain <= {max_items} items")
    for item in values:
        _check_bounded_text(item, field=field, max_length=max_item_length)


@dataclass(frozen=True, slots=True)
class WorkerRegistration:
    """Control Plane 视角的 worker 注册事实（有界字段，非硬件清单）。"""

    worker_id: str
    protocol_version: str
    runtime_version: str
    capabilities: frozenset[str]
    backend_kinds: frozenset[str]
    platform: str  # 仅 "os/arch"
    partition_slots: frozenset[int]
    max_concurrency: int
    registration_generation: int = 0  # 0 = 尚未由 registry 分配
    state: str = WorkerState.State.REGISTERING
    last_heartbeat: Timestamp | None = None
    drain_requested: bool = False
    # M17：可选 GPU 观测（注册时整体替换）；gpu_observed_at 是服务端收到
    # 该观测的时钟（TTL freshness 判定唯一依据），worker 自报 probed_at 不参与。
    gpu_observation: WorkerGpuObservation | None = None
    gpu_observed_at: Timestamp | None = None

    def __post_init__(self) -> None:
        _check_bounded_text(self.worker_id, field="worker_id", max_length=MAX_WORKER_ID_LENGTH)
        _check_bounded_text(
            self.protocol_version, field="protocol_version", max_length=MAX_VERSION_LENGTH
        )
        _check_bounded_text(
            self.runtime_version, field="runtime_version", max_length=MAX_VERSION_LENGTH
        )
        _check_bounded_text(self.platform, field="platform", max_length=MAX_PLATFORM_LENGTH)
        _check_bounded_set(
            self.capabilities,
            field="capabilities",
            max_items=MAX_CAPABILITIES,
            max_item_length=MAX_CAPABILITY_LENGTH,
        )
        _check_bounded_set(
            self.backend_kinds,
            field="backend_kinds",
            max_items=MAX_BACKEND_KINDS,
            max_item_length=MAX_CAPABILITY_LENGTH,
        )
        if self.gpu_observation is None and self.gpu_observed_at is not None:
            raise ValueError("gpu_observed_at requires gpu_observation")
        if len(self.partition_slots) > PARTITION_COUNT:
            raise ValueError(f"partition_slots must contain <= {PARTITION_COUNT} items")
        for slot in self.partition_slots:
            if not 0 <= slot < PARTITION_COUNT:
                raise ValueError(f"partition slot must be in [0, {PARTITION_COUNT}): {slot!r}")
        if not 1 <= self.max_concurrency <= MAX_CONCURRENCY:
            raise ValueError(f"max_concurrency must be in [1, {MAX_CONCURRENCY}]")
        if self.registration_generation < 0:
            raise ValueError("registration_generation must be >= 0")
        valid_states = frozenset(
            getattr(WorkerState.State, name)
            for name in dir(WorkerState.State)
            if not name.startswith("_")
        )
        if self.state not in valid_states:
            raise ValueError(f"unknown worker state: {self.state!r}")

    def with_state(self, state: str, *, drain_requested: bool | None = None) -> WorkerRegistration:
        """返回替换 state（及可选 drain 标记）的副本；state 合法性由构造校验。"""
        return WorkerRegistration(
            worker_id=self.worker_id,
            protocol_version=self.protocol_version,
            runtime_version=self.runtime_version,
            capabilities=self.capabilities,
            backend_kinds=self.backend_kinds,
            platform=self.platform,
            partition_slots=self.partition_slots,
            max_concurrency=self.max_concurrency,
            registration_generation=self.registration_generation,
            state=state,
            last_heartbeat=self.last_heartbeat,
            drain_requested=self.drain_requested if drain_requested is None else drain_requested,
            gpu_observation=self.gpu_observation,
            gpu_observed_at=self.gpu_observed_at,
        )
