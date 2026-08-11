"""OpenAIChatGateway 基础路径与错误分类离线测试（httpx.MockTransport）。"""

from __future__ import annotations

import json

import httpx
import pytest

from adapters.relay.gateway import RelayHTTPError
from packages.application.model_relay.ports import CompletionRequest
from packages.domain.enums import FailureCategory

from .relay_fakes import (
    CREDENTIAL,
    ENDPOINT,
    gateway,
    json_response,
    sse_response,
)


class TestListModels:
    def test_parses_model_ids(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/models"
            return json_response({
                "object": "list",
                "data": [{"id": "model-alpha"}, {"id": "model-beta"}],
            })

        result = gateway(handler).list_models(ENDPOINT, CREDENTIAL)
        assert result.model_ids == ("model-alpha", "model-beta")

    def test_authorization_header_present(self) -> None:
        captured: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["auth"] = request.headers.get("authorization", "")
            return json_response({"object": "list", "data": []})

        gateway(handler).list_models(ENDPOINT, CREDENTIAL)
        assert captured["auth"] == "Bearer sk-test-token-123456"

    def test_base_url_used_as_is_without_v1_join(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/models"
            return json_response({"object": "list", "data": [{"id": "m"}]})

        result = gateway(handler).list_models(ENDPOINT, CREDENTIAL)
        assert result.model_ids == ("m",)


class TestComplete:
    def test_non_stream_completion(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["model"] == "model-alpha"
            assert "stream" not in body
            return json_response(
                {
                    "id": "chatcmpl-1",
                    "model": "model-alpha",
                    "system_fingerprint": "fp_1",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": "pong"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
                },
                headers={"x-request-id": "req-1"},
            )

        result = gateway(handler).complete(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(model="model-alpha", messages=[{"role": "user", "content": "hi"}]),
        )
        assert result.content == "pong"
        assert result.returned_model_name == "model-alpha"
        assert result.system_fingerprint == "fp_1"
        assert result.usage_reported is True
        assert result.safe_response_metadata["x-request-id"] == "req-1"

    def test_tool_calls_parsed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["tools"] is not None
            return json_response({
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {"name": "pong", "arguments": '{"value":"x"}'},
                                }
                            ],
                        }
                    }
                ]
            })

        result = gateway(handler).complete(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="model-alpha",
                messages=[{"role": "user", "content": "hi"}],
                tools=[{"type": "function", "function": {"name": "pong"}}],
            ),
        )
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "pong"
        assert result.tool_calls[0].arguments == '{"value":"x"}'

    def test_structured_output_request(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["response_format"]["type"] == "json_schema"
            return json_response({
                "choices": [{"message": {"role": "assistant", "content": '{"pong":"pong"}'}}]
            })

        result = gateway(handler).complete(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="model-alpha",
                messages=[{"role": "user", "content": "hi"}],
                response_format={"type": "json_schema", "json_schema": {"name": "pong"}},
            ),
        )
        assert result.content == '{"pong":"pong"}'

    def test_stream_completion_accumulates(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["stream"] is True
            return sse_response(
                [
                    {
                        "id": "c1",
                        "object": "chat.completion.chunk",
                        "choices": [{"delta": {"content": "po"}}],
                    },
                    {
                        "id": "c1",
                        "object": "chat.completion.chunk",
                        "choices": [{"delta": {"content": "ng"}}],
                    },
                    {
                        "id": "c1",
                        "object": "chat.completion.chunk",
                        "choices": [],
                        "usage": {"total_tokens": 6},
                    },
                ],
                headers={"x-request-id": "req-stream"},
            )

        result = gateway(handler).complete(
            ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="model-alpha", messages=[{"role": "user", "content": "hi"}], stream=True
            ),
        )
        assert result.content == "pong"
        assert result.usage_reported is True
        assert result.safe_response_metadata["x-request-id"] == "req-stream"


class TestErrorClassification:
    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (401, FailureCategory.MODEL_AUTH),
            (403, FailureCategory.MODEL_AUTH),
            (429, FailureCategory.MODEL_RATE_LIMIT),
            (400, FailureCategory.MODEL_INCOMPATIBLE),
            (404, FailureCategory.MODEL_INCOMPATIBLE),
            (422, FailureCategory.MODEL_INCOMPATIBLE),
            (500, FailureCategory.MODEL_RELAY_UNAVAILABLE),
            (503, FailureCategory.MODEL_RELAY_UNAVAILABLE),
        ],
    )
    def test_status_mapping(self, status: int, expected: FailureCategory) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response({"error": {"message": "boom"}}, status=status)

        with pytest.raises(RelayHTTPError) as exc_info:
            gateway(handler).list_models(ENDPOINT, CREDENTIAL)
        assert exc_info.value.category is expected

    def test_error_message_redacted(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response(
                {"error": {"message": "invalid key sk-secret-token-987654321"}}, status=401
            )

        with pytest.raises(RelayHTTPError) as exc_info:
            gateway(handler).list_models(ENDPOINT, CREDENTIAL)
        assert "sk-secret-token-987654321" not in str(exc_info.value)
