"""Control Plane API 映射层：Domain → DTO 显式转换（禁止 __dict__ dump）。

本层允许 import packages.domain（services → application → domain 方向内），
不得 import adapters（.importlinter.api 门禁与 routers 同级）。
"""

from __future__ import annotations

from typing import Literal

from packages.application.model_relay.fingerprint import endpoint_config_digest
from packages.application.ports.errors import InvalidInputError
from packages.domain.models import LLMEndpoint
from packages.domain.serialization import digest_of
from services.api.composition import ApiDeps
from services.api.dto.endpoints import LlmEndpointReadDto
from services.api.errors import ApiError


def endpoint_version(endpoint: LLMEndpoint) -> str:
    """API resource version：全字段 canonical digest（If-Match 用）。

    与 domain `endpoint_config_digest`（M12 fingerprint 语义）分开：
    version 覆盖 name/api_style/enabled 等 UI 可见字段，任何变更都使
    ETag 变化；domain digest 语义不动（M12 冻结）。
    """
    canonical: dict[str, object] = {
        "id": endpoint.id,
        "name": endpoint.name,
        "protocol": endpoint.protocol,
        "base_url": endpoint.base_url,
        "api_style": endpoint.api_style,
        "enabled": endpoint.enabled,
        "request_timeout_seconds": endpoint.request_timeout_seconds,
        "max_retries": endpoint.max_retries,
        "concurrency_limit": endpoint.concurrency_limit,
        "discovery": {
            "enabled": endpoint.discovery.enabled,
            "allow_models": list(endpoint.discovery.allow_models),
        }
        if endpoint.discovery is not None
        else None,
        "circuit_breaker": {
            "failure_threshold": endpoint.circuit_breaker.failure_threshold,
            "open_timeout_seconds": endpoint.circuit_breaker.open_timeout_seconds,
            "half_open_max_probes": endpoint.circuit_breaker.half_open_max_probes,
        }
        if endpoint.circuit_breaker is not None
        else None,
    }
    return str(digest_of(canonical))


def endpoint_config_version(endpoint: LLMEndpoint) -> str:
    """domain endpoint_config_digest（M12 fingerprint 语义，冻结不动）。"""
    return str(endpoint_config_digest(endpoint))


def credential_state(deps: ApiDeps, credential_ref: str) -> Literal["configured", "missing"]:
    try:
        deps.credentials.resolve(credential_ref)
        return "configured"
    except InvalidInputError:
        return "missing"


def endpoint_read_dto(deps: ApiDeps, endpoint: LLMEndpoint) -> LlmEndpointReadDto:
    return LlmEndpointReadDto(
        id=endpoint.id,
        name=endpoint.name,
        protocol=endpoint.protocol,
        base_url=endpoint.base_url,
        api_style=endpoint.api_style,
        enabled=endpoint.enabled,
        credential=credential_state(deps, endpoint.credential_ref),
        request_timeout_seconds=endpoint.request_timeout_seconds,
        max_retries=endpoint.max_retries,
        concurrency_limit=endpoint.concurrency_limit,
        version=endpoint_version(endpoint),
    )


def endpoint_or_404(deps: ApiDeps, endpoint_id: str) -> LLMEndpoint:
    try:
        return deps.endpoint_store.get_endpoint(endpoint_id)
    except KeyError as exc:
        raise ApiError(404, "Not Found", f"endpoint not found: {endpoint_id}") from exc
