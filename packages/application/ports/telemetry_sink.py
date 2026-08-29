"""TelemetrySink Port:Research OS 内部观测信号落槽。

职责:接收 `OperationBegin/End` 与 `MetricSample`,交由 `adapters/otel`(或
Fake/Null)导出。fail-open:实现必须吞掉自身错误,不得把 exporter 失败传播
到业务路径;不是 Audit Store(telemetry 可 sampled/delayed/dropped)。

非职责:不做业务决策回读;不存储业务真相(domain event / budget / eval verdict
是唯一 truth);不承载内容(prompt/response/tool args/artifact body)。

对应 `docs/architecture/OBSERVABILITY.md`、ADR-0020 / ADR-0026。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.application.observability.attributes import MetricSample
from packages.application.observability.signals import OperationBegin, OperationEnd


@runtime_checkable
class TelemetrySink(Protocol):
    """operational signal sink;实现不得抛出,不是 Audit Store。"""

    def begin_operation(self, begin: OperationBegin) -> None: ...

    def end_operation(self, end: OperationEnd) -> None: ...

    def record_metric(self, sample: MetricSample) -> None: ...


class NullTelemetrySink:
    """telemetry off 的默认实现(fail-open,零开销)。"""

    def begin_operation(self, begin: OperationBegin) -> None:
        return None

    def end_operation(self, end: OperationEnd) -> None:
        return None

    def record_metric(self, sample: MetricSample) -> None:
        return None

    @property
    def calls(self) -> tuple[object, ...]:
        """contract-suite 约定:call log;Null 永远为空。"""
        return ()
