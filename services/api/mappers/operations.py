"""M15 operations 视图 mapper:domain state → DTO(纯映射,无业务决策)。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from packages.application.cost.aggregation import total_cost
from packages.application.cost.pricing import PricingTable, unpriced_table
from packages.application.cost.projection import project_dimensions
from packages.application.evaluation.trend import (
    RegressionMarker,
    TrendPoint,
    TrendSegment,
)
from packages.application.ports.eval_report_store import EvalReportStore
from packages.domain.task_state import ResearchTaskState
from services.api.composition import ApiDeps
from services.api.dto.operations import (
    CostAmountDto,
    CostDimensionDto,
    CostViewDto,
    RegressionMarkerDto,
    RunTelemetryDto,
    TelemetryOutboxDto,
    TelemetrySinkDto,
    TelemetryTaskCountsDto,
    TrendDivergenceDto,
    TrendPointDto,
    TrendSegmentDto,
    TrendViewDto,
)

_STATE_LABELS = {
    ResearchTaskState.State.SUCCEEDED: "succeeded",
    ResearchTaskState.State.FAILED: "failed",
    ResearchTaskState.State.CANCELLED: "cancelled",
    ResearchTaskState.State.QUEUED: "queued",
    ResearchTaskState.State.LEASED: "leased",
}


def run_telemetry_dto(deps: ApiDeps, run_id: str, run_task_ids: frozenset[str]) -> RunTelemetryDto:
    """telemetry summary:仅 canonical state + sink 自身计数器。"""
    engine = deps.runs._deps.workflow if deps.runs is not None else None
    tasks = _task_counts(engine, run_id, run_task_ids)
    return RunTelemetryDto(
        run_id=run_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        tasks=tasks,
        outbox=TelemetryOutboxDto(pending=_pending_outbox(engine, run_id)),
        sink=_sink_counters(deps),
    )


def pricing_of(deps: ApiDeps) -> PricingTable:
    """deps 注入的定价快照;缺省 → 出厂 unpriced_v1(显式不可计价)。"""
    pricing = deps.pricing
    if isinstance(pricing, PricingTable):
        return pricing
    return unpriced_table()


def cost_view_dto(
    deps: ApiDeps,
    run_id: str,
    run_task_ids: frozenset[str],
    pricing: PricingTable,
) -> CostViewDto:
    """cost 投影:唯一 usage 输入是 BudgetLedger.snapshot()(DoD-9)。"""
    if deps.budget is None:
        from services.api.errors import ApiError

        raise ApiError(503, "Budget Ledger Unavailable", "budget ledger not configured")
    scoped = tuple(
        entry for entry in deps.budget.snapshot().entries if entry.task_id in run_task_ids
    )
    dimensions = project_dimensions(scoped, pricing)
    total = total_cost(scoped, pricing)
    return CostViewDto(
        run_id=run_id,
        pricing_version=pricing.version,
        pricing_digest=pricing.pricing_digest(),
        dimensions=[
            CostDimensionDto(
                dimension=dimension.dimension,
                resource_key=dimension.resource_key,
                amount=CostAmountDto(
                    status=dimension.amount.status.value,
                    minor_units=dimension.amount.minor_units,
                    currency=dimension.amount.currency,
                ),
                entry_count=dimension.entry_count,
            )
            for dimension in dimensions
        ],
        total=CostAmountDto(
            status=total.status.value,
            minor_units=total.minor_units,
            currency=total.currency,
        ),
    )


def trend_view_dto(
    store: EvalReportStore,
    dataset_id: str | None,
) -> TrendViewDto:
    """trend 投影:唯一输入是 EvalReportStore;回归判定来自 compare_reports。"""
    from packages.application.evaluation.trend import build_trend
    from packages.application.ports.eval_report_store import EvalReportQuery

    entries = store.query(EvalReportQuery(dataset_id=dataset_id, limit=200))
    report = build_trend(tuple(entries), store)
    return TrendViewDto(
        dataset_id=dataset_id,
        segments=[_segment_dto(segment) for segment in report.segments],
        divergences=[
            TrendDivergenceDto(verdict=divergence.verdict.value, reason=divergence.reason)
            for divergence in report.divergences
        ],
        missing=[_point_dto(point) for point in report.missing],
    )


def _task_counts(
    engine: Any | None,
    run_id: str,
    run_task_ids: frozenset[str],
) -> TelemetryTaskCountsDto:
    counts = {"succeeded": 0, "failed": 0, "cancelled": 0, "queued": 0, "leased": 0}
    total = 0
    if engine is not None and run_task_ids:
        for row in engine.list_tasks(run_id):
            total += 1
            label = _STATE_LABELS.get(row.task.status)
            if label is None:
                continue
            counts[label] += 1
    return TelemetryTaskCountsDto(
        total=total,
        succeeded=counts["succeeded"],
        failed=counts["failed"],
        cancelled=counts["cancelled"],
        queued=counts["queued"],
        leased=counts["leased"],
        other=max(0, total - sum(counts.values())),
    )


def _pending_outbox(engine: Any | None, run_id: str) -> int:
    if engine is None:
        return 0
    try:
        return sum(1 for envelope in engine.pending_outbox() if envelope.run_id == run_id)
    except Exception:
        return 0


def _sink_counters(deps: ApiDeps) -> TelemetrySinkDto:
    telemetry = deps.telemetry
    from packages.application.ports.telemetry_sink import NullTelemetrySink

    inner = getattr(telemetry, "inner", telemetry)
    enabled = not isinstance(inner, NullTelemetrySink)
    dropped = int(getattr(telemetry, "drop_count", 0) or 0)
    last_error = getattr(telemetry, "last_error", None)
    return TelemetrySinkDto(
        enabled=enabled,
        dropped=dropped,
        last_error=last_error if isinstance(last_error, str) else None,
    )


def _point_dto(point: TrendPoint) -> TrendPointDto:
    return TrendPointDto(
        report_digest=point.report_digest,
        recorded_at=point.recorded_at.isoformat() if point.recorded_at else None,
        verdict=point.verdict,
        pass_count=point.pass_count,
        fail_count=point.fail_count,
        infra_error_count=point.infra_error_count,
        missing=point.missing,
    )


def _marker_dto(marker: RegressionMarker) -> RegressionMarkerDto:
    return RegressionMarkerDto(
        baseline_digest=marker.baseline_digest,
        candidate_digest=marker.candidate_digest,
        verdict=marker.verdict,
        newly_regressed=list(marker.newly_regressed),
        newly_fixed=list(marker.newly_fixed),
    )


def _segment_dto(segment: TrendSegment) -> TrendSegmentDto:
    return TrendSegmentDto(
        points=[_point_dto(point) for point in segment.points],
        comparisons=[_marker_dto(marker) for marker in segment.comparisons],
    )
