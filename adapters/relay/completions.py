"""Completion 变体执行（gateway 私有拆分）。

线形态由 `endpoint.protocol` 决定（`protocols.select_wire_shape`）：OpenAI-compatible
按 `api_style` 分 chat_completions / responses，Messages 形态单独一条；
请求体构造与解析在 chat_api / anthropic_api / responses_api / streaming（规模阈值拆分）。
"""

from __future__ import annotations

import json

import httpx

from adapters.relay.anthropic_api import messages_body, messages_result
from adapters.relay.chat_api import chat_result, completion_body, safe_headers_from
from adapters.relay.protocols import WireShape, request_headers, select_wire_shape
from adapters.relay.responses_api import responses_body, responses_result
from adapters.relay.streaming import consume_responses_stream, consume_stream_response
from adapters.relay.transport import (
    RelayHTTPError,
    decode_json,
    join_url,
    request_with_retries,
)
from packages.application.ports import CompletionRequest, CompletionResult, SecretValue
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.domain.enums import FailureCategory
from packages.domain.models import LLMEndpoint
from packages.domain.redaction import redact_exception_message, select_safe_headers


def complete_any(
    client: httpx.Client,
    endpoint: LLMEndpoint,
    credential: SecretValue,
    request: CompletionRequest,
    telemetry: TelemetrySink | None,
) -> CompletionResult:
    """按 `endpoint.protocol` 选线形态，再按 stream 分派到对应变体。

    未知协议在 `select_wire_shape` 内 fail-closed（抛分类错误，且不发起请求）。
    """
    shape = select_wire_shape(endpoint.protocol, endpoint.api_style)
    if shape is WireShape.ANTHROPIC_MESSAGES:
        return _complete_anthropic(client, endpoint, credential, request, telemetry)
    if shape is WireShape.RESPONSES:
        if request.stream:
            return _complete_stream_responses(client, endpoint, credential, request, telemetry)
        return _complete_responses(client, endpoint, credential, request, telemetry)
    if request.stream:
        return _complete_stream(client, endpoint, credential, request, telemetry)
    return _complete_chat(client, endpoint, credential, request, telemetry)


def _complete_anthropic(
    client: httpx.Client,
    endpoint: LLMEndpoint,
    credential: SecretValue,
    request: CompletionRequest,
    telemetry: TelemetrySink | None,
) -> CompletionResult:
    """Messages 形态（非流式）。

    流式**未实现**：点名拒绝，而不是降级成非流式或套用 OpenAI SSE 解析
    （降级会把「支持流式」变成假象）。
    """
    if request.stream:
        raise RelayHTTPError(
            FailureCategory.MODEL_INCOMPATIBLE,
            "anthropic messages streaming is not implemented; refusing rather than degrading",
        )
    response, _attempts = request_with_retries(
        client,
        "POST",
        join_url(endpoint.base_url, "/messages"),
        endpoint,
        credential,
        json_body=messages_body(request),
        telemetry=telemetry,
        headers=request_headers(endpoint.protocol, credential),
    )
    payload = decode_json(response, "messages")
    return messages_result(payload, safe_headers=safe_headers_from(response))


def _complete_chat(
    client: httpx.Client,
    endpoint: LLMEndpoint,
    credential: SecretValue,
    request: CompletionRequest,
    telemetry: TelemetrySink | None,
) -> CompletionResult:
    response, _attempts = request_with_retries(
        client,
        "POST",
        join_url(endpoint.base_url, "/chat/completions"),
        endpoint,
        credential,
        json_body=completion_body(request, stream=False),
        telemetry=telemetry,
    )
    payload = decode_json(response, "chat completion")
    return chat_result(payload, safe_headers=safe_headers_from(response))


def _complete_responses(
    client: httpx.Client,
    endpoint: LLMEndpoint,
    credential: SecretValue,
    request: CompletionRequest,
    telemetry: TelemetrySink | None,
) -> CompletionResult:
    response, _attempts = request_with_retries(
        client,
        "POST",
        join_url(endpoint.base_url, "/responses"),
        endpoint,
        credential,
        json_body=responses_body(request, stream=False),
        telemetry=telemetry,
    )
    payload = decode_json(response, "responses")
    return responses_result(payload, safe_headers=select_safe_headers(response.headers.items()))


def _complete_stream_responses(
    client: httpx.Client,
    endpoint: LLMEndpoint,
    credential: SecretValue,
    request: CompletionRequest,
    telemetry: TelemetrySink | None,
) -> CompletionResult:
    response, _attempts = request_with_retries(
        client,
        "POST",
        join_url(endpoint.base_url, "/responses"),
        endpoint,
        credential,
        json_body=responses_body(request, stream=True),
        telemetry=telemetry,
    )
    try:
        return consume_responses_stream(response)
    except json.JSONDecodeError as exc:
        raise RelayHTTPError(
            FailureCategory.MODEL_INCOMPATIBLE,
            redact_exception_message(f"malformed stream event: {exc}"),
        ) from exc
    except httpx.HTTPError as exc:
        raise RelayHTTPError(
            FailureCategory.EXECUTION_FAILURE,
            redact_exception_message(f"stream interrupted: {exc}"),
        ) from exc


def _complete_stream(
    client: httpx.Client,
    endpoint: LLMEndpoint,
    credential: SecretValue,
    request: CompletionRequest,
    telemetry: TelemetrySink | None,
) -> CompletionResult:
    response, _attempts = request_with_retries(
        client,
        "POST",
        join_url(endpoint.base_url, "/chat/completions"),
        endpoint,
        credential,
        json_body=completion_body(request, stream=True),
        telemetry=telemetry,
    )
    try:
        return consume_stream_response(response)
    except json.JSONDecodeError as exc:
        raise RelayHTTPError(
            FailureCategory.MODEL_INCOMPATIBLE,
            redact_exception_message(f"malformed stream event: {exc}"),
        ) from exc
    except httpx.HTTPError as exc:
        raise RelayHTTPError(
            FailureCategory.EXECUTION_FAILURE,
            redact_exception_message(f"stream interrupted: {exc}"),
        ) from exc
