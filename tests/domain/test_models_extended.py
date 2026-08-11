"""Model relay 扩展值对象不变量测试。

覆盖 ModelRuntimeFingerprint / ModelProbeResult / ProbeSuiteSpec /
FallbackAuditRecord / EndpointProbeSnapshot / CapabilityProbeFailure /
EndpointHealthRecord / EndpointDiscoveryConfig 的构建不变量。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.domain.circuit_breaker import CircuitBreakerConfig
from packages.domain.core import Digest
from packages.domain.enums import EndpointHealth, FailureCategory, ModelCapability
from packages.domain.models import (
    CapabilityProbeFailure,
    EndpointDiscoveryConfig,
    EndpointHealthRecord,
    EndpointProbeSnapshot,
    FallbackAuditRecord,
    LLMEndpoint,
    ModelProbeResult,
    ModelRuntimeFingerprint,
    ProbeSuiteSpec,
)

NOW = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)


class TestModelProbeResult:
    def test_empty_model_id_rejected(self) -> None:
        with pytest.raises(ValueError):
            ModelProbeResult(model_id="", ok=True)

    def test_naive_timestamp_rejected(self) -> None:
        with pytest.raises(ValueError):
            ModelProbeResult(
                model_id="m1",
                ok=True,
                probed_at=datetime(2026, 8, 11, 12, 0, 0),
            )

    def test_valid_result(self) -> None:
        result = ModelProbeResult(
            model_id="m1",
            ok=True,
            observed_capabilities=frozenset({ModelCapability.CHAT}),
            returned_model_name="model-alpha",
            system_fingerprint="fp1",
            probed_at=NOW,
        )
        assert result.ok
        assert result.returned_model_name == "model-alpha"


class TestProbeSuiteSpec:
    def test_empty_version_rejected(self) -> None:
        with pytest.raises(ValueError):
            ProbeSuiteSpec(
                version="",
                steps=("chat",),
                fixture_message="pong",
                structured_schema={"type": "object"},
            )

    def test_no_steps_rejected(self) -> None:
        with pytest.raises(ValueError):
            ProbeSuiteSpec(
                version="probe-suite-v1",
                steps=(),
                fixture_message="pong",
                structured_schema={"type": "object"},
            )

    def test_empty_structured_schema_rejected(self) -> None:
        with pytest.raises(ValueError):
            ProbeSuiteSpec(
                version="probe-suite-v1",
                steps=("chat",),
                fixture_message="pong",
                structured_schema={},
            )

    def test_valid_spec(self) -> None:
        spec = ProbeSuiteSpec(
            version="probe-suite-v1",
            steps=("connectivity", "chat", "streaming", "tool_calling", "structured_output"),
            fixture_message="Reply with the single word: pong",
            structured_schema={
                "type": "object",
                "properties": {"pong": {"type": "string"}},
                "required": ["pong"],
            },
        )
        assert spec.version == "probe-suite-v1"
        assert len(spec.steps) == 5


class TestFallbackAuditRecord:
    def test_empty_from_model_rejected(self) -> None:
        with pytest.raises(ValueError):
            FallbackAuditRecord(from_model="", to_model="b", reason="r", occurred_at=NOW)

    def test_empty_reason_rejected(self) -> None:
        with pytest.raises(ValueError):
            FallbackAuditRecord(from_model="a", to_model="b", reason="", occurred_at=NOW)

    def test_session_switch_defaults_false(self) -> None:
        record = FallbackAuditRecord(from_model="a", to_model="b", reason="r", occurred_at=NOW)
        assert record.session_switched is False

    def test_valid_record_with_metadata(self) -> None:
        record = FallbackAuditRecord(
            from_model="research_alpha",
            to_model="coding_beta",
            reason="MODEL_RATE_LIMIT_EXHAUSTED",
            occurred_at=NOW,
            task_ref="research-task:example-001",
            manifest_policy="fallback_allowed_when_hard_capabilities_satisfied",
            session_switched=False,
        )
        assert record.from_model == "research_alpha"


class TestEndpointProbeSnapshot:
    def test_failure_snapshot(self) -> None:
        snapshot = EndpointProbeSnapshot(
            ok=False,
            error_category=FailureCategory.MODEL_AUTH,
            error_message_redacted="401 ***REDACTED***",
        )
        assert snapshot.ok is False
        assert snapshot.error_category is FailureCategory.MODEL_AUTH

    def test_success_snapshot(self) -> None:
        snapshot = EndpointProbeSnapshot(
            ok=True,
            returned_model_name="model-alpha",
            safe_response_metadata={"x-request-id": "req-1"},
            usage_reported=True,
        )
        assert snapshot.ok is True
        assert snapshot.safe_response_metadata["x-request-id"] == "req-1"
        assert snapshot.usage_reported is True


class TestCapabilityProbeFailure:
    def test_valid_failure(self) -> None:
        failure = CapabilityProbeFailure(
            capability=ModelCapability.STREAMING,
            error_category=FailureCategory.MODEL_INCOMPATIBLE,
            error_message_redacted="HTTP 400: unsupported",
            probed_at=NOW,
        )
        assert failure.capability is ModelCapability.STREAMING
        assert failure.error_category is FailureCategory.MODEL_INCOMPATIBLE

    def test_naive_timestamp_rejected(self) -> None:
        with pytest.raises(ValueError):
            CapabilityProbeFailure(
                capability=ModelCapability.CHAT,
                error_category=FailureCategory.EXECUTION_FAILURE,
                probed_at=datetime(2026, 8, 11, 12, 0, 0),
            )


class TestEndpointHealthRecord:
    def test_valid_record(self) -> None:
        record = EndpointHealthRecord(
            endpoint_id="main",
            state=EndpointHealth.OPEN_CIRCUIT,
            recorded_at=NOW,
            circuit_state="OPEN",
            consecutive_failures=5,
            last_error_category=FailureCategory.MODEL_RATE_LIMIT,
            opened_at=NOW,
        )
        assert record.state is EndpointHealth.OPEN_CIRCUIT
        assert record.last_error_category is FailureCategory.MODEL_RATE_LIMIT

    def test_empty_endpoint_id_rejected(self) -> None:
        with pytest.raises(ValueError):
            EndpointHealthRecord(endpoint_id="", state=EndpointHealth.HEALTHY, recorded_at=NOW)

    def test_naive_recorded_at_rejected(self) -> None:
        with pytest.raises(ValueError):
            EndpointHealthRecord(
                endpoint_id="main",
                state=EndpointHealth.HEALTHY,
                recorded_at=datetime(2026, 8, 11, 12, 0, 0),
            )


class TestLLMEndpointExtended:
    def test_discovery_config_defaults(self) -> None:
        endpoint = LLMEndpoint(
            id="main",
            name="Main",
            protocol="OPENAI_COMPATIBLE",
            base_url="https://relay.example.com/v1",
            credential_ref="k",
            discovery=EndpointDiscoveryConfig(),
        )
        assert endpoint.discovery is not None
        assert endpoint.discovery.enabled is False
        assert endpoint.discovery.allow_models == ()

    def test_discovery_with_allowlist(self) -> None:
        endpoint = LLMEndpoint(
            id="main",
            name="Main",
            protocol="OPENAI_COMPATIBLE",
            base_url="https://relay.example.com/v1",
            credential_ref="k",
            discovery=EndpointDiscoveryConfig(enabled=True, allow_models=("model-alpha",)),
        )
        assert endpoint.discovery is not None
        assert endpoint.discovery.enabled is True
        assert endpoint.discovery.allow_models == ("model-alpha",)

    def test_circuit_breaker_config_round_trip(self) -> None:
        endpoint = LLMEndpoint(
            id="main",
            name="Main",
            protocol="OPENAI_COMPATIBLE",
            base_url="https://relay.example.com/v1",
            credential_ref="k",
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=5, open_timeout_seconds=60, half_open_max_probes=1
            ),
        )
        assert endpoint.circuit_breaker is not None
        assert endpoint.circuit_breaker.failure_threshold == 5

    def test_invalid_circuit_breaker_rejected(self) -> None:
        with pytest.raises(ValueError):
            CircuitBreakerConfig(failure_threshold=0)


class TestModelRuntimeFingerprint:
    def test_empty_requested_model_rejected(self) -> None:
        with pytest.raises(ValueError):
            ModelRuntimeFingerprint(
                endpoint_config_digest=Digest("a" * 64),
                requested_model_id="",
            )

    def test_naive_captured_at_rejected(self) -> None:
        with pytest.raises(ValueError):
            ModelRuntimeFingerprint(
                endpoint_config_digest=Digest("a" * 64),
                requested_model_id="model-alpha",
                captured_at=datetime(2026, 8, 11, 12, 0, 0),
            )

    def test_valid_fingerprint(self) -> None:
        fingerprint = ModelRuntimeFingerprint(
            endpoint_config_digest=Digest("a" * 64),
            requested_model_id="model-alpha",
            returned_model_identifier="model-alpha",
            system_fingerprint="fp_example_001",
            selected_response_metadata={"x-request-id": "req_example_001"},
            probe_suite_digest=Digest("b" * 64),
            calibration_prompt_version="probe-suite-v1",
            calibration_result_digest=Digest("c" * 64),
            observed_capabilities=frozenset({ModelCapability.CHAT, ModelCapability.STREAMING}),
            captured_at=NOW,
        )
        assert fingerprint.requested_model_id == "model-alpha"
        assert ModelCapability.STREAMING in fingerprint.observed_capabilities
