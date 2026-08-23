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

from adapters.relay.parsing import (
    consume_stream_event,
    stream_result,
    tool_calls_from_message,
)
from adapters.relay.sse import parse_sse_events
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


def _completion_body(request: CompletionRequest, *, stream: bool) -> dict[str, Any]:
    body: dict[str, Any] = {"model": request.model, "messages": request.messages}
    if request.tools is not None:
        body["tools"] = request.tools
    if request.response_format is not None:
        body["response_format"] = request.response_format
    if stream:
        body["stream"] = True
    return body


def _usage_int(usage: Any, key: str) -> int | None:
    """从 usage dict 提取整数 token 字段；缺失/非法返回 None（不得伪造）。"""
    if not isinstance(usage, dict):
        return None
    value = usage.get(key)
    if not isinstance(value, int):
        return None
    return value


class OpenAIChatGateway:
    """httpx 实现的 OpenAI-compatible 网关。"""

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
        if request.stream:
            return self._complete_stream(endpoint, credential, request)
        response = self._request(
            "POST",
            _join_url(endpoint.base_url, "/chat/completions"),
            endpoint,
            credential,
            json_body=_completion_body(request, stream=False),
        )
        payload = _decode_json(response, "chat completion")
        choices = payload.get("choices") or []
        message = choices[0].get("message", {}) if choices else {}
        usage = payload.get("usage")
        returned = str(payload.get("model")) if payload.get("model") else None
        fingerprint = (
            str(payload["system_fingerprint"]) if payload.get("system_fingerprint") else None
        )
        return CompletionResult(
            content=str(message.get("content")) if message.get("content") is not None else None,
            tool_calls=tool_calls_from_message(message),
            returned_model_name=returned,
            system_fingerprint=fingerprint,
            usage_reported=isinstance(usage, dict) and usage.get("total_tokens") is not None,
            safe_response_metadata=select_safe_headers(response.headers.items()),
            prompt_tokens=_usage_int(usage, "prompt_tokens"),
            completion_tokens=_usage_int(usage, "completion_tokens"),
            total_tokens=_usage_int(usage, "total_tokens"),
            usage_unavailable_reason=(
                None
                if isinstance(usage, dict) and usage.get("total_tokens") is not None
                else "provider did not return usage"
            ),
        )

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
            json_body=_completion_body(request, stream=True),
        )
        content_parts: list[str] = []
        returned_model: list[str | None] = [None]
        fingerprint: list[str | None] = [None]
        usage_reported: list[bool] = [False]
        try:
            for event in parse_sse_events(response.iter_lines()):
                consume_stream_event(
                    event, content_parts, returned_model, fingerprint, usage_reported
                )
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
        return stream_result(
            content_parts,
            returned_model,
            fingerprint,
            usage_reported,
            select_safe_headers(response.headers.items()),
        )

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
