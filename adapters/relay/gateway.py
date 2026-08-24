"""OpenAI-compatible Chat Completions 网关（httpx + tenacity）。

协议基线：OpenAI openapi.yaml v2.3.0 的 `/v1/chat/completions` 与 `/v1/models`。
错误分类（docs/reliability/FAILURE_MODEL.md）：
- 401/403 → MODEL_AUTH
- 429 → MODEL_RATE_LIMIT（可重试退避）
- timeout → MODEL_TIMEOUT（可重试退避）
- 5xx → MODEL_RELAY_UNAVAILABLE（中转站故障，可重试退避）
- 其余 4xx（400/404/422...）→ MODEL_INCOMPATIBLE（模型不支持某能力/请求不兼容）
- 网络/连接错误 → EXECUTION_FAILURE
响应头只采集白名单（Authorization 永不进入结果）；错误消息一律 redacted。
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential, wait_random

from adapters.relay.chat_api import (
    chat_result,
    completion_body,
    safe_headers_from,
)
from adapters.relay.responses_api import (
    responses_body,
    responses_result,
)
from adapters.relay.streaming import (
    consume_responses_stream,
    consume_stream_response,
)
from packages.application.ports import (
    CompletionRequest,
    CompletionResult,
    ModelsListResult,
    SecretValue,
    failure_category_of_http_status,
)
from packages.domain.enums import FailureCategory
from packages.domain.models import EndpointProbeSnapshot, LLMEndpoint
from packages.domain.redaction import redact_exception_message, select_safe_headers

_RETRYABLE_CATEGORIES = frozenset({
    FailureCategory.MODEL_RATE_LIMIT,
    FailureCategory.MODEL_TIMEOUT,
    FailureCategory.MODEL_RELAY_UNAVAILABLE,
})


class RelayHTTPError(RuntimeError):
    """带失败分类的 HTTP/传输错误；message 已 redacted。"""

    def __init__(self, category: FailureCategory, message: str) -> None:
        super().__init__(message)
        self.category = category


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, RelayHTTPError) and exc.category in _RETRYABLE_CATEGORIES


def _make_retrying(max_attempts: int) -> Retrying:
    return Retrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8.0) + wait_random(0, 0.2),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )


def _join_url(base_url: str, path: str) -> str:
    """base_url 已含版本前缀（如 /api/v1），只追加资源路径。"""
    return f"{base_url.rstrip('/')}{path}"


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    body = response.text[:500]
    raise RelayHTTPError(
        failure_category_of_http_status(response.status_code),
        redact_exception_message(f"HTTP {response.status_code}: {body}"),
    )


def _decode_json(payload: Any, context: str) -> Any:
    try:
        return payload.json()
    except (ValueError, json.JSONDecodeError) as exc:
        raise RelayHTTPError(
            FailureCategory.MODEL_INCOMPATIBLE,
            redact_exception_message(f"malformed {context} response: {exc}"),
        ) from exc


class OpenAIChatGateway:
    """OpenAI-compatible 网关（httpx + tenacity）。

    支持 chat_completions 与 responses 两种 API 风格（LLMEndpoint.api_style），
    共用 error classification / retry / 脱敏；请求/解析在 chat_api /
    responses_api / streaming（规模阈值拆分）。
    """

    def __init__(
        self,
        transport: httpx.BaseTransport | None = None,
        default_timeout_seconds: float = 60.0,
    ) -> None:
        self._client = httpx.Client(transport=transport, timeout=default_timeout_seconds)

    def _request(
        self,
        method: str,
        url: str,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {credential.value}",
            "Accept": "application/json",
        }
        retrying = _make_retrying(max(1, endpoint.max_retries + 1))
        for attempt in retrying:
            with attempt:
                try:
                    response = self._client.request(
                        method,
                        url,
                        headers=headers,
                        json=json_body,
                        timeout=endpoint.request_timeout_seconds,
                    )
                except httpx.TimeoutException as exc:
                    raise RelayHTTPError(
                        FailureCategory.MODEL_TIMEOUT,
                        redact_exception_message(f"request timed out: {exc}"),
                    ) from exc
                except httpx.HTTPError as exc:
                    raise RelayHTTPError(
                        FailureCategory.EXECUTION_FAILURE,
                        redact_exception_message(f"transport error: {exc}"),
                    ) from exc
                _raise_for_status(response)
                return response
        raise AssertionError("unreachable: tenacity must reraise")

    def list_models(self, endpoint: LLMEndpoint, credential: SecretValue) -> ModelsListResult:
        url = _join_url(endpoint.base_url, "/models")
        response = self._request("GET", url, endpoint, credential)
        payload = _decode_json(response, "models")
        ids = tuple(
            str(item.get("id")) for item in payload.get("data", []) if isinstance(item, dict)
        )
        return ModelsListResult(model_ids=ids)

    def complete(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult:
        if endpoint.api_style == "responses":
            if request.stream:
                return self._complete_stream_responses(endpoint, credential, request)
            return self._complete_responses(endpoint, credential, request)
        if request.stream:
            return self._complete_stream(endpoint, credential, request)
        return self._complete_chat(endpoint, credential, request)

    def _complete_chat(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult:
        response = self._request(
            "POST",
            _join_url(endpoint.base_url, "/chat/completions"),
            endpoint,
            credential,
            json_body=completion_body(request, stream=False),
        )
        payload = _decode_json(response, "chat completion")
        return chat_result(payload, safe_headers=safe_headers_from(response))

    def _complete_responses(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult:
        response = self._request(
            "POST",
            _join_url(endpoint.base_url, "/responses"),
            endpoint,
            credential,
            json_body=responses_body(request, stream=False),
        )
        payload = _decode_json(response, "responses")
        return responses_result(payload, safe_headers=select_safe_headers(response.headers.items()))

    def _complete_stream_responses(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult:
        response = self._request(
            "POST",
            _join_url(endpoint.base_url, "/responses"),
            endpoint,
            credential,
            json_body=responses_body(request, stream=True),
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
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> CompletionResult:
        response = self._request(
            "POST",
            _join_url(endpoint.base_url, "/chat/completions"),
            endpoint,
            credential,
            json_body=completion_body(request, stream=True),
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

    def probe_connectivity(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
    ) -> EndpointProbeSnapshot:
        """GET /models 连通性探测：任意失败返回快照，不抛异常。"""
        try:
            self.list_models(endpoint, credential)
        except RelayHTTPError as exc:
            return EndpointProbeSnapshot(
                ok=False,
                error_category=exc.category,
                error_message_redacted=str(exc),
            )
        return EndpointProbeSnapshot(ok=True)

    def probe_endpoint(
        self,
        endpoint: LLMEndpoint,
        credential: SecretValue,
        request: CompletionRequest,
    ) -> EndpointProbeSnapshot:
        """endpoint 探测：任意失败都返回快照，不抛异常。"""
        try:
            result = self.complete(endpoint, credential, request)
        except RelayHTTPError as exc:
            return EndpointProbeSnapshot(
                ok=False,
                error_category=exc.category,
                error_message_redacted=str(exc),
            )
        return EndpointProbeSnapshot(
            ok=True,
            returned_model_name=result.returned_model_name,
            system_fingerprint=result.system_fingerprint,
            safe_response_metadata=dict(result.safe_response_metadata),
            usage_reported=result.usage_reported,
        )

    def close(self) -> None:
        self._client.close()
