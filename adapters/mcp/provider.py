"""McpToolProvider：MCP adapter 实现扩展后的 ToolProvider Port。

边界（AGENTS.md §5 / CAPABILITY_SECURITY.md §6）：
- mcp SDK 类型只在本 adapter 内可见，不泄漏进 application/domain；
- 凭据只经 CredentialResolver 按声明的 credential_ref 解析并注入
  transport，禁止 token passthrough（不转发模型/其它域凭据）；
- 大结果经 ArtifactStore spill，ToolResultRecord 只留 digest；
- MCP 错误映射到 ports/errors.py transient/permanent 分类。

执行模型：每次操作独立会话（stateless per-op），同步 Port 方法内部
以 asyncio.run 桥接 MCP SDK 异步 API；连接失败归类 transient，
协议/schema 类失败归类 permanent。

**工具参数**与 REST 适配器同形：经 ArtifactStore 的
`tool-args:{task_id}:{operation_key}` 传递，读回后**重算 digest** 与
`call.argument_digest` 比对（内容寻址防篡改）。此前的实现以**空参数**调用工具
（`session.call_tool(tool_name, {})`），任何 MCP 工具都收不到 query / ids
⇒ 运行链在其上不可能成立（GOAL-027 EC-02 修的真实缺陷）。
**唯一与 REST 不同的分支**：制品**缺席**时，仅当声明值恰为 `{}` 的 canonical
序列化才回落到空参数（既有契约套件声明空参数且不落制品，逐字节未改）；
声明了非空参数却没有制品 ⇒ **fail closed**，不静默降级。
"""

from __future__ import annotations

import asyncio
import json

import httpx

from adapters.mcp.transport import (
    McpConnectionSpec,
    call_tool_with_timeout,
    open_mcp_session,
    with_hard_timeout,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.credential_resolver import CredentialResolver
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortTimeoutError,
    TransientPortError,
)
from packages.application.tool_plane.results import spill_large_result
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import (
    EndpointHealth,
    FailureCategory,
    ProviderType,
    ToolResultStatus,
)
from packages.domain.redaction import redact_exception_message
from packages.domain.serialization import digest_of
from packages.domain.tools import (
    ToolCallRecord,
    ToolHealthReport,
    ToolProviderSpec,
    ToolResultRecord,
    ToolSpec,
)

#: 工具参数制品的 id 前缀（与 `adapters/research_tools/ncbi.py` 同源）。
ARGS_ARTIFACT_PREFIX = "tool-args:"
#: 空参数对象的 canonical 序列化（`json.dumps({}, sort_keys=True)`）——
#: 调用方**声明**空参数时允许不落 args 制品。
EMPTY_ARGS_PAYLOAD = b"{}"


class McpToolProvider:
    """MCP ToolProvider：stdio 子进程或 Streamable HTTP 服务。"""

    def __init__(
        self,
        connection: McpConnectionSpec,
        *,
        credentials: CredentialResolver | None = None,
        credential_ref: str | None = None,
        artifact_store: ArtifactStore,
        spill_threshold_bytes: int = 32 * 1024,
    ) -> None:
        if connection.transport == "streamable_http" and credential_ref is None:
            raise ValueError("streamable_http transport requires a credential_ref")
        if credentials is None and credential_ref is not None:
            raise ValueError("credential_ref requires a CredentialResolver")
        self._connection = connection
        self._credentials = credentials
        self._credential_ref = credential_ref
        self._artifact_store = artifact_store
        self._spill_threshold = spill_threshold_bytes

    def execute(self, provider: ToolProviderSpec, call: ToolCallRecord) -> ToolResultRecord:
        try:
            return asyncio.run(self._execute_async(call))
        except InvalidInputError as exc:
            raise PermanentPortError(
                str(exc),
                failure_category=FailureCategory.CONFIGURATION,
            ) from exc
        except (PortTimeoutError, TransientPortError, PermanentPortError):
            raise
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise PortTimeoutError(
                "mcp tool call timed out",
                failure_category=FailureCategory.TOOL_TIMEOUT,
            ) from exc
        except (
            httpx.HTTPError,
            ConnectionError,
            OSError,
            ExceptionGroup,
        ) as exc:
            raise TransientPortError(
                f"mcp connection failure: {exc}",
                failure_category=FailureCategory.TOOL_UNAVAILABLE,
            ) from exc
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise PermanentPortError(
                f"mcp protocol error: {exc}",
                failure_category=FailureCategory.TOOL_SCHEMA_MISMATCH,
            ) from exc

    def list_tools(self, provider: ToolProviderSpec) -> tuple[ToolSpec, ...]:
        try:
            return asyncio.run(self._list_tools_async(provider))
        except (PortTimeoutError, TransientPortError, PermanentPortError):
            raise
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise PortTimeoutError(
                "mcp tool listing timed out",
                failure_category=FailureCategory.TOOL_TIMEOUT,
            ) from exc
        except (
            httpx.HTTPError,
            ConnectionError,
            OSError,
            ExceptionGroup,
        ) as exc:
            raise TransientPortError(
                f"mcp connection failure: {exc}",
                failure_category=FailureCategory.TOOL_UNAVAILABLE,
            ) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise PermanentPortError(
                f"mcp protocol error: {exc}",
                failure_category=FailureCategory.TOOL_SCHEMA_MISMATCH,
            ) from exc

    def check_health(self, provider: ToolProviderSpec) -> ToolHealthReport:
        try:
            tools = asyncio.run(self._list_tools_async(provider))
        except Exception:  # noqa: BLE001 — 健康探测失败统一归为 open circuit
            return ToolHealthReport(
                provider_id=provider.id,
                status=EndpointHealth.OPEN_CIRCUIT,
                detail="mcp health probe failed",
            )
        schema_digest = digest_of({"tools": [tool.id for tool in tools]})
        return ToolHealthReport(
            provider_id=provider.id,
            status=EndpointHealth.HEALTHY,
            observed_schema_digest=schema_digest,
            detail=f"{len(tools)} tools",
        )

    def close(self) -> None:
        """stateless per-op 模型：无持久连接可关闭。"""

    def _resolved_spec(self) -> McpConnectionSpec:
        """按需解析 TOOL 域凭据并注入 transport（禁止 token passthrough）。"""
        spec = self._connection
        if spec.transport == "streamable_http" and self._credential_ref:
            assert self._credentials is not None
            secret = self._credentials.resolve(self._credential_ref)
            return McpConnectionSpec(
                transport=spec.transport,
                command=spec.command,
                env=spec.env,
                url=spec.url,
                headers={**spec.headers, "Authorization": f"Bearer {secret.value}"},
                timeout_seconds=spec.timeout_seconds,
            )
        return spec

    def _read_args(self, call: ToolCallRecord) -> dict[str, object]:
        """读参（防篡改）→ MCP 工具的参数对象。

        与 REST 适配器同形：制品 id 为 `tool-args:{task_id}:{operation_key}`，
        读回后**重算 digest** 与 `call.argument_digest` 比对。

        **缺席分支是两者唯一的差别**（且是 fail-closed 的）：制品不在时，仅当
        声明值恰为 `{}` 的 canonical 序列化才回落到空参数；声明了非空参数却没有
        制品 ⇒ `InvalidInputError`（调用方 bug，不猜、不编造、不静默降级）。
        本方法在**打开会话之前**调用 ⇒ 参数不合法时**零子进程 / 零请求**。
        """
        artifact_id = f"{ARGS_ARTIFACT_PREFIX}{call.task_id}:{call.operation_key}"
        if self._artifact_store.meta(artifact_id) is None:
            if call.argument_digest == Digest.of_bytes(EMPTY_ARGS_PAYLOAD):
                return {}
            raise InvalidInputError(
                "mcp tool args artifact is missing but the declared arguments are not empty"
            )
        content = self._artifact_store.get(artifact_id)
        if Digest.of_bytes(content) != call.argument_digest:
            raise InvalidInputError("tool args digest mismatch")
        parsed = json.loads(content.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise InvalidInputError("tool args must be a JSON object")
        return parsed

    async def _execute_async(self, call: ToolCallRecord) -> ToolResultRecord:
        args = self._read_args(call)
        spec = self._resolved_spec()
        async with open_mcp_session(spec) as session:
            result = await call_tool_with_timeout(session, call.tool_id, args, spec.timeout_seconds)
        payload = _serialize_call_tool_result(result)
        if result.isError:
            return ToolResultRecord(
                task_id=call.task_id,
                attempt=call.attempt,
                operation_key=call.operation_key,
                tool_id=call.tool_id,
                status=ToolResultStatus.FAILED,
                failure_category=FailureCategory.TOOL_UNAVAILABLE,
                error_message_redacted=redact_exception_message(
                    payload.decode("utf-8", errors="replace")[:200]
                ),
                recorded_at=Timestamp.now(),
            )
        spill = spill_large_result(
            self._artifact_store,
            call,
            payload,
            threshold_bytes=self._spill_threshold,
        )
        return spill.record

    async def _list_tools_async(self, provider: ToolProviderSpec) -> tuple[ToolSpec, ...]:
        spec = self._resolved_spec()
        async with open_mcp_session(spec) as session:
            listing = await with_hard_timeout(session.list_tools(), spec.timeout_seconds)
        return tuple(
            ToolSpec(
                id=tool.name,
                name=tool.name,
                effect_class=provider.effect_class,
                provider_kind=ProviderType.MCP,
                capabilities=list(provider.capabilities),
                description=tool.description or "",
            )
            for tool in listing.tools
        )


def _serialize_call_tool_result(result: object) -> bytes:
    """把 MCP CallToolResult 归一化为确定性 JSON bytes。"""
    content = getattr(result, "content", None) or []
    structured = getattr(result, "structuredContent", None)
    texts = [
        item.text
        for item in content
        if getattr(item, "type", None) == "text" and hasattr(item, "text")
    ]
    payload: dict[str, object] = {
        "text": texts,
        "structured": structured if structured is not None else {},
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
