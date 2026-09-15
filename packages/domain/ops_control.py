"""Ops 控制面域（G7 / GOAL-20260915-002 EC-04）：告警规则与事故登记。

与 `ops_view.py`（只读派生视图）的分工：

- `AlertRule` 是**被消费的**配置：`GET /projects/{id}/ops/alerts` 用启用中的规则给
  派生告警打 `muted` 标记（不隐藏——静音不等于消失，隐藏只会让问题更难发现）；
- `Incident` 是**被消费的**登记：事故关联到来源 run，使告警带上 `incident_id`，
  事故列表区分"已登记"与"失败 Run 候选"。

状态机沿用仓内模式（terminal 无出边，非法迁移抛 `InvalidTransitionError`）：
OPEN → ASSIGNED → CLOSED；OPEN → CLOSED（直接关闭）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.domain.core import Timestamp
from packages.domain.ops_view import AlertItem, AlertKind, AlertSeverity
from packages.domain.state_base import InvalidTransitionError

MAX_RULE_NAME_LENGTH = 128
MAX_INCIDENT_TITLE_LENGTH = 256
MAX_RESOLUTION_LENGTH = 1024
MAX_ASSIGNEE_LENGTH = 128

# 严重度排序：数值越大越严重（规则用 max_severity 表达"只静音到这个级别"）。
_SEVERITY_RANK = {
    AlertSeverity.INFO: 0,
    AlertSeverity.WARNING: 1,
    AlertSeverity.CRITICAL: 2,
}


class IncidentStatus:
    """事故生命周期状态与迁移表。"""

    class State:
        OPEN = "OPEN"
        ASSIGNED = "ASSIGNED"
        CLOSED = "CLOSED"

    class Transition:
        ASSIGN = "ASSIGN"
        CLOSE = "CLOSE"

    _TRANSITIONS: dict[tuple[str, str], str] = {
        (State.OPEN, Transition.ASSIGN): State.ASSIGNED,
        (State.OPEN, Transition.CLOSE): State.CLOSED,
        (State.ASSIGNED, Transition.ASSIGN): State.ASSIGNED,
        (State.ASSIGNED, Transition.CLOSE): State.CLOSED,
    }

    @staticmethod
    def initial() -> str:
        return IncidentStatus.State.OPEN

    @staticmethod
    def terminal() -> frozenset[str]:
        return frozenset({IncidentStatus.State.CLOSED})

    @staticmethod
    def transition(current: str, event: str) -> str:
        try:
            return IncidentStatus._TRANSITIONS[(current, event)]
        except KeyError:
            raise InvalidTransitionError(current, event) from None


@dataclass(frozen=True, slots=True)
class AlertRule:
    """告警静音规则（项目内；`kind=None` 表示适用全部来源）。"""

    id: str
    project_id: str
    name: str
    kind: AlertKind | None = None
    max_severity: AlertSeverity | None = None
    enabled: bool = True
    created_at: Timestamp | None = None
    updated_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("alert rule id must not be empty")
        if not self.project_id:
            raise ValueError("alert rule project_id must not be empty")
        if not self.name or len(self.name) > MAX_RULE_NAME_LENGTH:
            raise ValueError(f"alert rule name must be 1..{MAX_RULE_NAME_LENGTH} chars")
        if self.kind is not None and not isinstance(self.kind, AlertKind):
            raise ValueError(f"unknown alert kind: {self.kind!r}")
        if self.max_severity is not None and not isinstance(self.max_severity, AlertSeverity):
            raise ValueError(f"unknown alert severity: {self.max_severity!r}")

    def matches(self, alert: AlertItem) -> bool:
        """该规则是否静音这条告警（纯函数；只影响标记，不影响是否返回）。"""
        if not self.enabled:
            return False
        if self.kind is not None and alert.kind is not self.kind:
            return False
        if self.max_severity is None:
            return True
        return _SEVERITY_RANK[alert.severity] <= _SEVERITY_RANK[self.max_severity]


@dataclass(frozen=True, slots=True)
class Incident:
    """已登记事故（declare → assign → close）；来源 run 可为空（人工登记的事故）。"""

    id: str
    project_id: str
    title: str
    severity: AlertSeverity = AlertSeverity.WARNING
    status: str = field(default_factory=IncidentStatus.initial)
    run_id: str | None = None
    assignee: str | None = None
    resolution: str | None = None
    opened_at: Timestamp | None = None
    updated_at: Timestamp | None = None
    closed_at: Timestamp | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("incident id must not be empty")
        if not self.project_id:
            raise ValueError("incident project_id must not be empty")
        if not self.title or len(self.title) > MAX_INCIDENT_TITLE_LENGTH:
            raise ValueError(f"incident title must be 1..{MAX_INCIDENT_TITLE_LENGTH} chars")
        if not isinstance(self.severity, AlertSeverity):
            raise ValueError(f"unknown alert severity: {self.severity!r}")
        if self.status not in {
            IncidentStatus.State.OPEN,
            IncidentStatus.State.ASSIGNED,
            IncidentStatus.State.CLOSED,
        }:
            raise ValueError(f"unknown incident status: {self.status!r}")
        if self.assignee is not None and (
            not self.assignee or len(self.assignee) > MAX_ASSIGNEE_LENGTH
        ):
            raise ValueError(f"assignee must be 1..{MAX_ASSIGNEE_LENGTH} chars")
        if self.resolution is not None and len(self.resolution) > MAX_RESOLUTION_LENGTH:
            raise ValueError(f"resolution must be <= {MAX_RESOLUTION_LENGTH} chars")

    @property
    def open(self) -> bool:
        # 用 `!=` 而非 `is not`：status 从持久面解出时是普通 str，身份比较不可靠。
        return self.status != IncidentStatus.State.CLOSED

    def assigned_to(self, assignee: str, *, now: Timestamp) -> Incident:
        """指派（可重复指派）；已关闭的事故不可再指派。"""
        status = IncidentStatus.transition(self.status, IncidentStatus.Transition.ASSIGN)
        return _replace(self, status=status, assignee=assignee, updated_at=now)

    def close(self, resolution: str, *, now: Timestamp) -> Incident:
        """关闭并留下处理结论（resolution 必填）。"""
        status = IncidentStatus.transition(self.status, IncidentStatus.Transition.CLOSE)
        return _replace(
            self,
            status=status,
            resolution=resolution,
            updated_at=now,
            closed_at=now,
        )


def _replace(incident: Incident, **changes: Any) -> Incident:
    values: dict[str, Any] = {
        "id": incident.id,
        "project_id": incident.project_id,
        "title": incident.title,
        "severity": incident.severity,
        "status": incident.status,
        "run_id": incident.run_id,
        "assignee": incident.assignee,
        "resolution": incident.resolution,
        "opened_at": incident.opened_at,
        "updated_at": incident.updated_at,
        "closed_at": incident.closed_at,
    }
    values.update(changes)
    return Incident(**values)
