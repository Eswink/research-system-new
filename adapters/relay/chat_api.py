"""Chat Completions 请求构造与响应解析 helper（与 gateway.py 拆分）。

纯转换，不涉及网络/凭据/错误分类：body 构造、usage 提取、响应解析。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports import CompletionRequest, CompletionResult
from packages.domain.redaction import select_safe_headers


def completion_body(request: CompletionRequest, *, stream: bool) -> dict[str, Any]:
    """Chat Completions 请求体。"""
    body: dict[str, Any] = {"model": request.model, "messages": request.messages}
    if request.tools is not None:
        body["tools"] = request.tools
    if request.response_format is not None:
        body["response_format"] = request.response_format
    if stream:
        body["stream"] = True
    return body


def usage_int(usage: Any, key: str) -> int | None:
    """从 usage dict 提取整数 token 字段；缺失/非法返回 None（不得伪造）。"""
    if not isinstance(usage, dict):
        return None
    value = usage.get(key)
    if not isinstance(value, int):
        return None
    return value


def chat_result(
    response_payload: dict[str, Any],
    *,
    safe_headers: dict[str, str],
) -> CompletionResult:
    """从 chat.completions 响应构造 CompletionResult。"""
    choices = response_payload.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    usage = response_payload.get("usage")
    returned = str(response_payload.get("model")) if response_payload.get("model") else None
    fingerprint = (
        str(response_payload["system_fingerprint"])
        if response_payload.get("system_fingerprint")
        else None
    )
    from adapters.relay.parsing import tool_calls_from_message

    return CompletionResult(
        content=str(message.get("content")) if message.get("content") is not None else None,
        tool_calls=tool_calls_from_message(message),
        returned_model_name=returned,
        system_fingerprint=fingerprint,
        usage_reported=isinstance(usage, dict) and usage.get("total_tokens") is not None,
        safe_response_metadata=safe_headers,
        prompt_tokens=usage_int(usage, "prompt_tokens"),
        completion_tokens=usage_int(usage, "completion_tokens"),
        total_tokens=usage_int(usage, "total_tokens"),
        usage_unavailable_reason=(
            None
            if isinstance(usage, dict) and usage.get("total_tokens") is not None
            else "provider did not return usage"
        ),
    )


def safe_headers_from(response: Any) -> dict[str, str]:
    """从 httpx.Response 提取白名单 header。"""
    return select_safe_headers(response.headers.items())


__all__ = ["chat_result", "completion_body", "safe_headers_from", "usage_int"]