"""M15 operations 只读路由:telemetry / cost / trend。

- 全部只读;浏览器不做任何计算、不发明阈值、不连 telemetry vendor;
- telemetry summary 来自 canonical state + sink 自身计数器(非 vendor);
- cost 唯一 usage 输入是 BudgetLedger.snapshot();定价来自版本化 pricing.yaml;
- trend 唯一输入是 EvalReportStore;回归判定来自 compare_reports。
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.operations import (
    ClusterViewDto,
    CostDailyViewDto,
    CostViewDto,
    RunPlacementDto,
    RunTelemetryDto,
    TrendViewDto,
)
from services.api.errors import ApiError
from services.api.mappers.cost_daily import cost_daily_view_dto
from services.api.mappers.operations import (
    cost_view_dto,
    run_placement_dto,
    run_telemetry_dto,
    trend_view_dto,
    worker_cluster_dto,
)
from services.api.run_access import get_run_or_error

router = APIRouter(tags=["operations"])


@router.get("/cost/daily", response_model=CostDailyViewDto)
async def cost_daily(
    request: Request,
    date_from: str | None = Query(default=None, max_length=10),
    date_to: str | None = Query(default=None, max_length=10),
) -> CostDailyViewDto:
    """跨 run 成本日序列（WP-D 只读；五状态语义，无预测无插值）。"""
    deps: ApiDeps = get_deps(request)
    return cost_daily_view_dto(deps, date_from, date_to)


@router.get("/runs/{run_id}/telemetry", response_model=RunTelemetryDto)
async def run_telemetry(run_id: str, request: Request) -> RunTelemetryDto:
    """run 级 telemetry summary:canonical 投影 + sink 健康计数(只读)。"""
    deps: ApiDeps = get_deps(request)
    run = get_run_or_error(deps, run_id)
    return run_telemetry_dto(
        deps,
        run_id,
        _run_task_ids(deps, run_id),
        run=run,
    )


@router.get("/runs/{run_id}/cost", response_model=CostViewDto)
async def run_cost(run_id: str, request: Request) -> CostViewDto:
    """run 级成本视图:UsageLedger × 版本化定价快照(五状态,不伪造 0)。"""
    deps: ApiDeps = get_deps(request)
    run = get_run_or_error(deps, run_id)
    return cost_view_dto(deps, run, _run_task_ids(deps, run_id))


@router.get("/evaluations/trend", response_model=TrendViewDto)
async def evaluations_trend(
    request: Request,
    dataset_id: str | None = None,
    expected_digests: list[str] | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
) -> TrendViewDto:
    """评测趋势:分段可比序列 + 回归标记 + 缺失评测第三态。"""
    deps: ApiDeps = get_deps(request)
    store = deps.eval_report_store
    if store is None:
        raise ApiError(503, "Eval Report Store Unavailable", "eval report store not configured")
    return trend_view_dto(
        store,
        dataset_id,
        expected_digests=tuple(expected_digests or ()),
        limit=limit,
    )


def _run_task_ids(deps: ApiDeps, run_id: str) -> frozenset[str]:
    if deps.projection is None:
        return frozenset()
    return frozenset(task.id.value for task, _contract in deps.projection.list_tasks(run_id))


@router.get("/cluster/workers", response_model=ClusterViewDto)
async def cluster_workers(request: Request) -> ClusterViewDto:
    """Worker 集群只读视图(worker_ref 短 digest;不暴露原始 id/凭据)。"""
    deps: ApiDeps = get_deps(request)
    if deps.worker_registry is None:
        raise ApiError(503, "Worker Registry Unavailable", "worker registry not configured")
    return worker_cluster_dto(deps.worker_registry.list_workers())


@router.get("/runs/{run_id}/placement", response_model=RunPlacementDto)
async def run_placement(run_id: str, request: Request) -> RunPlacementDto:
    """run 的远程执行 placement(只读投影;Console 不直连 Worker)。"""
    deps: ApiDeps = get_deps(request)
    get_run_or_error(deps, run_id)
    registry = deps.worker_registry
    workers = registry.list_workers() if registry is not None else ()
    task_ids = tuple(
        task.id.value
        for task, _contract in (deps.projection.list_tasks(run_id) if deps.projection else ())
        if str(task.kind.value) == "EXECUTION"
    )
    return run_placement_dto(run_id, workers, task_ids)
