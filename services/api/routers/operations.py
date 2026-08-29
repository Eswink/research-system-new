"""M15 operations 只读路由:telemetry / cost / trend。

- 全部只读;浏览器不做任何计算、不发明阈值、不连 telemetry vendor;
- telemetry summary 来自 canonical state + sink 自身计数器(非 vendor);
- cost 唯一 usage 输入是 BudgetLedger.snapshot();定价来自版本化 pricing.yaml;
- trend 唯一输入是 EvalReportStore;回归判定来自 compare_reports。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.operations import CostViewDto, RunTelemetryDto, TrendViewDto
from services.api.errors import ApiError
from services.api.mappers.operations import pricing_of
from services.api.run_access import get_run_or_error

router = APIRouter(tags=["operations"])


@router.get("/runs/{run_id}/telemetry", response_model=RunTelemetryDto)
async def run_telemetry(run_id: str, request: Request) -> RunTelemetryDto:
    """run 级 telemetry summary:canonical 投影 + sink 健康计数(只读)。"""
    deps: ApiDeps = get_deps(request)
    get_run_or_error(deps, run_id)
    from services.api.mappers.operations import run_telemetry_dto as mapper

    return mapper(deps, run_id, _run_task_ids(deps, run_id))


@router.get("/runs/{run_id}/cost", response_model=CostViewDto)
async def run_cost(run_id: str, request: Request) -> CostViewDto:
    """run 级成本视图:UsageLedger × 版本化定价快照(五状态,不伪造 0)。"""
    deps: ApiDeps = get_deps(request)
    get_run_or_error(deps, run_id)
    from services.api.mappers.operations import cost_view_dto as mapper

    return mapper(deps, run_id, _run_task_ids(deps, run_id), pricing_of(deps))


@router.get("/evaluations/trend", response_model=TrendViewDto)
async def evaluations_trend(request: Request, dataset_id: str | None = None) -> TrendViewDto:
    """评测趋势:分段可比序列 + 回归标记 + 缺失评测第三态。"""
    deps: ApiDeps = get_deps(request)
    store = deps.eval_report_store
    if store is None:
        raise ApiError(503, "Eval Report Store Unavailable", "eval report store not configured")
    from services.api.mappers.operations import trend_view_dto as mapper

    return mapper(store, dataset_id)


def _run_task_ids(deps: ApiDeps, run_id: str) -> frozenset[str]:
    if deps.projection is None:
        return frozenset()
    return frozenset(task.id.value for task, _contract in deps.projection.list_tasks(run_id))
