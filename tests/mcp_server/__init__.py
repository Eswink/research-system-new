"""测试 MCP server 支撑包（mock provider，双 transport 共享 tool 定义）。"""

from __future__ import annotations

from tests.mcp_server.server import (
    FAULT_BIG,
    FAULT_NONE,
    FAULT_SCHEMA,
    FAULT_SLOW,
    FAULT_TOOL_ERROR,
    FAULTS,
    build_test_server,
)

__all__ = [
    "FAULTS",
    "FAULT_BIG",
    "FAULT_NONE",
    "FAULT_SCHEMA",
    "FAULT_SLOW",
    "FAULT_TOOL_ERROR",
    "build_test_server",
]
