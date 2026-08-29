"""FailSafeTelemetrySink:fail-open 外壳(port 契约的兜底层)。

包装任意 TelemetrySink:inner 的任何异常都被吞掉并计数;`shutdown`/`flush`
透传给支持生命周期的 inner(如 OtelTelemetrySink),同样吞错。
Canonical state 与 telemetry 故障完全隔离(ADR-0026 / DoD-7)。
"""

from __future__ import annotations

import threading

from packages.application.observability.attributes import MetricSample
from packages.application.observability.signals import OperationBegin, OperationEnd
from packages.application.ports.telemetry_sink import TelemetrySink

_DEFAULT_LIFECYCLE_TIMEOUT_SECONDS = 5.0


class FailSafeTelemetrySink:
    """永不抛出的 TelemetrySink 外壳;drop 计数可被控制面读取。"""

    def __init__(self, inner: TelemetrySink) -> None:
        self._inner = inner
        self._dropped = 0
        self._last_error: str | None = None
        self._lock = threading.Lock()

    def begin_operation(self, begin: OperationBegin) -> None:
        try:
            self._inner.begin_operation(begin)
        except Exception as error:
            self._count_drop("begin_operation", error)

    def end_operation(self, end: OperationEnd) -> None:
        try:
            self._inner.end_operation(end)
        except Exception as error:
            self._count_drop("end_operation", error)

    def record_metric(self, sample: MetricSample) -> None:
        try:
            self._inner.record_metric(sample)
        except Exception as error:
            self._count_drop("record_metric", error)

    @property
    def drop_count(self) -> int:
        """inner 抛错的累计次数(诊断/exporter 健康可见性)。"""
        return self._dropped

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def inner(self) -> TelemetrySink:
        return self._inner

    def flush(self, timeout_seconds: float = _DEFAULT_LIFECYCLE_TIMEOUT_SECONDS) -> None:
        self._lifecycle("flush", timeout_seconds)

    def shutdown(self, timeout_seconds: float = _DEFAULT_LIFECYCLE_TIMEOUT_SECONDS) -> None:
        self._lifecycle("shutdown", timeout_seconds)

    def _lifecycle(self, method: str, timeout_seconds: float) -> None:
        lifecycle = getattr(self._inner, method, None)
        if not callable(lifecycle):
            return
        try:
            lifecycle(timeout_seconds)
        except Exception as error:
            self._count_drop(method, error)

    def _count_drop(self, operation: str, error: Exception) -> None:
        with self._lock:
            self._dropped += 1
            self._last_error = f"{operation}: {error.__class__.__name__}"
