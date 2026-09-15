"""项目级成本预测只读路由（G12 / GOAL-20260915-002 EC-02）。

- `GET /projects/{project_id}/cost-forecast`：项目 runs 的已记录用量日序列 +
  **已计价日均外推**（方法/样本量/排除项随响应返回；无数据日不插值、UNKNOWN 不当 0、
  跨币种不求和）。
- run 级预算预留-消耗视图仍在 `GET /runs/{id}/cost-forecast`（预算口径，不外推）。

装配与归属规则见 `services/api/mappers/project_cost_forecast.py`；本模块只做参数校验与错误面。
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from packages.application.cost.series_projection import MAX_HORIZON_DAYS, MIN_HORIZON_DAYS
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.operations import ProjectCostForecastDto
from services.api.errors import ApiError
from services.api.mappers.project_cost_forecast import project_cost_forecast_dto

router = APIRouter(tags=["budget"])


def _horizon(raw: int) -> int:
    if raw < MIN_HORIZON_DAYS or raw > MAX_HORIZON_DAYS:
        raise ApiError(
            422,
            "Invalid Horizon",
            f"horizon_days must be between {MIN_HORIZON_DAYS} and {MAX_HORIZON_DAYS}",
        )
    return raw


@router.get("/projects/{project_id}/cost-forecast", response_model=ProjectCostForecastDto)
async def project_cost_forecast(
    project_id: str,
    request: Request,
    horizon_days: int = Query(default=7),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
) -> ProjectCostForecastDto:
    """项目级成本预测：日序列 + 已计价日均外推（无数据日不填充）。

    未知项目 → 空序列 + `NO_VALUED_DAYS`（与 `/projects/{id}/runs` 同口径，不 404）；
    未配置 budget ledger → 503；`horizon_days` 越界 → 422。
    """
    deps: ApiDeps = get_deps(request)
    return project_cost_forecast_dto(
        deps,
        project_id,
        date_from,
        date_to,
        _horizon(horizon_days),
    )


__all__ = ["router"]
