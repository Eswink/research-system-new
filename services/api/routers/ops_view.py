"""Ops 运维投影路由（PLAN-20260914-045 WP-B；PLAN-20260915-059 起写面接入）。

读面（本模块）仍是派生投影：alerts（失败 run ∪ 降级端点 ∪ 离线 worker）、
incidents（**已登记**事故 + 未被登记的失败 Run 候选）、data-health（端点健康计数 +
dataset 目录计数 + artifact 抽样校验）。写面在 `ops_control.py`——本模块消费它：
启用中的规则给告警打 `muted` 标记（不隐藏），未关闭的事故给其来源 run 的告警带上
`incident_id`。缺失依赖诚实在响应里标注，不伪装空成功。

`schedules` 已迁到 `ops_schedules.py`（GOAL-003 EC-03 起它不再是只读事实，而是
可写定义 + 运行事实）。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from packages.domain.ops_view import (
    AlertItem,
    AlertKind,
    AlertSeverity,
    DataHealthMetric,
)
from services.api.catalog_merge import merged_catalog_snapshot, require_registered_project
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.ops_view import (
    AlertsViewDto,
    DataHealthMetricDto,
    DataHealthViewDto,
    IncidentsViewDto,
)
from services.api.errors import ApiError
from services.api.ops_control_support import (
    RULES_UNAVAILABLE_REASON,
    WORKFLOW_UNAVAILABLE_REASON,
    alert_dto,
    incident_dto,
    incident_item_row,
    incidents_of,
    muted_by,
    open_incident_by_run,
    rules_of,
)
from services.api.preflight_support import build_endpoint_health

router = APIRouter(tags=["ops-view"])

_HEALTHY = "HEALTHY"


def _store_or_503(deps: ApiDeps) -> Any:
    if deps.runs_store is None and not deps.run_registry:
        raise ApiError(503, "Run Store Unavailable", "run store not configured")
    return deps.runs_store


def _failed_runs(deps: ApiDeps, project_id: str) -> list[Any]:
    if deps.runs_store is not None:
        return [run for run in deps.runs_store.list_runs(project_id) if run.state == "FAILED"]
    return [
        run
        for run in reversed(list(deps.run_registry.values()))
        if run.project_id == project_id and run.state == "FAILED"
    ]


def _run_alerts(deps: ApiDeps, project_id: str) -> list[AlertItem]:
    alerts: list[AlertItem] = []
    for run in _failed_runs(deps, project_id):
        alerts.append(
            AlertItem(
                kind=AlertKind.RUN_FAILED,
                severity=AlertSeverity.CRITICAL,
                subject=run.id.value,
                detail=f"run {run.id.value} state=FAILED protocol={run.protocol_id}",
            )
        )
    return alerts


def _endpoint_alerts(deps: ApiDeps) -> list[AlertItem]:
    catalog = merged_catalog_snapshot(deps)
    health = build_endpoint_health(deps, catalog)
    alerts: list[AlertItem] = []
    for endpoint_id, state in sorted(health.items()):
        value = state.value if hasattr(state, "value") else str(state)
        if value == _HEALTHY:
            continue
        alerts.append(
            AlertItem(
                kind=AlertKind.ENDPOINT_DEGRADED,
                severity=AlertSeverity.WARNING,
                subject=endpoint_id,
                detail=f"endpoint {endpoint_id} health={value}",
            )
        )
    return alerts


def _worker_alerts(deps: ApiDeps) -> list[AlertItem]:
    registry = deps.worker_registry
    if registry is None:
        return []
    alerts: list[AlertItem] = []
    for worker in registry.list_workers():
        state = getattr(worker.state, "value", worker.state)
        if state in {"LOST", "DRAINING"}:
            alerts.append(
                AlertItem(
                    kind=AlertKind.WORKER_OFFLINE,
                    severity=AlertSeverity.WARNING,
                    subject=worker.worker_id,
                    detail=f"worker {worker.worker_id} state={state}",
                )
            )
    return alerts


@router.get("/projects/{project_id}/ops/alerts", response_model=AlertsViewDto)
async def list_ops_alerts(project_id: str, request: Request) -> AlertsViewDto:
    """派生告警收件箱（失败 run ∪ 非健康端点 ∪ 离线/排水 worker）+ 规则静音标记。

    规则**不隐藏**告警：匹配的项带 `muted=true` + `muted_by=<rule id>` 并给出计数；
    来源 run 已登记未关闭事故的告警带 `incident_id`（写面被读面消费的第二个点）。
    store 缺失时 `rules_available=false` + 原因，不伪装成"没有规则"。
    """
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    _store_or_503(deps)
    items = [*_run_alerts(deps, project_id), *_endpoint_alerts(deps), *_worker_alerts(deps)]
    items.sort(key=lambda item: (item.severity.value, item.kind.value, item.subject))
    rules = rules_of(deps, project_id)
    incidents_by_run = open_incident_by_run(incidents_of(deps, project_id))
    alerts = [
        alert_dto(
            item,
            muted_by_id=muted_by(rules, item),
            incident_id=incidents_by_run.get(item.subject),
        )
        for item in items
    ]
    available = deps.ops_store is not None
    return AlertsViewDto(
        alerts=alerts,
        rules_available=available,
        rules_reason=None if available else RULES_UNAVAILABLE_REASON,
        rules_applied=sum(1 for rule in rules if rule.enabled),
        muted_count=sum(1 for alert in alerts if alert.muted),
    )


@router.get("/projects/{project_id}/ops/incidents", response_model=IncidentsViewDto)
async def list_ops_incidents(project_id: str, request: Request) -> IncidentsViewDto:
    """已登记事故 + 未被登记的失败 Run 候选（两者不混淆）。

    失败 Run **不**自动登记为事故：登记过的事故进 `incidents`，其余失败 Run 仍是
    `candidates`。**关闭过的事故也算已登记**——有记录就不该反复以"未处理候选"提醒；
    但它不再给告警挂 `incident_id`（只有未关闭的事故才表示"正在处理"）。
    处置动作见 `ops_control.py`（declare/assign/close）。
    """
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    _store_or_503(deps)
    registered = incidents_of(deps, project_id)
    claimed = {incident.run_id for incident in registered if incident.run_id is not None}
    candidates = [
        incident_item_row(run)
        for run in _failed_runs(deps, project_id)
        if run.id.value not in claimed
    ]
    candidates.sort(key=lambda item: item.run_id)
    available = deps.ops_store is not None
    return IncidentsViewDto(
        incidents=[incident_dto(incident) for incident in registered],
        candidates=candidates,
        workflow_available=available,
        workflow_reason=None if available else WORKFLOW_UNAVAILABLE_REASON,
    )


def _workspace_metrics(deps: ApiDeps) -> list[DataHealthMetric]:
    registry = deps.worker_registry
    if registry is None:
        return []
    workers = registry.list_workers()
    return [
        DataHealthMetric(metric="workers_registered", value=str(len(workers)), status="INFO"),
    ]


def _artifact_metrics(deps: ApiDeps) -> list[DataHealthMetric]:
    store = deps.artifacts
    if store is None:
        return []
    refs = store.list_refs()
    verified = sum(1 for artifact in refs if _safe_verified(store, artifact.id))
    return [
        DataHealthMetric(metric="artifacts_tracked", value=str(len(refs)), status="INFO"),
        DataHealthMetric(
            metric="artifacts_verified",
            value=f"{verified}/{len(refs)}",
            status="OK" if verified == len(refs) else "DEGRADED",
        ),
    ]


def _safe_verified(store: Any, artifact_id: str) -> bool:
    try:
        return bool(store.verify(artifact_id))
    except Exception:  # noqa: BLE001 - tombstone/缺 blob 均归入不可校验
        return False


@router.get("/projects/{project_id}/ops/data-health", response_model=DataHealthViewDto)
async def get_ops_data_health(project_id: str, request: Request) -> DataHealthViewDto:
    """数据健康聚合（端点健康计数 + dataset 目录计数 + artifact 抽样校验）。

    无聚合质量报告 API：只呈现可从既有状态直接观测到的计数与校验结果。
    """
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    catalog = merged_catalog_snapshot(deps)
    health = build_endpoint_health(deps, catalog)
    healthy = sum(1 for value in health.values() if str(value) == _HEALTHY)
    metrics: list[DataHealthMetric] = [
        DataHealthMetric(metric="endpoints_total", value=str(len(health)), status="INFO"),
        DataHealthMetric(
            metric="endpoints_healthy",
            value=f"{healthy}/{len(health)}",
            status="OK" if healthy == len(health) else "DEGRADED",
        ),
    ]
    if deps.library_store is not None:
        from packages.domain.library import ResourceKind

        datasets = deps.library_store.list_resources(project_id, ResourceKind.DATASET)
        metrics.append(
            DataHealthMetric(metric="datasets_registered", value=str(len(datasets)), status="INFO")
        )
    metrics.extend(_workspace_metrics(deps))
    metrics.extend(_artifact_metrics(deps))
    return DataHealthViewDto(
        metrics=[
            DataHealthMetricDto(metric=item.metric, value=item.value, status=item.status)
            for item in metrics
        ],
        aggregate_available=False,
        aggregate_reason="无聚合质量报告 API；以上为既有状态的可观测计数与校验结果",
    )
