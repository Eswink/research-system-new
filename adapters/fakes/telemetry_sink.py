"""TelemetrySink 的 Fake test-double 与 Null 组合(adapters/fakes)。

与真实 OtelTelemetrySink 遵守相同 Port 契约(fail-open:任何情况下不得抛出,
含 close 之后);记录 begin/end/metric 信号供 contract 与 observability 断言。
CallRecord 摘要只含 span 引用/scope/name/outcome,不含 attributes 原文。
"""

from __future__ import annotations

from adapters.fakes.base import CallRecord
from packages.application.observability.attributes import MetricSample
from packages.application.observability.signals import OperationBegin, OperationEnd
from packages.application.ports.telemetry_sink import NullTelemetrySink

_PORT_NAME = "telemetry_sink"


class FakeTelemetrySink:
    """记录全部信号的 Fake;close 后不再记录,信号计 drop,永不抛出。"""

    def __init__(self) -> None:
        self._begins: list[OperationBegin] = []
        self._ends: list[OperationEnd] = []
        self._metrics: list[MetricSample] = []
        self._calls: list[CallRecord] = []
        self._closed = False
        self._post_close_drops = 0

    def begin_operation(self, begin: OperationBegin) -> None:
        if self._closed:
            self._drop_after_close()
            return
        self._begins.append(begin)
        summary = f"span={begin.span_ref.value} scope={begin.scope.value} name={begin.name}"
        self._record("begin_operation", summary)

    def end_operation(self, end: OperationEnd) -> None:
        if self._closed:
            self._drop_after_close()
            return
        self._ends.append(end)
        summary = f"span={end.span_ref.value} outcome={end.outcome.value}"
        self._record("end_operation", summary, result=end.outcome.value)

    def record_metric(self, sample: MetricSample) -> None:
        if self._closed:
            self._drop_after_close()
            return
        self._metrics.append(sample)
        summary = f"metric={sample.name.value} value={sample.value!r}"
        self._record("record_metric", summary, result=f"{sample.value!r}")

    @property
    def calls(self) -> tuple[CallRecord, ...]:
        return tuple(self._calls)

    @property
    def begins(self) -> tuple[OperationBegin, ...]:
        return tuple(self._begins)

    @property
    def ends(self) -> tuple[OperationEnd, ...]:
        return tuple(self._ends)

    @property
    def metrics(self) -> tuple[MetricSample, ...]:
        return tuple(self._metrics)

    @property
    def post_close_drops(self) -> int:
        return self._post_close_drops

    def method_calls(self, method: str) -> int:
        return sum(1 for call in self._calls if call.method == method)

    def close(self) -> None:
        """close 语义:停止记录并计 drop;与其它 Fake 不同,绝不抛出(fail-open)。"""
        self._closed = True

    def _record(self, method: str, args_summary: str, *, result: str | None = None) -> None:
        self._calls.append(
            CallRecord(
                port=_PORT_NAME,
                method=method,
                index=len(self._calls),
                args_summary=args_summary,
                result_summary=result,
            )
        )

    def _drop_after_close(self) -> None:
        self._post_close_drops += 1
        self._record("post_close_drop", "signal dropped after close", result="dropped")


__all__ = ["FakeTelemetrySink", "NullTelemetrySink"]
