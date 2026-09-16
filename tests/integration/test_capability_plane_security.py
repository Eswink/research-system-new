"""M8 Capability Plane 安全验证：supply-chain pin / frozen set / 大结果 / schema 漂移 / Skill 权限。

切片与双权限测试见 test_capability_plane.py；共享 fixture 见
tests/integration/capability_plane_support.py。
"""

from __future__ import annotations

import sys
from dataclasses import replace

import pytest

from adapters.fakes import (
    FakeArtifactStore,
    FakeEventPublisher,
    FakePolicyEvaluator,
    FakeToolPackStore,
)
from adapters.mcp import McpConnectionSpec, McpToolProvider
from packages.application.ports.errors import PermanentPortError
from packages.application.preflight.preflight import run_preflight
from packages.application.protocol_compile import compile_protocol
from packages.application.skill_registry import (
    build_registry,
    capability_union_for_skills,
)
from packages.application.tool_plane import (
    ResolutionInput,
    ToolPackLifecycle,
    freeze_tool_set,
    require_frozen_tool_set,
    resolve_capability,
    spill_large_result,
)
from packages.application.tool_plane.results import fetch_spilled_result
from packages.domain.enums import (
    EffectClass,
    PolicyDecision,
    ProviderType,
    ToolResultStatus,
    TrustLevel,
)
from packages.domain.serialization import canonical_json_bytes
from packages.domain.tools import CapabilityGrant, ToolProviderSpec
from tests.application import protocol_fixtures
from tests.integration.capability_plane_support import (
    MCP_PROVIDER,
    make_call,
    make_catalog_with_tool,
    make_manifest,
    make_skill,
)
from tests.mcp_server.server import FAULT_BIG, FAULT_NONE, FAULT_SCHEMA


class TestSupplyChainPin:
    def test_tampered_manifest_digest_rejected_at_install(self) -> None:
        lifecycle = ToolPackLifecycle(
            FakeToolPackStore(),
            FakePolicyEvaluator(),
            FakeEventPublisher(),
        )
        manifest = make_manifest()
        tampered = replace(manifest, network_domains=["evil.example.com"])
        with pytest.raises(PermanentPortError, match="digest mismatch"):
            lifecycle.submit(tampered)

    def test_pinned_digest_satisfies_preflight(self) -> None:
        base = protocol_fixtures.catalog()
        provider = ToolProviderSpec(
            id="mcp-tools",
            kind=ProviderType.MCP,
            trust_level=TrustLevel.VERIFIED,
            capabilities=["literature.search"],
            effect_class=EffectClass.READ_ONLY,
        )
        catalog = replace(
            base,
            tool_providers={"mcp-tools": provider},
            tool_pack_digests={"mcp-tools": "sha256:" + "0" * 64},
        )
        context = protocol_fixtures.context(catalog)
        result = compile_protocol(protocol_fixtures.protocol(), catalog, context.project)
        assert result.plan is not None
        report = run_preflight(result.plan, context)
        assert "SUPPLY_CHAIN_UNPINNED" not in {item.code for item in report.findings}


class TestFrozenToolSet:
    def test_provider_outside_frozen_set_rejected(self) -> None:
        with pytest.raises(PermanentPortError, match="frozen tool set"):
            require_frozen_tool_set(("allowed-provider",), "intruder-provider")

    def test_frozen_set_is_deterministic(self) -> None:
        catalog, _ = make_catalog_with_tool()
        allow = ResolutionInput(policy_decisions={"search.academic": PolicyDecision.ALLOW})
        first = resolve_capability(catalog, "search.academic", allow)
        second = resolve_capability(catalog, "search.academic", allow)
        assert freeze_tool_set((first,)) == freeze_tool_set((second,)) == ("research-mcp-test",)


class TestLargeResultIndirection:
    def test_spill_roundtrip_never_enters_domain_json(self) -> None:
        store = FakeArtifactStore()
        payload = b"z" * 8192
        outcome = spill_large_result(store, make_call(), payload, threshold_bytes=1024)
        assert outcome.spilled is True
        encoded = canonical_json_bytes(outcome.record).decode("utf-8")
        assert "z" * 64 not in encoded
        assert len(encoded) < 1024
        fetched = fetch_spilled_result(store, outcome.record)
        assert fetched == payload

    def test_mcp_big_result_spills_via_adapter(self) -> None:
        """真实 MCP stdio 链路：大结果自动溢出到 ArtifactStore。"""
        store = FakeArtifactStore()
        provider = McpToolProvider(
            McpConnectionSpec(
                transport="stdio",
                command=(sys.executable, "-B", "-m", "tests.mcp_server.run_stdio", FAULT_BIG),
                timeout_seconds=30.0,
            ),
            artifact_store=store,
            spill_threshold_bytes=1024,
        )
        result = provider.execute(MCP_PROVIDER, make_call("big_tool", operation_key="big"))
        assert result.status is ToolResultStatus.SUCCEEDED
        assert result.output_digest is not None
        fetched = fetch_spilled_result(store, result)
        assert fetched is not None and len(fetched) > 4096


class TestSchemaHashDrift:
    def test_health_schema_digest_differs_after_server_schema_change(self) -> None:
        """health probe 的 schema digest 是漂移检测数据面。"""
        baseline_provider = McpToolProvider(
            McpConnectionSpec(
                transport="stdio",
                command=(sys.executable, "-B", "-m", "tests.mcp_server.run_stdio", FAULT_NONE),
                timeout_seconds=30.0,
            ),
            artifact_store=FakeArtifactStore(),
        )
        drifted_provider = McpToolProvider(
            McpConnectionSpec(
                transport="stdio",
                command=(sys.executable, "-B", "-m", "tests.mcp_server.run_stdio", FAULT_SCHEMA),
                timeout_seconds=30.0,
            ),
            artifact_store=FakeArtifactStore(),
        )
        baseline = baseline_provider.check_health(MCP_PROVIDER)
        drifted = drifted_provider.check_health(MCP_PROVIDER)
        assert baseline.status.value == "HEALTHY"
        assert baseline.observed_schema_digest != drifted.observed_schema_digest


class TestSkillCannotGrantPermissions:
    def test_skill_declared_capability_outside_role_denied(self) -> None:
        """Skill 只声明所需 capability；超出 role 能力面必须被 preflight 拒绝。"""
        base = protocol_fixtures.catalog()
        skill = make_skill(capabilities=("admin.evil",))
        agent = replace(base.agents["agent-1"], skill_refs=["evil_skill"])
        catalog = replace(
            base,
            agents={"agent-1": agent},
            skills={"evil_skill": skill},
        )
        context = protocol_fixtures.context(catalog)
        result = compile_protocol(protocol_fixtures.protocol(), catalog, context.project)
        assert result.plan is not None
        report = run_preflight(result.plan, context)
        assert "AGENT_PERMISSION_DENIED" in {item.code for item in report.findings}

    def test_skill_routing_does_not_produce_grants(self) -> None:
        registry, _ = build_registry({"scout": make_skill("scout")})
        capabilities, _ = capability_union_for_skills(registry, ("scout",), "agent-1")
        assert not isinstance(capabilities, CapabilityGrant)
        assert capabilities == ("search.academic",)
