"""M15 operations 视图 mapper:domain state → DTO(纯映射,无业务决策)。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

from packages.application.cost.aggregation import total_cost
from packages.application.cost.pricing import PriceDimension, PricingTable, unpriced_table
from packages.application.cost.projection import (
    CostAmount,
    DimensionCost,
    project_dimensions,
    resolve_run_pricing,
)
from packages.application.evaluation.trend import (
    RegressionMarker,
    TrendPoint,
    TrendSegment,
    build_trend,
)
from packages.application.ports.eval_report_store import EvalReportQuery, EvalReportStore
from packages.application.ports.telemetry_sink import NullTelemetrySink, TelemetrySink
from packages.domain.enums import QualityGateVerdict
from packages.domain.run import ResearchRun
from packages.domain.task_state import ResearchTaskState
from services.api.composition import ApiDeps
from services.api.dto.enums import (
    PriceDimensionValue,
    RegressionVerdictValue,
    TrendPointVerdictValue,
)
from services.api.dto.operations import (
    ClusterViewDto,
    CostAmountDto,
    CostDimensionDto,
    CostViewDto,
    RegressionMarkerDto,
    RunPlacementDto,
    RunTelemetryDto,
    TelemetryOutboxDto,
    TelemetrySinkDto,
    TelemetryTaskCountsDto,
    TrendDivergenceDto,
    TrendPointDto,
    TrendSegmentDto,
    TrendViewDto,
    ClusterWorkerDto,
)
from services.api.errors import ApiError

_STATE_LABELS = {
    ResearchTaskState.State.SUCCEEDED: "succeeded",
    ResearchTaskState.State.FAILED: "failed",
    ResearchTaskState.State.CANCELLED: "cancelled",
    ResearchTaskState.State.QUEUED: "queued",
    ResearchTaskState.State.LEASED: "leased",
}

# trend 点位的 verdict 闭集 = QualityGateVerdict + 两个非质量态(trend.py 产出)。
_TREND_POINT_VERDICTS: frozenset[str] = frozenset({
    *(verdict.value for verdict in QualityGateVerdict),
    "INDETERMINATE",
    "MISSING_EVALUATION",
})
# 回归 marker 的 verdict 闭集 = QualityGateVerdict + INDETERMINATE(compare_reports 产出)。
_REGRESSION_VERDICTS: frozenset[str] = frozenset({
    *(verdict.value for verdict in QualityGateVerdict),
    "INDETERMINATE",
})


def _price_dimension(value: str) -> PriceDimensionValue:
    """Fail-closed 收敛到 DTO 的 dimension 闭集。"""
    return PriceDimension(value).value


def _trend_point_verdict(value: str) -> TrendPointVerdictValue:
    if value not in _TREND_POINT_VERDICTS:
        raise ValueError(f"unknown trend point verdict: {value!r}")
    return cast(TrendPointVerdictValue, value)


def _regression_verdict(value: str) -> RegressionVerdictValue:
    if value not in _REGRESSION_VERDICTS:
        raise ValueError(f"unknown regression verdict: {value!r}")
    return cast(RegressionVerdictValue, value)


def run_telemetry_dto(
    deps: ApiDeps,
    run_id: str,
    run_task_ids: frozenset[str],
    *,
    run: ResearchRun | None = None,
) -> RunTelemetryDto:
    """telemetry summary:仅 canonical state + sink 自身计数器。"""
    engine = deps.workflow
    tasks = _task_counts(engine, run_id, run_task_ids)
    return RunTelemetryDto(
        run_id=run_id,
        manifest_digest=str(run.manifest_digest) if run and run.manifest_digest else None,
        exporter_config_digest=deps.exporter_config_digest,
        generated_at=datetime.now(timezone.utc).isoformat(),
        tasks=tasks,
        outbox=_pending_outbox(engine, run_id),
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
    run: ResearchRun,
    run_task_ids: frozenset[str],
) -> CostViewDto:
    """成本投影只按 run 冻结的价表快照计价(BLOCKER-6)。

    不读取 `deps.pricing` 来计价：它是 composition root 此刻加载的当期表，
    在 run 完成后可变。`resolve_run_pricing` 只接受 run 行的
    (pricing_version, pricing_digest) 并从快照存储寻址；遗留或存储缺失均
    显式降级为 computed monetary unavailable，而不是回落当期表。
    """
    if deps.budget is None:
        raise ApiError(503, "Budget Ledger Unavailable", "budget ledger not configured")
    resolution = resolve_run_pricing(run, deps.pricing_snapshot_store)
    scoped = tuple(
        entry
        for entry in deps.budget.snapshot().entries
        if entry.run_id == run.id.value or entry.task_id in run_task_ids
    )
    dimensions = project_dimensions(scoped, resolution.pricing)
    total = total_cost(scoped, resolution.pricing)
    return CostViewDto(
        run_id=run.id.value,
        pricing_version=resolution.pricing_version,
        pricing_digest=resolution.pricing_digest,
        pricing_frozen=resolution.frozen,
        pricing_degraded_reason=resolution.degraded_reason,
        dimensions=[_cost_dimension_dto(dimension) for dimension in dimensions],
        total=_cost_amount_dto(total),
    )


def _cost_dimension_dto(dimension: DimensionCost) -> CostDimensionDto:
    return CostDimensionDto(
        dimension=_price_dimension(dimension.dimension),
        resource_key=dimension.resource_key,
        amount=_cost_amount_dto(dimension.amount),
        entry_count=dimension.entry_count,
    )


def _cost_amount_dto(amount: CostAmount) -> CostAmountDto:
    return CostAmountDto(
        status=amount.status.value,
        minor_units=amount.minor_units,
        currency=amount.currency,
        effective_from=amount.effective_from,
        calculation_method=amount.calculation_method,
    )


def trend_view_dto(
    store: EvalReportStore,
    dataset_id: str | None,
    *,
    expected_digests: tuple[str, ...] = (),
    limit: int = 200,
) -> TrendViewDto:
    """trend 投影:唯一输入是 EvalReportStore;回归判定来自 compare_reports。"""
    page = store.query_page(EvalReportQuery(dataset_id=dataset_id, limit=limit))
    report = build_trend(
        page.entries,
        store,
        expected_digests=expected_digests,
    )
    return TrendViewDto(
        dataset_id=dataset_id,
        truncated=page.truncated,
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


def _pending_outbox(engine: Any | None, run_id: str) -> TelemetryOutboxDto:
    if engine is None:
        return TelemetryOutboxDto(
            pending=None,
            status="UNKNOWN",
            unavailable_reason="workflow engine not configured",
        )
    try:
        pending = sum(1 for envelope in engine.pending_outbox() if envelope.run_id == run_id)
        return TelemetryOutboxDto(pending=pending, status="KNOWN")
    except Exception as error:
        return TelemetryOutboxDto(
            pending=None,
            status="UNKNOWN",
            unavailable_reason=f"outbox read failed: {type(error).__name__}",
        )


def sink_counters_dto(telemetry: TelemetrySink) -> TelemetrySinkDto:
    """telemetry sink 健康投影(纯函数;可被 canary 直接断言)。

    `dropped` 聚合 inner 自报计数——`FailSafeTelemetrySink` 只数 inner 抛错,
    而 OTel sink 自吞全部错误,单看外壳会得到结构性恒 0 的健康信号。
    `unlinked` 与 `dropped` 分离:父引用不可解析是链接降级,不是信号丢失。
    """
    inner = getattr(telemetry, "inner", telemetry)
    enabled = not isinstance(inner, NullTelemetrySink)
    dropped = int(getattr(telemetry, "drop_count", 0) or 0)
    unlinked = int(getattr(inner, "unlinked", 0) or 0)
    last_error = getattr(telemetry, "last_error", None)
    return TelemetrySinkDto(
        enabled=enabled,
        dropped=dropped,
        unlinked=unlinked,
        last_error=last_error if isinstance(last_error, str) else None,
    )


def _sink_counters(deps: ApiDeps) -> TelemetrySinkDto:
    return sink_counters_dto(deps.telemetry)


def _point_dto(point: TrendPoint) -> TrendPointDto:
    return TrendPointDto(
        report_digest=point.report_digest,
        recorded_at=point.recorded_at.isoformat() if point.recorded_at else None,
        verdict=_trend_point_verdict(point.verdict),
        dataset_id=point.dataset_id,
        dataset_version=point.dataset_version,
        dataset_digest=point.dataset_digest,
        gate_config_id=point.gate_config_id,
        gate_config_version=point.gate_config_version,
        gate_config_digest=point.gate_config_digest,
        system_version=point.system_version,
        comparison_digest=point.comparison_digest,
        run_id=point.run_id,
        pass_count=point.pass_count,
        fail_count=point.fail_count,
        infra_error_count=point.infra_error_count,
        reviewer_failure_count=point.reviewer_failure_count,
        missing=point.missing,
        integrity_error=point.integrity_error,
    )


def _marker_dto(marker: RegressionMarker) -> RegressionMarkerDto:
    return RegressionMarkerDto(
        baseline_digest=marker.baseline_digest,
        candidate_digest=marker.candidate_digest,
        verdict=_regression_verdict(marker.verdict),
        newly_regressed=list(marker.newly_regressed),
        newly_fixed=list(marker.newly_fixed),
    )


def _segment_dto(segment: TrendSegment) -> TrendSegmentDto:
    return TrendSegmentDto(
        points=[_point_dto(point) for point in segment.points],
        comparisons=[_marker_dto(marker) for marker in segment.comparisons],
    )


def _cluster_worker_dto(reg: Any) -> "ClusterWorkerDto":
    from packages.application.observability.attributes import worker_ref

    return ClusterWorkerDto(
        worker_ref=worker_ref(str(reg.worker_id)),
        state=str(reg.state),
        protocol_version=str(reg.protocol_version),
        runtime_version=str(reg.runtime_version),
        platform=str(reg.platform),
        registration_generation=int(reg.registration_generation),
        max_concurrency=int(reg.max_concurrency),
        drain_requested=bool(reg.drain_requested),
        last_heartbeat=reg.last_heartbeat.value.isoformat() if reg.last_heartbeat else None,
    )


def worker_cluster_dto(worker_registrations: tuple[Any, ...]) -> ClusterViewDto:
    """WorkerRegistry.list_workers() → 只读 cluster 视图(worker_ref 不含原始 id)。"""
    return ClusterViewDto(workers=[_cluster_worker_dto(reg) for reg in worker_registrations])


def run_placement_dto(
    run_id: str,
    worker_registrations: tuple[Any, ...],
    execution_task_ids: tuple[str, ...],
) -> RunPlacementDto:
    """run 的执行 placement:该 run 的 execution tasks 与参与 worker(只读)。"""
    return RunPlacementDto(
        run_id=run_id,
        placements=[_cluster_worker_dto(reg) for reg in worker_registrations],
        execution_tasks=list(execution_task_ids),
    )
