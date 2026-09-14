"""成本预测路由（PLAN-20260914-046 WP-B，EC-04 第一批）。

`GET /runs/{run_id}/cost-forecast` 是**只读派生投影**：由 BudgetLedger
snapshot 中归属本 run 的 reservations/usage entries 计算预留-消耗-剩余，
不外推未预留开销、不跨币种求和、UNKNOWN 不解释为 0（语义见
packages/domain/cost_forecast.py）。

run 级隔离与 `/runs/{id}/usage` 同口径：entry 归属 = `run_id == run` 或
`task_id ∈ run 的 task 投影`；未知 run → 404；账本未配置 → 503。
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from packages.application.ports.budget_ledger import LedgerSnapshot
from packages.domain.budget import BudgetReservation
from packages.domain.cost_forecast import (
    CostForecast,
    ReservationAttribution,
    build_cost_forecast,
)
from services.api.composition import ApiDeps
from services.api.deps import get_deps
from services.api.dto.budget_forecast import CostForecastDto, ForecastLineDto
from services.api.errors import ApiError
from services.api.run_access import get_run_or_error

router = APIRouter(prefix="/runs", tags=["budget"])


def _run_task_ids(deps: ApiDeps, run_id: str) -> frozenset[str]:
    if deps.projection is None:
        return frozenset()
    return frozenset(task.id.value for task, _contract in deps.projection.list_tasks(run_id))


def _forecast_dto(view: CostForecast) -> CostForecastDto:
    return CostForecastDto(
        run_id=view.run_id,
        lines=[
            ForecastLineDto(
                resource_type=line.resource_type.value,
                unit=line.unit,
                reserved=line.reserved,
                consumed=line.consumed,
                remaining=line.remaining,
                data_status=line.data_status.value,
                entry_count=line.entry_count,
                unknown_entry_count=line.unknown_entry_count,
            )
            for line in view.lines
        ],
        consumed_cost_minor=view.consumed_cost_minor,
        currency=view.currency,
        cost_status=view.cost_status.value,
        unknown_cost_entries=view.unknown_cost_entries,
        attribution=view.attribution.value,
        unattributed_reserved=view.unattributed_reserved,
        forecast_scope=view.forecast_scope,
        scope_note=view.scope_note,
    )


@router.get("/{run_id}/cost-forecast", response_model=CostForecastDto)
async def run_cost_forecast(run_id: str, request: Request) -> CostForecastDto:
    """run 成本预测投影（预留-消耗-剩余；只覆盖已预留部分）。

    预留归属（不猜）：冻结 manifest/预算调整登记的 ref 解析成功时用其覆盖的
    预留集合；ref 不可解析（跨进程重启后进程内记账丢失）才退化为
    `run:<id>` 作用域匹配，并在 `attribution` 显式标注；正式 preflight 的
    `phase:<id>` 预留无法归属时不并入预留总量，条数记在 `unattributed_reserved`。
    """
    deps: ApiDeps = get_deps(request)
    if deps.budget is None:
        raise ApiError(503, "Budget Ledger Unavailable", "budget ledger not configured")
    get_run_or_error(deps, run_id)
    task_ids = _run_task_ids(deps, run_id)
    snapshot = deps.budget.snapshot()
    entries = tuple(
        entry for entry in snapshot.entries if entry.run_id == run_id or entry.task_id in task_ids
    )
    reservations, attribution, unattributed = _attribute_reservations(deps, snapshot, run_id)
    return _forecast_dto(
        build_cost_forecast(
            run_id,
            reservations,
            entries,
            attribution=attribution,
            unattributed_reserved=unattributed,
        )
    )


def _attribute_reservations(
    deps: ApiDeps, snapshot: LedgerSnapshot, run_id: str
) -> tuple[tuple[BudgetReservation, ...], ReservationAttribution, int]:
    """账本快照 → 本 run 的预留集合（权威 ref 优先，退化作用域匹配显式标注）。"""
    ref = deps.runs.reservation_ref(run_id) if deps.runs is not None else None
    by_ref = snapshot.reservations_by_ref.get(ref) if ref is not None else None
    if by_ref is not None:
        return by_ref, ReservationAttribution.RESERVATION_REF, 0
    scope = f"run:{run_id}"
    scoped = tuple(item for item in snapshot.reservations if item.scope == scope)
    if scoped:
        return scoped, ReservationAttribution.RUN_SCOPE, 0
    return (), ReservationAttribution.NONE, len(snapshot.reservations)
