"""M15 operations 只读视图 DTO(telemetry / cost / trend)。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from services.api.dto.enums import (
    ComparabilityVerdictValue,
    CostAmountStatusValue,
    OutboxPendingStatusValue,
    PriceDimensionValue,
    RegressionVerdictValue,
    TrendPointVerdictValue,
)


class TelemetryTaskCountsDto(BaseModel):
    total: int
    succeeded: int
    failed: int
    cancelled: int
    queued: int
    leased: int
    other: int = 0


class TelemetryOutboxDto(BaseModel):
    pending: int | None = None
    status: OutboxPendingStatusValue = "KNOWN"
    unavailable_reason: str | None = None


class TelemetrySinkDto(BaseModel):
    """exporter 健康:dropped 是真实丢弃,unlinked 是 trace 链接降级(信号未丢)。"""

    enabled: bool
    dropped: int
    unlinked: int = 0
    last_error: str | None = None


class RunTelemetryDto(BaseModel):
    """telemetry summary:canonical state + sink 计数器;不含任何 vendor 数据。"""

    run_id: str
    manifest_digest: str | None = None
    exporter_config_digest: str | None = None
    generated_at: str
    tasks: TelemetryTaskCountsDto
    outbox: TelemetryOutboxDto
    sink: TelemetrySinkDto


class CostAmountDto(BaseModel):
    status: CostAmountStatusValue
    minor_units: int | None = None
    currency: str
    effective_from: str | None = None
    calculation_method: str | None = None


class CostDimensionDto(BaseModel):
    dimension: PriceDimensionValue
    resource_key: str
    amount: CostAmountDto
    entry_count: int


class CostViewDto(BaseModel):
    run_id: str
    pricing_version: str
    pricing_digest: str
    # `pricing_frozen=False` 是遗留 run 的显式状态;computed 成本绝不因为
    # endpoint 启动时加载的当期价表而被追溯重算。
    pricing_frozen: bool
    pricing_degraded_reason: str | None = None
    dimensions: list[CostDimensionDto] = Field(default_factory=list)
    total: CostAmountDto


class PricingGroupDto(BaseModel):
    """一个定价表分组（同 (version, digest) 的 entries 小计；WP-D）。"""

    pricing_version: str
    pricing_digest: str
    pricing_frozen: bool
    amount: CostAmountDto
    entry_count: int


class CostDayPointDto(BaseModel):
    date: str
    total: CostAmountDto
    # 一天内跨多个定价表：total 不求和（PARTIALLY_METERED），分组小计如实列出。
    mixed_pricing: bool = False
    groups: list[PricingGroupDto] = Field(default_factory=list)


class CostDailyViewDto(BaseModel):
    """跨 run 成本日序列（WP-D；只含有数据的日期，无预测、无插值）。"""

    truncated: bool = False
    days: list[CostDayPointDto] = Field(default_factory=list)
    attribution_note: str | None = None


class ProjectCostDayDto(BaseModel):
    """项目日序列的一天：`included_in_projection=false` 时给出排除原因（G12）。"""

    date: str
    amount: CostAmountDto
    mixed_pricing: bool = False
    included_in_projection: bool = False
    exclusion_reason: str | None = None


class ProjectCostProjectionDto(BaseModel):
    """已计价日均外推（`MEAN_OF_VALUED_DAYS`）；`unavailable_reason` 非空时不给金额。"""

    method: str
    horizon_days: int
    valued_days: int
    excluded_days: int
    observed_minor: int | None = None
    observed_status: str
    currency: str | None = None
    pricing_version: str | None = None
    daily_mean_minor: int | None = None
    projected_minor: int | None = None
    unavailable_reason: str | None = None
    note: str


class ProjectCostForecastDto(BaseModel):
    """项目级成本预测（G12）：日序列 + 外推 + 排除项 + 归属注记，全部随响应返回。"""

    project_id: str
    from_date: str | None = None
    to_date: str | None = None
    truncated: bool = False
    days: list[ProjectCostDayDto] = Field(default_factory=list)
    projection: ProjectCostProjectionDto
    unattributed_entries: int = 0
    attribution_note: str | None = None
    scope_note: str


class TrendPointDto(BaseModel):
    report_digest: str
    recorded_at: str | None = None
    verdict: TrendPointVerdictValue
    dataset_id: str | None = None
    dataset_version: str | None = None
    dataset_digest: str | None = None
    gate_config_id: str | None = None
    gate_config_version: str | None = None
    gate_config_digest: str | None = None
    system_version: str | None = None
    comparison_digest: str | None = None
    run_id: str | None = None
    pass_count: int = 0
    fail_count: int = 0
    infra_error_count: int = 0
    reviewer_failure_count: int = 0
    missing: bool = False
    integrity_error: str | None = None


class RegressionMarkerDto(BaseModel):
    baseline_digest: str
    candidate_digest: str
    verdict: RegressionVerdictValue
    newly_regressed: list[str] = Field(default_factory=list)
    newly_fixed: list[str] = Field(default_factory=list)


class TrendSegmentDto(BaseModel):
    points: list[TrendPointDto] = Field(default_factory=list)
    comparisons: list[RegressionMarkerDto] = Field(default_factory=list)


class TrendDivergenceDto(BaseModel):
    verdict: ComparabilityVerdictValue
    reason: str


class TrendViewDto(BaseModel):
    dataset_id: str | None = None
    truncated: bool = False
    segments: list[TrendSegmentDto] = Field(default_factory=list)
    divergences: list[TrendDivergenceDto] = Field(default_factory=list)
    missing: list[TrendPointDto] = Field(default_factory=list)


class ClusterWorkerDto(BaseModel):
    """Worker cluster read view (Control Plane 只读投影;非调度真相)。

    PA-1 debt #7: exposes the GPU *observation digest + stamp* so operators
    can see GPU capability without any raw device identity (the digest is a
    hash; device names never enter telemetry/DTOs — M17 privacy precedent).
    """

    worker_ref: str
    state: str
    protocol_version: str
    runtime_version: str
    platform: str
    registration_generation: int
    max_concurrency: int
    drain_requested: bool
    last_heartbeat: str | None = None
    gpu_probe_digest: str | None = None
    gpu_observed_at: str | None = None


class ClusterViewDto(BaseModel):
    workers: list[ClusterWorkerDto] = Field(default_factory=list)


class RunPlacementDto(BaseModel):
    run_id: str
    placements: list[ClusterWorkerDto] = Field(default_factory=list)
    execution_tasks: list[str] = Field(default_factory=list)
