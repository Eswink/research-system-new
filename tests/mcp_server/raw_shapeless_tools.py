"""Raw stdio fixture：申报一个**形状不符**的工具声明（空名字），用于 EC-02 反证判据。

它不是产品件，是**测试夹具**（同类先例：`tests/mcp_server/server.py` 的 FAULT_SCHEMA）。
它故意绕开 FastMCP，直接讲 stdio 的 JSON-RPC（MCP stdio 传输是换行分隔的 JSON 消息）：

- `initialize`：回显调用方请求的 `protocolVersion`（恒为受支持版本），声明 tools 能力；
- `tools/list`：返回**一条 `name` 为空字符串的 tool** —— 这违反调用方对工具声明的形状
  要求（`ToolSpec` 要求 name 非空），调用方必须**点名拒绝**（`TOOL_SCHEMA_MISMATCH`），
  而不是静默丢弃这条声明、装作只有剩下的工具；
- 其它带 id 的请求：回 JSON-RPC error（不静默不回）；

**它没有** `tools/call` 行为：本夹具唯一的被测面是「声明不符」在 list_tools / check_health
上的拒绝形态。它不出网、不读环境、不落任何文件。
"""

from __future__ import annotations

import json
import sys
from typing import Any

FIXTURE_NAME = "raw-shapeless-fixture"

#: 形状不符的声明：`name` 为空串（空名字的工具在调用方会被 ToolSpec 拒绝）。
SHAPELESS_TOOL: dict[str, object] = {
    "name": "",
    "description": "tool declaration with an empty name (deliberate shape violation)",
    "inputSchema": {"type": "object", "properties": {}},
}


def _reply(message_id: object, result: dict[str, object]) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _initialize_result(message: dict[str, Any]) -> dict[str, object]:
    """回显调用方请求的协议版本（恒为它支持的版本），声明 tools 能力。"""
    params = message.get("params")
    requested = params.get("protocolVersion") if isinstance(params, dict) else None
    version = requested if isinstance(requested, str) and requested else "2025-11-25"
    return {
        "protocolVersion": version,
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": {"name": FIXTURE_NAME, "version": "0.0.1"},
    }


def respond(message: dict[str, Any]) -> dict[str, object] | None:
    """一条入站消息 → 一条出站响应（通知类消息回 None）。"""
    method = message.get("method")
    if method == "initialize":
        return _reply(message.get("id"), _initialize_result(message))
    if method == "tools/list":
        return _reply(message.get("id"), {"tools": [dict(SHAPELESS_TOOL)]})
    if "id" not in message:
        return None  # 通知（如 notifications/initialized）：无需响应
    return {
        "jsonrpc": "2.0",
        "id": message.get("id"),
        "error": {"code": -32601, "message": f"not supported by fixture: {method!r}"},
    }


def main() -> None:
    """读 stdin 的换行分隔 JSON 消息，逐条响应；stdin 关闭即退出。"""
    for line in sys.stdin:
        stripped = line.strip()
        if not stripped:
            continue
        parsed: object = json.loads(stripped)
        if not isinstance(parsed, dict):
            continue
        response = respond(parsed)
        if response is None:
            continue
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
