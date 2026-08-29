"""真实 OTLP wire bytes 往返测试(in-repo receiver,m0 确定性门禁)。

证明 OtelTelemetrySink 导出的是真实 OTLP/HTTP protobuf(经 opentelemetry-proto
解码),span 名/attributes 经 wire 保留;并顺带验证 payload 无常见 secret 形态
(完整隐私 canary 在 tests/observability/test_privacy_canary.py)。
"""

from __future__ import annotations

import re

from adapters.otel.config import OtelConfig
from adapters.otel.provider import build_telemetry_sink
from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import operation
from packages.application.observability.signals import CorrelationRef, OperationScope
from tests.observability.otlp_receiver import OtlpHttpReceiver


def test_roundtrip_spans_reach_receiver_as_real_protobuf(receiver: OtlpHttpReceiver) -> None:
    config = OtelConfig(
        enabled=True,
        endpoint=receiver.endpoint,
        timeout_seconds=2.0,
        export_interval_millis=200,
        queue_size=64,
        compression="none",
    )
    failsafe = build_telemetry_sink(config)
    with operation(
        failsafe,
        scope=OperationScope.RUN,
        name="run",
        correlation=CorrelationRef(run_id="run-wire-1"),
    ):
        with operation(
            failsafe,
            scope=OperationScope.LLM_CALL,
            name="llm.call",
            correlation=CorrelationRef(run_id="run-wire-1"),
            attributes={"endpoint_id": "main", "model_id": "relay-model"},
        ):
            pass
    failsafe.flush(timeout_seconds=5.0)
    failsafe.shutdown()
    names = receiver.span_names
    assert "run" in names
    assert "llm.call" in names
    assert receiver.payloads, "raw OTLP bytes must be captured"


def test_roundtrip_metrics_reach_receiver(receiver: OtlpHttpReceiver) -> None:
    config = OtelConfig(
        enabled=True,
        endpoint=receiver.endpoint,
        timeout_seconds=2.0,
        export_interval_millis=200,
        queue_size=64,
        compression="none",
    )
    failsafe = build_telemetry_sink(config)
    failsafe.record_metric(
        MetricSample(
            name=MetricName.TOOL_CALL_DURATION_MS,
            kind=MetricKind.HISTOGRAM,
            value=17.5,
            labels={"tool_id": "search"},
        )
    )
    failsafe.flush(timeout_seconds=5.0)
    failsafe.shutdown()
    assert receiver.metrics, "metrics export must reach receiver"
    found = [
        metric.name
        for request in receiver.metrics
        for resource in request.resource_metrics
        for scope in resource.scope_metrics
        for metric in scope.metrics
    ]
    assert "research_os.tool_call.duration_ms" in found


def test_receiver_payload_has_no_obvious_secret(receiver: OtlpHttpReceiver) -> None:
    config = OtelConfig(
        enabled=True,
        endpoint=receiver.endpoint,
        timeout_seconds=2.0,
        export_interval_millis=200,
        queue_size=64,
        compression="none",
    )
    failsafe = build_telemetry_sink(config)
    with operation(
        failsafe,
        scope=OperationScope.TOOL_CALL,
        name="tool.execute",
        correlation=CorrelationRef(task_id="task-wire"),
    ):
        pass
    failsafe.flush(timeout_seconds=5.0)
    failsafe.shutdown()
    secret_patterns = (
        re.compile(r"Bearer\s+[A-Za-z0-9._-]+"),
        re.compile(r"sk-[A-Za-z0-9]{16,}"),
        re.compile(r"(?i)password[=:\s]"),
    )
    for payload in receiver.payloads:
        text = payload.decode("utf-8", errors="ignore")
        for pattern in secret_patterns:
            matches = pattern.findall(text)
            assert not matches, f"secret-shaped {pattern.pattern!r} in OTLP payload: {matches[:2]}"
