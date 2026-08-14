"""M8 Tool Plane Domain 增量测试。

覆盖：classify_risk 分层、skill/toolpack 内容 digest、ToolHealthReport、
CredentialScope 类型化、SkillStatus 默认生命周期（docs/architecture/TOOL_RUNTIME.md、
docs/architecture/CAPABILITY_SECURITY.md §4、docs/security/PLUGIN_TOOL_SUPPLY_CHAIN.md）。
"""

from __future__ import annotations

import dataclasses

import pytest

from packages.domain.core import Digest, Version
from packages.domain.enums import (
    CredentialScope,
    EffectClass,
    EndpointHealth,
    ProviderType,
    RiskClass,
    SkillStatus,
    ToolCallStatus,
    ToolResultStatus,
    TrustLevel,
)
from packages.domain.tools import (
    CredentialRequirement,
    SkillSpec,
    ToolHealthReport,
    ToolPackManifest,
    ToolSpec,
    classify_risk,
    skill_content_digest,
    toolpack_content_digest,
)


class TestClassifyRisk:
    def test_untrusted_always_critical(self) -> None:
        assert classify_risk(EffectClass.READ_ONLY, TrustLevel.UNTRUSTED) is RiskClass.CRITICAL
        assert classify_risk(EffectClass.READ_ONLY, TrustLevel.REVOKED) is RiskClass.CRITICAL

    def test_destructive_and_publish_critical(self) -> None:
        assert classify_risk(EffectClass.DESTRUCTIVE, TrustLevel.VERIFIED) is RiskClass.CRITICAL
        assert (
            classify_risk(EffectClass.EXTERNAL_PUBLISH, TrustLevel.VERIFIED) is RiskClass.CRITICAL
        )

    def test_secret_and_execute_high(self) -> None:
        assert classify_risk(EffectClass.SECRET_USE, TrustLevel.VERIFIED) is RiskClass.HIGH
        assert classify_risk(EffectClass.EXECUTE, TrustLevel.VERIFIED) is RiskClass.HIGH

    def test_write_and_network_medium(self) -> None:
        assert classify_risk(EffectClass.WRITE, TrustLevel.VERIFIED) is RiskClass.MEDIUM
        assert classify_risk(EffectClass.NETWORK, TrustLevel.VERIFIED) is RiskClass.MEDIUM

    def test_read_only_low_for_verified(self) -> None:
        assert classify_risk(EffectClass.READ_ONLY, TrustLevel.BUILT_IN) is RiskClass.LOW
        assert classify_risk(EffectClass.READ_ONLY, TrustLevel.VERIFIED) is RiskClass.LOW

    def test_read_only_medium_for_user_approved(self) -> None:
        assert classify_risk(EffectClass.READ_ONLY, TrustLevel.USER_APPROVED) is RiskClass.MEDIUM


class TestSkillDigest:
    def _skill(
        self,
        *,
        capabilities: list[str] | None = None,
        description: str | None = None,
    ) -> SkillSpec:
        return SkillSpec(
            id="literature_scouting",
            version=Version("1.2.0"),
            capabilities=capabilities or ["search.academic", "citation.parse"],
            description="scout literature" if description is None else description,
        )

    def test_digest_deterministic_and_field_insensitive_order(self) -> None:
        first = self._skill(capabilities=["search.academic", "citation.parse"])
        second = self._skill(capabilities=["citation.parse", "search.academic"])
        assert skill_content_digest(first) == skill_content_digest(second)

    def test_digest_changes_with_content(self) -> None:
        base = skill_content_digest(self._skill())
        changed = skill_content_digest(self._skill(description="changed"))
        assert base != changed

    def test_digest_field_not_part_of_content(self) -> None:
        spec = self._skill()
        with_digest = SkillSpec(
            id=spec.id,
            version=spec.version,
            capabilities=spec.capabilities,
            description=spec.description,
            digest=Digest.of_bytes(b"x"),
        )
        assert skill_content_digest(spec) == skill_content_digest(with_digest)

    def test_default_status_active(self) -> None:
        assert self._skill().status is SkillStatus.ACTIVE


def _placeholder_manifest() -> ToolPackManifest:
    tool = ToolSpec(
        id="lit_search",
        name="lit_search",
        effect_class=EffectClass.NETWORK,
        provider_kind=ProviderType.MCP,
        capabilities=["search.academic"],
    )
    skill = SkillSpec(
        id="scouting",
        version=Version("1.0.0"),
        capabilities=["search.academic"],
    )
    return ToolPackManifest(
        id="literature-pack",
        version=Version("1.0.0"),
        source="fixture://literature-pack",
        resolved_revision="abc123",
        digest=Digest.of_bytes(b"placeholder"),
        license="MIT",
        tools=[tool],
        skills=[skill],
    )


class TestToolPackDigest:
    def test_verify_content_digest_ok(self) -> None:
        manifest = _placeholder_manifest()
        correct = toolpack_content_digest(manifest)
        verified = dataclasses.replace(manifest, digest=correct)
        assert verified.verify_content_digest() is True

    def test_verify_content_digest_detects_tamper(self) -> None:
        manifest = _placeholder_manifest()
        correct = toolpack_content_digest(manifest)
        tampered = dataclasses.replace(
            manifest,
            digest=correct,
            requested_capabilities=["extra.evil"],
        )
        assert tampered.verify_content_digest() is False

    def test_network_domains_participate_in_digest(self) -> None:
        manifest = _placeholder_manifest()
        changed = dataclasses.replace(manifest, network_domains=["evil.example.com"])
        assert toolpack_content_digest(manifest) != toolpack_content_digest(changed)


class TestToolHealthReport:
    def test_requires_provider_id(self) -> None:
        with pytest.raises(ValueError):
            ToolHealthReport(provider_id="", status=EndpointHealth.HEALTHY)

    def test_holds_schema_digest(self) -> None:
        digest = Digest.of_bytes(b"schema")
        report = ToolHealthReport(
            provider_id="p1",
            status=EndpointHealth.HEALTHY,
            observed_schema_digest=digest,
        )
        assert report.observed_schema_digest == digest


class TestCredentialRequirement:
    def test_scope_typed(self) -> None:
        requirement = CredentialRequirement(name="MCP_TOKEN", scope=CredentialScope.TOOL)
        assert requirement.scope is CredentialScope.TOOL

    def test_scopes_are_distinct_domains(self) -> None:
        domains = {
            CredentialScope.LLM,
            CredentialScope.TOOL,
            CredentialScope.WORKSPACE,
            CredentialScope.USER_OAUTH,
        }
        assert len(domains) == 4


class TestStatusEnums:
    def test_tool_call_status_values(self) -> None:
        assert {status.value for status in ToolCallStatus} == {
            "REQUESTED",
            "IN_FLIGHT",
            "SUCCEEDED",
            "FAILED",
            "CANCELLED",
        }

    def test_tool_result_status_values(self) -> None:
        assert {status.value for status in ToolResultStatus} == {
            "SUCCEEDED",
            "FAILED",
            "TIMED_OUT",
            "CANCELLED",
        }
