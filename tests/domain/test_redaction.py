"""Secret redaction 纯函数测试。

覆盖异常消息、header 白名单采集、config repr 与 telemetry 四类路径；
断言 Authorization 与 api-key 永不进入输出。
"""

from __future__ import annotations

from packages.domain.redaction import (
    REDACTED,
    redact_config_repr,
    redact_exception_message,
    redact_text,
    select_safe_headers,
)


class TestRedactText:
    def test_bearer_token_is_redacted(self) -> None:
        text = "Authorization: Bearer sk-proj-abcdef1234567890 failed"
        assert REDACTED in redact_text(text)
        assert "sk-proj-abcdef1234567890" not in redact_text(text)

    def test_bearer_prefix_preserved(self) -> None:
        redacted = redact_text("Bearer tok_12345678")
        assert redacted.startswith("Bearer " + REDACTED)

    def test_api_key_like_token_is_redacted(self) -> None:
        redacted = redact_text("key=sk-abcdefghijklmnopqrstuvwxyz123456")
        assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in redacted

    def test_url_embedded_credentials_redacted(self) -> None:
        redacted = redact_text("https://user:secret123@relay.example/v1")
        assert "secret123" not in redacted
        assert "relay.example/v1" in redacted

    def test_plain_text_unchanged(self) -> None:
        text = "model request completed"
        assert redact_text(text) == text


class TestRedactExceptionMessage:
    def test_message_with_token_redacted(self) -> None:
        message = "401 Unauthorized: invalid api key sk-test-aaaaaaaaa123"
        redacted = redact_exception_message(message)
        assert "sk-test-aaaaaaaaa123" not in redacted
        assert REDACTED in redacted


class TestSelectSafeHeaders:
    def test_authorization_never_collected(self) -> None:
        headers = [
            ("Authorization", "Bearer sk-secret-token-12345678"),
            ("x-request-id", "req-001"),
        ]
        result = select_safe_headers(headers)
        assert "authorization" not in result
        assert result["x-request-id"] == "req-001"

    def test_api_key_header_never_collected(self) -> None:
        headers = [("api-key", "sk-abcdefghijklmnop1234567890"), ("cf-ray", "ray-1")]
        result = select_safe_headers(headers)
        assert "api-key" not in result
        assert result["cf-ray"] == "ray-1"

    def test_unknown_headers_dropped(self) -> None:
        headers = [("x-custom-secret", "value"), ("x-request-id", "req-002")]
        result = select_safe_headers(headers)
        assert "x-custom-secret" not in result
        assert result == {"x-request-id": "req-002"}


class TestRedactConfigRepr:
    def test_config_repr_never_exposes_credential_reference(self) -> None:
        endpoint_id = "main"
        base_url = "https://relay.example/v1"
        repr_text = redact_config_repr(endpoint_id, base_url)
        assert "llm_main_key" not in repr_text
        assert repr_text == (
            "LLMEndpoint(id='main', base_url='https://relay.example/v1', credential=<configured>)"
        )

    def test_config_repr_without_credential(self) -> None:
        repr_text = redact_config_repr(
            "main", "https://relay.example/v1", credential_configured=False
        )
        assert "<not-configured>" in repr_text

    def test_config_repr_redacts_embedded_url_credentials(self) -> None:
        repr_text = redact_config_repr("main", "https://user:secret123@relay.example/v1")
        assert "secret123" not in repr_text
        assert "relay.example/v1" in repr_text
