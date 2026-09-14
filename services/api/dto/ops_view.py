"""Ops 只读运维投影 DTO（PLAN-20260914-045 WP-B）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AlertItemDto(BaseModel):
    kind: str
    severity: str
    subject: str
    detail: str


class AlertsViewDto(BaseModel):
    alerts: list[AlertItemDto] = Field(default_factory=list)
    rules_available: bool = False
    rules_reason: str | None = None


class IncidentItemDto(BaseModel):
    run_id: str
    protocol_id: str
    state: str
    updated_at: str


class IncidentsViewDto(BaseModel):
    incidents: list[IncidentItemDto] = Field(default_factory=list)
    workflow_available: bool = False
    workflow_reason: str | None = None


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
