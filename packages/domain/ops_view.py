"""Ops 视图域：只读运维投影的视图类型（PLAN-20260914-045 / EC-03 第二批）。

本模块只定义**派生视图类型**，不含任何持久化：alerts/incidents/schedules/
data-health 四页的数据全部由既有真实状态投影而来（RunStore、worker registry、
endpoint health、artifact verify、进程内 scheduler 配置）。

为何不建持久域：这些页面若引入"用户注册的定时任务/告警规则"等持久实体，
在进程内 scheduler 并不读取它们之前，就是一个**不被消费的假真相**——本仓明令
禁止伪装实现。故此处以只读投影如实呈现"系统当前真实可观测到的状态"，
能力缺口在页面与文档逐条标注。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

MAX_SUBJECT_LENGTH = 256
MAX_DETAIL_LENGTH = 1024


class AlertKind(StrEnum):
    RUN_FAILED = "RUN_FAILED"
    ENDPOINT_DEGRADED = "ENDPOINT_DEGRADED"
    WORKER_OFFLINE = "WORKER_OFFLINE"


class AlertSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True, slots=True)
class AlertItem:
    """派生告警项（无持久化；由真实状态投影）。"""

    kind: AlertKind
    severity: AlertSeverity
    subject: str
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AlertKind):
            raise ValueError(f"unknown alert kind: {self.kind!r}")
        if not isinstance(self.severity, AlertSeverity):
            raise ValueError(f"unknown alert severity: {self.severity!r}")
        if not self.subject or len(self.subject) > MAX_SUBJECT_LENGTH:
            raise ValueError(f"subject must be non-empty and <= {MAX_SUBJECT_LENGTH} chars")
        if len(self.detail) > MAX_DETAIL_LENGTH:
            raise ValueError(f"detail must be <= {MAX_DETAIL_LENGTH} chars")


@dataclass(frozen=True, slots=True)
class IncidentItem:
    """事故候选（FAILED run）；无处置工作流（declare/assign/close）。"""

    run_id: str
    protocol_id: str
    state: str
    updated_at: str

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must not be empty")
        if not self.state:
            raise ValueError("state must not be empty")


@dataclass(frozen=True, slots=True)
class ScheduleEntry:
    """进程内 scheduler 的配置事实（只读；非用户可见调度）。"""

    name: str
    interval_seconds: float
    purpose: str
    enabled: bool

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("schedule name must not be empty")
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        if not self.purpose:
            raise ValueError("purpose must not be empty")


@dataclass(frozen=True, slots=True)
class DataHealthMetric:
    """数据健康聚合项（真实计数/抽样校验结果）。"""

    metric: str
    value: str
    status: str

    def __post_init__(self) -> None:
        if not self.metric:
            raise ValueError("metric must not be empty")
        if not self.status:
            raise ValueError("status must not be empty")
