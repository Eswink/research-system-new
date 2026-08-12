"""FakeToolProvider：工具执行（operation_key 幂等 + 错误注入）。"""

from __future__ import annotations

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import PermanentPortError
from packages.domain.core import Timestamp
from packages.domain.enums import FailureCategory
from packages.domain.tools import ToolCallRecord, ToolProviderSpec, ToolResultRecord


class FakeToolProvider(FakeBase):
    """execute 按 operation_key 幂等；工具级失败返回 FAILED 记录（不抛异常）。"""

    def __init__(self, *, registered_tools: tuple[str, ...] = ()) -> None:
        super().__init__("tool_provider")
        self._registered = set(registered_tools)
        self._results: dict[str, ToolResultRecord] = {}
        self._tool_failures: set[str] = set()

    def register_tool(self, tool_id: str) -> None:
        self._registered.add(tool_id)

    def fail_tool(self, tool_id: str) -> None:
        self._tool_failures.add(tool_id)

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
                status="FAILED",
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
                status="SUCCEEDED",
                recorded_at=Timestamp.now(),
            )
        self._results[key] = result
        self._record("execute", key, result=result.status)
        return result
