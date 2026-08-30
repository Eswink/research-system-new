"""Telemetry 生命周期硬上界回归(M15 复审 BLOCKER-4)。

复审实测:请求 `flush(1.0)` / `shutdown(1.0)` 时,pinned OTLP/HTTP exporter 自算
deadline 并重试 6 次指数退避、SDK 又丢弃 export timeout,实际墙钟分别为 10.781s
与 20.047s——`timeout_seconds` 参数完全无效。`services/api/app.py` 在停机时调用
`shutdown()`,因此 collector 无响应时 API 进程阻塞约 20s。

本套件断言上界由**构造**保证(daemon watchdog + 硬 join),与上游重试行为无关:
把 exporter 指向一个接受连接但永不响应的 blackhole,再测量真实墙钟。
"""

from __future__ import annotations

import time
from collections.abc import Iterator

import pytest

from adapters.otel.config import OtelConfig
from adapters.otel.provider import build_telemetry_sink
from packages.application.observability.scope import operation
from packages.application.observability.signals import CorrelationRef, OperationScope
from tests.observability.fault_collector import FaultyCollector

# 上界余量:watchdog 只保证不超过 timeout + 线程调度开销。
_SLACK_SECONDS = 1.0
_REQUESTED_TIMEOUT = 1.0


@pytest.fixture
def blackhole() -> Iterator[FaultyCollector]:
    collector = FaultyCollector()
    collector.start()
    collector.set_mode("blackhole")
    try:
        yield collector
    finally:
        collector.stop()


def _config(endpoint: str) -> OtelConfig:
    return OtelConfig(
        enabled=True,
        endpoint=endpoint,
        # 每次导出的 HTTP 超时故意大于请求的生命周期预算:若上界依赖上游
        # 行为而非 watchdog,本套件必然失败。
        timeout_seconds=5.0,
        export_interval_millis=200,
        queue_size=64,
        compression="none",
    )


def _emit(sink: object, count: int = 5) -> None:
    for index in range(count):
        with operation(
            sink,  # type: ignore[arg-type]
            scope=OperationScope.LLM_CALL,
            name="llm.call",
            correlation=CorrelationRef(run_id=f"run-{index}"),
        ):
            pass


def test_flush_is_bounded_by_its_timeout_argument(blackhole: FaultyCollector) -> None:
    sink = build_telemetry_sink(_config(blackhole.endpoint))
    _emit(sink)
    started = time.monotonic()
    sink.flush(timeout_seconds=_REQUESTED_TIMEOUT)
    elapsed = time.monotonic() - started
    sink.shutdown(timeout_seconds=_REQUESTED_TIMEOUT)
    assert elapsed < _REQUESTED_TIMEOUT + _SLACK_SECONDS, (
        f"flush({_REQUESTED_TIMEOUT}) took {elapsed:.3f}s against an unresponsive collector; "
        "the timeout argument must be a hard bound, not a suggestion"
    )


def test_shutdown_is_bounded_by_its_timeout_argument(blackhole: FaultyCollector) -> None:
    sink = build_telemetry_sink(_config(blackhole.endpoint))
    _emit(sink)
    started = time.monotonic()
    sink.shutdown(timeout_seconds=_REQUESTED_TIMEOUT)
    elapsed = time.monotonic() - started
    assert elapsed < _REQUESTED_TIMEOUT + _SLACK_SECONDS, (
        f"shutdown({_REQUESTED_TIMEOUT}) took {elapsed:.3f}s against an unresponsive collector; "
        "API process teardown must not block on exporter retries"
    )


def test_exporter_failure_is_visible_in_drop_count(blackhole: FaultyCollector) -> None:
    """exporter 健康信号必须能报告失败(原先结构性恒 0)。

    `FailSafeTelemetrySink.drop_count` 过去只数 inner **抛出**的异常,而
    `OtelTelemetrySink` 自吞全部错误 → 全量导出失败下该字段仍为 0,
    `GET /runs/{id}/telemetry` 因此永远报告"零丢弃"。
    """
    sink = build_telemetry_sink(_config(blackhole.endpoint))
    _emit(sink)
    sink.shutdown(timeout_seconds=_REQUESTED_TIMEOUT)
    assert sink.drop_count > 0, (
        "total export failure must surface as a non-zero drop_count; "
        f"got {sink.drop_count} (wrapper-only={sink.wrapper_drop_count})"
    )


def test_healthy_collector_lifecycle_stays_fast_and_clean() -> None:
    """正常 collector 下生命周期远低于预算且无 drop(避免上界测试变成恒真)。"""
    collector = FaultyCollector()
    collector.start()
    collector.set_mode("ok")
    try:
        sink = build_telemetry_sink(_config(collector.endpoint))
        _emit(sink)
        started = time.monotonic()
        sink.flush(timeout_seconds=_REQUESTED_TIMEOUT)
        sink.shutdown(timeout_seconds=_REQUESTED_TIMEOUT)
        elapsed = time.monotonic() - started
    finally:
        collector.stop()
    assert elapsed < _REQUESTED_TIMEOUT, f"healthy lifecycle took {elapsed:.3f}s"
    assert sink.drop_count == 0, f"healthy run reported drops: {sink.last_error}"
