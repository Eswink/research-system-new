"""Anthropic Messages 形态的请求构造与响应解析（与 chat_api / responses_api 同层）。

纯转换，不涉及网络/凭据/错误分类；形态差异集中在本模块，避免散落网关。

形态事实（与 OpenAI-compatible 的差异）：
- 路径 `/messages`；鉴权头 `x-api-key` + `anthropic-version`（见 `protocols.py`）；
- `max_tokens` **必填**；
- `system` 是**顶层参数**，不出现在 `messages` 里；
- 响应文本在 `content[]` 的 `text` 块；工具调用是 `tool_use` 块；
- usage 是 `input_tokens` / `output_tokens`（**没有** `total_tokens`）；
- **没有** `system_fingerprint` 等价字段（保持 None，不得拿别的字段顶替）。

不支持即**点名拒绝**：`stream`（见 completions）与 `response_format`（本模块）都没有
实现，缺失/不支持的形态一律拒绝而不是静默丢弃或降级。
"""

from __future__ import annotations

import json
from typing import Any

from adapters.relay.chat_api import usage_int
from adapters.relay.transport import RelayHTTPError
from packages.application.ports import CompletionRequest, CompletionResult, ToolCallDraft
from packages.domain.enums import FailureCategory


def messages_body(request: CompletionRequest) -> dict[str, Any]:
    """Messages 形态请求体。

    `max_tokens` 缺失 ⇒ 点名拒绝：编造默认值会在**不可见**的情况下截断输出。
    `response_format` 非空 ⇒ 点名拒绝：Messages 形态没有该参数，静默丢弃等于
    声称支持了没支持的能力。
    """
    if request.max_tokens is None:
        raise RelayHTTPError(
            FailureCategory.MODEL_INCOMPATIBLE,
            "anthropic messages shape requires max_tokens (none supplied by caller)",
        )
    if request.response_format is not None:
        raise RelayHTTPError(
            FailureCategory.MODEL_INCOMPATIBLE,
            "anthropic messages shape has no response_format equivalent (not implemented)",
        )
    system, messages = split_system(request.messages)
    body: dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_tokens,
        "messages": messages,
    }
    if system:
        body["system"] = system
    if request.tools:
        body["tools"] = [tool_spec(item) for item in request.tools]
    return body


def split_system(
    messages: list[dict[str, object]],
) -> tuple[str | None, list[dict[str, object]]]:
    """把 system 消息抽到顶层参数；其余消息按原序保留。

    非字符串 content 点名拒绝（Messages 的内容块形态与本仓既有用法不同，
    不在此处猜译）。
    """
    system_parts: list[str] = []
    rest: list[dict[str, object]] = []
    for message in messages:
        content = message.get("content")
        if not isinstance(content, str):
            raise RelayHTTPError(
                FailureCategory.MODEL_INCOMPATIBLE,
                "anthropic messages shape supports string content only (got non-string)",
            )
        if message.get("role") == "system":
            system_parts.append(content)
            continue
        rest.append(message)
    return ("\n\n".join(system_parts) or None), rest


def tool_spec(item: dict[str, object]) -> dict[str, object]:
    """OpenAI `{type:function,function:{...}}` ⇒ Messages `{name,description,input_schema}`."""
    function = item.get("function")
    source = function if isinstance(function, dict) else item
    spec: dict[str, object] = {"name": source.get("name")}
    if source.get("description") is not None:
        spec["description"] = source["description"]
    parameters = source.get("parameters")
    spec["input_schema"] = parameters if parameters is not None else {"type": "object"}
    return spec


def tool_calls_from_content(payload: dict[str, Any]) -> tuple[ToolCallDraft, ...]:
    """`tool_use` 块 ⇒ ToolCallDraft（arguments 为该块的 input 的 JSON 文本）。"""
    drafts: list[ToolCallDraft] = []
    for block in payload.get("content") or []:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        drafts.append(
            ToolCallDraft(
                id=str(block.get("id") or ""),
                name=str(block.get("name") or ""),
                arguments=json.dumps(block.get("input") if block.get("input") is not None else {}),
            )
        )
    return tuple(drafts)


def text_from_content(payload: dict[str, Any]) -> str | None:
    """`content[]` 的 text 块按序拼接；无文本块返回 None。"""
    parts = [
        str(block["text"])
        for block in payload.get("content") or []
        if isinstance(block, dict) and block.get("type") == "text" and block.get("text") is not None
    ]
    return "".join(parts) if parts else None


def messages_result(
    payload: dict[str, Any],
    *,
    safe_headers: dict[str, str],
) -> CompletionResult:
    """从 Messages 响应构造 CompletionResult（口径与 chat_result 对齐）。"""
    usage = payload.get("usage")
    prompt_tokens = usage_int(usage, "input_tokens")
    completion_tokens = usage_int(usage, "output_tokens")
    # 该形态不报 total：两项都在时才给出和，否则保持 None（不伪造）。
    total_tokens: int | None = None
    if prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens
    returned = payload.get("model")
    return CompletionResult(
        content=text_from_content(payload),
        tool_calls=tool_calls_from_content(payload),
        returned_model_name=str(returned) if returned else None,
        # Messages 无 system fingerprint 等价字段：保持 None，不拿别的字段顶替。
        system_fingerprint=None,
        usage_reported=total_tokens is not None,
        safe_response_metadata=safe_headers,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        usage_unavailable_reason=(
            None
            if total_tokens is not None
            else "provider did not return input_tokens/output_tokens"
        ),
    )


__all__ = [
    "messages_body",
    "messages_result",
    "split_system",
    "text_from_content",
    "tool_calls_from_content",
    "tool_spec",
]
