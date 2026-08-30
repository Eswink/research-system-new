"""Relay 传输层：错误分类、重试与请求执行（gateway 私有拆分）。

错误分类（docs/reliability/FAILURE_MODEL.md）：
- 401/403 → MODEL_AUTH
- 429 → MODEL_RATE_LIMIT（可重试退避）
- timeout → MODEL_TIMEOUT（可重试退避）
- 5xx → MODEL_RELAY_UNAVAILABLE（中转站故障，可重试退避）
- 其余 4xx（400/404/422...）→ MODEL_INCOMPATIBLE
- 网络/连接错误 → EXECUTION_FAILURE
响应头只采集白名单（Authorization 永不进入结果）；错误消息一律 redacted。
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential, wait_random

from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import record_metric_safely
from packages.application.ports import SecretValue, failure_category_of_http_status
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.domain.enums import FailureCategory
from packages.domain.models import LLMEndpoint
from packages.domain.redaction import redact_exception_message

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


def is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, RelayHTTPError) and exc.category in _RETRYABLE_CATEGORIES


def _make_retrying(max_attempts: int) -> Retrying:
    return Retrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8.0) + wait_random(0, 0.2),
        retry=retry_if_exception(is_retryable),
        reraise=True,
    )


def join_url(base_url: str, path: str) -> str:
    """base_url 已含版本前缀（如 /api/v1），只追加资源路径。"""
    return f"{base_url.rstrip('/')}{path}"


def raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    body = response.text[:500]
    raise RelayHTTPError(
        failure_category_of_http_status(response.status_code),
        redact_exception_message(f"HTTP {response.status_code}: {body}"),
    )


def decode_json(payload: Any, context: str) -> Any:
    try:
        return payload.json()
    except (ValueError, json.JSONDecodeError) as exc:
        raise RelayHTTPError(
            FailureCategory.MODEL_INCOMPATIBLE,
            redact_exception_message(f"malformed {context} response: {exc}"),
        ) from exc


def _note_internal_retry(telemetry: TelemetrySink | None) -> None:
    """内部重试可见性(每次额外 HTTP 尝试计 1);telemetry 为 None 时零开销。"""
    record_metric_safely(
        telemetry,
        lambda: MetricSample(
            name=MetricName.LLM_CALL_RETRY_ATTEMPTS, kind=MetricKind.COUNTER, value=1
        ),
    )


def request_with_retries(  # noqa: PLR0913 - HTTP 语义参数完整,分组对象会降低可读性
    client: httpx.Client,
    method: str,
    url: str,
    endpoint: LLMEndpoint,
    credential: SecretValue,
    *,
    json_body: dict[str, Any] | None = None,
    telemetry: TelemetrySink | None = None,
) -> tuple[httpx.Response, int]:
    """执行请求,返回 (response, attempts) 使内部重试对外可见。"""
    headers = {
        "Authorization": f"Bearer {credential.value}",
        "Accept": "application/json",
    }
    retrying = _make_retrying(max(1, endpoint.max_retries + 1))
    attempts = 0
    for attempt in retrying:
        with attempt:
            attempts += 1
            try:
                response = client.request(
                    method,
                    url,
                    headers=headers,
                    json=json_body,
                    timeout=endpoint.request_timeout_seconds,
                )
            except httpx.TimeoutException as exc:
                _note_internal_retry(telemetry)
                raise RelayHTTPError(
                    FailureCategory.MODEL_TIMEOUT,
                    redact_exception_message(f"request timed out: {exc}"),
                ) from exc
            except httpx.HTTPError as exc:
                _note_internal_retry(telemetry)
                raise RelayHTTPError(
                    FailureCategory.EXECUTION_FAILURE,
                    redact_exception_message(f"transport error: {exc}"),
                ) from exc
            try:
                raise_for_status(response)
            except RelayHTTPError as exc:
                if is_retryable(exc):
                    _note_internal_retry(telemetry)
                raise
            return response, attempts
    raise AssertionError("unreachable: tenacity must reraise")
