"""RetrievalIndex adapter 公共基座：call recording + close 语义。

与 SqliteAdapterBase / FakeBase 同契约：contract suite 要求实现可审计
（calls 属性），close 后调用抛 PermanentPortError。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from packages.application.ports.errors import PermanentPortError
from packages.domain.enums import FailureCategory

_CLOSED_ERROR = PermanentPortError(
    "retrieval index adapter is closed",
    failure_category=FailureCategory.CONFIGURATION,
)


@dataclass(frozen=True, slots=True)
class CallRecord:
    """一次调用的可审计记录；参数/结果为摘要，绝不携带 secret 明文。"""

    port: str
    method: str
    index: int
    args_summary: str
    result_summary: str | None = None
    error: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class IndexAdapterBase:
    """RetrievalIndex adapter 公共基座：call log 与 close 语义。"""

    def __init__(self, port: str) -> None:
        self._port = port
        self._calls: list[CallRecord] = []
        self._closed = False

    @property
    def calls(self) -> tuple[CallRecord, ...]:
        return tuple(self._calls)

    def method_calls(self, method: str) -> int:
        return sum(1 for call in self._calls if call.method == method)

    def close(self) -> None:
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise _CLOSED_ERROR

    def _record(
        self,
        method: str,
        args_summary: str,
        *,
        result: str | None = None,
        error: str | None = None,
    ) -> None:
        self._calls.append(
            CallRecord(
                port=self._port,
                method=method,
                index=len(self._calls),
                args_summary=args_summary,
                result_summary=result,
                error=error,
            )
        )
