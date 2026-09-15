"""Ops 运维投影 DTO（PLAN-20260914-045 WP-B；PLAN-20260915-059 起含写面）。

读面仍是派生投影；写面（告警规则、事故处置）由 `OpsStore` 持久化。
`AlertsViewDto` 的规则字段与 `IncidentsViewDto` 的 `candidates`/`incidents` 分工
见各字段注释——"失败 Run 候选"与"已登记事故"是两个不同的东西。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AlertItemDto(BaseModel):
    kind: str
    severity: str
    subject: str
    detail: str
    # 规则只做**静音标记**（muted/muted_by），不隐藏告警：看不见的问题更难修。
    muted: bool = False
    muted_by: str | None = None
    # 该告警的来源 run 已有未关闭事故 ⇒ 带上事故 id（写面被读面消费的点）。
    incident_id: str | None = None


class AlertsViewDto(BaseModel):
    alerts: list[AlertItemDto] = Field(default_factory=list)
    rules_available: bool = False
    rules_reason: str | None = None
    rules_applied: int = 0
    muted_count: int = 0


class AlertRuleDto(BaseModel):
    id: str
    project_id: str
    name: str
    kind: str | None = None
    max_severity: str | None = None
    enabled: bool
    created_at: str | None = None
    updated_at: str | None = None


class AlertRulesViewDto(BaseModel):
    rules: list[AlertRuleDto] = Field(default_factory=list)
    rules_available: bool = False
    rules_reason: str | None = None


class AlertRuleCreateDto(BaseModel):
    name: str
    kind: str | None = None
    max_severity: str | None = None
    enabled: bool = True


class AlertRuleUpdateDto(BaseModel):
    name: str | None = None
    kind: str | None = None
    max_severity: str | None = None
    enabled: bool | None = None
    clear_kind: bool = False
    clear_max_severity: bool = False


class IncidentItemDto(BaseModel):
    """**已登记**事故（declare/assign/close 的真实状态）。"""

    id: str
    title: str
    severity: str
    status: str
    run_id: str | None = None
    assignee: str | None = None
    resolution: str | None = None
    opened_at: str | None = None
    updated_at: str | None = None
    closed_at: str | None = None


class IncidentCandidateDto(BaseModel):
    """**派生候选**（FAILED run）；失败 Run 不自动登记为事故。"""

    run_id: str
    protocol_id: str
    state: str
    updated_at: str


class IncidentsViewDto(BaseModel):
    incidents: list[IncidentItemDto] = Field(default_factory=list)
    candidates: list[IncidentCandidateDto] = Field(default_factory=list)
    workflow_available: bool = False
    workflow_reason: str | None = None


class IncidentDeclareDto(BaseModel):
    title: str
    severity: str = "WARNING"
    run_id: str | None = None


class IncidentAssignDto(BaseModel):
    assignee: str


class IncidentCloseDto(BaseModel):
    resolution: str


class ScheduleEntryDto(BaseModel):
    name: str
    interval_seconds: float
    purpose: str
    enabled: bool


class SchedulesViewDto(BaseModel):
    schedules: list[ScheduleEntryDto] = Field(default_factory=list)
    management_available: bool = False
    management_reason: str | None = None


class DataHealthMetricDto(BaseModel):
    metric: str
    value: str
    status: str


class DataHealthViewDto(BaseModel):
    metrics: list[DataHealthMetricDto] = Field(default_factory=list)
    aggregate_available: bool = False
    aggregate_reason: str | None = None
