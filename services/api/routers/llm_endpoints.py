"""LLM Endpoint 控制面路由（CONTROL_PLANE_API.md Models 节）。

流程：HTTP → DTO → use case（model_relay）→ Domain / Port。
密钥纪律：api_key 只在创建/更新入口接收并进入 Credential boundary
（RegistryCredentialResolver.register），任何响应/日志/错误不回显。
映射集中在 services.api.mappers（禁止 __dict__ dump）。
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response

from packages.application.model_relay.probe import run_endpoint_test
from packages.application.ports.credential_resolver import CredentialResolver
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import ID
from packages.domain.models import (
    EndpointDiscoveryConfig,
    EndpointProbeSnapshot,
    LLMEndpoint,
    ModelDefinition,
)
from services.api.composition import ApiDeps
from services.api.deps import get_deps, require_if_match
from services.api.dto.endpoints import (
    DiscoverModelsResultDto,
    DiscoveryConfigDto,
    EndpointHealthDto,
    EndpointTestRequestDto,
    EndpointTestResultDto,
    LlmEndpointCreateDto,
    LlmEndpointReadDto,
    LlmEndpointUpdateDto,
)
from services.api.errors import ApiError
from services.api.mappers.endpoints import endpoint_or_404, endpoint_read_dto, endpoint_version

router = APIRouter(prefix="/llm-endpoints", tags=["llm-endpoints"])


def _credential_ref(endpoint_id: str) -> str:
    return f"endpoint:{endpoint_id}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _register_key(deps: ApiDeps, endpoint_id: str, credential_ref: str, api_key: str) -> None:
    """api_key 只进入 Credential boundary；失败时回滚 endpoint 创建。"""
    resolver = deps.credentials
    if not isinstance(resolver, CredentialResolver):
        raise ApiError(500, "Credential Store Unavailable", "credential resolver unavailable")
    register = getattr(resolver, "register", None)
    if not callable(register):
        raise ApiError(500, "Credential Store Unavailable", "credential resolver cannot register")
    try:
        register(credential_ref, api_key)
    except InvalidInputError as exc:
        try:
            deps.endpoint_store.delete_endpoint(endpoint_id)
        except KeyError:
            pass
        raise ApiError(422, "Invalid Credential", str(exc)) from exc


def _model_for_endpoint(deps: ApiDeps, model_id: str, endpoint_id: str) -> ModelDefinition:
    try:
        model = deps.model_store.get_model(model_id)
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"model not found: {model_id}") from exc
    if model.endpoint_id != endpoint_id:
        raise ApiError(
            422,
            "Model Not On Endpoint",
            f"model {model_id} is not configured on endpoint {endpoint_id}",
        )
    return model


def _discovery_from_dto(discovery: DiscoveryConfigDto | None) -> EndpointDiscoveryConfig | None:
    if discovery is None:
        return None
    return EndpointDiscoveryConfig(
        enabled=discovery.enabled,
        allow_models=tuple(discovery.allow_models),
    )


@router.post("", status_code=201, response_model=LlmEndpointReadDto)
async def create_endpoint(
    payload: LlmEndpointCreateDto,
    request: Request,
    response: Response,
) -> LlmEndpointReadDto:
    deps: ApiDeps = get_deps(request)
    endpoint_id = ID.generate().value
    credential_ref = _credential_ref(endpoint_id)
    endpoint = LLMEndpoint(
        id=endpoint_id,
        name=payload.name,
        protocol=payload.protocol,
        base_url=payload.base_url,
        credential_ref=credential_ref,
        enabled=payload.enabled,
        request_timeout_seconds=payload.request_timeout_seconds,
        max_retries=payload.max_retries,
        concurrency_limit=payload.concurrency_limit,
        api_style=payload.api_style,
        discovery=_discovery_from_dto(payload.discovery),
    )
    deps.endpoint_store.save_endpoint(endpoint)
    if payload.api_key is not None:
        _register_key(deps, endpoint_id, credential_ref, payload.api_key)
    dto = endpoint_read_dto(deps, endpoint)
    response.headers["ETag"] = dto.version
    return dto


@router.get("", response_model=list[LlmEndpointReadDto])
async def list_endpoints(request: Request) -> list[LlmEndpointReadDto]:
    deps: ApiDeps = get_deps(request)
    return [endpoint_read_dto(deps, endpoint) for endpoint in deps.endpoint_store.list_endpoints()]


@router.get("/{endpoint_id}", response_model=LlmEndpointReadDto)
async def get_endpoint(
    endpoint_id: str, request: Request, response: Response
) -> LlmEndpointReadDto:
    deps: ApiDeps = get_deps(request)
    dto = endpoint_read_dto(deps, endpoint_or_404(deps, endpoint_id))
    response.headers["ETag"] = dto.version
    return dto


@router.patch("/{endpoint_id}", response_model=LlmEndpointReadDto)
async def update_endpoint(
    endpoint_id: str,
    payload: LlmEndpointUpdateDto,
    request: Request,
    response: Response,
) -> LlmEndpointReadDto:
    deps: ApiDeps = get_deps(request)
    endpoint = endpoint_or_404(deps, endpoint_id)
    require_if_match(request, endpoint_version(endpoint))
    updated = LLMEndpoint(
        id=endpoint.id,
        name=payload.name if payload.name is not None else endpoint.name,
        protocol=endpoint.protocol,
        base_url=payload.base_url if payload.base_url is not None else endpoint.base_url,
        credential_ref=endpoint.credential_ref,
        enabled=payload.enabled if payload.enabled is not None else endpoint.enabled,
        request_timeout_seconds=(
            payload.request_timeout_seconds
            if payload.request_timeout_seconds is not None
            else endpoint.request_timeout_seconds
        ),
        max_retries=(
            payload.max_retries if payload.max_retries is not None else endpoint.max_retries
        ),
        concurrency_limit=(
            payload.concurrency_limit
            if payload.concurrency_limit is not None
            else endpoint.concurrency_limit
        ),
        api_style=payload.api_style if payload.api_style is not None else endpoint.api_style,
    )
    if payload.api_key is not None:
        _register_key(deps, endpoint_id, endpoint.credential_ref, payload.api_key)
    deps.endpoint_store.save_endpoint(updated)
    dto = endpoint_read_dto(deps, updated)
    response.headers["ETag"] = dto.version
    return dto


@router.delete("/{endpoint_id}", status_code=204)
async def delete_endpoint(endpoint_id: str, request: Request) -> None:
    """删除用户 relay（G10，WP-B）。

    引用完整性：任何用户 model 的 endpoint_id 指向该 relay 的 id 或 name
    （catalog_merge 的 relay-name alias 语义）→ 409，不静默悬空。
    credential 条目为进程内注册表（永不落盘），重启即散，无泄漏面。
    """
    deps: ApiDeps = get_deps(request)
    endpoint = endpoint_or_404(deps, endpoint_id)
    bound = {endpoint_id, endpoint.name}
    referencing = sorted(
        model.id for model in deps.model_store.list_models() if model.endpoint_id in bound
    )
    if referencing:
        raise ApiError(
            409,
            "Endpoint In Use",
            f"referenced by models: {', '.join(referencing)}",
        )
    deps.endpoint_store.delete_endpoint(endpoint.id)


@router.post("/{endpoint_id}/test", response_model=EndpointTestResultDto)
async def test_endpoint(
    endpoint_id: str,
    payload: EndpointTestRequestDto,
    request: Request,
) -> EndpointTestResultDto:
    """endpoint test：connectivity + basic chat（显式配置操作，非 dry-run）。"""
    deps: ApiDeps = get_deps(request)
    endpoint = endpoint_or_404(deps, endpoint_id)
    model = _model_for_endpoint(deps, payload.model_id, endpoint_id)
    result = run_endpoint_test(
        gateway=deps.gateway,
        credential_resolver=deps.credentials,
        endpoint=endpoint,
        model_name=model.model_name,
        url_policy=deps.endpoint_url_policy,
    )
    return EndpointTestResultDto(
        ok=result.ok,
        returned_model_name=result.returned_model_name,
        system_fingerprint=result.system_fingerprint,
        error_category=result.error_category.value if result.error_category else None,
        error_message_redacted=result.error_message,
        probed_at=result.probed_at.isoformat() if result.probed_at else None,
    )


@router.post("/{endpoint_id}/discover-models", response_model=DiscoverModelsResultDto)
async def discover_models(endpoint_id: str, request: Request) -> DiscoverModelsResultDto:
    """GET /v1/models discovery；allow_models 白名单过滤（若配置）。"""
    deps: ApiDeps = get_deps(request)
    endpoint = endpoint_or_404(deps, endpoint_id)
    try:
        credential = deps.credentials.resolve(endpoint.credential_ref)
    except InvalidInputError as exc:
        raise ApiError(422, "Credential Missing", str(exc)) from exc
    try:
        listing = deps.gateway.list_models(endpoint, credential)
    except Exception as exc:  # noqa: BLE001 - gateway 错误已 redacted，映射 503
        raise ApiError(503, "Relay Unavailable", str(exc)) from exc
    allow = endpoint.discovery.allow_models if endpoint.discovery is not None else ()
    ids = [item for item in listing.model_ids if not allow or item in allow]
    return DiscoverModelsResultDto(model_ids=ids)


@router.get("/{endpoint_id}/health", response_model=EndpointHealthDto)
async def endpoint_health(endpoint_id: str, request: Request) -> EndpointHealthDto:
    """实时连通性探测（GET /models）；不伪造缓存健康状态。"""
    deps: ApiDeps = get_deps(request)
    endpoint = endpoint_or_404(deps, endpoint_id)
    try:
        credential = deps.credentials.resolve(endpoint.credential_ref)
        snapshot: EndpointProbeSnapshot = deps.gateway.probe_connectivity(endpoint, credential)
    except InvalidInputError as exc:
        raise ApiError(422, "Credential Missing", str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise ApiError(503, "Relay Unavailable", str(exc)) from exc
    return EndpointHealthDto(
        ok=snapshot.ok,
        error_category=snapshot.error_category.value if snapshot.error_category else None,
        error_message_redacted=snapshot.error_message_redacted,
        checked_at=_now(),
    )
