"""ToolCatalog 只读索引：providers / packs / tools 的确定性查询视图。

输入是已通过 install 门禁的 ToolPack 与 ToolProvider 注册；
本模块不做 digest 校验（lifecycle 负责），只做结构完整性检查。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from packages.application.ports.tool_pack_store import ToolPackRecord
from packages.domain.enums import ToolPackState, TrustLevel
from packages.domain.tools import ToolPackManifest, ToolProviderSpec, ToolSpec

_TRUST_RANK: dict[TrustLevel, int] = {
    TrustLevel.BUILT_IN: 0,
    TrustLevel.VERIFIED: 1,
    TrustLevel.USER_APPROVED: 2,
    TrustLevel.UNTRUSTED: 3,
    TrustLevel.REVOKED: 4,
}


@dataclass(frozen=True, slots=True)
class ToolCatalog:
    providers: Mapping[str, ToolProviderSpec] = field(default_factory=dict)
    packs: Mapping[str, ToolPackManifest] = field(default_factory=dict)
    tools: Mapping[str, ToolSpec] = field(default_factory=dict)
    pack_of_tool: Mapping[str, str] = field(default_factory=dict)

    def providers_by_capability(self, capability: str) -> tuple[ToolProviderSpec, ...]:
        return tuple(
            sorted(
                (
                    provider
                    for provider in self.providers.values()
                    if capability in provider.capabilities
                ),
                key=provider_preference_key,
            )
        )

    def tools_by_capability(self, capability: str) -> tuple[ToolSpec, ...]:
        return tuple(
            sorted(
                (tool for tool in self.tools.values() if capability in tool.capabilities),
                key=lambda tool: tool.id,
            )
        )

    def tools_for_provider(self, provider: ToolProviderSpec) -> tuple[ToolSpec, ...]:
        return tuple(
            sorted(
                (tool for tool in self.tools.values() if tool.provider_kind is provider.kind),
                key=lambda tool: tool.id,
            )
        )

    def pack_digest_for_tool(self, tool_id: str) -> str | None:
        pack_id = self.pack_of_tool.get(tool_id)
        if pack_id is None:
            return None
        pack = self.packs.get(pack_id)
        return str(pack.digest) if pack is not None else None


def provider_preference_key(provider: ToolProviderSpec) -> tuple[int, str]:
    """确定性偏好：信任级别优先，同级按 id 排序。"""
    return (_TRUST_RANK[provider.trust_level], provider.id)


def build_tool_catalog(
    providers: Mapping[str, ToolProviderSpec],
    packs: Mapping[str, ToolPackManifest],
) -> tuple[ToolCatalog, list[str]]:
    """聚合 providers 与 packs 为索引；返回 (catalog, 结构错误列表)。"""
    errors: list[str] = []
    tools: dict[str, ToolSpec] = {}
    pack_of_tool: dict[str, str] = {}
    for pack_id, pack in packs.items():
        if pack_id != pack.id:
            errors.append(f"pack key {pack_id!r} does not match manifest id {pack.id!r}")
        for tool in pack.tools:
            if tool.id in tools:
                errors.append(f"duplicate tool id across packs: {tool.id}")
                continue
            tools[tool.id] = tool
            pack_of_tool[tool.id] = pack_id
    catalog = ToolCatalog(
        providers=dict(providers),
        packs=dict(packs),
        tools=tools,
        pack_of_tool=pack_of_tool,
    )
    return catalog, errors


def catalog_from_pack_records(
    providers: Mapping[str, ToolProviderSpec],
    records: Mapping[str, ToolPackRecord],
) -> tuple[ToolCatalog, list[str]]:
    """从 ToolPackStore snapshot 构建索引（跳过 REVOKED pack）。"""
    packs = {
        pack_id: record.manifest
        for pack_id, record in records.items()
        if record.state is not ToolPackState.REVOKED
    }
    return build_tool_catalog(providers, packs)


def catalog_snapshot_dict(catalog: ToolCatalog) -> dict[str, object]:
    """确定性序列化视图（供 digest / 冻结记录）。"""
    return {
        "providers": sorted(catalog.providers),
        "packs": sorted(catalog.packs),
        "tools": sorted(catalog.tools),
    }
