"""Chat Completions 响应解析（非 HTTP 层）。

工具调用与 SSE 事件累积逻辑独立于此模块，便于穷尽测试；
不涉及网络、凭据或错误分类。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports import CompletionResult, ToolCallDraft


def tool_calls_from_message(message: dict[str, Any]) -> tuple[ToolCallDraft, ...]:
    raw_calls = message.get("tool_calls") or []
    calls: list[ToolCallDraft] = []
    for raw in raw_calls:
        function = raw.get("function") or {}
        calls.append(
            ToolCallDraft(
                id=str(raw.get("id") or ""),
                name=str(function.get("name") or ""),
                arguments=str(function.get("arguments") or ""),
            )
        )
    return tuple(calls)


def consume_stream_event(
    event: dict[str, object],
    content_parts: list[str],
    returned_model: list[str | None],
    fingerprint: list[str | None],
    usage_reported: list[bool],
) -> None:
    """解析单个 SSE 事件，就地累积流式结果。"""
    raw_choices = event.get("choices")
    if isinstance(raw_choices, list) and raw_choices:
        raw_delta = raw_choices[0].get("delta") if isinstance(raw_choices[0], dict) else None
        if isinstance(raw_delta, dict):
            piece = raw_delta.get("content")
            if isinstance(piece, str) and piece:
                content_parts.append(piece)
    if event.get("usage") is not None:
        usage_reported[0] = True
    raw_model = event.get("model")
    if isinstance(raw_model, str):
        returned_model[0] = raw_model
    raw_fingerprint = event.get("system_fingerprint")
    if isinstance(raw_fingerprint, str):
        fingerprint[0] = raw_fingerprint


def stream_result(
    content_parts: list[str],
    returned_model: list[str | None],
    fingerprint: list[str | None],
    usage_reported: list[bool],
    safe_response_metadata: dict[str, str],
) -> CompletionResult:
    """将累积的流式状态装配为 CompletionResult。"""
    return CompletionResult(
        content="".join(content_parts) or None,
        returned_model_name=returned_model[0],
        system_fingerprint=fingerprint[0],
        usage_reported=usage_reported[0],
        safe_response_metadata=safe_response_metadata,
    )
