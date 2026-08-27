"""Postgres adapter call recording + close semantics (mirrors sqlite/base.py)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from packages.application.ports.errors import PermanentPortError
from packages.domain.enums import FailureCategory

_CLOSED_ERROR = PermanentPortError(
    "postgres adapter is closed",
    failure_category=FailureCategory.CONFIGURATION,
)


@dataclass(frozen=True, slots=True)
class CallRecord:
    port: str
    method: str
    index: int
    args_summary: str
    result_summary: str | None = None
    error: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PostgresAdapterBase:
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
        # Redact DSN password if it ever appears in summary
        safe = args_summary.replace("password=", "password=***REDACTED***")
        if "://" in safe and "@" in safe:
            import re

            safe = re.sub(r"://[^@]*@", "://***REDACTED***@", safe)
        self._calls.append(
            CallRecord(
                port=self._port,
                method=method,
                index=len(self._calls),
                args_summary=safe,
                result_summary=result,
                error=error,
            )
        )
