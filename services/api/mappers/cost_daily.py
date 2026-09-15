"""成本日序列映射（WP-D）：ledger 全扫描 + 按 run 冻结定价归属 + 按 UTC 日投影。

扫描 budget.snapshot()（BudgetLedger Port 的唯一读面）与 per-run 定价解析
组合；不做预测、无数据日不填充；跨定价表的天不静默求和。
"""

from __future__ import annotations

from datetime import date
from typing import Any

from packages.application.cost.daily import DayCost, PricingGroup, daily_series
from packages.application.cost.pricing import PricingTable
from packages.application.cost.pricing_resolution import resolve_run_pricing
from packages.domain.budget import UsageLedgerEntry
from services.api.composition import ApiDeps
from services.api.dto.operations import (
    CostDailyViewDto,
    CostDayPointDto,
    PricingGroupDto,
)
from services.api.errors import ApiError
from services.api.mappers.operations import cost_amount_dto


def parse_day(raw: str | None, field: str) -> date | None:
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ApiError(422, "Invalid Date", f"{field} must be ISO YYYY-MM-DD") from exc


def _enumerate_runs(deps: ApiDeps) -> list[Any]:
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


class _Attribution:
    """run/task 归属 + 定价解析（unattributed 计数供诚实注记）。"""

    def __init__(self, deps: ApiDeps, runs: list[Any]) -> None:
        self._run_by_id = {run.id.value: run for run in runs}
        self._owners = _task_owner_map(deps, runs)
        self._store = deps.pricing_snapshot_store
        self.unattributed = 0

    def resolve(self, entry: UsageLedgerEntry) -> PricingTable | None:
        run = self._run_by_id.get(entry.run_id or "") or self._run_by_id.get(
            self._owners.get(entry.task_id or "", "")
        )
        if run is None:
            self.unattributed += 1
            return None
        return resolve_run_pricing(run, self._store).pricing


def cost_daily_view_dto(
    deps: ApiDeps,
    date_from: str | None,
    date_to: str | None,
) -> CostDailyViewDto:
    if deps.budget is None:
        raise ApiError(503, "Budget Ledger Unavailable", "budget ledger not configured")
    attribution = _Attribution(deps, _enumerate_runs(deps))
    days, truncated = daily_series(
        deps.budget.snapshot().entries,
        attribution.resolve,
        parse_day(date_from, "date_from"),
        parse_day(date_to, "date_to"),
    )
    return CostDailyViewDto(
        truncated=truncated,
        days=[_day_dto(day) for day in days],
        attribution_note=note_for_unattributed(attribution.unattributed),
    )


def note_for_unattributed(unattributed: int) -> str | None:
    if unattributed == 0:
        return None
    return (
        f"{unattributed} usage entries could not be attributed to a known run; "
        "they are grouped as unfrozen pricing (never valued against the current table)"
    )


def _day_dto(day: DayCost) -> CostDayPointDto:
    return CostDayPointDto(
        date=day.day.isoformat(),
        total=cost_amount_dto(day.total),
        mixed_pricing=day.mixed_pricing,
        groups=[_group_dto(group) for group in day.groups],
    )


def _group_dto(group: PricingGroup) -> PricingGroupDto:
    pricing = group.pricing
    return PricingGroupDto(
        pricing_version=pricing.version if pricing is not None else "unfrozen",
        pricing_digest=pricing.pricing_digest() if pricing is not None else "-",
        pricing_frozen=pricing is not None,
        amount=cost_amount_dto(group.amount),
        entry_count=group.entry_count,
    )
