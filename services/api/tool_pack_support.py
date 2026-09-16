"""ToolPack 写面的支持面（GOAL-003 / EC-02）：503 原因、词表、DTO 投影。

集中三件事，避免路由里各写一份：

- **平台 capability 词表**：与离线 bundle validator 同源（`examples/config/capabilities.yaml`），
  运行时用它做写入侧取值域校验。词表读不到 → 503（不降级成"放行"）。
- **内置 pack id**：`examples/contracts/toolpack_*.yaml`（平台自带基线）不可被覆盖。
- **DTO 投影**：pack 记录 → 响应体；生效版本与待批准更新分别呈现，不混成一份。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from packages.application.ports.tool_pack_store import ToolPackRecord
from packages.application.tool_plane.lifecycle import permission_diff
from packages.domain.core import Timestamp
from packages.domain.tools import ToolPackManifest
from services.api.composition import ApiDeps
from services.api.dto.tool_packs import (
    ToolPackDto,
    ToolPackPendingDto,
    ToolPackPermissionDiffDto,
)
from services.api.errors import ApiError

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = "examples/config"
_CONTRACTS_DIR = "examples/contracts"

STORE_UNAVAILABLE_REASON = "ToolPack store 不可用（控制面未装配配置存储）"
POLICY_UNAVAILABLE_REASON = "Policy 求值器不可用（控制面未装配策略面）"
VOCABULARY_UNAVAILABLE_REASON = "capability 词表不可用（examples/config/capabilities.yaml 读不到）"

PACK_NOTE = (
    "install 由控制面重算 manifest 内容 digest 并要求与声明的 digest 相等（pin 与提交内容自洽）；"
    "权限扩张（新增 capability / network domain / credential）不立即生效——登记为待批准更新，"
    "approve-update 后才替换；REVOKE 为终态。生效版本与待批准版本分别呈现。"
)


@dataclass(frozen=True, slots=True)
class CapabilityVocabulary:
    """平台 capability 词表（写入侧取值域）。"""

    names: frozenset[str]

    def unknown(self, candidates: list[str]) -> list[str]:
        return sorted({item for item in candidates if item not in self.names})


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_capability_vocabulary() -> CapabilityVocabulary:
    """读 `examples/config/capabilities.yaml`；读不到/形状不对 → 503（不静默放行）。"""
    path = _ROOT / _CONFIG_DIR / "capabilities.yaml"
    try:
        payload = _read_yaml(path)
    except OSError as exc:
        raise ApiError(
            503, "Capability Vocabulary Unavailable", VOCABULARY_UNAVAILABLE_REASON
        ) from exc
    names = payload.get("capabilities") if isinstance(payload, dict) else None
    if not isinstance(names, list) or not names:
        raise ApiError(503, "Capability Vocabulary Unavailable", VOCABULARY_UNAVAILABLE_REASON)
    return CapabilityVocabulary(names=frozenset(str(item) for item in names))


def builtin_pack_ids() -> frozenset[str]:
    """平台自带 pack id（`examples/contracts/toolpack_*.yaml`）。

    `toolpack_manifest.yaml` 是 manifest 的 schema 规格，不是真实 pack，跳过。
    """
    result: set[str] = set()
    for path in sorted((_ROOT / _CONTRACTS_DIR).glob("toolpack_*.yaml")):
        if path.stem == "toolpack_manifest":
            continue
        payload = _read_yaml(path)
        pack_id = payload.get("id") if isinstance(payload, dict) else None
        if isinstance(pack_id, str) and pack_id:
            result.add(pack_id)
    return frozenset(result)


def pack_store_of(deps: ApiDeps) -> Any:
    store = deps.tool_pack_store
    if store is None:
        raise ApiError(503, "ToolPack Store Unavailable", STORE_UNAVAILABLE_REASON)
    return store


def policy_of(deps: ApiDeps) -> Any:
    evaluator = deps.policy_evaluator
    if evaluator is None:
        raise ApiError(503, "Policy Unavailable", POLICY_UNAVAILABLE_REASON)
    return evaluator


def manifest_capabilities(manifest: ToolPackManifest) -> list[str]:
    """pack 声明的全部 capability（请求集合 ∪ 各 tool 声明的集合）。"""
    declared = set(manifest.requested_capabilities)
    for tool in manifest.tools:
        declared.update(tool.capabilities)
    return sorted(declared)


def iso(value: Timestamp | None) -> str | None:
    return None if value is None else value.value.isoformat()


def diff_dto(diff: Any) -> ToolPackPermissionDiffDto:
    return ToolPackPermissionDiffDto(
        added_capabilities=list(diff.added_capabilities),
        added_network_domains=list(diff.added_network_domains),
        added_credentials=list(diff.added_credentials),
    )


def pack_dto(record: ToolPackRecord, *, catalog_active: bool) -> ToolPackDto:
    """记录 → DTO：生效版本与待批准版本分开呈现（不把 pending 当已生效）。"""
    manifest = record.manifest
    pending = record.pending_manifest
    return ToolPackDto(
        id=record.pack_id,
        state=record.state.value,
        digest=str(manifest.digest),
        version=manifest.version.text,
        source=manifest.source,
        resolved_revision=manifest.resolved_revision,
        license=manifest.license,
        capabilities=manifest_capabilities(manifest),
        network_domains=sorted(set(manifest.network_domains)),
        credential_names=sorted({item.name for item in manifest.credentials}),
        tool_ids=sorted({item.id for item in manifest.tools}),
        installed_at=iso(record.installed_at),
        revoked_reason=record.revoked_reason,
        pending=(
            ToolPackPendingDto(
                digest=str(pending.digest),
                version=pending.version.text,
                capabilities=manifest_capabilities(pending),
                diff=diff_dto(permission_diff(manifest, pending)),
            )
            if pending is not None
            else None
        ),
        catalog_digest_active=catalog_active,
    )
