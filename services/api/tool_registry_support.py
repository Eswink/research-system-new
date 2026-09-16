"""Tool Provider 注册面的 DTO 投影与枚举解析（PLAN-20260915-060）。

路由只做 HTTP 语义（状态码、幂等、404/409），枚举与投影在这里集中，避免
"同一份注册在列表与单条返回里长得不一样"。
"""

from __future__ import annotations

from packages.application.ports.tool_provider_registry import ToolProviderRegistry
from packages.domain.core import Timestamp
from packages.domain.enums import EffectClass, ProviderType
from packages.domain.tool_registry import ProviderRegistration
from services.api.composition import ApiDeps
from services.api.dto.tool_providers import ToolProviderRegistrationDto
from services.api.errors import ApiError

REGISTRY_UNAVAILABLE_REASON = "Tool Provider 注册表不可用（控制面未装配配置存储）"

REGISTRATION_NOTE = (
    "PENDING 只表示已登记，不进入 tool_providers 目录；APPROVE 后以 USER_APPROVED "
    "进入目录（preflight/compile 立即可见），REVOKE 为终态退出。信任级别由状态推导，"
    "注册方无法声明 BUILT_IN/VERIFIED；pin 必须是 sha256:<hex> 内容寻址 digest。"
)


def registry_of(deps: ApiDeps) -> ToolProviderRegistry:
    """取注册表（未装配 → 503，不伪造成功）。"""
    registry = deps.tool_provider_registry
    if registry is None:
        raise ApiError(503, "Tool Provider Registry Unavailable", REGISTRY_UNAVAILABLE_REASON)
    return registry


def provider_kind(raw: str) -> ProviderType:
    try:
        return ProviderType(raw)
    except ValueError as exc:
        raise ApiError(422, "Invalid Provider Kind", f"unknown provider kind: {raw!r}") from exc


def effect_class(raw: str) -> EffectClass:
    try:
        return EffectClass(raw)
    except ValueError as exc:
        raise ApiError(422, "Invalid Effect Class", f"unknown effect class: {raw!r}") from exc


def iso(value: Timestamp | None) -> str | None:
    return None if value is None else value.value.isoformat()


def registration_dto(registration: ProviderRegistration) -> ToolProviderRegistrationDto:
    """注册实体 → DTO（健康事实直接取实体上的最近一次探测，不另开参数）。"""
    return ToolProviderRegistrationDto(
        id=registration.id,
        kind=registration.kind.value,
        state=registration.state,
        trust_level=registration.trust_level.value,
        capabilities=sorted(set(registration.capabilities)),
        effect_class=registration.effect_class.value,
        pinned_revision=registration.pinned_revision,
        transport=registration.transport,
        protocol_version=registration.protocol_version,
        network_domains=sorted(set(registration.network_domains)),
        health_check=registration.health_check,
        registered_at=iso(registration.registered_at),
        updated_at=iso(registration.updated_at),
        approved_at=iso(registration.approved_at),
        revoked_at=iso(registration.revoked_at),
        revoked_reason=registration.revoked_reason,
        last_health=registration.last_health,
        health_detail=registration.health_detail,
        health_checked_at=iso(registration.health_checked_at),
        last_schema_digest=registration.last_schema_digest,
        schema_baseline_digest=registration.schema_baseline_digest,
        schema_drift=registration.schema_drift,
        schema_drift_since=iso(registration.schema_drift_since),
        catalog_active=registration.active,
    )
