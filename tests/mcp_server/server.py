"""M8 本地测试 MCP server（mock Research Tool Provider，非真实第三方工具）。"""

from __future__ import annotations

import time

from mcp.server.fastmcp import FastMCP

FAULT_NONE = "none"
FAULT_TOOL_ERROR = "tool_error"
FAULT_SLOW = "slow"
FAULT_BIG = "big"
FAULT_SCHEMA = "schema"
FAULTS = (FAULT_NONE, FAULT_TOOL_ERROR, FAULT_SLOW, FAULT_BIG, FAULT_SCHEMA)


def _register_base_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def literature_search(query: str = "") -> dict[str, object]:
        """Mock literature search（无真实第三方数据）。"""
        return {"query": query, "hits": [{"id": "doc-1", "title": "Mock paper"}]}

    @mcp.tool()
    def citation_inspect(citation_id: str = "") -> dict[str, object]:
        """Mock citation inspection."""
        return {"citation_id": citation_id, "cited_by": 3}


def _register_fault_tools(mcp: FastMCP, fault: str) -> None:
    if fault == FAULT_SCHEMA:

        @mcp.tool()
        def schema_drift_tool() -> str:
            """额外 tool：模拟 server 升级后的 schema 漂移。"""
            return "drifted"

    if fault == FAULT_TOOL_ERROR:

        @mcp.tool()
        def failing_tool(reason: str = "") -> str:
            raise RuntimeError(f"injected failure: {reason or 'fault-tool_error'}")

    if fault == FAULT_SLOW:

        @mcp.tool()
        def slow_tool() -> str:
            time.sleep(10)
            return "late"

    if fault == FAULT_BIG:

        @mcp.tool()
        def big_tool() -> str:
            return "x" * (64 * 1024)


def build_test_server(fault: str = FAULT_NONE) -> FastMCP:
    """构建测试 MCP server；fault 开关注入确定性故障。"""
    mcp = FastMCP("research-tools-test", json_response=True)
    _register_base_tools(mcp)
    _register_fault_tools(mcp, fault)
    return mcp
