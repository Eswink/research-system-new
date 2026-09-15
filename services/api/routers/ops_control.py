"""Ops 写面路由（G7 / PLAN-20260915-059 WP-C）：告警规则 CRUD + 事故处置。

两写面都是**被消费**的：规则被 `GET /projects/{id}/ops/alerts` 用来打静音标记
（不隐藏），事故被同一读面用来给来源 run 的告警带上 `incident_id`、并让
`GET /projects/{id}/ops/incidents` 区分"已登记"与"失败 Run 候选"。

诚实边界：store 未配置 → 503（不伪造成功）；未知 id → 404；未知枚举值 → 422；
关闭的事故不可再指派/关闭（域状态机抛 `InvalidTransitionError` → 409）。
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Request, Response

from packages.application.ports.ops_store import OpsStore
from packages.domain.core import ID, Timestamp
from packages.domain.ops_control import AlertRule, Incident
from packages.domain.ops_view import AlertKind, AlertSeverity
from packages.domain.state_base import InvalidTransitionError
from services.api.catalog_merge import require_registered_project
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.ops_view import (
    AlertRuleCreateDto,
    AlertRuleDto,
    AlertRulesViewDto,
    AlertRuleUpdateDto,
    IncidentAssignDto,
    IncidentCloseDto,
    IncidentDeclareDto,
    IncidentItemDto,
)
from services.api.errors import ApiError
from services.api.ops_control_support import (
    RULES_UNAVAILABLE_REASON,
    incident_dto,
    rule_dto,
    rules_of,
)

router = APIRouter(tags=["ops-control"])


def _store(deps: ApiDeps) -> OpsStore:
    if deps.ops_store is None:
        raise ApiError(503, "Ops Store Unavailable", RULES_UNAVAILABLE_REASON)
    return deps.ops_store


def _kind(raw: str | None) -> AlertKind | None:
    if raw is None:
        return None
    try:
        return AlertKind(raw)
    except ValueError as exc:
        raise ApiError(422, "Invalid Alert Kind", f"unknown alert kind: {raw!r}") from exc


def _severity(raw: str | None) -> AlertSeverity | None:
    if raw is None:
        return None
    try:
        return AlertSeverity(raw)
    except ValueError as exc:
        raise ApiError(422, "Invalid Severity", f"unknown severity: {raw!r}") from exc


def _require_severity(raw: str) -> AlertSeverity:
    severity = _severity(raw)
    if severity is None:
        raise ApiError(422, "Invalid Severity", "severity must not be empty")
    return severity


@router.get("/projects/{project_id}/ops/alert-rules", response_model=AlertRulesViewDto)
async def list_alert_rules(project_id: str, request: Request) -> AlertRulesViewDto:
    """项目内的告警静音规则（store 未配置 → 200 + rules_available=false + 原因）。"""
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    available = deps.ops_store is not None
    return AlertRulesViewDto(
        rules=[rule_dto(rule) for rule in rules_of(deps, project_id)],
        rules_available=available,
        rules_reason=None if available else RULES_UNAVAILABLE_REASON,
    )


@router.post("/projects/{project_id}/ops/alert-rules", response_model=AlertRuleDto, status_code=201)
async def create_alert_rule(
    project_id: str, payload: AlertRuleCreateDto, request: Request
) -> AlertRuleDto:
    """新建静音规则（`kind=None` 表示适用全部来源；`max_severity` 限静音上限）。"""
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    store = _store(deps)
    now = Timestamp.now()
    try:
        rule = AlertRule(
            id=str(ID.generate().value),
            project_id=project_id,
            name=payload.name,
            kind=_kind(payload.kind),
            max_severity=_severity(payload.max_severity),
            enabled=payload.enabled,
            created_at=now,
            updated_at=now,
        )
    except ValueError as exc:
        raise ApiError(422, "Invalid Alert Rule", str(exc)) from exc
    store.save_rule(rule)
    return rule_dto(rule)


@router.patch("/ops/alert-rules/{rule_id}", response_model=AlertRuleDto)
async def update_alert_rule(
    rule_id: str, payload: AlertRuleUpdateDto, request: Request
) -> AlertRuleDto:
    """改名/启停/改适用范围；`clear_kind` / `clear_max_severity` 显式清空范围。"""
    deps: ApiDeps = get_deps(request)
    store = _store(deps)
    try:
        current = store.get_rule(rule_id)
    except KeyError as exc:
        raise ApiError(404, "Alert Rule Not Found", str(exc)) from exc
    if (
        payload.name is None
        and payload.kind is None
        and payload.max_severity is None
        and payload.enabled is None
        and not payload.clear_kind
        and not payload.clear_max_severity
    ):
        raise ApiError(422, "Empty Patch", "patch must change at least one field")
    try:
        updated = _patched(current, payload)
    except ValueError as exc:
        raise ApiError(422, "Invalid Alert Rule", str(exc)) from exc
    store.save_rule(updated)
    return rule_dto(updated)


def _patched(rule: AlertRule, payload: AlertRuleUpdateDto) -> AlertRule:
    kind = None if payload.clear_kind else _kind(payload.kind) or rule.kind
    max_severity = (
        None if payload.clear_max_severity else _severity(payload.max_severity) or rule.max_severity
    )
    return AlertRule(
        id=rule.id,
        project_id=rule.project_id,
        name=payload.name if payload.name is not None else rule.name,
        kind=kind,
        max_severity=max_severity,
        enabled=rule.enabled if payload.enabled is None else payload.enabled,
        created_at=rule.created_at,
        updated_at=Timestamp.now(),
    )


@router.delete("/ops/alert-rules/{rule_id}", status_code=204)
async def delete_alert_rule(rule_id: str, request: Request) -> Response:
    """删除规则（删除后该规则不再静音任何告警——读面即时反映）。"""
    deps: ApiDeps = get_deps(request)
    store = _store(deps)
    try:
        store.delete_rule(rule_id)
    except KeyError as exc:
        raise ApiError(404, "Alert Rule Not Found", str(exc)) from exc
    return Response(status_code=204)


@router.post(
    "/projects/{project_id}/ops/incidents", response_model=IncidentItemDto, status_code=201
)
async def declare_incident(
    project_id: str, payload: IncidentDeclareDto, request: Request
) -> IncidentItemDto:
    """登记事故（可关联来源 run；失败 Run 不会自动登记，必须显式声明）。"""
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    store = _store(deps)
    now = Timestamp.now()
    try:
        incident = Incident(
            id=str(ID.generate().value),
            project_id=project_id,
            title=payload.title,
            severity=_require_severity(payload.severity),
            run_id=payload.run_id,
            opened_at=now,
            updated_at=now,
        )
    except ValueError as exc:
        raise ApiError(422, "Invalid Incident", str(exc)) from exc
    store.save_incident(incident)
    return incident_dto(incident)


@router.post("/ops/incidents/{incident_id}/assign", response_model=IncidentItemDto)
async def assign_incident(
    incident_id: str, payload: IncidentAssignDto, request: Request
) -> IncidentItemDto:
    """指派处理人（可重复指派；已关闭事故 → 409）。"""
    return _transition(
        request,
        incident_id,
        lambda incident, now: incident.assigned_to(payload.assignee, now=now),
    )


@router.post("/ops/incidents/{incident_id}/close", response_model=IncidentItemDto)
async def close_incident(
    incident_id: str, payload: IncidentCloseDto, request: Request
) -> IncidentItemDto:
    """关闭事故并留下处理结论（resolution 必填；已关闭 → 409）。"""
    return _transition(
        request,
        incident_id,
        lambda incident, now: incident.close(payload.resolution, now=now),
    )


def _transition(
    request: Request,
    incident_id: str,
    apply: Callable[[Incident, Timestamp], Incident],
) -> IncidentItemDto:
    deps: ApiDeps = get_deps(request)
    store = _store(deps)
    try:
        current = store.get_incident(incident_id)
    except KeyError as exc:
        raise ApiError(404, "Incident Not Found", str(exc)) from exc
    try:
        updated = apply(current, Timestamp.now())
    except InvalidTransitionError as exc:
        raise ApiError(409, "Incident Closed", f"incident {incident_id} is already closed") from exc
    except ValueError as exc:
        raise ApiError(422, "Invalid Incident", str(exc)) from exc
    store.save_incident(updated)
    return incident_dto(updated)
