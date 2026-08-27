"""SSE 流式响应消费 helper（与 gateway.py 拆分保持规模阈值）。

consume_stream_response / consume_responses_stream 分别处理
chat.completions chunk 与 Responses API 事件，返回累积的
content/model/fingerprint/usage 状态。
"""

from __future__ import annotations

from typing import Any

from adapters.relay.parsing import (
    consume_responses_stream_event,
    consume_stream_event,
    stream_result,
)
from adapters.relay.sse import parse_sse_events
from packages.application.ports import CompletionResult


def consume_stream_response(response: Any) -> CompletionResult:
    """消费 chat.completions SSE 流并装配 CompletionResult。"""
    content_parts: list[str] = []
    returned_model: list[str | None] = [None]
    fingerprint: list[str | None] = [None]
    usage_reported: list[bool] = [False]
    for event in parse_sse_events(response.iter_lines()):
        consume_stream_event(event, content_parts, returned_model, fingerprint, usage_reported)
    return stream_result(
        content_parts,
        returned_model,
        fingerprint,
        usage_reported,
        _safe_headers(response),
    )


def consume_responses_stream(response: Any) -> CompletionResult:
    """消费 Responses API SSE 流并装配 CompletionResult。"""
    content_parts: list[str] = []
    returned_model: list[str | None] = [None]
    fingerprint: list[str | None] = [None]
    usage_reported: list[bool] = [False]
    for event in parse_sse_events(response.iter_lines()):
        consume_responses_stream_event(
            event, content_parts, returned_model, fingerprint, usage_reported
        )
    return stream_result(
        content_parts,
        returned_model,
        fingerprint,
        usage_reported,
        _safe_headers(response),
    )


def _safe_headers(response: Any) -> dict[str, str]:
    from packages.domain.redaction import select_safe_headers

    return select_safe_headers(response.headers.items())


__all__ = ["consume_responses_stream", "consume_stream_response"]
