"""Completion 变体执行（gateway 私有拆分）。

chat_completions / responses 两种 API 风格 × 同步/流式，共四种路径；
请求体构造与解析在 chat_api / responses_api / streaming（规模阈值拆分）。
"""

from __future__ import annotations

import json

import httpx

from adapters.relay.chat_api import chat_result, completion_body, safe_headers_from
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
    """按 api_style / stream 分派到对应变体。"""
    if endpoint.api_style == "responses":
        if request.stream:
            return _complete_stream_responses(client, endpoint, credential, request, telemetry)
        return _complete_responses(client, endpoint, credential, request, telemetry)
    if request.stream:
        return _complete_stream(client, endpoint, credential, request, telemetry)
    return _complete_chat(client, endpoint, credential, request, telemetry)


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
