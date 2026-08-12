"""Fake test-double 公共基座（adapters/fakes）。

Fake 是 test-double adapter：遵守与真实 adapter 相同的 Port Contract
（由 tests/contracts 强制），不绕过签名/错误分类/幂等规则。
- deterministic：行为由显式脚本驱动，无随机；
- 错误注入：set_script 按调用序次注入 PortError（None 表示成功）；
- call recording：每次调用（含失败）记录 CallRecord（参数/结果为摘要，
  不记录 secret 明文）；
- resource cleanup：close() 后所有方法抛 PermanentPortError。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence

from packages.application.ports.errors import PermanentPortError, PortError
from packages.domain.enums import FailureCategory

_CLOSED_ERROR = PermanentPortError(
    "fake is closed",
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


class FakeBase:
    """Fake 公共基座：call log、行为脚本、close 语义。"""

    def __init__(self, port: str) -> None:
        self._port = port
        self._calls: list[CallRecord] = []
        self._scripts: dict[str, list[PortError | None]] = {}
        self._closed = False

    @property
    def calls(self) -> tuple[CallRecord, ...]:
        return tuple(self._calls)

    def method_calls(self, method: str) -> int:
        return sum(1 for call in self._calls if call.method == method)

    def set_script(self, method: str, steps: Sequence[PortError | None]) -> None:
        """按调用序次注入失败；None 表示成功；脚本消费完后默认成功。"""
        self._scripts[method] = list(steps)

    def close(self) -> None:
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise _CLOSED_ERROR

    def _enter(self, method: str, args_summary: str) -> None:
        """公共方法入口：open 检查 + 脚本注入（失败记录后抛出）。"""
        self._ensure_open()
        try:
            self._apply_script(method)
        except PortError as error:
            self._record(method, args_summary, error=error.__class__.__name__)
            raise

    def _apply_script(self, method: str) -> None:
        steps = self._scripts.get(method)
        if not steps:
            return
        failure = steps.pop(0)
        if failure is not None:
            raise failure

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
