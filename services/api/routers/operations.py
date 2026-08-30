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
from services.api.dto.operations import CostViewDto, RunTelemetryDto, TrendViewDto
from services.api.errors import ApiError
from services.api.mappers.operations import (
    cost_view_dto,
    run_telemetry_dto,
    trend_view_dto,
)
from services.api.run_access import get_run_or_error

router = APIRouter(tags=["operations"])


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
