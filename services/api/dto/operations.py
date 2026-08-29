"""M15 operations 只读视图 DTO(telemetry / cost / trend)。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TelemetryTaskCountsDto(BaseModel):
    total: int
    succeeded: int
    failed: int
    cancelled: int
    queued: int
    leased: int
    other: int = 0


class TelemetryOutboxDto(BaseModel):
    pending: int


class TelemetrySinkDto(BaseModel):
    enabled: bool
    dropped: int
    last_error: str | None = None


class RunTelemetryDto(BaseModel):
    """telemetry summary:canonical state + sink 计数器;不含任何 vendor 数据。"""

    run_id: str
    generated_at: str
    tasks: TelemetryTaskCountsDto
    outbox: TelemetryOutboxDto
    sink: TelemetrySinkDto


class CostAmountDto(BaseModel):
    status: str
    minor_units: int | None = None
    currency: str


class CostDimensionDto(BaseModel):
    dimension: str
    resource_key: str
    amount: CostAmountDto
    entry_count: int


class CostViewDto(BaseModel):
    run_id: str
    pricing_version: str
    pricing_digest: str
    dimensions: list[CostDimensionDto] = Field(default_factory=list)
    total: CostAmountDto


class TrendPointDto(BaseModel):
    report_digest: str
    recorded_at: str | None = None
    verdict: str
    pass_count: int = 0
    fail_count: int = 0
    infra_error_count: int = 0
    missing: bool = False


class RegressionMarkerDto(BaseModel):
    baseline_digest: str
    candidate_digest: str
    verdict: str
    newly_regressed: list[str] = Field(default_factory=list)
    newly_fixed: list[str] = Field(default_factory=list)


class TrendSegmentDto(BaseModel):
    points: list[TrendPointDto] = Field(default_factory=list)
    comparisons: list[RegressionMarkerDto] = Field(default_factory=list)


class TrendDivergenceDto(BaseModel):
    verdict: str
    reason: str


class TrendViewDto(BaseModel):
    dataset_id: str | None = None
    segments: list[TrendSegmentDto] = Field(default_factory=list)
    divergences: list[TrendDivergenceDto] = Field(default_factory=list)
    missing: list[TrendPointDto] = Field(default_factory=list)
