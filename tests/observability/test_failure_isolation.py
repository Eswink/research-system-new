"""故障注入套件:telemetry 故障不得破坏 canonical state(DoD-7)。

对每个注入故障(collector down / OTLP timeout / exporter 500 / slow / queue
full / malformed endpoint / restart / network interruption),运行同一确定性
canonical 工作流(workflow 提交→claim→heartbeat→complete、outbox、budget
reserve/usage、evidence source/evidence/claim),断言 canonical state 与
telemetry-off baseline 完全相等。SQLite 路径 m0 确定性;PG 路径见
test_postgres_failure_isolation.py(postgres 标记)。
"""

from __future__ import annotations

import pytest

from adapters.otel.config import OtelConfig
from adapters.otel.failsafe import FailSafeTelemetrySink
from adapters.otel.provider import build_telemetry_sink
from tests.observability.fault_collector import FaultyCollector
from tests.observability.isolation_scenario import (
    _begin_only,
    _engine,
    _evidence,
    _ledger,
    _run_workflow,
    _state_with,
)
from tests.observability.otlp_receiver import OtlpHttpReceiver


def test_scenario_is_deterministic_against_telemetry_off_baseline() -> None:
    assert _state_with(None) == _state_with(None)


def test_collector_down_preserves_canonical_state(collector: FaultyCollector) -> None:
    baseline = _state_with(None)
    endpoint = collector.endpoint
    collector.stop()
    failsafe = build_telemetry_sink(OtelConfig(enabled=True, endpoint=endpoint))
    state = _state_with(failsafe)
    failsafe.shutdown()
    assert state == baseline


def test_collector_500_preserves_canonical_state(collector: FaultyCollector) -> None:
    baseline = _state_with(None)
    collector.set_mode("500")
    failsafe = build_telemetry_sink(OtelConfig(enabled=True, endpoint=collector.endpoint))
    state = _state_with(failsafe)
    failsafe.shutdown()
    assert state == baseline
    assert collector.requests > 0


def test_otlp_timeout_preserves_canonical_state(collector: FaultyCollector) -> None:
    baseline = _state_with(None)
    collector.set_mode("slow")
    collector.set_slow_seconds(1.5)
    failsafe = build_telemetry_sink(
        OtelConfig(enabled=True, endpoint=collector.endpoint, timeout_seconds=0.2)
    )
    state = _state_with(failsafe)
    failsafe.shutdown(timeout_seconds=0.5)
    assert state == baseline


def test_slow_collector_preserves_canonical_state(collector: FaultyCollector) -> None:
    baseline = _state_with(None)
    collector.set_mode("slow")
    collector.set_slow_seconds(0.3)
    failsafe = build_telemetry_sink(
        OtelConfig(enabled=True, endpoint=collector.endpoint, timeout_seconds=5.0)
    )
    state = _state_with(failsafe)
    failsafe.shutdown()
    assert state == baseline


def test_network_interruption_preserves_canonical_state(collector: FaultyCollector) -> None:
    baseline = _state_with(None)
    collector.set_mode("hangup")
    failsafe = build_telemetry_sink(OtelConfig(enabled=True, endpoint=collector.endpoint))
    state = _state_with(failsafe)
    failsafe.shutdown()
    assert state == baseline


def test_collector_restart_preserves_canonical_state(collector: FaultyCollector) -> None:
    baseline = _state_with(None)
    failsafe = build_telemetry_sink(OtelConfig(enabled=True, endpoint=collector.endpoint))
    with collector.restart_window():
        state_mid = _state_with(failsafe)
    state_after = _state_with(failsafe)
    failsafe.shutdown()
    assert state_mid == baseline
    assert state_after == baseline


def test_malformed_endpoint_falls_back_to_null_and_preserves_state() -> None:
    """malformed endpoint → composition 装配回退 Null,canonical state 不变。"""
    from services.api.settings import ApiSettings, OtelSettings
    from services.api.telemetry import build_api_telemetry

    baseline = _state_with(None)
    composed = build_api_telemetry(ApiSettings(otel=OtelSettings(enabled=True, endpoint="::bad::")))
    assert isinstance(composed, FailSafeTelemetrySink)
    state = _state_with(composed)
    composed.shutdown()
    assert state == baseline


def test_span_mapper_overflow_drops_without_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """in-flight 上限淘汰:queue full 语义,丢弃计 drop,绝不抛出。"""
    monkeypatch.setattr("adapters.otel.span_mapping._MAX_IN_FLIGHT", 4)
    from adapters.otel.sink import OtelTelemetrySink

    receiver = OtlpHttpReceiver()
    receiver.start()
    try:
        config = OtelConfig(
            enabled=True,
            endpoint=receiver.endpoint,
            timeout_seconds=1.0,
            export_interval_millis=200,
            queue_size=2,
            compression="none",
        )
        failsafe = build_telemetry_sink(config)
        sink = failsafe.inner
        assert isinstance(sink, OtelTelemetrySink)
        # 并发 in-flight 超上限:begin 不 end → FIFO 淘汰计 drop,不抛出
        for index in range(12):
            sink.begin_operation(
                _begin_only(f"call-{index}"),
            )
        state = _state_with(failsafe)
        failsafe.flush(timeout_seconds=5.0)
        failsafe.shutdown()
        assert sink.dropped > 0
        assert state == _state_with(None)
    finally:
        receiver.stop()


def test_usage_ledger_entries_survive_collector_failure(collector: FaultyCollector) -> None:
    """usage 记账与 telemetry 故障完全隔离(DoD-9 前置)。"""
    collector.set_mode("500")
    failsafe = build_telemetry_sink(OtelConfig(enabled=True, endpoint=collector.endpoint))
    engine = _engine(failsafe)
    ledger = _ledger()
    evidence = _evidence()
    _run_workflow(engine, ledger, evidence)
    failsafe.shutdown()
    entries = ledger.snapshot().entries
    assert [(e.entry_id, e.quantity) for e in entries] == [("entry-1", 100)]
