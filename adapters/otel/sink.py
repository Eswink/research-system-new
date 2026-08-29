"""OtelTelemetrySink:TelemetrySink Port 的 OpenTelemetry 实现。

自身吞错并计 drop(port 契约:实现不得抛出);上层组合再包一层
`FailSafeTelemetrySink` 兜底(含 drop 计数,供 GET /runs/{id}/telemetry 读)。
不是 Audit Store:信号可 sampled/delayed/dropped,业务决策绝不回读。

duration metric 由 sink 在 `end_operation` 自动派生(scope→MetricName 映射),
站点无需重复计时;metric label 只取 `MetricLabel` 闭集内、且出现在 end
attributes 中的键——业务 id(run/task/trace)绝不进入 metric。
"""

from __future__ import annotations

import threading

from opentelemetry.metrics import Meter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import Tracer

from adapters.otel.metric_mapping import MetricMapper
from adapters.otel.span_mapping import SpanMapper
from packages.application.observability.attributes import (
    MetricKind,
    MetricName,
    MetricSample,
)
from packages.application.observability.signals import (
    OperationBegin,
    OperationEnd,
    OperationScope,
)

_DEFAULT_LIFECYCLE_TIMEOUT_SECONDS = 5.0

# scope → duration metric;EXPERIMENT 名义单位为秒(词汇定义),其余毫秒
# TASK 不在此列:WORKFLOW_TASK_DURATION_MS 由 workflow engine 按
# created_at 精确计时,避免编排层 TASK span 二次计数。
_DURATION_METRICS: dict[OperationScope, MetricName] = {
    OperationScope.LLM_CALL: MetricName.LLM_CALL_DURATION_MS,
    OperationScope.TOOL_CALL: MetricName.TOOL_CALL_DURATION_MS,
    OperationScope.EXPERIMENT_RUN: MetricName.EXPERIMENT_DURATION_SECONDS,
    OperationScope.EVAL_RUN: MetricName.EVAL_RUN_DURATION_MS,
}

# metric 允许继承的 end attribute 键(必须是 MetricLabel 闭集成员)
_METRIC_LABEL_FROM_ATTRS = ("provider", "model_id", "tool_id", "resource_type", "failure_category")


def duration_metric_for(scope: OperationScope) -> MetricName | None:
    return _DURATION_METRICS.get(scope)


class OtelTelemetrySink:
    """OTel SDK sink;begin/end 经 SpanMapper,metric 经 MetricMapper。"""

    def __init__(
        self,
        tracer: Tracer,
        meter: Meter,
        tracer_provider: TracerProvider,
        meter_provider: MeterProvider,
    ) -> None:
        self._span_mapper = SpanMapper(tracer)
        self._metric_mapper = MetricMapper(meter)
        self._tracer_provider = tracer_provider
        self._meter_provider = meter_provider
        self._dropped = 0
        self._lock = threading.Lock()
        self._scopes: dict[str, OperationScope] = {}

    def begin_operation(self, begin: OperationBegin) -> None:
        try:
            self._span_mapper.begin(begin)
            self._scopes[begin.span_ref.value] = begin.scope
        except Exception:
            self._count_drop()

    def end_operation(self, end: OperationEnd) -> None:
        try:
            scope = self._scopes.pop(end.span_ref.value, None)
            # 乱序 end 的丢弃由 span mapper 计数(见 dropped 聚合)
            self._span_mapper.end(end)
            if end.duration_ms is not None and scope is not None:
                self._emit_duration_metric(scope, end)
        except Exception:
            self._count_drop()

    def record_metric(self, sample: MetricSample) -> None:
        try:
            self._metric_mapper.record(sample)
        except Exception:
            self._count_drop()

    @property
    def dropped(self) -> int:
        """sink 内部丢弃计数:映射失败 + 乱序 end + in-flight 淘汰。"""
        return self._dropped + self._span_mapper.dropped

    def flush(self, timeout_seconds: float = _DEFAULT_LIFECYCLE_TIMEOUT_SECONDS) -> None:
        """有界 flush;失败只计 drop,不抛出。"""
        try:
            self._tracer_provider.force_flush(timeout_millis=int(timeout_seconds * 1000))
            self._meter_provider.force_flush(timeout_millis=int(timeout_seconds * 1000))
        except Exception:
            self._count_drop()

    def shutdown(self, timeout_seconds: float = _DEFAULT_LIFECYCLE_TIMEOUT_SECONDS) -> None:
        """有界 shutdown:先 flush 再停 provider;失败只计 drop,不抛出。"""
        self.flush(timeout_seconds)
        for provider in (self._meter_provider, self._tracer_provider):
            try:
                provider.shutdown()
            except Exception:
                self._count_drop()

    def _emit_duration_metric(self, scope: OperationScope, end: OperationEnd) -> None:
        metric_name = duration_metric_for(scope)
        if metric_name is None or end.duration_ms is None:
            return
        value: float = float(end.duration_ms)
        if metric_name is MetricName.EXPERIMENT_DURATION_SECONDS:
            value = value / 1000.0
        labels: dict[str, str] = {"scope": scope.value, "outcome": end.outcome.value}
        for key in _METRIC_LABEL_FROM_ATTRS:
            attr_value = end.attributes.get(key)
            if isinstance(attr_value, str):
                labels[key] = attr_value
        self._metric_mapper.record(
            MetricSample(name=metric_name, kind=MetricKind.HISTOGRAM, value=value, labels=labels)
        )

    def _count_drop(self) -> None:
        with self._lock:
            self._dropped += 1
