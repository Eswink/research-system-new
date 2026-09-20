"""Anthropic Messages 形态离线判据（httpx.MockTransport，无真实网络）。

覆盖 EC-01 的三类判据：
- 正向：`protocol=ANTHROPIC` 走 Messages 形态（路径 / 鉴权头 / 请求体 / 响应解析）；
- 回归：`protocol=OPENAI_COMPATIBLE` 的线上形态与改动前一致（含**不含** max_tokens 键）；
- fail-closed：未知协议 / 缺 max_tokens / 流式 / response_format ⇒ 点名拒绝且**零出站**。
"""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

from adapters.relay.protocols import ANTHROPIC_VERSION, WireShape, select_wire_shape
from adapters.relay.transport import RelayHTTPError
from packages.application.ports import CompletionRequest, SecretValue
from packages.domain.models import LLMEndpoint

from .relay_fakes import gateway, json_response

# 不可用的占位凭据（与真实端点无关）；断言只比对其在头里的位置，不回显。
PLACEHOLDER_KEY = "placeholder-not-a-real-credential"
CREDENTIAL = SecretValue(PLACEHOLDER_KEY)
BASE_URL = "https://relay.example.com/api/v1"

MESSAGES_ENDPOINT = LLMEndpoint(
    id="anthropic-main",
    name="Anthropic Relay",
    protocol="ANTHROPIC",
    base_url=BASE_URL,
    credential_ref="llm_main_key",
    max_retries=0,
)
CHAT_ENDPOINT = LLMEndpoint(
    id="openai-main",
    name="OpenAI Relay",
    protocol="OPENAI_COMPATIBLE",
    base_url=BASE_URL,
    credential_ref="llm_main_key",
    max_retries=0,
)


def messages_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "relay-model-alpha",
        "content": [{"type": "text", "text": "pong"}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 7, "output_tokens": 2},
    }
    payload.update(overrides)
    return payload


def counting_gateway(
    handler: Callable[[httpx.Request], httpx.Response],
) -> tuple[object, list[httpx.Request]]:
    """记录每一次出站请求，用于「拒绝时出站为 0」的判据。"""
    seen: list[httpx.Request] = []

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    return gateway(recording), seen


class TestAnthropicMessagesShape:
    def test_request_shape_and_response_parse(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/messages"
            assert request.headers["x-api-key"] == PLACEHOLDER_KEY
            assert request.headers["anthropic-version"] == ANTHROPIC_VERSION
            # Messages 形态不使用 Bearer 鉴权：不得同时发出 Authorization
            assert "authorization" not in request.headers
            body = json.loads(request.content)
            assert body["model"] == "relay-model-alpha"
            assert body["max_tokens"] == 256
            assert body["messages"] == [{"role": "user", "content": "hi"}]
            assert "stream" not in body
            return json_response(messages_payload(), headers={"x-request-id": "req-msg"})

        result = gateway(handler).complete(
            MESSAGES_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="relay-model-alpha",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=256,
            ),
        )
        assert result.content == "pong"
        assert result.returned_model_name == "relay-model-alpha"
        assert result.prompt_tokens == 7
        assert result.completion_tokens == 2
        assert result.total_tokens == 9
        assert result.usage_reported is True
        assert result.safe_response_metadata["x-request-id"] == "req-msg"

    def test_system_fingerprint_is_not_invented(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response(messages_payload())

        result = gateway(handler).complete(
            MESSAGES_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="relay-model-alpha",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=64,
            ),
        )
        # 该形态没有等价字段：必须是 None，不得拿别的字段顶替
        assert result.system_fingerprint is None

    def test_system_message_is_hoisted_to_top_level(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["system"] == "be terse"
            assert body["messages"] == [{"role": "user", "content": "hi"}]
            return json_response(messages_payload())

        gateway(handler).complete(
            MESSAGES_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="relay-model-alpha",
                messages=[
                    {"role": "system", "content": "be terse"},
                    {"role": "user", "content": "hi"},
                ],
                max_tokens=64,
            ),
        )

    def test_tools_are_translated_to_input_schema(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["tools"] == [
                {
                    "name": "pong",
                    "description": "Always return pong",
                    "input_schema": {"type": "object"},
                }
            ]
            return json_response(messages_payload())

        gateway(handler).complete(
            MESSAGES_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="relay-model-alpha",
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
                max_tokens=64,
            ),
        )

    def test_tool_use_block_becomes_tool_call(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response(
                messages_payload(
                    content=[
                        {"type": "text", "text": "calling"},
                        {
                            "type": "tool_use",
                            "id": "toolu_1",
                            "name": "pong",
                            "input": {"value": "x"},
                        },
                    ],
                )
            )

        result = gateway(handler).complete(
            MESSAGES_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="relay-model-alpha",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=64,
            ),
        )
        assert result.content == "calling"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "pong"
        assert json.loads(result.tool_calls[0].arguments) == {"value": "x"}

    def test_usage_absent_is_not_fabricated(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return json_response(messages_payload(usage={}))

        result = gateway(handler).complete(
            MESSAGES_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="relay-model-alpha",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=64,
            ),
        )
        assert result.usage_reported is False
        assert result.total_tokens is None
        assert result.usage_unavailable_reason is not None

    def test_list_models_uses_messages_auth_header(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert request.url.path == "/api/v1/models"
            assert request.headers["x-api-key"] == PLACEHOLDER_KEY
            assert "authorization" not in request.headers
            return json_response({"data": [{"id": "relay-model-alpha"}]})

        result = gateway(handler).list_models(MESSAGES_ENDPOINT, CREDENTIAL)
        assert result.model_ids == ("relay-model-alpha",)


class TestOpenAiShapeRegression:
    """回归对照：OpenAI-compatible 的线上形态必须与改动前一致。"""

    def test_chat_shape_unchanged_and_has_no_max_tokens_key(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/chat/completions"
            assert request.headers["authorization"] == f"Bearer {PLACEHOLDER_KEY}"
            assert "x-api-key" not in request.headers
            body = json.loads(request.content)
            assert body["model"] == "relay-model-alpha"
            assert body["messages"] == [{"role": "user", "content": "hi"}]
            # 关键回归：OpenAI-compatible 请求体**不**携带 max_tokens 键
            assert "max_tokens" not in body
            return json_response(
                {
                    "model": "relay-model-alpha",
                    "choices": [{"message": {"content": "pong"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }
            )

        result = gateway(handler).complete(
            CHAT_ENDPOINT,
            CREDENTIAL,
            CompletionRequest(
                model="relay-model-alpha",
                messages=[{"role": "user", "content": "hi"}],
            ),
        )
        assert result.content == "pong"
        assert result.total_tokens == 2


class TestFailClosed:
    def test_unknown_protocol_refused_with_zero_outbound(self) -> None:
        # 域校验已禁止该取值；此处以绕过 __init__ 的方式构造，
        # 证明**执行侧**同样 fail-closed（纵深防御），且不发起任何请求。
        endpoint = LLMEndpoint(
            id="weird",
            name="Weird Relay",
            protocol="OPENAI_COMPATIBLE",
            base_url=BASE_URL,
            credential_ref="llm_main_key",
            max_retries=0,
        )
        object.__setattr__(endpoint, "protocol", "SOMETHING_ELSE")
        client, seen = counting_gateway(lambda request: json_response({}))
        with pytest.raises(RelayHTTPError) as excinfo:
            client.complete(
                endpoint,
                CREDENTIAL,
                CompletionRequest(model="m", messages=[{"role": "user", "content": "hi"}]),
            )
        assert "unsupported endpoint protocol" in str(excinfo.value)
        assert seen == []

    def test_missing_max_tokens_refused_with_zero_outbound(self) -> None:
        client, seen = counting_gateway(lambda request: json_response(messages_payload()))
        with pytest.raises(RelayHTTPError) as excinfo:
            client.complete(
                MESSAGES_ENDPOINT,
                CREDENTIAL,
                CompletionRequest(model="m", messages=[{"role": "user", "content": "hi"}]),
            )
        assert "requires max_tokens" in str(excinfo.value)
        assert seen == []

    def test_streaming_refused_with_zero_outbound(self) -> None:
        client, seen = counting_gateway(lambda request: json_response(messages_payload()))
        with pytest.raises(RelayHTTPError) as excinfo:
            client.complete(
                MESSAGES_ENDPOINT,
                CREDENTIAL,
                CompletionRequest(
                    model="m",
                    messages=[{"role": "user", "content": "hi"}],
                    max_tokens=64,
                    stream=True,
                ),
            )
        assert "streaming is not implemented" in str(excinfo.value)
        assert seen == []

    def test_response_format_refused_with_zero_outbound(self) -> None:
        client, seen = counting_gateway(lambda request: json_response(messages_payload()))
        with pytest.raises(RelayHTTPError) as excinfo:
            client.complete(
                MESSAGES_ENDPOINT,
                CREDENTIAL,
                CompletionRequest(
                    model="m",
                    messages=[{"role": "user", "content": "hi"}],
                    max_tokens=64,
                    response_format={"type": "json_schema", "json_schema": {"name": "x"}},
                ),
            )
        assert "no response_format equivalent" in str(excinfo.value)
        assert seen == []


class TestWireShapeSelection:
    def test_shapes(self) -> None:
        assert select_wire_shape("ANTHROPIC", "chat_completions") is WireShape.ANTHROPIC_MESSAGES
        assert select_wire_shape("ANTHROPIC", "responses") is WireShape.ANTHROPIC_MESSAGES
        assert (
            select_wire_shape("OPENAI_COMPATIBLE", "chat_completions")
            is WireShape.CHAT_COMPLETIONS
        )
        assert select_wire_shape("OPENAI_COMPATIBLE", "responses") is WireShape.RESPONSES

    def test_unknown_protocol_names_the_legal_values(self) -> None:
        with pytest.raises(RelayHTTPError) as excinfo:
            select_wire_shape("NOPE", "chat_completions")
        message = str(excinfo.value)
        assert "unsupported endpoint protocol" in message
        assert "OPENAI_COMPATIBLE" in message
        assert "ANTHROPIC" in message
