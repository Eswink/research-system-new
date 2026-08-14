"""MCP transport 会话管理（stdio / Streamable HTTP）。

只在本 adapter 层消费 mcp SDK 类型（import-linter 强制 Domain/Application
不可见）。每次操作建立独立会话（stateless per-op），保证同步 Port 语义
简单可靠；连接生命周期完全由本模块控制。spec.timeout_seconds 对两种
transport 都是硬超时：操作（initialize/call_tool/list_tools）经
with_hard_timeout 强制中断；HTTP 请求面用 httpx.Timeout(connect=read=
timeout_seconds) 约束（v1 废弃的 streamablehttp_client 只约束 connect，
sse_read_timeout 默认 300s，故改用 streamable_http_client + 自建 client）。
超时取消触发的 SDK TaskGroup 关闭异常在本模块归一化为 TimeoutError
（provider 映射 TOOL_TIMEOUT，避免误分类为连接失败）。
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Mapping, TypeVar

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult

_T = TypeVar("_T")

_TIMEOUT_TYPES = (TimeoutError, httpx.TimeoutException)


@dataclass(frozen=True, slots=True)
class McpConnectionSpec:
    """MCP 连接规格：stdio 子进程或 Streamable HTTP 端点。

    凭据不在 spec 内：由 McpToolProvider 经 CredentialResolver 按
    credential_ref 解析后注入 transport headers（禁止 token passthrough）。
    """

    transport: str  # "stdio" | "streamable_http"
    command: tuple[str, ...] = ()
    env: Mapping[str, str] = field(default_factory=dict)
    url: str | None = None
    headers: Mapping[str, str] = field(default_factory=dict)
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.transport == "stdio":
            if not self.command:
                raise ValueError("stdio transport requires a command")
        elif self.transport == "streamable_http":
            if not self.url:
                raise ValueError("streamable_http transport requires a url")
        else:
            raise ValueError(f"unsupported MCP transport: {self.transport!r}")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


def _stdio_params(spec: McpConnectionSpec) -> StdioServerParameters:
    return StdioServerParameters(
        command=spec.command[0],
        args=list(spec.command[1:]),
        env=dict(spec.env) or None,
    )


async def with_hard_timeout(awaitable: Awaitable[_T], timeout_seconds: float) -> _T:
    """给 MCP 操作加硬超时（wait_for 超时后自动取消底层任务）。"""
    return await asyncio.wait_for(awaitable, timeout=timeout_seconds)


async def call_tool_with_timeout(
    session: ClientSession,
    tool_name: str,
    arguments: dict[str, object],
    timeout_seconds: float,
) -> CallToolResult:
    """call_tool 的硬超时：慢工具按 timeout_seconds 强制中断（双 transport）。"""
    return await with_hard_timeout(session.call_tool(tool_name, arguments), timeout_seconds)


def _derived_from_timeout(error: BaseException) -> bool:
    """异常链（含 BaseExceptionGroup 嵌套与 cause/context）是否源自超时。

    wait_for 取消在途 MCP 请求后，SDK task group 在关闭时抛出的
    ExceptionGroup 会掩盖原始 TimeoutError；本函数沿异常链识别
    “超时驱动”的关闭失败，避免把工具超时误分类为连接失败。
    """
    seen: set[int] = set()

    def walk(current: BaseException) -> bool:
        if id(current) in seen:
            return False
        seen.add(id(current))
        if isinstance(current, _TIMEOUT_TYPES):
            return True
        if isinstance(current, BaseExceptionGroup):
            if any(walk(sub) for sub in current.exceptions):
                return True
        if current.__cause__ is not None and walk(current.__cause__):
            return True
        if current.__context__ is not None and walk(current.__context__):
            return True
        return False

    return walk(error)


def _http_client(spec: McpConnectionSpec) -> httpx.AsyncClient:
    """自建 httpx client：connect/read 超时均为 spec.timeout_seconds。"""
    return httpx.AsyncClient(
        headers=dict(spec.headers) or None,
        timeout=httpx.Timeout(spec.timeout_seconds, read=spec.timeout_seconds),
    )


@asynccontextmanager
async def open_mcp_session(
    spec: McpConnectionSpec,
) -> AsyncIterator[ClientSession]:
    """打开 MCP 会话并完成 initialize 握手；退出时关闭会话与 transport。"""
    try:
        if spec.transport == "stdio":
            params = _stdio_params(spec)
            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await with_hard_timeout(session.initialize(), spec.timeout_seconds)
                    yield session
            return
        async with _http_client(spec) as client:
            async with streamable_http_client(
                spec.url or "",
                http_client=client,
                terminate_on_close=True,
            ) as (read_stream, write_stream, _get_session_id):
                async with ClientSession(read_stream, write_stream) as session:
                    await with_hard_timeout(session.initialize(), spec.timeout_seconds)
                    yield session
    except BaseExceptionGroup as group:
        if _derived_from_timeout(group):
            raise TimeoutError("mcp operation timed out") from group
        raise
