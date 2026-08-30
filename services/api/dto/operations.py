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
