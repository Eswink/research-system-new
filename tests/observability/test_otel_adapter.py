"""OtelTelemetrySink 映射测试:真实 OTel SDK(InMemory exporter,无网络)。

覆盖:operation() → 真实 span(correlation/scope/attributes)、显式 parent
linkage、outcome → Status、显式时间戳、COUNTER/HISTOGRAM 映射、乱序 end
计 drop。OTLP 线上格式与隐私 canary 由后续 suite 覆盖(otlp_receiver)。
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import Histogram as HistogramData
from opentelemetry.sdk.metrics.export import InMemoryMetricReader, NumberDataPoint, Sum
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from adapters.otel.config import OtelConfig
from adapters.otel.resource import build_resource
from adapters.otel.sink import OtelTelemetrySink
from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import operation
from packages.application.observability.signals import (
    CorrelationRef,
    OperationBegin,
    OperationEnd,
    OperationOutcome,
    OperationScope,
    ParentSpanRef,
    SpanRef,
)

_UTC = timezone.utc


@dataclass
class _Harness:
    sink: OtelTelemetrySink
    exporter: InMemorySpanExporter
    reader: InMemoryMetricReader
    tracer_provider: TracerProvider
    meter_provider: MeterProvider


@pytest.fixture()
def harness() -> Iterator[_Harness]:
    resource = build_resource(OtelConfig(enabled=True))
    tracer_provider = TracerProvider(resource=resource, shutdown_on_exit=False)
    exporter = InMemorySpanExporter()
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    reader = InMemoryMetricReader()
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    sink = OtelTelemetrySink(
        tracer=tracer_provider.get_tracer("research-os"),
        meter=meter_provider.get_meter("research-os"),
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
    )
    try:
        yield _Harness(
            sink=sink,
            exporter=exporter,
            reader=reader,
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
        )
    finally:
        try:
            meter_provider.shutdown()
            tracer_provider.shutdown()
        except Exception:
            pass


def _flushed_spans(harness: _Harness) -> tuple[ReadableSpan, ...]:
    assert harness.tracer_provider.force_flush()
    return tuple(harness.exporter.get_finished_spans())


def test_operation_emits_span_with_correlation_and_sanitized_attributes(
    harness: _Harness,
) -> None:
    with operation(
        harness.sink,
        scope=OperationScope.LLM_CALL,
        name="relay.chat_completion",
        correlation=CorrelationRef(run_id="run-1", agent_session_id="session-9"),
        attributes={"provider": "relay-x", "attempt": 2, "unknown_key": "drop-me"},
    ):
        pass
    spans = _flushed_spans(harness)
    assert len(spans) == 1
    span = spans[0]
    attributes = dict(span.attributes or {})
    assert span.name == "relay.chat_completion"
    assert attributes["research_os.scope"] == "llm_call"
    assert attributes["research_os.correlation.run_id"] == "run-1"
    assert attributes["research_os.correlation.agent_session_id"] == "session-9"
    assert attributes["provider"] == "relay-x"
    assert attributes["attempt"] == 2
    assert "unknown_key" not in attributes
    assert span.status.status_code is StatusCode.OK
    assert span.parent is None


def test_parent_linkage_follows_correlation_hierarchy(harness: _Harness) -> None:
    """层级 scope 按约定以 scope.value 命名,子 span 才能按 correlation 链接。"""
    correlation = CorrelationRef(run_id="run-1", task_id="task-1")
    with operation(
        harness.sink,
        scope=OperationScope.RUN,
        name="run",
        correlation=correlation,
    ):
        with operation(
            harness.sink,
            scope=OperationScope.TASK,
            name="task",
            correlation=correlation,
        ):
            pass
    spans = _flushed_spans(harness)
    assert len(spans) == 2
    by_name = {span.name: span for span in spans}
    task_span = by_name["task"]
    run_span = by_name["run"]
    parent = task_span.parent
    assert parent is not None
    assert parent.span_id == run_span.context.span_id
    assert task_span.context.trace_id == run_span.context.trace_id


def test_failure_outcome_sets_error_status(harness: _Harness) -> None:
    with operation(
        harness.sink,
        scope=OperationScope.TOOL_CALL,
        name="tool.execute",
        correlation=CorrelationRef(run_id="run-1"),
    ) as op:
        op.set_outcome(OperationOutcome.FAILED, failure_category="tool_execution")
    (span,) = _flushed_spans(harness)
    assert span.status.status_code is StatusCode.ERROR
    assert (span.attributes or {})["research_os.outcome"] == "FAILED"
    assert (span.attributes or {})["research_os.failure_category"] == "tool_execution"


def test_exception_maps_to_failed(harness: _Harness) -> None:
    with (
        pytest.raises(RuntimeError),
        operation(
            harness.sink,
            scope=OperationScope.TASK,
            name="task.execute",
            correlation=CorrelationRef(run_id="run-1"),
        ),
    ):
        raise RuntimeError("boom")
    (span,) = _flushed_spans(harness)
    assert (span.attributes or {})["research_os.outcome"] == "FAILED"
    assert span.status.status_code is StatusCode.ERROR


def test_explicit_timestamps_are_preserved(harness: _Harness) -> None:
    started_at = datetime(2026, 8, 29, 12, 0, 0, 123456, tzinfo=_UTC)
    ended_at = datetime(2026, 8, 29, 12, 0, 1, 223456, tzinfo=_UTC)
    harness.sink.begin_operation(_begin_signal(started_at))
    harness.sink.end_operation(_end_signal(ended_at))
    (span,) = _flushed_spans(harness)
    assert span.start_time == int(started_at.timestamp()) * 1_000_000_000 + 123_456_000
    assert span.end_time == int(ended_at.timestamp()) * 1_000_000_000 + 223_456_000


def test_end_without_begin_counts_drop(harness: _Harness) -> None:
    harness.sink.end_operation(_end_signal(datetime.now(_UTC)))
    assert harness.sink.dropped == 1
    assert harness.exporter.get_finished_spans() == ()


def test_counter_and_histogram_reach_reader(harness: _Harness) -> None:
    harness.sink.record_metric(
        MetricSample(
            name=MetricName.OUTBOX_DRAINED,
            kind=MetricKind.COUNTER,
            value=3,
            labels={"outcome": "OK"},
        )
    )
    harness.sink.record_metric(
        MetricSample(
            name=MetricName.LLM_CALL_DURATION_MS,
            kind=MetricKind.HISTOGRAM,
            value=42.5,
            labels={"provider": "relay-x", "model_id": "model-1"},
        )
    )
    metrics_data = harness.reader.get_metrics_data()
    assert metrics_data is not None
    collected: dict[str, object] = {}
    for resource_metric in metrics_data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                collected[metric.name] = metric.data
    counter_data = collected[MetricName.OUTBOX_DRAINED.value]
    assert isinstance(counter_data, Sum)
    (counter_point,) = counter_data.data_points
    assert isinstance(counter_point, NumberDataPoint)
    assert counter_point.value == 3
    assert (counter_point.attributes or {}) == {"outcome": "OK"}
    histogram_data = collected[MetricName.LLM_CALL_DURATION_MS.value]
    assert isinstance(histogram_data, HistogramData)
    (histogram_point,) = histogram_data.data_points
    assert histogram_point.sum == pytest.approx(42.5)
    assert histogram_point.count == 1


def _begin_signal(started_at: datetime) -> OperationBegin:
    return OperationBegin(
        span_ref=SpanRef(value="a" * 32),
        parent_span_ref=ParentSpanRef(value=None),
        scope=OperationScope.TASK,
        name="task.execute",
        correlation=CorrelationRef(run_id="run-1", task_id="task-1"),
        started_at=started_at,
    )


def _end_signal(ended_at: datetime) -> OperationEnd:
    return OperationEnd(
        span_ref=SpanRef(value="a" * 32),
        outcome=OperationOutcome.OK,
        ended_at=ended_at,
    )


def test_repeated_leaf_operations_get_distinct_refs() -> None:
    """nonce 规则:叶子 scope 同 (scope,name,correlation) 重复/并发不碰撞。"""
    from adapters.fakes.telemetry_sink import FakeTelemetrySink

    fake = FakeTelemetrySink()
    for _ in range(3):
        with operation(fake, scope=OperationScope.LLM_CALL, name="llm.call"):
            pass
    refs = {begin.span_ref.value for begin in fake.begins}
    assert len(refs) == 3


def test_parent_scopes_keep_deterministic_refs() -> None:
    """父候选 scope 引用保持确定性(子操作可反推父引用)。"""
    from adapters.fakes.telemetry_sink import FakeTelemetrySink
    from packages.application.observability.scope import span_ref_of

    fake = FakeTelemetrySink()
    correlation = CorrelationRef(run_id="run-x")
    with operation(fake, scope=OperationScope.RUN, name="run", correlation=correlation):
        pass
    with operation(fake, scope=OperationScope.RUN, name="run", correlation=correlation):
        pass
    assert fake.begins[0].span_ref == fake.begins[1].span_ref
    assert fake.begins[0].span_ref == span_ref_of(correlation, OperationScope.RUN, "run")
