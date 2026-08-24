"""OpenAI Responses API 请求构造与响应解析（与 gateway.py 拆分保持规模阈值）。

Responses API（POST /responses）与 Chat Completions 的差异：
- 请求：input 替代 messages；tools 为扁平结构（type/name/parameters）；
  response_format 放入 text.format（json_schema 扁平化）；
- 响应：output[] 含 message（content[].text）与 function_call（call_id/name/
  arguments）；usage 用 input_tokens/output_tokens；
- 流：SSE 事件为 response.created / response.output_text.delta /
  response.completed（response 内嵌 model/usage）。
本模块为纯转换，不涉及网络/凭据/错误分类。
"""

from __future__ import annotations

from typing import Any

from packages.application.ports import CompletionRequest, CompletionResult, ToolCallDraft


def responses_body(request: CompletionRequest, *, stream: bool) -> dict[str, Any]:
    """Responses API 请求体（input/tools/text 扁平结构）。"""
    body: dict[str, Any] = {"model": request.model, "input": request.messages}
    if request.tools is not None:
        body["tools"] = [_responses_tool(tool) for tool in request.tools]
    if request.response_format is not None:
        body["text"] = {"format": _responses_format(request.response_format)}
    if stream:
        body["stream"] = True
    return body


def parse_responses_output(payload: dict[str, Any]) -> tuple[str | None, tuple[ToolCallDraft, ...]]:
    """从 responses 响应的 output[] 提取文本与工具调用。"""
    output = payload.get("output") or []
    content_parts: list[str] = []
    tool_calls: list[ToolCallDraft] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "message":
            for content in item.get("content") or []:
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    content_parts.append(content["text"])
        elif item.get("type") == "function_call":
            tool_calls.append(
                ToolCallDraft(
                    id=str(item.get("call_id") or ""),
                    name=str(item.get("name") or ""),
                    arguments=str(item.get("arguments") or ""),
                )
            )
    return ("".join(content_parts) or None, tuple(tool_calls))


def usage_tokens(usage: Any) -> tuple[int | None, int | None, int | None]:
    """Responses usage 字段映射（input/output/total tokens）；缺失返回 None。"""
    if not isinstance(usage, dict):
        return None, None, None
    return (
        _int(usage.get("input_tokens")),
        _int(usage.get("output_tokens")),
        _int(usage.get("total_tokens")),
    )


def _int(value: Any) -> int | None:
    return value if isinstance(value, int) else None


def _responses_tool(tool: dict[str, Any]) -> dict[str, Any]:
    """Chat Completions 风格 tool → Responses 扁平结构（已是扁平则原样）。"""
    if isinstance(tool.get("name"), str):
        return tool
    function = tool.get("function") if isinstance(tool, dict) else None
    if not isinstance(function, dict):
        return tool
    flat: dict[str, Any] = {"type": "function", "name": str(function.get("name") or "")}
    if function.get("description") is not None:
        flat["description"] = function["description"]
    if function.get("parameters") is not None:
        flat["parameters"] = function["parameters"]
    return flat


def _responses_format(response_format: dict[str, Any]) -> dict[str, Any]:
    """Chat Completions response_format → Responses text.format（json_schema 扁平）。"""
    if response_format.get("type") != "json_schema":
        return response_format
    inner = response_format.get("json_schema")
    if not isinstance(inner, dict):
        return response_format
    flat: dict[str, Any] = {"type": "json_schema"}
    if inner.get("name") is not None:
        flat["name"] = inner["name"]
    if inner.get("schema") is not None:
        flat["schema"] = inner["schema"]
    return flat


def responses_result(payload: dict[str, Any], *, safe_headers: dict[str, str]) -> CompletionResult:
    """从 responses 非流式响应构造 CompletionResult。"""
    content, tool_calls = parse_responses_output(payload)
    prompt_tokens, completion_tokens, total_tokens = usage_tokens(payload.get("usage"))
    usage = payload.get("usage")
    return CompletionResult(
        content=content,
        tool_calls=tool_calls,
        returned_model_name=str(payload.get("model")) if payload.get("model") else None,
        system_fingerprint=None,
        usage_reported=isinstance(usage, dict) and usage.get("total_tokens") is not None,
        safe_response_metadata=safe_headers,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        usage_unavailable_reason=(
            None
            if isinstance(usage, dict) and usage.get("total_tokens") is not None
            else "provider did not return usage"
        ),
    )


def merge_responses_result(
    result: CompletionResult,
    *,
    content: str | None,
    tool_calls: tuple[ToolCallDraft, ...],
) -> CompletionResult:
    """用 responses output 覆盖 content/tool_calls，保留其余字段。"""
    return CompletionResult(
        content=content,
        tool_calls=tool_calls,
        returned_model_name=result.returned_model_name,
        system_fingerprint=result.system_fingerprint,
        usage_reported=result.usage_reported,
        safe_response_metadata=result.safe_response_metadata,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
        usage_unavailable_reason=result.usage_unavailable_reason,
    )


__all__ = [
    "merge_responses_result",
    "parse_responses_output",
    "responses_body",
    "usage_tokens",
]