"""Model / Endpoint 契约加载器。"""

from __future__ import annotations

from adapters.contracts.base import load_flat_collection, load_yaml, mapping_under
from packages.domain.circuit_breaker import CircuitBreakerConfig
from packages.domain.enums import CapabilitySource, CapabilityStatus, ModelCapability
from packages.domain.models import (
    CapabilityAssertion,
    EndpointDiscoveryConfig,
    LLMEndpoint,
    ModelDefinition,
    ModelProfile,
)


def load_llm_endpoints(relative_path: str) -> dict[str, LLMEndpoint]:
    collection: dict[str, LLMEndpoint] = {}
    for key, raw in load_flat_collection(
        relative_path, "llm_endpoints", "llm-endpoint.schema.json"
    ).items():
        discovery_raw = raw.get("discovery") or {}
        circuit_raw = raw.get("circuit_breaker") or {}
        collection[key] = LLMEndpoint(
            id=raw["id"],
            name=raw["name"],
            protocol=raw["protocol"],
            base_url=raw["base_url"],
            credential_ref=raw["credential_ref"],
            enabled=raw.get("enabled", True),
            request_timeout_seconds=raw.get("request_timeout_seconds", 60),
            max_retries=raw.get("max_retries", 3),
            concurrency_limit=raw.get("concurrency_limit", 4),
            discovery=EndpointDiscoveryConfig(
                enabled=bool(discovery_raw.get("enabled", False)),
                allow_models=tuple(str(item) for item in (discovery_raw.get("allow_models") or [])),
            )
            if discovery_raw
            else None,
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=int(circuit_raw.get("failure_threshold", 5)),
                open_timeout_seconds=int(circuit_raw.get("open_timeout_seconds", 60)),
                half_open_max_probes=int(circuit_raw.get("half_open_max_probes", 1)),
            )
            if circuit_raw
            else None,
        )
    return collection


def load_models(relative_path: str) -> dict[str, ModelDefinition]:
    # 示例将 endpoint 键重命名为 schema 的 endpoint_id（与 validator 一致）
    collection: dict[str, ModelDefinition] = {}
    for key, raw in load_flat_collection(
        relative_path, "models", "model-definition.schema.json", rename={"endpoint": "endpoint_id"}
    ).items():
        capabilities: dict[ModelCapability, CapabilityAssertion] = {}
        for capability_name, assertion in raw.get("capabilities", {}).items():
            capabilities[ModelCapability(capability_name)] = CapabilityAssertion(
                status=CapabilityStatus(assertion["status"]),
                confidence=assertion["confidence"],
                source=CapabilitySource(assertion["source"]),
                last_verified_at=None,
                probe_version=assertion.get("probe_version"),
            )
        collection[key] = ModelDefinition(
            id=raw["id"],
            endpoint_id=raw["endpoint_id"],
            model_name=raw["model_name"],
            display_name=raw.get("display_name"),
            enabled=raw.get("enabled", True),
            capabilities=capabilities,
        )
    return collection


def load_model_profiles(relative_path: str) -> dict[str, ModelProfile]:
    section = mapping_under(load_yaml(relative_path), "model_profiles", relative_path)
    collection: dict[str, ModelProfile] = {}
    for profile_id, body in section.items():
        if not isinstance(body, dict):
            raise ValueError(f"{relative_path}/{profile_id} must be a mapping")
        collection[profile_id] = ModelProfile(
            id=profile_id,
            primary=body["primary"],
            fallback=list(body.get("fallback", [])),
            hard_capabilities=[ModelCapability(item) for item in body.get("hard_capabilities", [])],
        )
    return collection
