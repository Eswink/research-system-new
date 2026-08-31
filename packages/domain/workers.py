"""Worker 域：生命周期状态机 + 注册值对象（M16 / ADR-0027）。

状态集合与迁移表来自 M16 计划 §3（Distributed Execution Plane）。
Worker 是 untrusted 执行方：本模块只表达 Control Plane 侧观察到的
worker 生命周期事实，不表达 worker 本地资源。

`WorkerRegistration` 是**有界字段**（基本身份 + 能力声明），不是硬件清单；
GPU/内存/拓扑等资源平面属 M17，M16 不表达。所有边界 fail closed：
超限即拒绝构造（注册入口在 gateway 层同样拒绝）。
"""

from __future__ import annotations

from dataclasses import dataclass

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


def _check_bounded_text(value: str, *, field: str, max_length: int) -> None:
    if not value or len(value) > max_length:
        raise ValueError(f"{field} must be non-empty and <= {max_length} chars")


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
        )
