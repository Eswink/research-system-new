"""M8 Tool Plane 单元测试（解析面）：catalog / resolver / health。

执行面（lifecycle/execution/results/preflight risk）见
test_tool_plane_execution.py；共享 fixture 构造器在
tests/application/tool_plane_support.py。
"""

from __future__ import annotations

import pytest

from adapters.fakes import FakeToolPackStore
from packages.application.ports.tool_pack_store import ToolPackRecord
from packages.application.tool_plane import (
    ResolutionInput,
    build_tool_catalog,
    catalog_from_pack_records,
    freeze_tool_set,
    mark_disabled,
    record_probe,
    record_probe_failure,
    resolve_capability,
    unresolved_capabilities,
)
from packages.application.tool_plane.health import ToolHealthSnapshot
from packages.domain.circuit_breaker import CircuitBreakerTransitionError
from packages.domain.core import Timestamp
from packages.domain.enums import (
    EndpointHealth,
    PolicyDecision,
    RiskClass,
    ToolPackState,
    TrustLevel,
)
from packages.domain.tools import ToolHealthReport
from tests.application.tool_plane_support import (
    NOW,
    make_manifest,
    make_provider,
    make_tool,
)


class TestCatalog:
    def test_indexes_tools_and_packs(self) -> None:
        pack = make_manifest(tools=(make_tool(),))
        catalog, errors = build_tool_catalog(
            {"mcp-lit": make_provider()},
            {"lit-pack": pack},
        )
        assert errors == []
        assert catalog.tools["lit_search"].name == "lit_search"
        assert catalog.pack_of_tool["lit_search"] == "lit-pack"
        assert catalog.pack_digest_for_tool("lit_search") == str(pack.digest)

    def test_duplicate_tool_id_across_packs(self) -> None:
        pack_a = make_manifest(tools=(make_tool(),), pack_id="pack-a")
        pack_b = make_manifest(tools=(make_tool(),), pack_id="pack-b")
        _, errors = build_tool_catalog(
            {"mcp-lit": make_provider()},
            {"pack-a": pack_a, "pack-b": pack_b},
        )
        assert any("duplicate tool id" in error for error in errors)

    def test_revoked_pack_excluded_from_catalog(self) -> None:
        pack = make_manifest(tools=(make_tool(),))
        store = FakeToolPackStore()
        store.install(
            ToolPackRecord(
                pack_id=pack.id,
                state=ToolPackState.INSTALLED,
                manifest=pack,
                installed_at=Timestamp(NOW),
            )
        )
        store.revoke(pack.id, "supply chain alert")
        catalog, errors = catalog_from_pack_records(
            {"mcp-lit": make_provider()},
            store.snapshot(),
        )
        assert errors == []
        assert catalog.tools == {}


class TestResolver:
    @staticmethod
    def _allow(*capabilities: str) -> ResolutionInput:
        return ResolutionInput(
            policy_decisions={capability: PolicyDecision.ALLOW for capability in capabilities}
        )

    def test_resolves_preferred_provider_and_tools(self) -> None:
        pack = make_manifest(tools=(make_tool(),))
        catalog, _ = build_tool_catalog(
            {
                "mcp-lit": make_provider("mcp-lit", trust=TrustLevel.USER_APPROVED),
                "mcp-lit-verified": make_provider("mcp-lit-verified"),
            },
            {"lit-pack": pack},
        )
        resolution = resolve_capability(catalog, "search.academic", self._allow("search.academic"))
        assert resolution.provider_ids == ("mcp-lit-verified",)
        assert resolution.tool_ids == ("lit_search",)
        assert resolution.bindings[0].risk_class is RiskClass.MEDIUM
        assert resolution.bindings[0].pack_digest == str(pack.digest)

    def test_policy_denied_capability(self) -> None:
        catalog, _ = build_tool_catalog({"mcp-lit": make_provider()}, {})
        inputs = ResolutionInput(policy_decisions={"search.academic": PolicyDecision.DENY})
        resolution = resolve_capability(catalog, "search.academic", inputs)
        assert resolution.bindings == ()
        assert resolution.findings[0].startswith("policy denied")

    def test_no_explicit_allow_is_fail_closed(self) -> None:
        """策略覆盖缺口不得静默放行：无显式 ALLOW 一律视为 DENY。"""
        catalog, _ = build_tool_catalog({"mcp-lit": make_provider()}, {})
        resolution = resolve_capability(catalog, "search.academic", ResolutionInput())
        assert resolution.bindings == ()
        assert "no explicit allow" in resolution.findings[0]

    def test_unhealthy_provider_excluded(self) -> None:
        catalog, _ = build_tool_catalog({"mcp-lit": make_provider()}, {})
        inputs = ResolutionInput(
            policy_decisions={"search.academic": PolicyDecision.ALLOW},
            provider_health={"mcp-lit": EndpointHealth.OPEN_CIRCUIT},
        )
        resolution = resolve_capability(catalog, "search.academic", inputs)
        assert resolution.bindings == ()
        assert "no healthy trusted provider" in resolution.findings[0]

    def test_revoked_provider_excluded(self) -> None:
        catalog, _ = build_tool_catalog(
            {"mcp-lit": make_provider(trust=TrustLevel.REVOKED)},
            {},
        )
        resolution = resolve_capability(catalog, "search.academic", self._allow("search.academic"))
        assert resolution.bindings == ()

    def test_provider_without_implementing_tool(self) -> None:
        catalog, _ = build_tool_catalog({"mcp-lit": make_provider()}, {})
        resolution = resolve_capability(catalog, "search.academic", self._allow("search.academic"))
        assert resolution.bindings == ()
        assert "no tool implements it" in resolution.findings[0]

    def test_freeze_tool_set_is_deterministic_union(self) -> None:
        catalog, _ = build_tool_catalog(
            {
                "b-provider": make_provider("b-provider", capabilities=("search.academic",)),
                "a-provider": make_provider("a-provider", capabilities=("citation.parse",)),
            },
            {
                "pack-a": make_manifest(tools=(make_tool("tool-a"),), pack_id="pack-a"),
                "pack-b": make_manifest(
                    tools=(make_tool("tool-b", capabilities=("citation.parse",)),),
                    capabilities=("citation.parse",),
                    pack_id="pack-b",
                ),
            },
        )
        resolutions = (
            resolve_capability(catalog, "search.academic", self._allow("search.academic")),
            resolve_capability(catalog, "citation.parse", self._allow("citation.parse")),
        )
        assert freeze_tool_set(resolutions) == ("a-provider", "b-provider")
        assert unresolved_capabilities(resolutions) == ()


class TestHealth:
    def test_failures_open_circuit(self) -> None:
        snapshot = ToolHealthSnapshot()
        for _ in range(5):
            snapshot = record_probe_failure(snapshot, "mcp-lit")
        assert snapshot.provider_health["mcp-lit"] is EndpointHealth.OPEN_CIRCUIT
        assert snapshot.breaker_states["mcp-lit"].is_open

    def test_success_after_open_is_invalid_transition(self) -> None:
        snapshot = ToolHealthSnapshot()
        for _ in range(5):
            snapshot = record_probe_failure(snapshot, "mcp-lit")
        healthy_report = ToolHealthReport(
            provider_id="mcp-lit",
            status=EndpointHealth.HEALTHY,
        )
        with pytest.raises(CircuitBreakerTransitionError):
            record_probe(snapshot, "mcp-lit", healthy_report)

    def test_disabled_marker(self) -> None:
        snapshot = mark_disabled(ToolHealthSnapshot(), "mcp-lit")
        assert snapshot.provider_health["mcp-lit"] is EndpointHealth.DISABLED

    def test_four_failures_stay_closed(self) -> None:
        snapshot = ToolHealthSnapshot()
        for _ in range(4):
            snapshot = record_probe_failure(snapshot, "mcp-lit")
        assert snapshot.provider_health["mcp-lit"] is EndpointHealth.DEGRADED
