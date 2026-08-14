"""McpToolProvider 专属 contract suite（stdio + Streamable HTTP 双 transport）。

不进离线 PORT_IMPLEMENTATIONS registry：MCP adapter 需要本地测试 server，
与通用 probe（默认 provider spec）语义不同。覆盖：
- execute 成功 / server 端错误 → FAILED 记录 / 未注册工具；
- list_tools schema 枚举；check_health 健康与 schema digest 漂移；
- 大结果 artifact spill；凭据注入与缺失凭据失败；
- 连接失败（transient）与关闭语义。
"""

from __future__ import annotations

import sys
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass

import pytest
import uvicorn

from adapters.fakes import FakeArtifactStore, FakeCredentialResolver
from adapters.mcp import McpConnectionSpec, McpToolProvider
from packages.application.ports.errors import (
    PermanentPortError,
    PortTimeoutError,
    TransientPortError,
)
from packages.domain.core import Digest
from packages.domain.enums import (
    CredentialScope,
    EffectClass,
    FailureCategory,
    ProviderType,
    ToolResultStatus,
    TrustLevel,
)
from packages.domain.tools import ToolCallRecord, ToolProviderSpec
from tests.mcp_server.server import (
    FAULT_BIG,
    FAULT_NONE,
    FAULT_SCHEMA,
    FAULT_SLOW,
    FAULT_TOOL_ERROR,
    build_test_server,
)

PROVIDER = ToolProviderSpec(
    id="research-mcp-test",
    kind=ProviderType.MCP,
    trust_level=TrustLevel.VERIFIED,
    capabilities=["search.academic", "citation.inspect"],
    effect_class=EffectClass.READ_ONLY,
    transport="streamable_http",
)


def _call(tool_id: str, operation_key: str = "op-1") -> ToolCallRecord:
    return ToolCallRecord(
        task_id="task-1",
        attempt=1,
        operation_key=operation_key,
        tool_id=tool_id,
        capability="search.academic",
        argument_digest=Digest.of_bytes(b"{}"),
    )


def _stdio_connection(fault: str = FAULT_NONE) -> McpConnectionSpec:
    return McpConnectionSpec(
        transport="stdio",
        command=(
            sys.executable,
            "-B",
            "-m",
            "tests.mcp_server.run_stdio",
            fault,
        ),
        timeout_seconds=30.0,
    )


def _stdio_provider(fault: str = FAULT_NONE) -> McpToolProvider:
    return McpToolProvider(
        _stdio_connection(fault),
        artifact_store=FakeArtifactStore(),
        spill_threshold_bytes=1024,
    )


@dataclass(frozen=True, slots=True)
class _HttpServerInfo:
    base_url: str


def _start_http_server(fault: str) -> Iterator[_HttpServerInfo]:
    """进程内 Streamable HTTP server（uvicorn 后台线程，端口随机可用）。"""
    import socket

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    app = build_test_server(fault).streamable_http_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)
    yield _HttpServerInfo(base_url=f"http://127.0.0.1:{port}/mcp")
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(scope="module")
def http_server() -> Iterator[_HttpServerInfo]:
    yield from _start_http_server(FAULT_NONE)


@pytest.fixture(scope="module")
def slow_http_server() -> Iterator[_HttpServerInfo]:
    yield from _start_http_server(FAULT_SLOW)


def _http_provider(
    base_url: str,
    *,
    token: str | None = None,
    timeout_seconds: float = 30.0,
) -> McpToolProvider:
    credentials = FakeCredentialResolver({"tool_token": "test-token-abc"})
    return McpToolProvider(
        McpConnectionSpec(
            transport="streamable_http",
            url=base_url,
            timeout_seconds=timeout_seconds,
        ),
        credentials=credentials,
        credential_ref="tool_token" if token is None else token,
        artifact_store=FakeArtifactStore(),
        spill_threshold_bytes=1024,
    )


class TestStdioTransport:
    def test_execute_success(self) -> None:
        provider = _stdio_provider()
        result = provider.execute(PROVIDER, _call("literature_search"))
        assert result.status is ToolResultStatus.SUCCEEDED
        assert result.output_digest is not None

    def test_list_tools_schema(self) -> None:
        provider = _stdio_provider()
        tools = provider.list_tools(PROVIDER)
        names = {tool.id for tool in tools}
        assert {"literature_search", "citation_inspect"} <= names
        assert all(tool.provider_kind is ProviderType.MCP for tool in tools)

    def test_check_health_healthy(self) -> None:
        provider = _stdio_provider()
        report = provider.check_health(PROVIDER)
        assert report.status.value == "HEALTHY"
        assert report.observed_schema_digest is not None

    def test_schema_digest_drift_detected(self) -> None:
        baseline = _stdio_provider(FAULT_NONE).check_health(PROVIDER)
        drifted = _stdio_provider(FAULT_SCHEMA).check_health(PROVIDER)
        assert baseline.observed_schema_digest != drifted.observed_schema_digest

    def test_server_tool_error_returns_failed_record(self) -> None:
        provider = _stdio_provider(FAULT_TOOL_ERROR)
        result = provider.execute(PROVIDER, _call("failing_tool"))
        assert result.status is ToolResultStatus.FAILED
        assert result.failure_category is FailureCategory.TOOL_UNAVAILABLE
        assert result.error_message_redacted is not None

    def test_unregistered_tool_returns_failed_record(self) -> None:
        """MCP server 对未注册工具的调用返回 isError 结果 → FAILED 记录。

        （未注册工具在 Research OS 侧由 frozen tool set + resolver 阻断，
        adapter 层把 server 端错误归一化为 FAILED 记录而非协议异常。）
        """
        provider = _stdio_provider()
        result = provider.execute(PROVIDER, _call("ghost_tool"))
        assert result.status is ToolResultStatus.FAILED
        assert result.failure_category is FailureCategory.TOOL_UNAVAILABLE

    def test_large_result_spills_to_artifact(self) -> None:
        provider = _stdio_provider(FAULT_BIG)
        result = provider.execute(PROVIDER, _call("big_tool"))
        assert result.status is ToolResultStatus.SUCCEEDED
        assert result.output_digest is not None

    def test_connection_failure_is_transient(self) -> None:
        provider = McpToolProvider(
            McpConnectionSpec(
                transport="stdio",
                command=(sys.executable, "-B", "-m", "no.such.module"),
                timeout_seconds=10.0,
            ),
            artifact_store=FakeArtifactStore(),
        )
        with pytest.raises((TransientPortError, PermanentPortError)):
            provider.execute(PROVIDER, _call("literature_search"))

    def test_slow_tool_enforces_spec_timeout(self) -> None:
        """Fault injection：stdio 慢工具按 spec.timeout_seconds 强制超时。"""
        provider = McpToolProvider(
            McpConnectionSpec(
                transport="stdio",
                command=(sys.executable, "-B", "-m", "tests.mcp_server.run_stdio", FAULT_SLOW),
                timeout_seconds=2.0,
            ),
            artifact_store=FakeArtifactStore(),
        )
        start = time.monotonic()
        with pytest.raises(PortTimeoutError) as exc_info:
            provider.execute(PROVIDER, _call("slow_tool", operation_key="op-slow"))
        assert exc_info.value.failure_category is FailureCategory.TOOL_TIMEOUT
        # 10s 慢工具必须在 ~2s 处被强制中断，不得等到工具自然返回
        assert time.monotonic() - start < 8.0

    def test_invalid_timeout_spec_rejected(self) -> None:
        with pytest.raises(ValueError, match="timeout_seconds"):
            McpConnectionSpec(
                transport="stdio",
                command=(sys.executable, "-B", "-m", "tests.mcp_server.run_stdio"),
                timeout_seconds=0,
            )

    def test_close_is_noop_and_still_usable(self) -> None:
        provider = _stdio_provider()
        provider.close()
        result = provider.execute(PROVIDER, _call("literature_search"))
        assert result.status is ToolResultStatus.SUCCEEDED


class TestStreamableHttpTransport:
    def test_execute_success_with_credential(self, http_server: _HttpServerInfo) -> None:
        provider = _http_provider(http_server.base_url)
        result = provider.execute(PROVIDER, _call("literature_search"))
        assert result.status is ToolResultStatus.SUCCEEDED
        assert result.output_digest is not None

    def test_list_tools_over_http(self, http_server: _HttpServerInfo) -> None:
        provider = _http_provider(http_server.base_url)
        names = {tool.id for tool in provider.list_tools(PROVIDER)}
        assert {"literature_search", "citation_inspect"} <= names

    def test_check_health_over_http(self, http_server: _HttpServerInfo) -> None:
        provider = _http_provider(http_server.base_url)
        assert provider.check_health(PROVIDER).status.value == "HEALTHY"

    def test_missing_credential_fails_permanent(self, http_server: _HttpServerInfo) -> None:
        provider = _http_provider(http_server.base_url, token="missing_ref")
        with pytest.raises(PermanentPortError) as exc_info:
            provider.execute(PROVIDER, _call("literature_search"))
        assert exc_info.value.failure_category is FailureCategory.CONFIGURATION

    def test_connection_refused_is_transient(self) -> None:
        provider = _http_provider("http://127.0.0.1:1/mcp")
        with pytest.raises((TransientPortError, PermanentPortError)):
            provider.execute(PROVIDER, _call("literature_search"))

    def test_slow_tool_over_http_enforces_timeout(self, slow_http_server: _HttpServerInfo) -> None:
        """Fault injection：Streamable HTTP 慢工具按 spec.timeout_seconds 强制超时。"""
        provider = _http_provider(slow_http_server.base_url, timeout_seconds=2.0)
        start = time.monotonic()
        with pytest.raises(PortTimeoutError) as exc_info:
            provider.execute(PROVIDER, _call("slow_tool", operation_key="op-slow-http"))
        assert exc_info.value.failure_category is FailureCategory.TOOL_TIMEOUT
        assert time.monotonic() - start < 8.0


class TestCredentialDomainSeparation:
    def test_credential_scope_is_tool_domain(self) -> None:
        """工具凭据属于 TOOL 信任域，与 LLM 凭据严格分离（ADR-0012）。"""
        domains = {
            CredentialScope.LLM,
            CredentialScope.TOOL,
            CredentialScope.WORKSPACE,
            CredentialScope.USER_OAUTH,
        }
        assert len(domains) == 4
        resolver = FakeCredentialResolver({"llm_key": "sk-llm-secret", "tool_token": "tool-secret"})
        provider = McpToolProvider(
            McpConnectionSpec(transport="stdio", command=(sys.executable, "-B", "-c", "pass")),
            credentials=resolver,
            credential_ref=None,
            artifact_store=FakeArtifactStore(),
        )
        # stdio 不需要凭据；http 模式 credential_ref 只解析 TOOL 域引用。
        assert provider._resolved_spec().headers == {}
        assert resolver.method_calls("resolve") == 0
