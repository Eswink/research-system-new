"""M8 Tool Plane 测试共享 fixture（provider/tool/manifest/call 构造器）。"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from packages.domain.core import Digest, Version
from packages.domain.enums import EffectClass, ProviderType, TrustLevel
from packages.domain.tools import (
    CredentialRequirement,
    ToolCallRecord,
    ToolPackManifest,
    ToolProviderSpec,
    ToolSpec,
    toolpack_content_digest,
)

NOW = datetime(2026, 8, 14, 10, 0, 0, tzinfo=timezone.utc)


def make_provider(
    provider_id: str = "mcp-lit",
    *,
    capabilities: tuple[str, ...] = ("search.academic",),
    trust: TrustLevel = TrustLevel.VERIFIED,
    effect: EffectClass = EffectClass.NETWORK,
) -> ToolProviderSpec:
    return ToolProviderSpec(
        id=provider_id,
        kind=ProviderType.MCP,
        trust_level=trust,
        capabilities=list(capabilities),
        effect_class=effect,
    )


def make_tool(
    tool_id: str = "lit_search",
    *,
    capabilities: tuple[str, ...] = ("search.academic",),
    effect: EffectClass = EffectClass.NETWORK,
) -> ToolSpec:
    return ToolSpec(
        id=tool_id,
        name=tool_id,
        effect_class=effect,
        provider_kind=ProviderType.MCP,
        capabilities=list(capabilities),
    )


def make_manifest(
    *,
    tools: tuple[ToolSpec, ...] = (),
    capabilities: tuple[str, ...] = ("search.academic",),
    credentials: tuple[CredentialRequirement, ...] = (),
    pack_id: str = "lit-pack",
) -> ToolPackManifest:
    placeholder = ToolPackManifest(
        id=pack_id,
        version=Version("1.0.0"),
        source="fixture://lit-pack",
        resolved_revision="abc123",
        digest=Digest.of_bytes(b"placeholder"),
        license="MIT",
        tools=list(tools),
        requested_capabilities=list(capabilities),
        credentials=list(credentials),
    )
    return replace(placeholder, digest=toolpack_content_digest(placeholder))


def make_call(
    *,
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
