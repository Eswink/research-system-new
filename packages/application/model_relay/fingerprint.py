"""ModelRuntimeFingerprint 构建与 endpoint config digest。

fingerprint 使用 canonical serialization 计算 digest（AGENTS.md §4 漂移可见性）。
"""

from __future__ import annotations

from datetime import datetime, timezone

from packages.domain.core import Digest
from packages.domain.enums import ModelCapability
from packages.domain.models import (
    EndpointProbeSnapshot,
    LLMEndpoint,
    ModelRuntimeFingerprint,
    ProbeSuiteSpec,
)
from packages.domain.serialization import canonical_json_bytes, digest_of


def endpoint_config_digest(endpoint: LLMEndpoint) -> Digest:
    """对 endpoint 关键配置计算确定性 digest（不含 credential 明文）。"""
    discovery = None
    if endpoint.discovery is not None:
        discovery = {
            "enabled": endpoint.discovery.enabled,
            "allow_models": list(endpoint.discovery.allow_models),
        }
    circuit_breaker = None
    if endpoint.circuit_breaker is not None:
        circuit_breaker = {
            "failure_threshold": endpoint.circuit_breaker.failure_threshold,
            "open_timeout_seconds": endpoint.circuit_breaker.open_timeout_seconds,
            "half_open_max_probes": endpoint.circuit_breaker.half_open_max_probes,
        }
    payload = {
        "id": endpoint.id,
        "protocol": endpoint.protocol,
        "base_url": endpoint.base_url,
        "request_timeout_seconds": endpoint.request_timeout_seconds,
        "max_retries": endpoint.max_retries,
        "concurrency_limit": endpoint.concurrency_limit,
        "discovery": discovery,
        "circuit_breaker": circuit_breaker,
    }
    return Digest.of_bytes(canonical_json_bytes(payload))


def probe_suite_digest(spec: ProbeSuiteSpec) -> Digest:
    """probe suite 定义的确定性 digest（docs/integration/MODEL_PROBE.md）。"""
    payload = {
        "version": spec.version,
        "steps": list(spec.steps),
        "fixture_message": spec.fixture_message,
        "structured_schema": spec.structured_schema,
        "include_vision": spec.include_vision,
    }
    return Digest.of_bytes(canonical_json_bytes(payload))


def build_fingerprint(
    *,
    endpoint: LLMEndpoint,
    requested_model_id: str,
    snapshot: EndpointProbeSnapshot,
    suite_spec: ProbeSuiteSpec,
    observed_capabilities: frozenset[ModelCapability],
) -> ModelRuntimeFingerprint:
    """从单次探测快照构建 runtime fingerprint。"""
    captured = datetime.now(timezone.utc)
    calibration_payload = {
        "returned_model": snapshot.returned_model_name,
        "system_fingerprint": snapshot.system_fingerprint,
    }
    return ModelRuntimeFingerprint(
        endpoint_config_digest=endpoint_config_digest(endpoint),
        requested_model_id=requested_model_id,
        returned_model_identifier=snapshot.returned_model_name,
        system_fingerprint=snapshot.system_fingerprint,
        selected_response_metadata=dict(snapshot.safe_response_metadata),
        probe_suite_digest=probe_suite_digest(suite_spec),
        calibration_prompt_version=suite_spec.version,
        calibration_result_digest=digest_of(calibration_payload),
        observed_capabilities=frozenset(observed_capabilities),
        captured_at=captured,
    )
