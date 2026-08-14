"""FakeToolProvider：工具执行（operation_key 幂等 + 错误注入）。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import PermanentPortError
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import (
    EndpointHealth,
    FailureCategory,
    ToolResultStatus,
)
from packages.domain.serialization import digest_of
from packages.domain.tools import (
    ToolCallRecord,
    ToolHealthReport,
    ToolProviderSpec,
    ToolResultRecord,
    ToolSpec,
)


class FakeToolProvider(FakeBase):
    """execute 按 operation_key 幂等；工具级失败返回 FAILED 记录（不抛异常）。"""

    def __init__(self, *, registered_tools: tuple[str, ...] = ()) -> None:
        super().__init__("tool_provider")
        self._registered: set[str] = set(registered_tools)
        self._results: dict[str, ToolResultRecord] = {}
        self._tool_failures: set[str] = set()
        self._health_failures: set[str] = set()
        self._specs: dict[str, ToolSpec] = {}

    def register_tool(self, tool_id: str) -> None:
        self._registered.add(tool_id)

    def register_spec(self, spec: ToolSpec) -> None:
        self._registered.add(spec.id)
        self._specs[spec.id] = spec

    def fail_tool(self, tool_id: str) -> None:
        self._tool_failures.add(tool_id)

    def fail_health(self, provider_id: str) -> None:
        self._health_failures.add(provider_id)

    def execute(self, provider: ToolProviderSpec, call: ToolCallRecord) -> ToolResultRecord:
        self._enter("execute", call.operation_key)
        if call.tool_id not in self._registered:
            self._record("execute", call.operation_key, error="PermanentPortError")
            raise PermanentPortError(
                f"tool not registered: {call.tool_id}",
                failure_category=FailureCategory.TOOL_UNAVAILABLE,
            )
        key = call.operation_key
        if key in self._results:
            self._record("execute", key, result="deduped")
            return self._results[key]
        if call.tool_id in self._tool_failures:
            result = ToolResultRecord(
                task_id=call.task_id,
                attempt=call.attempt,
                operation_key=key,
                tool_id=call.tool_id,
                status=ToolResultStatus.FAILED,
                failure_category=FailureCategory.TOOL_UNAVAILABLE,
                error_message_redacted="tool failed ***REDACTED***",
                recorded_at=Timestamp.now(),
            )
        else:
            result = ToolResultRecord(
                task_id=call.task_id,
                attempt=call.attempt,
                operation_key=key,
                tool_id=call.tool_id,
                status=ToolResultStatus.SUCCEEDED,
                recorded_at=Timestamp.now(),
            )
        self._results[key] = result
        self._record("execute", key, result=result.status)
        return result

    def list_tools(self, provider: ToolProviderSpec) -> tuple[ToolSpec, ...]:
        self._enter("list_tools", provider.id)
        registered = sorted(self._specs.items())
        return tuple(spec for tool_id, spec in registered if tool_id in self._registered)

    def check_health(self, provider: ToolProviderSpec) -> ToolHealthReport:
        self._enter("check_health", provider.id)
        if provider.id in self._health_failures:
            self._record("check_health", provider.id, result="UNREACHABLE")
            return ToolHealthReport(
                provider_id=provider.id,
                status=EndpointHealth.OPEN_CIRCUIT,
                detail="injected health failure",
            )
        schema_digest = self._schema_digest(provider.id)
        self._record("check_health", provider.id, result="HEALTHY")
        return ToolHealthReport(
            provider_id=provider.id,
            status=EndpointHealth.HEALTHY,
            observed_schema_digest=schema_digest,
        )

    def _schema_digest(self, provider_id: str) -> Digest | None:
        specs = [self._specs[key] for key in sorted(self._specs) if key in self._registered]
        if not specs:
            return None
        return digest_of({"tools": [tool.id for tool in specs]})
