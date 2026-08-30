"""M15 privacy canary(WP4,DoD-5/6)——真实注入版。

复审发现前一版是**空测试**:它在模块级声明 7 个 uuid marker,而
`_emit_canary_signals` 一个都没注入,断言因此恒真;"Console 投影"那半更是拿
测试内部拼出的字面量自比,既不构造 DTO 也不调端点。

本版把 marker 真实注入到每一个可达通道,再扫描真实输出。两类断言的强度不同,
因为可达成的保证不同:

1. **凭据类**(API key / Authorization / DSN 密码):无论出现在哪个字段,
   都必须被 `redact_text` 抹掉。这是真正的安全属性,注入面覆盖 operation
   attributes、`failure_category`、span `name`、metric label、correlation id、
   resource(`service.version`)、异常消息与 OTLP header。
2. **内容类**(prompt / response / tool args / tool output / source / artifact
   body):保证是"**不存在内容通道**"——闭集里没有任何键以承载它们为职责,
   未知键被丢弃,`gen_ai.*` 全不存在,导出的键集严格落在闭集内。
   把内容硬塞进 identity 字段(例如往 `endpoint_id` 里写 prompt)属于调用方
   误用,词汇层无法在不使自身失效的前提下消除——诚实地按"无命名通道 +
   键集闭合"来验证,不写成"任意字符串都会消失"这种做不到的断言。

非空性由 `scratch` 变异实验独立证明:关闭 `redact_text` 后本套件必失败。
词汇/注入/解码的机械部分在 `canary_support.py`(单文件 300 行阈值)。
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

from adapters.otel.config import OtelConfig
from adapters.otel.provider import build_telemetry_sink
from packages.application.observability.attributes import (
    MetricKind,
    MetricLabel,
    MetricName,
    MetricSample,
    sanitize_attributes,
)
from packages.application.observability.scope import operation
from packages.application.observability.signals import CorrelationRef, OperationScope
from tests.observability.canary_support import (
    BEARER,
    CONTENT_KEY_CANDIDATES,
    CREDENTIAL_CANARIES,
    PROMPT,
    allowed_span_attribute_keys,
    decoded_span_text,
    emit_canary_signals,
    iter_metric_points,
    iter_spans,
    scan_surfaces,
)
from tests.observability.otlp_receiver import OtlpHttpReceiver

_MAX_LABEL_LENGTH = 64


@pytest.fixture
def receiver() -> Iterator[OtlpHttpReceiver]:
    instance = OtlpHttpReceiver()
    instance.start()
    try:
        yield instance
    finally:
        instance.stop()


def _emit_and_scan(
    receiver: OtlpHttpReceiver,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> dict[str, str]:
    with caplog.at_level(logging.DEBUG):
        sink = emit_canary_signals(receiver)
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    return scan_surfaces(receiver, sink, log_text, capsys.readouterr())


def test_credential_canaries_never_reach_any_telemetry_output(
    receiver: OtlpHttpReceiver,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """凭据 marker 注入全部通道后,不得出现在任何遥测输出面(DoD-5/6)。"""
    surfaces = _emit_and_scan(receiver, caplog, capsys)
    leaks = [
        f"{canary.kind} -> {surface}"
        for canary in CREDENTIAL_CANARIES
        for surface, text in surfaces.items()
        if canary.token in text
    ]
    assert not leaks, f"credential canaries leaked into telemetry: {sorted(leaks)}"


def test_content_named_keys_are_rejected_by_the_closed_vocabulary() -> None:
    """内容命名键在 attribute 与 metric label 两侧都必须被拒绝。"""
    dropped = sanitize_attributes({key: PROMPT.value for key in CONTENT_KEY_CANDIDATES})
    assert dropped == {}, f"content-named attribute keys must be dropped, kept: {dropped}"
    for key in CONTENT_KEY_CANDIDATES:
        with pytest.raises(ValueError, match="MetricLabel"):
            MetricSample(
                name=MetricName.OUTBOX_DRAINED,
                kind=MetricKind.COUNTER,
                value=1,
                labels={key: PROMPT.value},
            )


def test_no_named_content_channel_reaches_exported_spans(
    receiver: OtlpHttpReceiver,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """导出面无 `gen_ai.*`、无内容键,span attribute 键集严格闭合。"""
    surfaces = _emit_and_scan(receiver, caplog, capsys)
    for surface, text in surfaces.items():
        assert "gen_ai." not in text, f"GenAI convention key reached {surface}"
    for key in CONTENT_KEY_CANDIDATES:
        assert f'key: "{key}"' not in surfaces["DECODED_SPANS"], (
            f"content key {key} reached exported span attributes"
        )
    exported = {str(kv.key) for span in iter_spans(receiver) for kv in span.attributes}
    allowed = allowed_span_attribute_keys()
    assert exported <= allowed, (
        f"span attribute keys outside closed vocabulary: {sorted(exported - allowed)}"
    )


def test_canary_export_credential_stays_in_http_header_only(
    receiver: OtlpHttpReceiver,
) -> None:
    """OTLP 凭据只走 header:必须出现在 header,且不得进入 body 或解码属性。"""
    emit_canary_signals(receiver)
    headers = receiver.request_headers
    assert headers, "no OTLP request captured"
    assert any(BEARER.value == header.get("authorization") for header in headers), (
        "resolved credential must reach the authorization header (otherwise this test "
        "would pass trivially for the wrong reason)"
    )
    body = b"\n".join(receiver.payloads).decode("utf-8", errors="ignore")
    assert BEARER.token not in body, "credential must never enter the OTLP body"
    assert BEARER.token not in decoded_span_text(receiver)


def test_metric_labels_stay_in_closed_set_and_bounded(receiver: OtlpHttpReceiver) -> None:
    """metric label 键闭集 + 值有界:高基数 id 直接被构造期拒绝。"""
    for forbidden in ("run_id", "task_id", "trace_id", "phase_run_id", "prompt", "path"):
        with pytest.raises(ValueError, match="MetricLabel"):
            MetricSample(
                name=MetricName.OUTBOX_DRAINED,
                kind=MetricKind.COUNTER,
                value=1,
                labels={forbidden: "x"},
            )

    emit_canary_signals(receiver)
    allowed = {label.value for label in MetricLabel}
    seen_keys: set[str] = set()
    seen_values: set[str] = set()
    for _name, point in iter_metric_points(receiver):
        for kv in point.attributes:
            seen_keys.add(str(kv.key))
            seen_values.add(str(kv.value.string_value))
    assert seen_keys <= allowed, f"metric label keys outside closed set: {seen_keys - allowed}"
    for value in seen_values:
        assert len(value) <= _MAX_LABEL_LENGTH, f"unbounded metric label value: {value!r}"


def test_resource_attributes_ignore_environment_injection(
    receiver: OtlpHttpReceiver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`OTEL_RESOURCE_ATTRIBUTES` 不得把闭集外属性注入 resource。"""
    injected = "Z9RESOURCEENVcanary"
    monkeypatch.setenv("OTEL_RESOURCE_ATTRIBUTES", f"leaked.secret={injected}")
    emit_canary_signals(receiver)
    wire = b"\n".join(receiver.payloads).decode("utf-8", errors="ignore")
    assert injected not in wire, "OTEL_RESOURCE_ATTRIBUTES must not reach exported resources"
    assert "leaked.secret" not in wire


def test_export_headers_ignore_environment_injection(
    receiver: OtlpHttpReceiver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`OTEL_EXPORTER_OTLP_HEADERS` 不得绕过 CredentialResolver。"""
    injected = "Z9ENVHEADERcanary"
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", f"authorization=Bearer {injected}")
    sink = build_telemetry_sink(
        OtelConfig(
            enabled=True,
            endpoint=receiver.endpoint,
            timeout_seconds=2.0,
            export_interval_millis=200,
            compression="none",
        )
    )
    with operation(
        sink,
        scope=OperationScope.EVAL_RUN,
        name="eval.run",
        correlation=CorrelationRef(eval_run_id="eval-plain"),
    ):
        pass
    sink.flush(timeout_seconds=5.0)
    sink.shutdown(timeout_seconds=5.0)
    observed = [header.get("authorization", "") for header in receiver.request_headers]
    assert all(injected not in value for value in observed), (
        f"env-supplied credential bypassed CredentialResolver: {observed}"
    )
