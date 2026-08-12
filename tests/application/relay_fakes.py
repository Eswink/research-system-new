"""Model relay probe use cases 测试共享 fakes（无真实网络）。"""

from __future__ import annotations

from packages.application.ports import (
    CompletionRequest,
    CompletionResult,
    InvalidInputError,
    ModelsListResult,
    SecretValue,
)
from packages.domain.enums import FailureCategory
from packages.domain.models import EndpointProbeSnapshot, LLMEndpoint, ModelDefinition


class FakeCredentialResolver:
    def resolve(self, credential_ref: str) -> SecretValue:
        return SecretValue("sk-test-token-1234567890")


class MissingCredentialResolver:
    def resolve(self, credential_ref: str) -> SecretValue:
        raise InvalidInputError(f"credential_ref not found: {credential_ref!r}")


class FakeGateway:
    """可控响应的 fake gateway；按请求特征返回不同结果。"""

    def __init__(
        self,
        *,
        auth_fails: bool = False,
        stream_fails: bool = False,
        tool_fails: bool = False,
        structured_fails: bool = False,
        no_usage: bool = False,
    ) -> None:
        self._auth_fails = auth_fails
        self._stream_fails = stream_fails
        self._tool_fails = tool_fails
        self._structured_fails = structured_fails
        self._no_usage = no_usage
        self.calls: list[CompletionRequest] = []

    def list_models(self, endpoint: LLMEndpoint, credential: SecretValue) -> ModelsListResult:
        return ModelsListResult(model_ids=("model-alpha", "model-beta"))

    def complete(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult:
        return CompletionResult(
            content="pong",
            returned_model_name="model-alpha",
            system_fingerprint="fp_1",
            usage_reported=True,
            safe_response_metadata={"x-request-id": "req-1"},
        )

    def probe_connectivity(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
    ) -> EndpointProbeSnapshot:
        if self._auth_fails:
            return EndpointProbeSnapshot(
                ok=False,
                error_category=FailureCategory.MODEL_AUTH,
                error_message_redacted="401 ***REDACTED***",
            )
        return EndpointProbeSnapshot(ok=True)

    def probe_endpoint(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> EndpointProbeSnapshot:
        self.calls.append(request)
        if request.stream and self._stream_fails:
            return EndpointProbeSnapshot(
                ok=False,
                error_category=FailureCategory.EXECUTION_FAILURE,
                error_message_redacted="stream interrupted ***REDACTED***",
            )
        if request.tools and self._tool_fails:
            return EndpointProbeSnapshot(
                ok=False,
                error_category=FailureCategory.MODEL_INCOMPATIBLE,
                error_message_redacted="HTTP 400: tools unsupported",
            )
        if request.response_format and self._structured_fails:
            return EndpointProbeSnapshot(
                ok=False,
                error_category=FailureCategory.MODEL_INCOMPATIBLE,
                error_message_redacted="HTTP 422: response_format unsupported",
            )
        return EndpointProbeSnapshot(
            ok=True,
            returned_model_name="model-alpha",
            system_fingerprint="fp_1",
            safe_response_metadata={"x-request-id": "req-1"} if not self._no_usage else {},
            usage_reported=not self._no_usage,
        )


ENDPOINT = LLMEndpoint(
    id="main",
    name="Main Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="https://relay.example.com/api/v1",
    credential_ref="llm_main_key",
)

LOCALHOST_ENDPOINT = LLMEndpoint(
    id="local",
    name="Local Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url="http://127.0.0.1:8080/v1",
    credential_ref="llm_main_key",
)

MODEL = ModelDefinition(id="model-alpha", endpoint_id="main", model_name="model-alpha")
