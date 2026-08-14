#!/usr/bin/env python3
from __future__ import annotations

import json
import re

from common import ask, deny, read_event_result

SENSITIVE_PATH_RE = re.compile(
    r"(?i)(?:^|[/\\])(?:\.env(?:[.-][^/\\]*)?|\.ssh|\.aws|\.kube|credentials?|secrets?)(?:$|[/\\])"
)
SECRET_MATERIAL_RE = re.compile(
    r"(?i)(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{20,}\b|"
    r"(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*[^\s,}\]]{8,})"
)


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
    tool_input = event.get("tool_input")
    if not isinstance(tool_name, str) or not tool_name.strip() or not isinstance(tool_input, dict):
        deny(
            "安全门禁缺少有效的 tool_name/tool_input 字段，已按 fail-closed 拒绝 MCP 调用。",
            "beforeMCPExecution 事件必须提供非空工具名和对象参数。",
        )
        return 0

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
