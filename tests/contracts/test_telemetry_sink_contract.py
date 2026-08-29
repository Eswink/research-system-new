"""TelemetrySink 专用 Port Contract suite(fail-open 语义,不进通用 suite)。

通用 suite 要求 close 后抛 PermanentPortError;TelemetrySink 的 port 契约
恰好相反:实现不得抛出(port docstring / ADR-0026)。本 suite 强制:
- 注册表内每个实现满足 Protocol、接收三类信号且永不抛出;
- Fake 记录信号、close 后计 drop;
- FailSafe 吞掉 inner 一切异常并计数;
- provider 构造失败回退 Null(telemetry off),不阻断调用方。
"""

from __future__ import annotations

from typing import Any

import pytest

from adapters.fakes import FakeTelemetrySink, NullTelemetrySink
from adapters.otel.config import OtelConfig
from adapters.otel.failsafe import FailSafeTelemetrySink
from adapters.otel.provider import build_telemetry_sink
from adapters.otel.sink import OtelTelemetrySink
from packages.application.observability.attributes import (
    MetricKind,
    MetricName,
    MetricSample,
)
from packages.application.observability.signals import (
    CorrelationRef,
    OperationBegin,
    OperationEnd,
    OperationOutcome,
    OperationScope,
    ParentSpanRef,
    SpanRef,
)
from packages.application.ports.telemetry_sink import TelemetrySink
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_SPAN_REF = SpanRef(value="0" * 32)
_PARENT_REF = ParentSpanRef(value="1" * 32)


def _begin() -> OperationBegin:
    return OperationBegin(
        span_ref=_SPAN_REF,
        parent_span_ref=_PARENT_REF,
        scope=OperationScope.LLM_CALL,
        name="relay.chat_completion",
        correlation=CorrelationRef(run_id="run-1"),
    )


def _end() -> OperationEnd:
    return OperationEnd(
        span_ref=_SPAN_REF,
        outcome=OperationOutcome.OK,
        duration_ms=12,
    )


def _metric() -> MetricSample:
    return MetricSample(
        name=MetricName.LLM_CALL_DURATION_MS,
        kind=MetricKind.HISTOGRAM,
        value=42,
    )


def _sink_implementations() -> list[object]:
    return [factory() for factory in PORT_IMPLEMENTATIONS["telemetry_sink"]]


_IMPLEMENTATION_IDS = lambda impl: type(impl).__name__  # noqa: E731


@pytest.mark.parametrize("implementation", _sink_implementations(), ids=_IMPLEMENTATION_IDS)
def test_implementations_satisfy_protocol(implementation: object) -> None:
    assert isinstance(implementation, TelemetrySink)


@pytest.mark.parametrize("implementation", _sink_implementations(), ids=_IMPLEMENTATION_IDS)
def test_fail_open_never_raises_on_signals(implementation: object) -> None:
    """三类信号(含重复 end、未知 span)都不得抛出。"""
    assert isinstance(implementation, TelemetrySink)
    sink = implementation
    sink.begin_operation(_begin())
    sink.begin_operation(_begin())
    sink.record_metric(_metric())
    sink.end_operation(_end())
    sink.end_operation(_end())


def test_fake_records_signals_in_order() -> None:
    fake = FakeTelemetrySink()
    fake.begin_operation(_begin())
    fake.end_operation(_end())
    fake.record_metric(_metric())
    assert fake.method_calls("begin_operation") == 1
    assert fake.method_calls("end_operation") == 1
    assert fake.method_calls("record_metric") == 1
    assert len(fake.begins) == 1 and len(fake.ends) == 1 and len(fake.metrics) == 1
    assert fake.calls[0].port == "telemetry_sink"
    assert fake.calls[0].index == 0


def test_fake_close_is_fail_open() -> None:
    fake = FakeTelemetrySink()
    fake.close()
    fake.begin_operation(_begin())
    fake.record_metric(_metric())
    assert fake.post_close_drops == 2
    assert fake.begins == ()
    assert fake.calls[-1].result_summary == "dropped"


def test_failsafe_swallows_inner_errors_and_counts() -> None:
    class ExplodingSink:
        def begin_operation(self, begin: OperationBegin) -> None:
            raise RuntimeError("boom")

        def end_operation(self, end: OperationEnd) -> None:
            raise RuntimeError("boom")

        def record_metric(self, sample: MetricSample) -> None:
            raise RuntimeError("boom")

    failsafe = FailSafeTelemetrySink(ExplodingSink())
    failsafe.begin_operation(_begin())
    failsafe.end_operation(_end())
    failsafe.record_metric(_metric())
    assert failsafe.drop_count == 3
    assert failsafe.last_error is not None
    assert "RuntimeError" in failsafe.last_error


def test_failsafe_lifecycle_passthrough_swallows() -> None:
    class LifecycleSink(NullTelemetrySink):
        def flush(self, timeout_seconds: float = 5.0) -> None:
            raise RuntimeError("flush boom")

        def shutdown(self, timeout_seconds: float = 5.0) -> None:
            raise RuntimeError("shutdown boom")

    failsafe = FailSafeTelemetrySink(LifecycleSink())
    failsafe.flush()
    failsafe.shutdown()
    assert failsafe.drop_count == 2


def test_failsafe_wrapping_null_counts_nothing() -> None:
    failsafe = FailSafeTelemetrySink(NullTelemetrySink())
    failsafe.begin_operation(_begin())
    failsafe.end_operation(_end())
    failsafe.record_metric(_metric())
    assert failsafe.drop_count == 0
    failsafe.shutdown()
    failsafe.flush()


def test_build_telemetry_sink_disabled_returns_null_composition() -> None:
    failsafe = build_telemetry_sink(OtelConfig(enabled=False))
    assert isinstance(failsafe.inner, NullTelemetrySink)
    failsafe.begin_operation(_begin())
    failsafe.shutdown()


def test_build_telemetry_sink_falls_back_to_null_on_construction_failure(
    monkeypatch: Any,
) -> None:
    """provider 构造失败 → 回退 Null(qualification:telemetry 保持 off,不阻断)。"""
    from adapters.otel import provider as otel_provider

    def _explode(config: OtelConfig, credentials: object) -> OtelTelemetrySink:
        raise RuntimeError("exporter construction failed")

    monkeypatch.setattr(otel_provider, "_build_otel_sink", _explode)
    failsafe = build_telemetry_sink(OtelConfig(enabled=True))
    assert isinstance(failsafe.inner, NullTelemetrySink)
    failsafe.begin_operation(_begin())
    failsafe.shutdown()


def test_otel_sink_with_dead_collector_is_fail_open() -> None:
    """真实 OTel sink 指向不可达 endpoint:信号永不抛出,shutdown 有界。"""
    config = OtelConfig(enabled=True, endpoint="http://127.0.0.1:9", timeout_seconds=0.5)
    failsafe = build_telemetry_sink(config)
    failsafe.begin_operation(_begin())
    failsafe.record_metric(_metric())
    failsafe.end_operation(_end())
    failsafe.shutdown(timeout_seconds=0.5)
