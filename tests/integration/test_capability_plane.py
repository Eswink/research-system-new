"""M8 Capability Plane 垂直集成（切片/双权限/凭据域）。

安全面测试见 test_capability_plane_security.py；共享 fixture 见
tests/integration/capability_plane_support.py。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from adapters.fakes import (
    FakeArtifactStore,
    FakeCredentialResolver,
    FakePolicyEvaluator,
    FakeToolProvider,
)
from adapters.mcp import McpConnectionSpec, McpToolProvider
from packages.application.policy.native import NativePolicyEvaluator
from packages.application.ports.errors import PermanentPortError
from packages.application.preflight.preflight import run_preflight
from packages.application.protocol_compile import compile_protocol
from packages.application.skill_registry import (
    build_registry,
    capability_union_for_skills,
)
from packages.application.tool_plane import (
    ResolutionInput,
    execute_tool_call,
    freeze_tool_set,
    require_frozen_tool_set,
    resolve_capability,
)
from packages.domain.enums import (
    CredentialScope,
    PolicyDecision,
    ToolResultStatus,
)
from tests.application import protocol_fixtures
from tests.integration.capability_plane_support import (
    MCP_PROVIDER,
    make_call,
    make_catalog_with_tool,
    make_deny_policy,
    make_manifest,
    make_skill,
)


class TestVerticalSlice:
    """Protocol(含 skill) → Compile → Preflight → Resolver → Freeze → Execute。"""

    def test_full_capability_plane_chain(self) -> None:
        # 1) Skill Registry：skill → capability 声明并集（无授权语义）
        registry, errors = build_registry({"literature_scouting": make_skill()})
        assert errors == []
        capabilities, issues = capability_union_for_skills(
            registry, ("literature_scouting",), "agent-1"
        )
        assert capabilities == ("search.academic",)
        assert issues == ()

        # 2) ToolCatalog + ToolResolver：policy(ALLOW) + health → 绑定
        catalog, catalog_errors = make_catalog_with_tool()
        assert catalog_errors == []
        resolution = resolve_capability(
            catalog,
            "search.academic",
            ResolutionInput(policy_decisions={"search.academic": PolicyDecision.ALLOW}),
        )
        assert resolution.provider_ids == ("research-mcp-test",)
        assert resolution.tool_ids == ("lit_search",)
        assert resolution.bindings[0].pack_digest == str(make_manifest().digest)

        # 3) Freeze：Effective Tool Set 确定且可强制
        frozen = freeze_tool_set((resolution,))
        assert frozen == ("research-mcp-test",)
        require_frozen_tool_set(frozen, "research-mcp-test")

        # 4) Execution：execution-time policy 门禁 → ToolProvider
        provider = FakeToolProvider(registered_tools=("lit_search",))
        outcome = execute_tool_call(
            provider,
            MCP_PROVIDER,
            make_call(),
            FakePolicyEvaluator(),
            actor="agent-1",
        )
        assert outcome.result is not None
        assert outcome.result.status is ToolResultStatus.SUCCEEDED


class TestDoubleEnforcement:
    def test_exposure_deny_blocks_before_resolution(self) -> None:
        """exposure-time：preflight check_policy 对 capability 的裁决。"""
        base_catalog = protocol_fixtures.catalog()
        policy = make_deny_policy(("literature.search",))
        catalog = replace(base_catalog, policy=policy)
        context = replace(
            protocol_fixtures.context(catalog),
            policy_evaluator=NativePolicyEvaluator(policy),
        )
        result = compile_protocol(protocol_fixtures.protocol(), catalog, context.project)
        assert result.plan is not None
        report = run_preflight(result.plan, context)
        assert "POLICY_DENIED" in {item.code for item in report.findings}
        assert report.passed is False

    def test_execution_deny_blocks_despite_exposure_allow(self) -> None:
        """execution-time：exposure ALLOW 但 execution 被 DENY → 阻断。"""
        provider = FakeToolProvider(registered_tools=("lit_search",))
        policy = FakePolicyEvaluator()
        policy.set_decision("search.academic", PolicyDecision.DENY)
        with pytest.raises(PermanentPortError) as exc_info:
            execute_tool_call(provider, MCP_PROVIDER, make_call(), policy, actor="agent-1")
        assert "policy denied" in str(exc_info.value)
        assert provider.method_calls("execute") == 0

    def test_policy_input_comes_from_evaluator_not_provider(self) -> None:
        """ToolProvider 不拥有 Policy truth：决策仅来自 PolicyEvaluator。"""
        provider = FakeToolProvider(registered_tools=("lit_search",))
        allow = execute_tool_call(
            provider,
            MCP_PROVIDER,
            make_call(operation_key="op-allow"),
            FakePolicyEvaluator(),
            actor="agent-1",
        )
        assert allow.result is not None
        deny = FakePolicyEvaluator()
        deny.set_decision("search.academic", PolicyDecision.DENY)
        with pytest.raises(PermanentPortError):
            execute_tool_call(
                provider,
                MCP_PROVIDER,
                make_call(operation_key="op-deny"),
                deny,
                actor="agent-1",
            )


class TestResolverFailClosed:
    def test_skill_declared_capability_without_explicit_allow_denied(self) -> None:
        """Skill 声明能力后仍需显式策略 ALLOW；无显式 ALLOW 一律 DENY。"""
        registry, errors = build_registry({"literature_scouting": make_skill()})
        assert errors == []
        capabilities, issues = capability_union_for_skills(
            registry, ("literature_scouting",), "agent-1"
        )
        assert capabilities == ("search.academic",)
        assert issues == ()
        catalog, _ = make_catalog_with_tool()
        resolution = resolve_capability(catalog, "search.academic", ResolutionInput())
        assert resolution.bindings == ()
        assert "no explicit allow" in resolution.findings[0]


class TestCredentialDomainSeparation:
    def test_tool_and_llm_credentials_are_distinct_domains(self) -> None:
        resolver = FakeCredentialResolver({"llm_key": "sk-llm-123", "tool_token": "tool-456"})
        assert resolver.resolve("llm_key").value == "sk-llm-123"
        assert resolver.resolve("tool_token").value == "tool-456"
        domains = {
            CredentialScope.LLM,
            CredentialScope.TOOL,
            CredentialScope.WORKSPACE,
            CredentialScope.USER_OAUTH,
        }
        assert len(domains) == 4

    def test_http_transport_requires_tool_domain_ref(self) -> None:
        """streamable_http 必须声明 TOOL 域 credential_ref（无默认 LLM 凭据）。"""
        with pytest.raises(ValueError, match="credential_ref"):
            McpToolProvider(
                McpConnectionSpec(transport="streamable_http", url="http://127.0.0.1:1/mcp"),
                artifact_store=FakeArtifactStore(),
            )

    def test_denied_tool_ref_fails_without_leaking_llm_secret(self) -> None:
        resolver = FakeCredentialResolver({"llm_key": "sk-llm-123"})
        resolver.deny_scope("tool_token")
        provider = McpToolProvider(
            McpConnectionSpec(transport="streamable_http", url="http://127.0.0.1:1/mcp"),
            credentials=resolver,
            credential_ref="tool_token",
            artifact_store=FakeArtifactStore(),
        )
        with pytest.raises(PermanentPortError):
            provider.execute(MCP_PROVIDER, make_call())
        assert all("sk-llm-123" not in call.args_summary for call in resolver.calls)
