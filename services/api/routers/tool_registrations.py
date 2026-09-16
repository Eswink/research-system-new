"""Tool Provider 注册/治理写面（G15 / PLAN-20260915-060 WP-B，EC-05）。

供应链治理面在控制面的可写投影：

    POST   /tool-provider-registrations                    → 登记（PENDING）
    PATCH  /tool-provider-registrations/{provider_id}      → 更新（re-pin/能力等）
    POST   /tool-provider-registrations/{provider_id}/approve      → PENDING → ACTIVE
    POST   /tool-provider-registrations/{provider_id}/revoke       → 任意非终态 → REVOKED
    POST   /tool-provider-registrations/{provider_id}/health-check → 写入一次健康事实

**被消费**：APPROVE 后 `merged_catalog_snapshot` 把该 provider 与其 pin 的
digest 合入目录，于是 compile 的 `provider_ids`、preflight 的工具可用性与
供应链 pin 检查、`GET /tool-providers`、会话 tool set 冻结都随之改变；
PENDING/REVOKED 不进入目录（未批准不可用、吊销即退出）。

诚实边界：注册表未装配 → 503；未知 id → 404；非法枚举/非法 pin（非
`sha256:<hex>`）/空 capabilities → 422；重复登记、对终态再处置、批准已批准项
→ 409；内置目录已占用的 id 拒绝注册（不影子覆盖平台自己的 provider）。
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Request

from packages.application.ports.tool_provider_registry import ToolProviderRegistry
from packages.domain.core import Timestamp
from packages.domain.state_base import InvalidTransitionError
from packages.domain.tool_registry import ProviderRegistration
from services.api.catalog import load_catalog_snapshot
from services.api.deps import get_deps
from services.api.dto.tool_providers import (
    ToolProviderRegisterDto,
    ToolProviderRegistrationDto,
    ToolProviderRegistrationListDto,
    ToolProviderRevokeDto,
    ToolProviderUpdateDto,
)
from services.api.errors import ApiError
from services.api.preflight_support import probe_provider_spec
from services.api.tool_registry_support import (
    REGISTRATION_NOTE,
    REGISTRY_UNAVAILABLE_REASON,
    effect_class,
    provider_kind,
    registration_dto,
    registry_of,
)

router = APIRouter(tags=["tool-providers"])


def _existing(registry: ToolProviderRegistry, provider_id: str) -> ProviderRegistration | None:
    try:
        return registry.get_registration(provider_id)
    except KeyError:
        return None


@router.get("/tool-provider-registrations", response_model=ToolProviderRegistrationListDto)
async def list_registrations(request: Request) -> ToolProviderRegistrationListDto:
    """全部注册（含 PENDING/REVOKED）；注册表未装配 → 200 + 显式不可用原因。"""
    deps = get_deps(request)
    registry = deps.tool_provider_registry
    if registry is None:
        return ToolProviderRegistrationListDto(
            registrations=[],
            management_available=False,
            management_reason=REGISTRY_UNAVAILABLE_REASON,
            note=REGISTRATION_NOTE,
        )
    return ToolProviderRegistrationListDto(
        registrations=[
            registration_dto(item, credentials=deps.credentials)
            for item in registry.list_registrations()
        ],
        management_available=True,
        management_reason=None,
        note=REGISTRATION_NOTE,
    )


@router.post(
    "/tool-provider-registrations",
    response_model=ToolProviderRegistrationDto,
    status_code=201,
)
async def register_provider(
    payload: ToolProviderRegisterDto, request: Request
) -> ToolProviderRegistrationDto:
    """登记 provider（初始 PENDING，需 approve 才进入目录）。"""
    deps = get_deps(request)
    registry = registry_of(deps)
    if _existing(registry, payload.id) is not None:
        raise ApiError(409, "Provider Already Registered", f"registration exists: {payload.id}")
    if payload.id in load_catalog_snapshot().tool_providers:
        raise ApiError(
            409,
            "Provider Id Reserved",
            f"provider id is defined by the built-in catalog: {payload.id}",
        )
    now = Timestamp.now()
    try:
        registration = ProviderRegistration(
            id=payload.id,
            kind=provider_kind(payload.kind),
            capabilities=list(payload.capabilities),
            effect_class=effect_class(payload.effect_class),
            pinned_revision=payload.pinned_revision,
            transport=payload.transport,
            protocol_version=payload.protocol_version,
            network_domains=list(payload.network_domains),
            health_check=payload.health_check,
            endpoint_env=payload.endpoint_env,
            credential_ref=payload.credential_ref,
            registered_at=now,
            updated_at=now,
        )
    except ValueError as exc:
        raise ApiError(422, "Invalid Registration", str(exc)) from exc
    registry.save_registration(registration)
    return registration_dto(registration, credentials=deps.credentials)


@router.patch(
    "/tool-provider-registrations/{provider_id}", response_model=ToolProviderRegistrationDto
)
async def update_registration(
    provider_id: str, payload: ToolProviderUpdateDto, request: Request
) -> ToolProviderRegistrationDto:
    """更新可变字段（re-pin / 能力 / 传输等）；已吊销 → 409。"""
    deps = get_deps(request)
    registry = registry_of(deps)
    current = _require_registration(registry, provider_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        raise ApiError(422, "Empty Patch", "patch must change at least one field")
    if "effect_class" in changes:
        changes["effect_class"] = effect_class(str(changes["effect_class"]))
    try:
        updated = current.updated(changes, now=Timestamp.now())
    except InvalidTransitionError as exc:
        raise ApiError(
            409, "Provider Revoked", f"registration {provider_id} is revoked (terminal)"
        ) from exc
    except ValueError as exc:
        raise ApiError(422, "Invalid Registration", str(exc)) from exc
    registry.save_registration(updated)
    return registration_dto(updated, credentials=deps.credentials)


@router.post(
    "/tool-provider-registrations/{provider_id}/approve",
    response_model=ToolProviderRegistrationDto,
)
async def approve_registration(provider_id: str, request: Request) -> ToolProviderRegistrationDto:
    """批准（PENDING → ACTIVE）：此后该 provider 进入目录，preflight 立即可见。"""
    return _transition(
        request,
        provider_id,
        lambda current, now: current.approve(now=now),
        conflict="Provider Not Pending",
        detail=f"registration {provider_id} is not in PENDING state",
    )


@router.post(
    "/tool-provider-registrations/{provider_id}/revoke", response_model=ToolProviderRegistrationDto
)
async def revoke_registration(
    provider_id: str, payload: ToolProviderRevokeDto, request: Request
) -> ToolProviderRegistrationDto:
    """吊销（终态）：退出目录；原因必填并留痕。"""
    return _transition(
        request,
        provider_id,
        lambda current, now: current.revoke(payload.reason, now=now),
        conflict="Provider Revoked",
        detail=f"registration {provider_id} is already revoked",
    )


@router.post(
    "/tool-provider-registrations/{provider_id}/health-check",
    response_model=ToolProviderRegistrationDto,
)
async def health_check_registration(
    provider_id: str, request: Request
) -> ToolProviderRegistrationDto:
    """复核健康并把事实写回注册（读面 `GET /tool-providers` 随后看到同一结论）。

    同时记下提供方这次声明的 schema 指纹：健康面只看三态是不够的，
    供应链面关心"对方的能力面还是不是当初那个"（漂移与否见 RECHECK-069）。
    """
    deps = get_deps(request)
    registry = registry_of(deps)
    current = _require_registration(registry, provider_id)
    probe = probe_provider_spec(deps, current.spec())
    checked = current.record_health(
        probe.status,
        detail=probe.detail,
        now=Timestamp.now(),
        observed_schema_digest=probe.observed_schema_digest,
    )
    registry.save_registration(checked)
    return registration_dto(checked, credentials=deps.credentials)


def _require_registration(registry: ToolProviderRegistry, provider_id: str) -> ProviderRegistration:
    found = _existing(registry, provider_id)
    if found is None:
        raise ApiError(
            404, "Provider Registration Not Found", f"registration not found: {provider_id}"
        )
    return found


def _transition(
    request: Request,
    provider_id: str,
    apply: Callable[[ProviderRegistration, Timestamp], ProviderRegistration],
    *,
    conflict: str,
    detail: str,
) -> ToolProviderRegistrationDto:
    deps = get_deps(request)
    registry = registry_of(deps)
    current = _require_registration(registry, provider_id)
    try:
        updated = apply(current, Timestamp.now())
    except InvalidTransitionError as exc:
        raise ApiError(409, conflict, detail) from exc
    except ValueError as exc:
        raise ApiError(422, "Invalid Transition", str(exc)) from exc
    registry.save_registration(updated)
    return registration_dto(updated, credentials=deps.credentials)
