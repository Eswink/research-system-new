"""Policy 可见性 DTO（PLAN-20260914-049 WP-C）。

只呈现策略面的事实（声明的规则 + 逐 scope 的**有效判决**）；判决由控制面实际
使用的同一求值器计算，不改写、不缓存、不暴露凭据或路径以外的运行细节。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PolicyRuleViewDto(BaseModel):
    """一条声明规则（effect 由所属规则组决定）。"""

    effect: str
    capability: str | None = None
    action: str | None = None
    scope: str | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)


class GateCapabilityViewDto(BaseModel):
    """门链能力（同一能力在多个 scope 上求值）的逐 scope 有效判决。"""

    capability: str
    scopes: list[str]
    # scope → 决策（DENY / REQUIRE_APPROVAL / ALLOW_WITH_CONSTRAINTS / ALLOW）。
    effects: dict[str, str]
    reasons: dict[str, str] = Field(default_factory=dict)


class PolicyCapabilitiesDto(BaseModel):
    policy_id: str
    version: str
    default_effect: str
    source: str
    rules: list[PolicyRuleViewDto] = Field(default_factory=list)
    gate_capabilities: list[GateCapabilityViewDto] = Field(default_factory=list)
    note: str
