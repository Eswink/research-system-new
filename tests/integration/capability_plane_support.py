"""M8 Capability Plane 集成测试共享 fixture（provider/tool/manifest/call）。"""

from __future__ import annotations

from dataclasses import replace

from packages.application.tool_plane import build_tool_catalog
from packages.application.tool_plane.catalog import ToolCatalog
from packages.domain.core import Digest, Version
from packages.domain.enums import (
    EffectClass,
    PolicyDecision,
    ProviderType,
    TrustLevel,
)
from packages.domain.policy import PolicyDefinition, PolicyRule
from packages.domain.tools import (
    SkillSpec,
    ToolCallRecord,
    ToolPackManifest,
    ToolProviderSpec,
    ToolSpec,
    skill_content_digest,
    toolpack_content_digest,
)

MCP_PROVIDER = ToolProviderSpec(
    id="research-mcp-test",
    kind=ProviderType.MCP,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["search.academic", "citation.inspect"],
    effect_class=EffectClass.READ_ONLY,
    transport="streamable_http",
)


def make_call(
    tool_id: str = "lit_search",
    capability: str = "search.academic",
    operation_key: str = "op-1",
) -> ToolCallRecord:
    return ToolCallRecord(
        task_id="task-1",
        attempt=1,
        operation_key=operation_key,
        tool_id=tool_id,
        capability=capability,
        argument_digest=Digest.of_bytes(b"{}"),
    )


def make_skill(
    skill_id: str = "literature_scouting",
    capabilities: tuple[str, ...] = ("search.academic",),
) -> SkillSpec:
    base = SkillSpec(
        id=skill_id,
        version=Version("1.0.0"),
        capabilities=list(capabilities),
        description="scout literature",
    )
    return replace(base, digest=skill_content_digest(base))


def make_tool(tool_id: str = "lit_search") -> ToolSpec:
    return ToolSpec(
        id=tool_id,
        name=tool_id,
        effect_class=EffectClass.READ_ONLY,
        provider_kind=ProviderType.MCP,
        capabilities=["search.academic"],
    )


def make_manifest(tool: ToolSpec | None = None) -> ToolPackManifest:
    placeholder = ToolPackManifest(
        id="lit-pack",
        version=Version("1.0.0"),
        source="fixture://lit-pack",
        resolved_revision="abc123",
        digest=Digest.of_bytes(b"placeholder"),
        license="MIT",
        tools=[tool or make_tool()],
        requested_capabilities=["search.academic"],
    )
    return replace(placeholder, digest=toolpack_content_digest(placeholder))


def make_catalog_with_tool(
    provider: ToolProviderSpec | None = None,
) -> tuple[ToolCatalog, list[str]]:
    return build_tool_catalog(
        {"research-mcp-test": provider or MCP_PROVIDER},
        {"lit-pack": make_manifest()},
    )


def make_deny_policy(capabilities: tuple[str, ...]) -> PolicyDefinition:
    return PolicyDefinition(
        id="project-policy",
        version=Version("0.4.0"),
        default_effect=PolicyDecision.ALLOW,
        deny=tuple(PolicyRule(capability=cap) for cap in capabilities),
    )
