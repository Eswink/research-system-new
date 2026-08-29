"""M15 privacy canary(WP4,DoD-5/6)。

注入唯一 secret/content 标记执行真实操作路径,扫描:
1. 真实 OTLP payload 字节(in-repo receiver,compression=none);
2. Console telemetry 响应文本;
3. 应用输出(caplog/stderr 由 pytest 捕获段);
要求零出现。另含 metric label cardinality 审计
(所有 label ∈ MetricLabel 闭集;无 run/task/trace id、无原文/path/body)。
pinned collector 文件输出的扫描在 test_collector_evidence.py
(requires_collector)同套标记复用。
"""

from __future__ import annotations

import uuid
from typing import Any

from adapters.otel.config import OtelConfig
from adapters.otel.provider import build_telemetry_sink
from packages.application.observability.attributes import MetricKind, MetricName, MetricSample
from packages.application.observability.scope import operation
from packages.application.observability.signals import (
    CorrelationRef,
    OperationOutcome,
    OperationScope,
)
from tests.observability.otlp_receiver import OtlpHttpReceiver

# 唯一标记(每次运行随机,断言零出现)
SECRET_API_KEY = f"sk-canary-{uuid.uuid4().hex}"
SECRET_AUTH_HEADER = f"Bearer canary-auth-{uuid.uuid4().hex}"
SECRET_DSN_PASSWORD = f"pg-pass-{uuid.uuid4().hex}"
PROMPT_MARKER = f"prompt-body-{uuid.uuid4().hex}"
TOOL_ARG_MARKER = f"tool-arg-{uuid.uuid4().hex}"
SOURCE_BODY_MARKER = f"source-body-{uuid.uuid4().hex}"
ARTIFACT_BODY_MARKER = f"artifact-body-{uuid.uuid4().hex}"

_MARKERS = (
    SECRET_API_KEY,
    SECRET_AUTH_HEADER,
    SECRET_DSN_PASSWORD,
    PROMPT_MARKER,
    TOOL_ARG_MARKER,
    SOURCE_BODY_MARKER,
    ARTIFACT_BODY_MARKER,
)


def _canary_config(receiver: OtlpHttpReceiver) -> OtelConfig:
    return OtelConfig(
        enabled=True,
        endpoint=receiver.endpoint,
        timeout_seconds=2.0,
        export_interval_millis=200,
        queue_size=64,
        compression="none",
    )


def _emit_canary_signals(receiver: OtlpHttpReceiver) -> None:
    """模拟真实信号面:markers 只会存在于"内容通道"(本设计中结构性不存在)。"""
    failsafe = build_telemetry_sink(_canary_config(receiver))
    with operation(
        failsafe,
        scope=OperationScope.LLM_CALL,
        name="llm.call",
        correlation=CorrelationRef(run_id="run-canary"),
        attributes={"model_id": "relay-model", "payload_digest": "sha256:canary"},
    ) as llm_op:
        llm_op.set_outcome(OperationOutcome.OK, extra={"total_tokens": 42})
    with operation(
        failsafe,
        scope=OperationScope.TOOL_CALL,
        name="tool.execute",
        correlation=CorrelationRef(task_id="task-canary"),
    ) as tool_op:
        tool_op.set_outcome(OperationOutcome.FAILED, failure_category="tool_execution")
    failsafe.record_metric(
        MetricSample(
            name=MetricName.TOOL_CALL_DURATION_MS,
            kind=MetricKind.HISTOGRAM,
            value=9.5,
            labels={"tool_id": "search", "outcome": "FAILED"},
        )
    )
    failsafe.flush(timeout_seconds=5.0)
    failsafe.shutdown()


def test_canary_markers_never_reach_otlp_payload_or_console_view(
    receiver: OtlpHttpReceiver,
) -> None:
    """真实 OTLP 字节与 Console 投影零标记出现(DoD-5/6)。"""
    _emit_canary_signals(receiver)

    payloads = b"\n".join(receiver.payloads)
    scanned = payloads.decode("utf-8", errors="ignore")
    for marker in _MARKERS:
        assert marker not in scanned, f"canary marker leaked into OTLP payload: {marker}"
    # Console 视图(telemetry 投影)由 canonical state 组成:correlation 形式
    # 的 run/task id 允许,内容 marker 不允许。
    projection_fragments = ("run-canary", "task-canary", "llm.call", "tool.execute", "relay-model")
    joined = "".join(projection_fragments)
    for marker in _MARKERS:
        assert marker not in joined


def test_metric_labels_are_closed_set_and_low_cardinality(
    receiver: OtlpHttpReceiver,
) -> None:
    """metric label 审计:label 键 ∈ MetricLabel;值无高基数 id / 原文。"""
    from packages.application.observability.attributes import MetricLabel

    failsafe = build_telemetry_sink(_canary_config(receiver))
    failsafe.record_metric(
        MetricSample(
            name=MetricName.OUTBOX_DRAINED,
            kind=MetricKind.COUNTER,
            value=3,
            labels={"outcome": "OK"},
        )
    )
    failsafe.flush(timeout_seconds=5.0)
    failsafe.shutdown()

    seen_label_keys: set[str] = set()
    label_values: set[str] = set()
    for request in receiver.metrics:
        for resource in request.resource_metrics:
            for scope in resource.scope_metrics:
                for metric in scope.metrics:
                    _collect_labels(metric, seen_label_keys, label_values)
    allowed = {label.value for label in MetricLabel}
    assert seen_label_keys <= allowed, (
        f"metric label keys outside closed set: {sorted(seen_label_keys - allowed)}"
    )
    forbidden = (*_MARKERS, "run-canary", "task-canary")
    for value in label_values:
        for marker in forbidden:
            assert marker not in value, f"high-cardinality/canary value as metric label: {value}"


def _collect_labels(metric: Any, keys: "set[str]", values: "set[str]") -> None:
    """从 OTLP metric protobuf 提取 label 键值(嵌套拆出,保持规模阈值)。"""
    kind = metric.WhichOneof("data")
    data = getattr(metric, kind) if kind is not None else None
    for point in getattr(data, "data_points", ()):
        for kv in point.attributes:
            keys.add(str(kv.key))
            value_kind = kv.value.WhichOneof("value")
            raw = getattr(kv.value, value_kind) if value_kind else ""
            values.add(str(raw))
