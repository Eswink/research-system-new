"""FailSafeTelemetrySink:fail-open 外壳(port 契约的兜底层)。

包装任意 TelemetrySink:inner 的任何异常都被吞掉并计数;`shutdown`/`flush`
透传给支持生命周期的 inner(如 OtelTelemetrySink),同样吞错。
Canonical state 与 telemetry 故障完全隔离(ADR-0026 / DoD-7)。

`drop_count` 聚合自身与 inner 的计数(M15 复审修复):本外壳只数 inner **抛出**
的异常,而 `OtelTelemetrySink` 把自己的全部错误内部吞掉并记在自有计数器上,
所以在出厂组装下该字段结构性恒 0——`GET /runs/{id}/telemetry` 的 exporter
健康信号因此永远报告"零丢弃",即使每一次导出都失败。
"""

from __future__ import annotations

import threading

from packages.application.observability.attributes import MetricSample
from packages.application.observability.signals import OperationBegin, OperationEnd
from packages.application.ports.telemetry_sink import TelemetrySink

_DEFAULT_LIFECYCLE_TIMEOUT_SECONDS = 3.0


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
        """外壳捕获的 inner 抛错 + inner 自报的丢弃(exporter 健康可见性)。

        必须聚合 inner:`OtelTelemetrySink` 自吞全部错误,只加自有计数器,
        单看外壳计数会得到结构性恒 0 的健康信号(M15 复审实测)。
        """
        inner_dropped = getattr(self._inner, "dropped", 0)
        return self._dropped + (inner_dropped if isinstance(inner_dropped, int) else 0)

    @property
    def wrapper_drop_count(self) -> int:
        """仅外壳自身捕获的 inner 抛错次数(契约测试用)。"""
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
