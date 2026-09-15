"""Ops 写面与读面的共享装配（PLAN-20260915-059 WP-C）。

放在路由之外是为了让 `ops_view.py`（读面）与 `ops_control.py`（写面）共用同一套
"规则如何被消费""事故如何被呈现"的口径，避免两处各写一遍而漂移。
"""

from __future__ import annotations

from typing import Any

from packages.domain.ops_control import AlertRule, Incident
from packages.domain.ops_view import AlertItem
from services.api.composition import ApiDeps
from services.api.dto.ops_view import (
    AlertItemDto,
    AlertRuleDto,
    IncidentCandidateDto,
    IncidentItemDto,
)

# 读面在写面不可用时的原因（store 缺失即规则/处置都读不到，如实标注）。
RULES_UNAVAILABLE_REASON = "OpsStore 未配置；规则 CRUD 与事故处置都不可用"
WORKFLOW_UNAVAILABLE_REASON = "OpsStore 未配置；事故 declare/assign/close 不可用"


def _iso(value: Any) -> str | None:
    return value.value.isoformat() if value is not None else None


def rule_dto(rule: AlertRule) -> AlertRuleDto:
    return AlertRuleDto(
        id=rule.id,
        project_id=rule.project_id,
        name=rule.name,
        kind=rule.kind.value if rule.kind is not None else None,
        max_severity=rule.max_severity.value if rule.max_severity is not None else None,
        enabled=rule.enabled,
        created_at=_iso(rule.created_at),
        updated_at=_iso(rule.updated_at),
    )


def incident_dto(incident: Incident) -> IncidentItemDto:
    return IncidentItemDto(
        id=incident.id,
        title=incident.title,
        severity=incident.severity.value,
        status=incident.status,
        run_id=incident.run_id,
        assignee=incident.assignee,
        resolution=incident.resolution,
        opened_at=_iso(incident.opened_at),
        updated_at=_iso(incident.updated_at),
        closed_at=_iso(incident.closed_at),
    )


def incident_item_row(run: Any) -> IncidentCandidateDto:
    """派生候选行（失败 Run）；候选不是事故，字段名也不假装成事故。"""
    return IncidentCandidateDto(
        run_id=run.id.value,
        protocol_id=run.protocol_id,
        state=run.state,
        updated_at=run.updated_at.value.isoformat(),
    )


def alert_dto(
    alert: AlertItem, *, muted_by_id: str | None, incident_id: str | None
) -> AlertItemDto:
    return AlertItemDto(
        kind=alert.kind.value,
        severity=alert.severity.value,
        subject=alert.subject,
        detail=alert.detail,
        muted=muted_by_id is not None,
        muted_by=muted_by_id,
        incident_id=incident_id,
    )


def rules_of(deps: ApiDeps, project_id: str) -> list[AlertRule]:
    """项目内规则（store 未配置 ⇒ 空表 + 读面用 rules_available=False 标注）。"""
    if deps.ops_store is None:
        return []
    return deps.ops_store.list_rules(project_id)


def incidents_of(deps: ApiDeps, project_id: str) -> list[Incident]:
    if deps.ops_store is None:
        return []
    return deps.ops_store.list_incidents(project_id)


def open_incident_by_run(incidents: list[Incident]) -> dict[str, str]:
    """run_id → 未关闭事故 id（同一 run 多条时取最早登记的那条）。"""
    mapping: dict[str, str] = {}
    for incident in incidents:
        if incident.run_id is None or not incident.open:
            continue
        mapping.setdefault(incident.run_id, incident.id)
    return mapping


def muted_by(rules: list[AlertRule], alert: AlertItem) -> str | None:
    """第一条匹配的启用规则 id（规则只做静音标记，不隐藏告警）。"""
    for rule in rules:
        if rule.matches(alert):
            return rule.id
    return None
