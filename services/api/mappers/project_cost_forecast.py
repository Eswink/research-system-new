"""项目级成本预测映射（G12）：项目 runs 的 ledger 条目 → 日序列 → 已计价日均外推。

与 `/cost/daily` 同一归属口径（run 冻结定价；混定价天不求和），但作用域限定在
**项目 runs**：属于其它项目已知 run 的条目明确排除，归属不明的条目计入
`unattributed_entries` 并在响应里说明（不猜测项目归属）。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from packages.application.cost.daily import DayCost, daily_series
from packages.application.cost.pricing import PricingTable
from packages.application.cost.pricing_resolution import resolve_run_pricing
from packages.application.cost.series_projection import (
    SeriesProjection,
    exclusion_reason,
    project_series,
)
from packages.domain.budget import UsageLedgerEntry
from services.api.composition import ApiDeps
from services.api.dto.operations import (
    ProjectCostDayDto,
    ProjectCostForecastDto,
    ProjectCostProjectionDto,
)
from services.api.errors import ApiError
from services.api.mappers.cost_daily import note_for_unattributed, parse_day
from services.api.mappers.operations import cost_amount_dto

SCOPE_NOTE = (
    "project-scope time-series projection over recorded usage attributed to this project's runs; "
    "reserved-vs-consumed budget for a single run stays on GET /runs/{id}/cost-forecast"
)

PricingResolver = Callable[[UsageLedgerEntry], PricingTable | None]


def _all_runs(deps: ApiDeps) -> list[Any]:
    if deps.runs_store is not None:
        return list(deps.runs_store.list_runs(None))
    return list(deps.run_registry.values())


def _task_owner_map(deps: ApiDeps, runs: list[Any]) -> dict[str, str]:
    owners: dict[str, str] = {}
    if deps.projection is None:
        return owners
    for run in runs:
        for task, _contract in deps.projection.list_tasks(run.id.value):
            owners[task.id.value] = run.id.value
    return owners


def _select(
    entries: list[UsageLedgerEntry],
    project_run_ids: set[str],
    owners: dict[str, str],
    known_projects: dict[str, str],
) -> tuple[list[UsageLedgerEntry], int]:
    """项目条目 + 归属不明计数；其它项目的已知 run 明确排除（不在范围，也不算不明）。"""
    selected: list[UsageLedgerEntry] = []
    unattributed = 0
    for entry in entries:
        run_id = entry.run_id or ""
        if run_id in project_run_ids or owners.get(entry.task_id or "") in project_run_ids:
            selected.append(entry)
            continue
        if run_id and run_id in known_projects:
            continue
        unattributed += 1
    return selected, unattributed


def _resolver(deps: ApiDeps, runs: list[Any]) -> PricingResolver:
    run_by_id = {run.id.value: run for run in runs}
    store = deps.pricing_snapshot_store

    def resolve(entry: UsageLedgerEntry) -> PricingTable | None:
        run = run_by_id.get(entry.run_id or "")
        return resolve_run_pricing(run, store).pricing if run is not None else None

    return resolve


def project_cost_forecast_dto(
    deps: ApiDeps,
    project_id: str,
    date_from: str | None,
    date_to: str | None,
    horizon_days: int,
) -> ProjectCostForecastDto:
    if deps.budget is None:
        raise ApiError(503, "Budget Ledger Unavailable", "budget ledger not configured")
    all_runs = _all_runs(deps)
    runs = [run for run in all_runs if run.project_id == project_id]
    owners = _task_owner_map(deps, runs)
    selected, unattributed = _select(
        list(deps.budget.snapshot().entries),
        {run.id.value for run in runs},
        owners,
        {run.id.value: run.project_id for run in all_runs},
    )
    days, truncated = daily_series(
        selected,
        _resolver(deps, runs),
        parse_day(date_from, "date_from"),
        parse_day(date_to, "date_to"),
    )
    projection = project_series(days, horizon_days)
    return ProjectCostForecastDto(
        project_id=project_id,
        from_date=date_from,
        to_date=date_to,
        truncated=truncated,
        days=[_day_dto(day) for day in days],
        projection=_projection_dto(projection),
        unattributed_entries=unattributed,
        attribution_note=note_for_unattributed(unattributed),
        scope_note=SCOPE_NOTE,
    )


def _day_dto(day: DayCost) -> ProjectCostDayDto:
    reason = exclusion_reason(day)
    return ProjectCostDayDto(
        date=day.day.isoformat(),
        amount=cost_amount_dto(day.total),
        mixed_pricing=day.mixed_pricing,
        included_in_projection=reason is None,
        exclusion_reason=reason,
    )


def _projection_dto(projection: SeriesProjection) -> ProjectCostProjectionDto:
    return ProjectCostProjectionDto(
        method=projection.method,
        horizon_days=projection.horizon_days,
        valued_days=projection.valued_days,
        excluded_days=len(projection.excluded_days),
        observed_minor=projection.observed_minor,
        observed_status=projection.observed_status,
        currency=projection.currency,
        pricing_version=projection.pricing_version,
        daily_mean_minor=projection.daily_mean_minor,
        projected_minor=projection.projected_minor,
        unavailable_reason=projection.unavailable_reason,
        note=projection.note,
    )
