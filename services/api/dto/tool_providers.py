"""Tool Provider 只读视图 DTO（PLAN-043 WP-A，EC-02）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ToolProviderDto(BaseModel):
    id: str
    kind: str
    trust_level: str
    effect_class: str
    capabilities: list[str] = Field(default_factory=list)
    transport: str | None = None
    protocol_version: str | None = None
    network_domains: list[str] = Field(default_factory=list)
    health_check: bool = False
    health: str = "UNKNOWN"


class ToolProviderListDto(BaseModel):
    providers: list[ToolProviderDto] = Field(default_factory=list)
    management_available: bool = False
    management_reason: str | None = None
