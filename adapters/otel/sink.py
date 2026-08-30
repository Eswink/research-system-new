"""OtelTelemetrySink:TelemetrySink Port 的 OpenTelemetry 实现。

自身吞错并计 drop(port 契约:实现不得抛出);上层组合再包一层
`FailSafeTelemetrySink` 兜底(含 drop 计数,供 GET /runs/{id}/telemetry 读)。
不是 Audit Store:信号可 sampled/delayed/dropped,业务决策绝不回读。

duration metric 由 sink 在 `end_operation` 自动派生(scope→MetricName 映射),
站点无需重复计时;metric label 只取 `MetricLabel` 闭集内、且出现在 end
attributes 中的键——业务 id(run/task/trace)绝不进入 metric。

生命周期上界(M15 复审修复):`flush`/`shutdown` 在 daemon watchdog 线程里执行
并硬性 `join(timeout)`。pinned OTLP/HTTP exporter 自算 deadline 并重试 6 次
指数退避、SDK 又丢弃 export timeout,所以 `force_flush(timeout_millis=…)`
**不受该参数约束**——实测请求 1s 实际 10.8s(flush) / 20.0s(shutdown),API 停机
因此阻塞约 20s。watchdog 让上界由构造保证,与上游重试行为无关。
"""

from __future__ import annotations

import threading
from collections.abc import Callable

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

_DEFAULT_LIFECYCLE_TIMEOUT_SECONDS = 3.0
# `_scopes` 与 SpanMapper in-flight 表同界:原先只在 end_operation 弹出,
# 未配对 begin 会让它无界增长(M15 复审实测 6 万次后达 60000,而 in-flight
# 正确停在 4096——上层反而抵消了下层的驱逐上界)。
_MAX_TRACKED_SCOPES = 4096

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
            self._track_scope(begin.span_ref.value, begin.scope)
        except Exception:
            self._count_drop()

    def end_operation(self, end: OperationEnd) -> None:
        try:
            with self._lock:
                scope = self._scopes.pop(end.span_ref.value, None)
            # 乱序 end 的丢弃由 span mapper 计数(见 dropped 聚合)
            self._span_mapper.end(end)
            if end.duration_ms is not None and scope is not None:
                self._emit_duration_metric(scope, end)
        except Exception:
            self._count_drop()

    def _track_scope(self, span_ref: str, scope: OperationScope) -> None:
        """记录 span_ref→scope,并与 in-flight 表同界(最旧先淘汰)。"""
        with self._lock:
            while len(self._scopes) >= _MAX_TRACKED_SCOPES:
                oldest = next(iter(self._scopes))
                self._scopes.pop(oldest, None)
                self._dropped += 1
            self._scopes[span_ref] = scope

    def record_metric(self, sample: MetricSample) -> None:
        try:
            self._metric_mapper.record(sample)
        except Exception:
            self._count_drop()

    @property
    def dropped(self) -> int:
        """真实丢弃计数(不含链接降级)。

        聚合:映射失败 + 乱序 end + in-flight 淘汰 + scope 表淘汰 +
        生命周期超时/失败。父引用不可解析**不**计入——那是链接降级,
        span 照常导出,合并会让健康 run 报幻影 drop(M15 复审实测每 run 3 次)。
        """
        with self._lock:
            own = self._dropped
        return own + self._span_mapper.dropped

    @property
    def unlinked(self) -> int:
        """父引用不可解析的次数(trace 层级不完整,信号未丢)。"""
        return self._span_mapper.unlinked

    def flush(self, timeout_seconds: float = _DEFAULT_LIFECYCLE_TIMEOUT_SECONDS) -> None:
        """硬性有界 flush:watchdog 线程 + join(timeout);失败只计 drop,不抛出。"""
        self._run_bounded(lambda: self._flush_providers(timeout_seconds), timeout_seconds)

    def shutdown(self, timeout_seconds: float = _DEFAULT_LIFECYCLE_TIMEOUT_SECONDS) -> None:
        """硬性有界 shutdown:flush + 停 provider 共享同一预算,整体不超 timeout。"""
        self._run_bounded(lambda: self._shutdown_providers(timeout_seconds), timeout_seconds)

    def _run_bounded(self, action: Callable[[], None], timeout_seconds: float) -> bool:
        """在 daemon 线程执行 action 并硬性 join;超时放弃线程并计 drop。

        放弃的线程是 daemon:进程退出不会被它阻塞。上游 exporter 的重试循环
        可能仍在后台跑完,但业务停机路径不再等它。
        """
        finished = threading.Event()

        def _target() -> None:
            try:
                action()
            except Exception:
                self._count_drop()
            finally:
                finished.set()

        worker = threading.Thread(target=_target, name="otel-lifecycle", daemon=True)
        worker.start()
        if not finished.wait(max(0.0, timeout_seconds)):
            self._count_drop()
            return False
        return True

    def _flush_providers(self, timeout_seconds: float) -> None:
        timeout_millis = int(max(0.0, timeout_seconds) * 1000)
        for provider in (self._tracer_provider, self._meter_provider):
            try:
                provider.force_flush(timeout_millis=timeout_millis)
            except Exception:
                self._count_drop()

    def _shutdown_providers(self, timeout_seconds: float) -> None:
        self._flush_providers(timeout_seconds)
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
