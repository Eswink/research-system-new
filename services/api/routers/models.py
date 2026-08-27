"""Model 控制面路由（CONTROL_PLANE_API.md Models 节）。

probe 执行正式 run_probe + build_fingerprint（M12 语义，不重写探测逻辑）；
probe 成功后把 PROBED 断言合并回 ModelDefinition 并持久化（backend truth
= ModelStore + 实时探测，DoD 2）。compatibility 是声明能力视图，不伪造
未探测的推断。映射集中在 services.api.mappers。
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from packages.application.model_relay.fingerprint import build_fingerprint
from packages.application.model_relay.probe import ProbeOptions, run_probe
from packages.application.model_relay.suite import default_probe_suite
from packages.domain.core import ID
from packages.domain.enums import CapabilitySource, CapabilityStatus, ModelCapability
from packages.domain.models import (
    CapabilityAssertion,
    EndpointProbeSnapshot,
    LLMEndpoint,
    ModelDefinition,
    ModelProbeResult,
    ProbeSuiteSpec,
)
from services.api.composition import ApiDeps
from services.api.deps import get_deps, require_if_match
from services.api.dto.models import (
    CapabilityAssertionDto,
    CompatibilityViewDto,
    ModelCreateDto,
    ModelReadDto,
    ModelRuntimeFingerprintDto,
    ModelUpdateDto,
    ProbeResultDto,
)
from services.api.errors import ApiError
from services.api.mappers.models import (
    capability_failures_dto,
    fingerprint_dto,
    model_read_dto,
    model_version,
)

router = APIRouter(prefix="/models", tags=["models"])


def _get_or_404(deps: ApiDeps, model_id: str) -> ModelDefinition:
    try:
        return deps.model_store.get_model(model_id)
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"model not found: {model_id}") from exc


def _endpoint_for(deps: ApiDeps, endpoint_id: str) -> LLMEndpoint:
    try:
        return deps.endpoint_store.get_endpoint(endpoint_id)
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"endpoint not found: {endpoint_id}") from exc


def _capabilities_from_payload(
    capabilities: dict[str, CapabilityAssertionDto],
) -> dict[ModelCapability, CapabilityAssertion]:
    result: dict[ModelCapability, CapabilityAssertion] = {}
    for name, assertion in capabilities.items():
        result[ModelCapability(name)] = CapabilityAssertion(
            status=CapabilityStatus(assertion.status),
            confidence=assertion.confidence,
            source=CapabilitySource(assertion.source),
            last_verified_at=None,
            probe_version=assertion.probe_version,
        )
    return result


def _merge_probed(
    model: ModelDefinition,
    assertions: dict[ModelCapability, CapabilityAssertion],
) -> ModelDefinition:
    """PROBED 断言合并（PROBED 优先于 USER_DECLARED，不降级已有 PROBED）。"""
    merged = dict(model.capabilities)
    for capability, assertion in assertions.items():
        if capability not in merged or merged[capability].source is not CapabilitySource.PROBED:
            merged[capability] = assertion
    return ModelDefinition(
        id=model.id,
        endpoint_id=model.endpoint_id,
        model_name=model.model_name,
        display_name=model.display_name,
        enabled=model.enabled,
        capabilities=merged,
    )


def _probe_result_dto(
    model: ModelDefinition,
    result: ModelProbeResult,
    fingerprint: ModelRuntimeFingerprintDto | None,
) -> ProbeResultDto:
    return ProbeResultDto(
        model_id=model.id,
        ok=result.ok,
        observed_capabilities=sorted(item.value for item in result.observed_capabilities),
        returned_model_name=result.returned_model_name,
        system_fingerprint=result.system_fingerprint,
        provider_fingerprint_available=result.system_fingerprint is not None,
        error_category=result.error_category.value if result.error_category else None,
        error_message_redacted=result.error_message,
        capability_failures=capability_failures_dto(result.capability_failures),
        probed_at=result.probed_at.isoformat() if result.probed_at else None,
        fingerprint=fingerprint,
    )


@router.post("", status_code=201, response_model=ModelReadDto)
async def create_model(
    payload: ModelCreateDto,
    request: Request,
    response: Response,
) -> ModelReadDto:
    deps: ApiDeps = get_deps(request)
    _endpoint_for(deps, payload.endpoint_id)
    model = ModelDefinition(
        id=ID.generate().value,
        endpoint_id=payload.endpoint_id,
        model_name=payload.model_name,
        display_name=payload.display_name,
        enabled=payload.enabled,
        capabilities=_capabilities_from_payload(payload.capabilities),
    )
    deps.model_store.save_model(model)
    dto = model_read_dto(model)
    response.headers["ETag"] = dto.version
    return dto


@router.get("", response_model=list[ModelReadDto])
async def list_models(request: Request, endpoint_id: str | None = None) -> list[ModelReadDto]:
    deps: ApiDeps = get_deps(request)
    models = deps.model_store.list_models()
    if endpoint_id is not None:
        models = [model for model in models if model.endpoint_id == endpoint_id]
    return [model_read_dto(model) for model in models]


@router.get("/{model_id}", response_model=ModelReadDto)
async def get_model(model_id: str, request: Request, response: Response) -> ModelReadDto:
    deps: ApiDeps = get_deps(request)
    dto = model_read_dto(_get_or_404(deps, model_id))
    response.headers["ETag"] = dto.version
    return dto


@router.patch("/{model_id}", response_model=ModelReadDto)
async def update_model(
    model_id: str,
    payload: ModelUpdateDto,
    request: Request,
    response: Response,
) -> ModelReadDto:
    deps: ApiDeps = get_deps(request)
    model = _get_or_404(deps, model_id)
    require_if_match(request, model_version(model))
    capabilities = model.capabilities
    if payload.capabilities is not None:
        capabilities = _capabilities_from_payload(payload.capabilities)
    updated = ModelDefinition(
        id=model.id,
        endpoint_id=model.endpoint_id,
        model_name=model.model_name,
        display_name=(
            payload.display_name if payload.display_name is not None else model.display_name
        ),
        enabled=payload.enabled if payload.enabled is not None else model.enabled,
        capabilities=capabilities,
    )
    deps.model_store.save_model(updated)
    dto = model_read_dto(updated)
    response.headers["ETag"] = dto.version
    return dto


@router.post("/{model_id}/probe", response_model=ProbeResultDto)
async def probe_model(model_id: str, request: Request) -> ProbeResultDto:
    """执行正式 capability probe（run_probe + fingerprint，M12 语义）。

    成功后把 PROBED 断言合并进 ModelDefinition 并持久化（probe 是配置
    操作；运行后能力声明与 backend truth 一致）。
    """
    deps: ApiDeps = get_deps(request)
    model = _get_or_404(deps, model_id)
    endpoint = _endpoint_for(deps, model.endpoint_id)
    suite = default_probe_suite()
    result, assertions = run_probe(
        gateway=deps.gateway,
        credential_resolver=deps.credentials,
        endpoint=endpoint,
        model=model,
        options=ProbeOptions(suite=suite, url_policy=deps.endpoint_url_policy),
    )
    fingerprint = _probe_fingerprint(endpoint, model, suite, result)
    merged = _merge_probed(model, assertions)
    deps.model_store.save_model(merged)
    return _probe_result_dto(model, result, fingerprint)


def _probe_fingerprint(
    endpoint: LLMEndpoint,
    model: ModelDefinition,
    suite: ProbeSuiteSpec,
    result: ModelProbeResult,
) -> ModelRuntimeFingerprintDto | None:
    """probe 成功且 relay 返回 system_fingerprint 时构建指纹 DTO。"""
    if not result.ok or result.system_fingerprint is None:
        return None
    snapshot = EndpointProbeSnapshot(
        ok=True,
        returned_model_name=result.returned_model_name,
        system_fingerprint=result.system_fingerprint,
        safe_response_metadata={},
        usage_reported=False,
    )
    fingerprint_model = build_fingerprint(
        endpoint=endpoint,
        requested_model_id=model.model_name,
        snapshot=snapshot,
        suite_spec=suite,
        observed_capabilities=frozenset(result.observed_capabilities),
    )
    return fingerprint_dto(fingerprint_model)


@router.get("/{model_id}/compatibility", response_model=CompatibilityViewDto)
async def model_compatibility(model_id: str, request: Request) -> CompatibilityViewDto:
    """兼容性视图：声明能力（含来源标注）+ endpoint 摘要；不含未探测推断。"""
    deps: ApiDeps = get_deps(request)
    model = _get_or_404(deps, model_id)
    return CompatibilityViewDto(
        model=model_read_dto(model),
        endpoint_id=model.endpoint_id,
        hard_capability_requirements=[],
    )
