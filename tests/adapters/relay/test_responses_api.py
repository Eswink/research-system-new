"""OpenAIChatGateway Responses API 路径离线测试（httpx.MockTransport）。"""

from __future__ import annotations

import json

import httpx

from packages.application.ports import CompletionRequest

from .relay_fakes import (
    CREDENTIAL,
    RESPONSES_ENDPOINT,
    gateway,
    json_response,
    sse_response,
)


class TestResponsesApi:
    def test_non_stream_responses(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/responses"
            body = json.loads(request.content)
            assert body["model"] == "model-alpha"
            assert body["input"] == [{"role": "user", "content": "hi"}]
            return json_response(
                {
                    "id": "resp_1",
                    "model": "model-alpha",
                    "output": [
                        {
                            "type": "message",
                            "content": [{"type": "output_text", "text": "pong"}],
                        }
                    ],
                    "usage": {"input_tokens": 5, "output_tokens": 1, "total_tokens": 6},
                },
                headers={"x-request-id": "req-resp"},
            )

        result = gateway(handler).complete(
            RESPONSES_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(model="model-alpha", messages=[{"role": "user", "content": "hi"}]),
        )
        assert result.content == "pong"
        assert result.returned_model_name == "model-alpha"
        assert result.usage_reported is True
        assert result.safe_response_metadata["x-request-id"] == "req-resp"

    def test_responses_function_call_parsed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/responses"
            body = json.loads(request.content)
            # Chat Completions 风格 tool 必须转 Responses 扁平结构
            assert body["tools"] == [
                {
                    "type": "function",
                    "name": "pong",
                    "description": "Always return pong",
                    "parameters": {"type": "object"},
                }
            ]
            return json_response(
                {
                    "model": "model-alpha",
                    "output": [
                        {
                            "type": "function_call",
                            "call_id": "call_1",
                            "name": "pong",
                            "arguments": '{"value":"x"}',
                        }
                    ],
                }
            )

        result = gateway(handler).complete(
            RESPONSES_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="model-alpha",
                messages=[{"role": "user", "content": "hi"}],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "pong",
                            "description": "Always return pong",
                            "parameters": {"type": "object"},
                        },
                    }
                ],
            ),
        )
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "pong"
        assert result.tool_calls[0].arguments == '{"value":"x"}'

    def test_responses_format_mapped(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["text"]["format"] == {
                "type": "json_schema",
                "name": "pong",
                "schema": {"type": "object"},
            }
            return json_response({"model": "model-alpha", "output": []})

        gateway(handler).complete(
            RESPONSES_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="model-alpha",
                messages=[{"role": "user", "content": "hi"}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "pong", "schema": {"type": "object"}},
                },
            ),
        )

    def test_responses_stream_accumulates(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/responses"
            body = json.loads(request.content)
            assert body["stream"] is True
            return sse_response(
                [
                    {"type": "response.created", "response": {"model": "model-alpha"}},
                    {"type": "response.output_text.delta", "delta": "po"},
                    {"type": "response.output_text.delta", "delta": "ng"},
                    {"type": "response.completed", "response": {"usage": {"total_tokens": 6}}},
                ],
                headers={"x-request-id": "req-resp-stream"},
            )

        result = gateway(handler).complete(
            RESPONSES_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="model-alpha", messages=[{"role": "user", "content": "hi"}], stream=True
            ),
        )
        assert result.content == "pong"
        assert result.returned_model_name == "model-alpha"
        assert result.usage_reported is True