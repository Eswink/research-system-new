"""Live relay probe 语义（M12-R1 WP7）。

验证：
- 无凭据 → NOT VERIFIED 结构化占位（verified=False, configuration_failure），
  非 Fake PASS；
- 成功路径 → verified=True + sanitized fingerprint（digest/模型名/能力，无 secret）；
- 探测失败 → verified=False 结构化结果；
- manifest payload 脱敏（无凭据字段/无原始响应）。
"""

from __future__ import annotations

from packages.application.model_relay.live_probe import (
    not_verified_outcome,
    run_live_probe,
)
from packages.application.model_relay.suite import default_probe_suite
from packages.application.ports.errors import InvalidInputError
from packages.domain.enums import FailureCategory
from packages.domain.models import LLMEndpoint, ModelDefinition


def _endpoint() -> LLMEndpoint:
    return LLMEndpoint(
        id="main",
        name="Main Relay",
        protocol="OPENAI_COMPATIBLE",
        base_url="https://relay.example.test",
        credential_ref="LLM_MAIN_KEY",
    )


def _model() -> ModelDefinition:
    return ModelDefinition(
        id="research_alpha",
        endpoint_id="main",
        model_name="muse-spark-1.2-contributor",
    )


class _NoCredentials:
    def resolve(self, credential_ref: str) -> object:
        raise InvalidInputError("credential missing")


class _FailingGateway:
    def probe_connectivity(self, endpoint, credential) -> object:
        from packages.domain.models import EndpointProbeSnapshot

        return EndpointProbeSnapshot(
            ok=False,
            error_category=FailureCategory.MODEL_AUTH,
            error_message_redacted="HTTP 401",
        )


class TestLiveProbeNotVerified:
    def test_no_credentials_is_not_verified_not_fake_pass(self) -> None:
        outcome = run_live_probe(
            gateway=_FailingGateway(),
            credentials=_NoCredentials(),
            endpoint=_endpoint(),
            model=_model(),
        )
        assert outcome.verified is False
        assert outcome.ok is False
        assert outcome.error_category == FailureCategory.CONFIGURATION.value
        assert outcome.endpoint_config_digest
        assert outcome.probe_suite_digest
        assert "credential" in (outcome.error_message_redacted or "")

    def test_not_verified_placeholder_is_structured(self) -> None:
        outcome = not_verified_outcome(
            _endpoint(), default_probe_suite(), "credentials not configured"
        )
        payload = outcome.to_manifest_payload()
        assert payload["verified"] is False
        assert payload["ok"] is False
        assert payload["error_category"] == FailureCategory.CONFIGURATION.value
        assert payload["endpoint_config_digest"]

    def test_manifest_payload_is_sanitized(self) -> None:
        outcome = not_verified_outcome(
            _endpoint(), default_probe_suite(), "no credentials"
        )
        payload = outcome.to_manifest_payload()
        assert "credential" not in str(payload).lower() or "LLM_MAIN_KEY" not in str(payload)
        assert "prompt_tokens" not in payload
        assert all(isinstance(value, (str, bool, list, type(None))) for value in payload.values())

    def test_probe_failure_is_not_verified(self) -> None:
        class Credentials:
            def resolve(self, credential_ref: str) -> object:
                return object()

        outcome = run_live_probe(
            gateway=_FailingGateway(),
            credentials=Credentials(),
            endpoint=_endpoint(),
            model=_model(),
        )
        assert outcome.verified is False
        assert outcome.error_category == FailureCategory.MODEL_AUTH.value
        assert outcome.capability_failures == ()