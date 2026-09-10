"""Preflight provider 健康三态测试（PLAN-20260910-037 WP-D）。

UNKNOWN = 警示不阻断（TOOL_HEALTH_UNPROVEN，绝不伪装健康）；
OPEN_CIRCUIT/DISABLED = 不可用；未注入 key 维持注入方契约（HEALTHY）。
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import Any, cast

from adapters.fakes.tool_provider import FakeToolProvider
from packages.application.ports import CatalogSnapshot
from packages.application.ports.resource_catalog import PreflightContext
from packages.application.preflight.checks import check_tools
from packages.domain.enums import EffectClass, EndpointHealth, ProviderType, TrustLevel
from packages.domain.protocols import FindingSeverity
from packages.domain.tools import ToolProviderSpec
from services.api.preflight_support import build_provider_health
from tests.application.protocol_fixtures import catalog, compiled


def _codes(findings: object) -> list[str]:
    return [finding.code for finding in cast(Any, findings)]


def _with_health(health: dict[str, EndpointHealth]) -> tuple[Any, PreflightContext]:
    plan, ctx = compiled()
    return plan, replace(ctx, provider_health=health)


def test_unknown_health_warns_without_blocking() -> None:
    plan, ctx = _with_health({"fixture-tools": EndpointHealth.UNKNOWN})
    findings = check_tools(plan, ctx)
    assert "TOOL_HEALTH_UNPROVEN" in _codes(findings)
    assert "TOOL_UNAVAILABLE" not in _codes(findings)
    assert all(
        finding.code != "TOOL_HEALTH_UNPROVEN" or finding.severity is FindingSeverity.WARNING
        for finding in findings
    )


def test_degraded_health_warns() -> None:
    plan, ctx = _with_health({"fixture-tools": EndpointHealth.DEGRADED})
    findings = check_tools(plan, ctx)
    assert "TOOL_HEALTH_DEGRADED" in _codes(findings)
    assert "TOOL_UNAVAILABLE" not in _codes(findings)


def test_open_circuit_disqualifies_the_only_provider() -> None:
    plan, ctx = _with_health({"fixture-tools": EndpointHealth.OPEN_CIRCUIT})
    findings = check_tools(plan, ctx)
    assert "TOOL_UNAVAILABLE" in _codes(findings)


def test_disabled_disqualifies() -> None:
    plan, ctx = _with_health({"fixture-tools": EndpointHealth.DISABLED})
    assert "TOOL_UNAVAILABLE" in _codes(check_tools(plan, ctx))


def test_absent_keys_keep_injector_contract() -> None:
    """未注入 provider_health（默认 {}）不产生健康类发现（M2 基线不翻转）。"""
    plan, ctx = _with_health({})
    findings = _codes(check_tools(plan, ctx))
    assert "TOOL_HEALTH_UNPROVEN" not in findings
    assert "TOOL_UNAVAILABLE" not in findings


def _rest_spec() -> ToolProviderSpec:
    return ToolProviderSpec(
        id="mcp-lit",
        kind=ProviderType.MCP,
        trust_level=TrustLevel.VERIFIED,
        capabilities=["literature.search"],
        effect_class=EffectClass.READ_ONLY,
        health_check=True,
    )


def _native_spec() -> ToolProviderSpec:
    return ToolProviderSpec(
        id="builtin",
        kind=ProviderType.NATIVE,
        trust_level=TrustLevel.BUILT_IN,
        capabilities=["literature.search"],
        effect_class=EffectClass.READ_ONLY,
    )


def _snapshot() -> CatalogSnapshot:
    base = catalog()
    return replace(
        base,
        tool_providers={"builtin": _native_spec(), "mcp-lit": _rest_spec()},
    )


def test_builder_native_healthy_unregistered_rest_unknown() -> None:
    deps = cast(Any, SimpleNamespace(tool_providers={}))
    health = build_provider_health(deps, _snapshot())
    assert health["builtin"] is EndpointHealth.HEALTHY
    assert health["mcp-lit"] is EndpointHealth.UNKNOWN


def test_builder_delegates_to_registered_provider_report() -> None:
    provider = FakeToolProvider()
    deps = cast(Any, SimpleNamespace(tool_providers={"mcp-lit": provider}))
    health = build_provider_health(deps, _snapshot())
    assert health["mcp-lit"] is EndpointHealth.HEALTHY
    provider.fail_health("mcp-lit")
    health = build_provider_health(deps, _snapshot())
    assert health["mcp-lit"] is EndpointHealth.OPEN_CIRCUIT


def test_builder_probe_exception_converges_unknown() -> None:
    class _Boom:
        def check_health(self, provider: object) -> object:
            raise RuntimeError("transport exploded")

    deps = cast(Any, SimpleNamespace(tool_providers={"mcp-lit": _Boom()}))
    assert build_provider_health(deps, _snapshot())["mcp-lit"] is EndpointHealth.UNKNOWN
