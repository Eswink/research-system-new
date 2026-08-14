"""ToolResolver：capability → ToolSpec/Provider 绑定（TOOL_RUNTIME.md §3）。

Effective Tool Set 公式：
Role requested capabilities + Agent override
∩ Project/Phase policy ∩ Provider health ∩ Credential scope
= Resolved Tool Bindings → Freeze

本模块是纯函数：输入 ToolCatalog + policy/health 快照，输出绑定与
findings；不做任何 I/O。ToolProvider 不拥有 Policy truth——policy 输入
来自 PolicyEvaluator 的调用结果。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from packages.application.tool_plane.catalog import ToolCatalog
from packages.domain.enums import (
    EndpointHealth,
    PolicyDecision,
    RiskClass,
    TrustLevel,
)
from packages.domain.tools import ToolProviderSpec, classify_risk

_FORBIDDEN_TRUST = {TrustLevel.REVOKED, TrustLevel.UNTRUSTED}
_UNAVAILABLE_HEALTH = {EndpointHealth.OPEN_CIRCUIT, EndpointHealth.DISABLED}


@dataclass(frozen=True, slots=True)
class ToolBinding:
    capability: str
    provider_id: str
    tool_id: str
    risk_class: RiskClass
    pack_digest: str | None = None


@dataclass(frozen=True, slots=True)
class CapabilityResolution:
    capability: str
    bindings: tuple[ToolBinding, ...]
    findings: tuple[str, ...] = ()

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return tuple(sorted({binding.provider_id for binding in self.bindings}))

    @property
    def tool_ids(self) -> tuple[str, ...]:
        return tuple(sorted({binding.tool_id for binding in self.bindings}))


@dataclass(frozen=True, slots=True)
class ResolutionInput:
    policy_decisions: Mapping[str, PolicyDecision] = field(default_factory=dict)
    provider_health: Mapping[str, EndpointHealth] = field(default_factory=dict)
    default_decision: PolicyDecision = PolicyDecision.ALLOW


# default_decision=ALLOW 不再隐式放行（fail-closed）；显式 per-capability
# ALLOW / ALLOW_WITH_CONSTRAINTS 是 resolution 面的唯一放行来源。


def _eligible_providers(
    catalog: ToolCatalog,
    capability: str,
    inputs: ResolutionInput,
) -> tuple[ToolProviderSpec, ...]:
    return tuple(
        provider
        for provider in catalog.providers_by_capability(capability)
        if provider.trust_level not in _FORBIDDEN_TRUST
        and inputs.provider_health.get(provider.id, EndpointHealth.HEALTHY)
        not in _UNAVAILABLE_HEALTH
    )


def _bindings_for(
    catalog: ToolCatalog,
    capability: str,
    provider: ToolProviderSpec,
) -> tuple[ToolBinding, ...]:
    return tuple(
        ToolBinding(
            capability=capability,
            provider_id=provider.id,
            tool_id=tool.id,
            risk_class=classify_risk(tool.effect_class, provider.trust_level),
            pack_digest=catalog.pack_digest_for_tool(tool.id),
        )
        for tool in catalog.tools_for_provider(provider)
        if capability in tool.capabilities
    )


def resolve_capability(
    catalog: ToolCatalog,
    capability: str,
    inputs: ResolutionInput,
) -> CapabilityResolution:
    """单一 capability 的确定性解析（fail-closed）。

    显式 ALLOW 缺失（既无 per-capability 决策也无 allow-with-constraints）
    时按 DENY 处理：策略面（preflight/execute）负责产出显式决策，静默
    ALLOW 默认值不作为解析依据，防止策略覆盖缺口导致非预期暴露。
    """
    findings: list[str] = []

    decision = _effective_decision(capability, inputs)
    if decision is PolicyDecision.DENY:
        reason = "policy denied" if capability in inputs.policy_decisions else "no explicit allow"
        return CapabilityResolution(
            capability,
            (),
            (f"{reason} capability {capability}",),
        )

    providers = _eligible_providers(catalog, capability, inputs)
    if not providers:
        if catalog.providers_by_capability(capability):
            findings.append(f"no healthy trusted provider for capability {capability}")
        else:
            findings.append(f"no provider exposes capability {capability}")
        return CapabilityResolution(capability, (), tuple(findings))

    provider = providers[0]
    bindings = _bindings_for(catalog, capability, provider)
    if not bindings:
        findings.append(
            f"provider {provider.id} declares capability {capability} but no tool implements it"
        )
        return CapabilityResolution(capability, (), tuple(findings))

    if decision is PolicyDecision.REQUIRE_APPROVAL:
        findings.append(f"capability {capability} requires approval")
    return CapabilityResolution(capability, bindings, tuple(findings))


def _effective_decision(capability: str, inputs: ResolutionInput) -> PolicyDecision:
    """resolution 视角的有效决策：显式决策优先，其次 constrained allow。

    ALLOW_WITH_CONSTRAINTS 由执行路径落实约束，解析面等价放行；
    per-capability ALLOW 是唯一无警告的放行来源。default_decision
    仅在默认值为 DENY/REQUIRE_APPROVAL 时保留收紧语义。
    """
    if capability in inputs.policy_decisions:
        return inputs.policy_decisions[capability]
    if inputs.default_decision is PolicyDecision.ALLOW:
        return PolicyDecision.DENY
    return inputs.default_decision


def resolve_all(
    catalog: ToolCatalog,
    capabilities: tuple[str, ...],
    inputs: ResolutionInput,
) -> tuple[CapabilityResolution, ...]:
    return tuple(resolve_capability(catalog, cap, inputs) for cap in capabilities)


def freeze_tool_set(resolutions: tuple[CapabilityResolution, ...]) -> tuple[str, ...]:
    """冻结的 Effective Tool Set（provider id 并集，确定性排序）。

    AgentSession 启动后该集合不可变（ADR-0004 / TOOL_RUNTIME.md §3）。
    """
    return tuple(
        sorted({
            provider_id for resolution in resolutions for provider_id in resolution.provider_ids
        })
    )


def unresolved_capabilities(
    resolutions: tuple[CapabilityResolution, ...],
) -> tuple[str, ...]:
    return tuple(resolution.capability for resolution in resolutions if not resolution.bindings)


def resolve_tool_call(
    resolutions: tuple[CapabilityResolution, ...],
    capability: str,
    tool_id: str,
) -> ToolBinding | None:
    for resolution in resolutions:
        if resolution.capability != capability:
            continue
        for binding in resolution.bindings:
            if binding.tool_id == tool_id:
                return binding
    return None


def risk_of(
    resolutions: tuple[CapabilityResolution, ...],
    tool_id: str,
) -> RiskClass | None:
    for resolution in resolutions:
        for binding in resolution.bindings:
            if binding.tool_id == tool_id:
                return binding.risk_class
    return None
