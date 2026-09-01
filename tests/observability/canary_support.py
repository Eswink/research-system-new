"""M15 privacy canary 支撑面:词汇、注入、解码与扫描面。

从 `test_privacy_canary.py` 拆出(单文件 300 行阈值)。断言留在测试文件里,
这里只提供"真实注入 + 真实解码"的机械部分。

marker 每次导入随机:任何把 marker 写进期望值的作弊都无法通过。
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, cast

from adapters.otel.config import OtelConfig
from adapters.otel.provider import build_telemetry_sink
from packages.application.observability.attributes import (
    AttributeKey,
    MetricKind,
    MetricLabel,
    MetricName,
    MetricSample,
)
from packages.application.observability.scope import operation
from packages.application.observability.signals import (
    CorrelationRef,
    OperationOutcome,
    OperationScope,
)
from packages.application.ports.credential_resolver import CredentialResolver
from services.api.mappers.operations import sink_counters_dto
from tests.observability.otlp_receiver import OtlpHttpReceiver

_RUN = uuid.uuid4().hex[:10]
RESEARCH_OS_SPAN_PREFIX = "research_os."


@dataclass(frozen=True, slots=True)
class Canary:
    kind: str
    value: str

    @property
    def token(self) -> str:
        """扫描用核心 token(不含可被 redaction 合法改写的前后缀)。"""
        return f"Z9{self.kind.upper()}{_RUN}"


def _canary(kind: str, template: str) -> Canary:
    return Canary(kind=kind, value=template.format(token=f"Z9{kind.upper()}{_RUN}"))


API_KEY = _canary("apikey", "sk-live-{token}0123456789abcdef")
BEARER = _canary("bearer", "Bearer {token}0123456789abcdef")
PG_PASSWORD = _canary("pgpassword", "postgresql://research_os:{token}@db.internal:5432/db")
CREDENTIAL_CANARIES = (API_KEY, BEARER, PG_PASSWORD)

PROMPT = _canary("prompt", "PROMPT[{token}]")
RESPONSE = _canary("response", "RESPONSE[{token}]")
TOOL_ARG = _canary("toolarg", '{{"query": "{token}"}}')
TOOL_OUTPUT = _canary("tooloutput", "TOOLOUT[{token}]")
SOURCE_BODY = _canary("sourcebody", "SOURCE[{token}]")
ARTIFACT_BODY = _canary("artifactbody", "ARTIFACT[{token}]")
CONTENT_CANARIES = (PROMPT, RESPONSE, TOOL_ARG, TOOL_OUTPUT, SOURCE_BODY, ARTIFACT_BODY)

# 内容通道候选键名:必须**全部**被闭集拒绝
CONTENT_KEY_CANDIDATES = (
    "prompt",
    "completion",
    "response",
    "messages",
    "input",
    "output",
    "body",
    "content",
    "tool_arguments",
    "tool_result",
    "reasoning",
    "chain_of_thought",
    "gen_ai.prompt",
    "gen_ai.completion",
    "gen_ai.system_instructions",
    "gen_ai.input.messages",
    "gen_ai.output.messages",
    "authorization",
    "api_key",
    "database_url",
)

STRING_ATTRIBUTE_KEYS = (
    AttributeKey.provider,
    AttributeKey.endpoint_id,
    AttributeKey.model_id,
    AttributeKey.tool_id,
    AttributeKey.resource_type,
    AttributeKey.status_code_class,
    AttributeKey.failure_category,
    AttributeKey.payload_digest,
    AttributeKey.circuit_state,
    AttributeKey.verdict,
    AttributeKey.dataset_digest,
    AttributeKey.image_digest,
)

CORRELATION_SUFFIXES = (
    "project_id",
    "run_id",
    "phase_run_id",
    "task_id",
    "agent_session_id",
    "tool_call_id",
    "experiment_run_id",
    "eval_run_id",
    "trace_id",
)


class _CanaryCredentialResolver:
    """把 canary 当成 OTLP header 凭据解析出来(必须只出现在 header)。"""

    def resolve(self, credential_ref: str) -> Any:
        @dataclass(frozen=True, slots=True)
        class _Secret:
            value: str

        return _Secret(value=BEARER.value)


class BoomWithSecret(RuntimeError):
    """异常消息里带 marker:验证异常不会被写进 telemetry。"""


def canary_config(endpoint: str, *, with_credential: bool = True) -> OtelConfig:
    return OtelConfig(
        enabled=True,
        endpoint=endpoint,
        timeout_seconds=2.0,
        export_interval_millis=200,
        queue_size=128,
        compression="none",  # 明文 wire bytes 才能逐字节扫描
        service_version=API_KEY.value,  # resource 通道注入
        header_credential_refs=(("authorization", "canary-ref"),) if with_credential else (),
    )


def _cycled(values: tuple[str, ...], keys: tuple[Any, ...]) -> dict[str, str]:
    return {key.value: values[index % len(values)] for index, key in enumerate(keys)}


def all_marker_values() -> tuple[str, ...]:
    return tuple(item.value for item in (*CREDENTIAL_CANARIES, *CONTENT_CANARIES))


def _emit_llm_call_with_markers(sink: Any, markers: tuple[str, ...]) -> None:
    """LLM_CALL 通道:attributes/correlation/name/outcome 全塞 marker。"""
    attributes: dict[str, object] = {
        **_cycled(markers, STRING_ATTRIBUTE_KEYS),
        # 内容命名键必须被 sanitize 丢弃
        **{key: PROMPT.value for key in CONTENT_KEY_CANDIDATES},
    }
    with operation(
        sink,
        scope=OperationScope.LLM_CALL,
        name=f"llm.call.{API_KEY.value}",
        correlation=CorrelationRef(
            run_id=f"run-{PG_PASSWORD.value}",
            task_id=f"task-{BEARER.value}",
            agent_session_id=f"sess-{API_KEY.value}",
            tool_call_id=API_KEY.value,
            trace_id=f"trace-{BEARER.value}",
        ),
        attributes=attributes,
    ) as llm_op:
        llm_op.set_outcome(
            OperationOutcome.FAILED,
            failure_category=f"{PG_PASSWORD.value} {BEARER.value}",
            extra=attributes,
        )


def emit_canary_signals(receiver: OtlpHttpReceiver, *, with_credential: bool = True) -> Any:
    """真实注入:每个通道都塞 marker,然后真实导出。"""
    sink = build_telemetry_sink(
        canary_config(receiver.endpoint, with_credential=with_credential),
        cast(CredentialResolver, _CanaryCredentialResolver()),
    )
    markers = all_marker_values()
    _emit_llm_call_with_markers(sink, markers)
    try:
        with operation(
            sink,
            scope=OperationScope.TOOL_CALL,
            name="tool.execute",
            correlation=CorrelationRef(task_id="task-plain"),
        ):
            raise BoomWithSecret(f"failed with {API_KEY.value} and {PG_PASSWORD.value}")
    except BoomWithSecret:
        pass
    sink.record_metric(
        MetricSample(
            name=MetricName.TOOL_CALL_DURATION_MS,
            kind=MetricKind.HISTOGRAM,
            value=9.5,
            labels=_cycled(markers, tuple(MetricLabel)),
        )
    )
    _emit_worker_channel(sink, markers)
    sink.flush(timeout_seconds=5.0)
    sink.shutdown(timeout_seconds=5.0)
    return sink


def _emit_worker_channel(sink: Any, markers: tuple[str, ...]) -> None:
    """M16 re-audit F-9: worker/remote-execution channels must not carry markers.

    Every M16 span scope (WORKER_SESSION / WORKER_DISPATCH / REMOTE_EXECUTION)
    and the worker/remote metrics are stuffed with the same canary markers in
    attributes, correlation ids and labels; the byte-scan then proves none of
    them reach the exported OTLP wire.
    """
    for scope in (
        OperationScope.WORKER_SESSION,
        OperationScope.WORKER_DISPATCH,
        OperationScope.REMOTE_EXECUTION,
    ):
        with operation(
            sink,
            scope=scope,
            name=f"{scope.value}.canary",
            correlation=CorrelationRef(
                run_id=f"run-{API_KEY.value}",
                task_id=f"task-{BEARER.value}",
                agent_session_id=f"sess-{PG_PASSWORD.value}",
            ),
            attributes={
                **_cycled(markers, STRING_ATTRIBUTE_KEYS),
                # raw worker id / bundle content must never be exported
                "worker_ref": PG_PASSWORD.value,
                **{key: PROMPT.value for key in CONTENT_KEY_CANDIDATES},
            },
        ):
            pass
    for metric in (
        MetricName.WORKER_REGISTERED_TOTAL,
        MetricName.WORKER_HEARTBEAT_LOST_TOTAL,
        MetricName.REMOTE_EXECUTION_DURATION_MS,
        MetricName.SCHEDULER_PARTITION_LAG,
    ):
        sink.record_metric(
            MetricSample(
                name=metric,
                kind=MetricKind.COUNTER if "total" in metric.value else MetricKind.HISTOGRAM,
                value=1,
                labels=_cycled(markers, tuple(MetricLabel)),
            )
        )


def iter_spans(receiver: OtlpHttpReceiver) -> Iterator[Any]:
    for request in receiver.traces:
        for resource in request.resource_spans:
            for scope in resource.scope_spans:
                yield from scope.spans


def iter_resource_attributes(receiver: OtlpHttpReceiver) -> Iterator[Any]:
    for request in receiver.traces:
        for resource in request.resource_spans:
            yield from resource.resource.attributes
    for request in receiver.metrics:
        for resource in request.resource_metrics:
            yield from resource.resource.attributes


def iter_metric_points(receiver: OtlpHttpReceiver) -> Iterator[tuple[str, Any]]:
    for request in receiver.metrics:
        for resource in request.resource_metrics:
            for scope in resource.scope_metrics:
                yield from _iter_scope_points(scope)


def _iter_scope_points(scope: Any) -> Iterator[tuple[str, Any]]:
    for metric in scope.metrics:
        kind = metric.WhichOneof("data")
        data = getattr(metric, kind) if kind else None
        for point in getattr(data, "data_points", ()):
            yield metric.name, point


def _event_text(span: Any) -> list[str]:
    chunks: list[str] = []
    for event in span.events:
        chunks.append(event.name)
        chunks.extend(str(kv) for kv in event.attributes)
    return chunks


def decoded_span_text(receiver: OtlpHttpReceiver) -> str:
    chunks: list[str] = [str(kv) for kv in iter_resource_attributes(receiver)]
    for span in iter_spans(receiver):
        chunks.append(span.name)
        chunks.append(str(span.status))
        chunks.extend(str(kv) for kv in span.attributes)
        chunks.extend(_event_text(span))
    return "\n".join(chunks)


def decoded_metric_text(receiver: OtlpHttpReceiver) -> str:
    chunks: list[str] = [str(kv) for kv in iter_resource_attributes(receiver)]
    for name, point in iter_metric_points(receiver):
        chunks.append(name)
        chunks.extend(str(kv) for kv in point.attributes)
    return "\n".join(chunks)


def scan_surfaces(
    receiver: OtlpHttpReceiver,
    sink: Any,
    log_text: str,
    captured: Any,
) -> dict[str, str]:
    """全部待扫描输出面(缺一面就等于放过一条通道)。"""
    wire_bytes = b"\n".join(receiver.payloads)
    assert wire_bytes, "canary must actually export OTLP bytes, otherwise it proves nothing"
    return {
        "OTLP_WIRE_BYTES": wire_bytes.decode("utf-8", errors="ignore"),
        "DECODED_SPANS": decoded_span_text(receiver),
        "DECODED_METRICS": decoded_metric_text(receiver),
        "APPLICATION_STDOUT": captured.out,
        "APPLICATION_STDERR": captured.err,
        "APPLICATION_LOGS": log_text,
        "TELEMETRY_PROJECTION": repr(sink_counters_dto(sink)),
    }


def allowed_span_attribute_keys() -> set[str]:
    """span attribute 键的闭集(词汇键 + research_os.* 元数据/correlation)。"""
    return (
        {key.value for key in AttributeKey}
        | {
            f"{RESEARCH_OS_SPAN_PREFIX}{suffix}"
            for suffix in ("scope", "outcome", "failure_category")
        }
        | {f"{RESEARCH_OS_SPAN_PREFIX}correlation.{suffix}" for suffix in CORRELATION_SUFFIXES}
    )
