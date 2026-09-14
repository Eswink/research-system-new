"""成本预测投影 DTO（PLAN-20260914-046 WP-B）。"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class ForecastLineDto(BaseModel):
    resource_type: str
    unit: str
    reserved: int
    # None = 不可计量或尚无消耗记录，由 data_status 区分（绝不为 0）。
    consumed: int | Decimal | None = None
    remaining: int | Decimal | None = None
    data_status: str
    entry_count: int
    unknown_entry_count: int


class CostForecastDto(BaseModel):
    run_id: str
    lines: list[ForecastLineDto] = Field(default_factory=list)
    consumed_cost_minor: int | None = None
    currency: str | None = None
    cost_status: str
    unknown_cost_entries: int
    # 预留归属：RESERVATION_REF（权威引用）/ RUN_SCOPE（退化匹配）/ NONE。
    attribution: str
    unattributed_reserved: int = 0
    forecast_scope: str
    scope_note: str
