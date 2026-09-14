"""Ops 只读运维投影路由（PLAN-20260914-045 WP-B，EC-03 第二批）。

四个端点全部**只读派生**：alerts（失败 run ∪ 降级端点 ∪ 离线 worker）、
incidents（失败 run 候选）、schedules（进程内 scheduler 配置事实）、
data-health（端点健康计数 + dataset 目录计数 + artifact 抽样校验）。
无持久化、无副作用；缺失依赖诚实在响应里标注，不伪装空成功。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from packages.domain.ops_view import (
    AlertItem,
    AlertKind,
    AlertSeverity,
    DataHealthMetric,
    IncidentItem,
    ScheduleEntry,
)
from services.api.catalog_merge import merged_catalog_snapshot, require_registered_project
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.ops_view import (
    AlertItemDto,
    AlertsViewDto,
    DataHealthMetricDto,
    DataHealthViewDto,
    IncidentItemDto,
    IncidentsViewDto,
    ScheduleEntryDto,
    SchedulesViewDto,
)
from services.api.errors import ApiError
from services.api.preflight_support import build_endpoint_health

router = APIRouter(tags=["ops-view"])

_HEALTHY = "HEALTHY"

# 进程内 scheduler 配置事实（与 services/api/app.py 的构造默认值一致）。
_SCHEDULES: tuple[ScheduleEntry, ...] = (
    ScheduleEntry(
        name="lease_recovery",
        interval_seconds=30.0,
        purpose="恢复过期 lease 并推进 LOST 转换",
        enabled=True,
    ),
    ScheduleEntry(
        name="outbox_relay",
        interval_seconds=5.0,
        purpose="中继 transactional outbox 事件",
        enabled=True,
    ),
    ScheduleEntry(
        name="retention",
        interval_seconds=3600.0,
        purpose="按 retention policy 清理 artifact",
        enabled=True,
    ),
    ScheduleEntry(
        name="worker_reaper",
        interval_seconds=15.0,
        purpose="标记心跳过期 worker 为 LOST",
        enabled=True,
    ),
)


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
    """派生告警收件箱（失败 run ∪ 非健康端点 ∪ 离线/排水 worker）。

    无告警规则 CRUD（无契约）；worker_registry 缺失时该来源诚实缺省。
    """
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    _store_or_503(deps)
    items = [*_run_alerts(deps, project_id), *_endpoint_alerts(deps), *_worker_alerts(deps)]
    items.sort(key=lambda item: (item.severity.value, item.kind.value, item.subject))
    return AlertsViewDto(
        alerts=[
            AlertItemDto(
                kind=item.kind.value,
                severity=item.severity.value,
                subject=item.subject,
                detail=item.detail,
            )
            for item in items
        ],
        rules_available=False,
        rules_reason="无告警规则 CRUD API；本视图为只读派生收件箱",
    )


@router.get("/projects/{project_id}/ops/incidents", response_model=IncidentsViewDto)
async def list_ops_incidents(project_id: str, request: Request) -> IncidentsViewDto:
    """事故候选（FAILED run）；无 declare/assign/close 处置工作流。

    失败 Run **不**自动成为已登记事故——本端点只列出候选，不改变任何状态。
    """
    deps: ApiDeps = get_deps(request)
    require_registered_project(deps, project_id)
    _store_or_503(deps)
    candidates = [
        IncidentItem(
            run_id=run.id.value,
            protocol_id=run.protocol_id,
            state=run.state,
            updated_at=run.updated_at.value.isoformat(),
        )
        for run in _failed_runs(deps, project_id)
    ]
    candidates.sort(key=lambda item: item.run_id)
    return IncidentsViewDto(
        incidents=[
            IncidentItemDto(
                run_id=item.run_id,
                protocol_id=item.protocol_id,
                state=item.state,
                updated_at=item.updated_at,
            )
            for item in candidates
        ],
        workflow_available=False,
        workflow_reason="无事故 declare/assign/close 处置 API；失败 Run 不自动登记为事故",
    )


@router.get("/ops/schedules", response_model=SchedulesViewDto)
async def list_ops_schedules() -> SchedulesViewDto:
    """进程内 scheduler 的配置事实（只读）。

    无用户可见调度 API：不能创建/启停/手动触发；本视图只暴露既有守护线程配置。
    """
    return SchedulesViewDto(
        schedules=[
            ScheduleEntryDto(
                name=entry.name,
                interval_seconds=entry.interval_seconds,
                purpose=entry.purpose,
                enabled=entry.enabled,
            )
            for entry in _SCHEDULES
        ],
        management_available=False,
        management_reason="scheduler 为进程内守护线程，无用户可见创建/启停/触发 API",
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
