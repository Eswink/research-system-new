#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from typing import Any

from common import ask, deny, read_event_result

SENSITIVE_PATH_RE = re.compile(
    r"(?i)(?:^|[/\\])(?:\.env(?:[.-][^/\\]*)?|\.ssh|\.aws|\.kube|credentials?|secrets?)(?:$|[/\\])"
)
SECRET_MATERIAL_RE = re.compile(
    r"(?i)(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{20,}\b|"
    r"(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*[^\s,}\]]{8,})"
)


def _parse_tool_input(event: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """从 beforeMCPExecution 事件解析 MCP 参数对象。

    Cursor 3.16.29 实测字段为 tool_input（JSON 字符串）；官方文档称 arguments。
    两者都接受 dict 或 JSON 对象字符串；空字符串视为空参数。
    """
    for key in ("arguments", "tool_input"):
        raw = event.get(key)
        if raw is None:
            continue
        if isinstance(raw, str):
            text = raw.strip()
            if not text:
                return {}, None
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                return None, f"{key} 不是有效 JSON: {exc.msg}"
            if not isinstance(parsed, dict):
                return None, f"{key} 解析结果不是对象"
            return parsed, None
        if isinstance(raw, dict):
            return raw, None
        return None, f"{key} 类型无效"
    return None, "缺少有效的 arguments/tool_input 字段"


def main() -> int:
    event, error = read_event_result()
    if error is not None:
        deny(
            f"安全门禁无法解析 Cursor Hook 输入，已按 fail-closed 拒绝 MCP 调用：{error}",
            "这是项目 Hook 环境内部错误，模型侧无法修复。请停止重试该调用，"
            "并告知用户检查 Cursor Hook 环境与 .cursor/hooks/ 配置。",
        )
        return 0
    assert event is not None

    tool_name = event.get("tool_name")
    if not isinstance(tool_name, str) or not tool_name.strip():
        deny(
            "安全门禁缺少有效的 tool_name 字段，已按 fail-closed 拒绝 MCP 调用。",
            "beforeMCPExecution 事件必须提供非空工具名（tool_name）。",
        )
        return 0

    # Cursor 3.16.29 实测：tool_input 为 JSON 字符串（"{\"action\":\"list\"}"）；
    # 官方文档称参数字段为 arguments。两个字段名与 dict/字符串两种形态都接受。
    tool_input, parse_error = _parse_tool_input(event)
    if parse_error is not None:
        deny(
            f"安全门禁无法解析 MCP 调用参数，已按 fail-closed 拒绝：{parse_error}",
            "beforeMCPExecution 的 arguments/tool_input 必须是 JSON 对象字符串或对象。不要改写参数重试。",
        )
        return 0
    assert tool_input is not None

    serialized = json.dumps(tool_input, ensure_ascii=False, sort_keys=True)
    if SECRET_MATERIAL_RE.search(serialized):
        deny(
            "MCP 调用参数疑似包含明文凭据/私钥；请改用受控 credential reference。",
            "该 MCP 调用参数被安全策略阻断。不要改写参数重试；"
            "改用受控 credential reference 后重新请求确认。",
        )
        return 0
    if SENSITIVE_PATH_RE.search(serialized):
        deny(
            "MCP 调用参数引用了敏感 credential 路径；禁止通过 MCP 读取/转发该路径。",
            "该路径被安全策略阻断。不要通过其他 MCP 或工具读取该路径；"
            "改用脱敏示例或受控 credential mechanism。",
        )
        return 0

    ask(
        "该 MCP 调用访问外部系统，需要显式确认。",
        "等待用户确认此 MCP 调用；不要通过 Shell、其他 MCP 或重试绕过该确认。",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
