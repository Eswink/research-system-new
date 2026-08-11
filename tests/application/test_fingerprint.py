"""ModelRuntimeFingerprint 构建与 digest 测试。"""

from __future__ import annotations

from packages.application.model_relay.fingerprint import (
    build_fingerprint,
    endpoint_config_digest,
    probe_suite_digest,
)
from packages.application.model_relay.suite import default_probe_suite
from packages.domain.circuit_breaker import CircuitBreakerConfig
from packages.domain.core import Digest
from packages.domain.enums import ModelCapability
from packages.domain.models import (
    EndpointDiscoveryConfig,
    EndpointProbeSnapshot,
    LLMEndpoint,
)
from packages.domain.serialization import digest_of

ENDPOINT = LLMEndpoint(
    id="main",
    name="Main Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="https://relay.example.com/api/v1",
    credential_ref="llm_main_key",
)


class TestEndpointConfigDigest:
    def test_digest_is_stable(self) -> None:
        first = endpoint_config_digest(ENDPOINT)
        second = endpoint_config_digest(ENDPOINT)
        assert first == second
        assert isinstance(first, Digest)

    def test_digest_changes_with_base_url(self) -> None:
        other = LLMEndpoint(
            id="main",
            name="Main Relay",
            protocol="OPENAI_COMPATIBLE",
            base_url="https://other.example.com/api/v1",
            credential_ref="llm_main_key",
        )
        assert endpoint_config_digest(ENDPOINT) != endpoint_config_digest(other)

    def test_credential_ref_not_part_of_digest(self) -> None:
        renamed = LLMEndpoint(
            id="main",
            name="Main Relay",
            protocol="OPENAI_COMPATIBLE",
            base_url="https://relay.example.com/api/v1",
            credential_ref="different_ref",
        )
        # credential_ref 不影响配置 digest（密钥轮换不改 manifest 明文语义）
        assert endpoint_config_digest(ENDPOINT) == endpoint_config_digest(renamed)

    def test_discovery_and_circuit_breaker_part_of_digest(self) -> None:
        configured = LLMEndpoint(
            id="main",
            name="Main Relay",
            protocol="OPENAI_COMPATIBLE",
            base_url="https://relay.example.com/api/v1",
            credential_ref="llm_main_key",
            discovery=EndpointDiscoveryConfig(enabled=True, allow_models=("model-alpha",)),
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=5, open_timeout_seconds=60, half_open_max_probes=1
            ),
        )
        assert endpoint_config_digest(ENDPOINT) != endpoint_config_digest(configured)


class TestProbeSuiteDigest:
    def test_digest_is_stable(self) -> None:
        spec = default_probe_suite()
        assert probe_suite_digest(spec) == probe_suite_digest(default_probe_suite())

    def test_digest_changes_with_version(self) -> None:
        spec = default_probe_suite()
        assert probe_suite_digest(spec) != probe_suite_digest(
            default_probe_suite(include_vision=True)
        )


class TestBuildFingerprint:
    def test_fingerprint_captures_drift_evidence(self) -> None:
        snapshot = EndpointProbeSnapshot(
            ok=True,
            returned_model_name="model-alpha",
            system_fingerprint="fp_example_001",
            safe_response_metadata={"x-request-id": "req_example_001"},
        )
        fingerprint = build_fingerprint(
            endpoint=ENDPOINT,
            requested_model_id="model-alpha",
            snapshot=snapshot,
            suite_spec=default_probe_suite(),
            observed_capabilities=frozenset({ModelCapability.CHAT}),
        )
        assert fingerprint.returned_model_identifier == "model-alpha"
        assert fingerprint.system_fingerprint == "fp_example_001"
        assert fingerprint.selected_response_metadata["x-request-id"] == "req_example_001"
        assert fingerprint.probe_suite_digest == probe_suite_digest(default_probe_suite())
        assert fingerprint.calibration_prompt_version == "probe-suite-v1"
        assert fingerprint.calibration_result_digest is not None

    def test_fingerprint_marks_drift_when_returned_differs(self) -> None:
        snapshot = EndpointProbeSnapshot(ok=True, returned_model_name="different-model")
        fingerprint = build_fingerprint(
            endpoint=ENDPOINT,
            requested_model_id="model-alpha",
            snapshot=snapshot,
            suite_spec=default_probe_suite(),
            observed_capabilities=frozenset[ModelCapability](),
        )
        assert fingerprint.requested_model_id == "model-alpha"
        assert fingerprint.returned_model_identifier == "different-model"
        assert fingerprint.requested_model_id != fingerprint.returned_model_identifier

    def test_calibration_result_digest_is_deterministic(self) -> None:
        snapshot = EndpointProbeSnapshot(
            ok=True, returned_model_name="model-alpha", system_fingerprint="fp_1"
        )
        first = build_fingerprint(
            endpoint=ENDPOINT,
            requested_model_id="model-alpha",
            snapshot=snapshot,
            suite_spec=default_probe_suite(),
            observed_capabilities=frozenset[ModelCapability](),
        )
        second = build_fingerprint(
            endpoint=ENDPOINT,
            requested_model_id="model-alpha",
            snapshot=snapshot,
            suite_spec=default_probe_suite(),
            observed_capabilities=frozenset[ModelCapability](),
        )
        assert first.calibration_result_digest == second.calibration_result_digest
        expected = digest_of({"returned_model": "model-alpha", "system_fingerprint": "fp_1"})
        assert first.calibration_result_digest == expected
