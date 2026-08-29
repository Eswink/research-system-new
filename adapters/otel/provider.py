"""OTel provider 初始化与 sink 组装(adapters/otel 私有)。

`build_telemetry_sink` 是唯一入口:
- `enabled=False` → FailSafe(Null),零网络依赖;
- 构造失败(含 malformed endpoint、header 凭据不可用)→ FailSafe(Null),
  telemetry 保持 off,不阻断业务(qualification:collector failure behavior)。
Exporter 为 OTLP/HTTP(gRPC exporter 已在 qualification 中拒绝);
BatchSpanProcessor 有界队列 + 超时,shutdown 只做有界 flush。
"""

from __future__ import annotations

from opentelemetry.exporter.otlp.proto.http import Compression
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    ParentBased,
    Sampler,
    TraceIdRatioBased,
)

from adapters.otel.config import OtelConfig
from adapters.otel.failsafe import FailSafeTelemetrySink
from adapters.otel.resource import build_resource
from adapters.otel.sink import OtelTelemetrySink
from packages.application.ports.credential_resolver import CredentialResolver
from packages.application.ports.telemetry_sink import NullTelemetrySink

_MAX_EXPORT_BATCH_SIZE = 512


def build_telemetry_sink(
    config: OtelConfig,
    credentials: CredentialResolver | None = None,
) -> FailSafeTelemetrySink:
    """组装 telemetry sink;任何构造失败回退 Null(fail-open,telemetry off)。"""
    if not config.enabled:
        return FailSafeTelemetrySink(NullTelemetrySink())
    try:
        return FailSafeTelemetrySink(_build_otel_sink(config, credentials))
    except Exception:
        return FailSafeTelemetrySink(NullTelemetrySink())


def _build_otel_sink(
    config: OtelConfig,
    credentials: CredentialResolver | None,
) -> OtelTelemetrySink:
    resource = build_resource(config)
    headers = _resolve_headers(config, credentials)
    timeout_millis = int(config.timeout_seconds * 1000)
    compression = _compression_for(config.compression)
    span_exporter = OTLPSpanExporter(
        endpoint=config.traces_endpoint(),
        headers=headers,
        timeout=config.timeout_seconds,
        compression=compression,
    )
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=_sampler_for(config.sample_ratio),
        shutdown_on_exit=False,
    )
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            span_exporter,
            max_queue_size=config.queue_size,
            max_export_batch_size=min(config.queue_size, _MAX_EXPORT_BATCH_SIZE),
            schedule_delay_millis=config.export_interval_millis,
            export_timeout_millis=timeout_millis,
        )
    )
    metric_exporter = OTLPMetricExporter(
        endpoint=config.metrics_endpoint(),
        headers=headers,
        timeout=config.timeout_seconds,
        compression=compression,
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(
                metric_exporter,
                export_interval_millis=config.export_interval_millis,
            )
        ],
    )
    return OtelTelemetrySink(
        tracer=tracer_provider.get_tracer(config.service_name),
        meter=meter_provider.get_meter(config.service_name),
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
    )


def _resolve_headers(
    config: OtelConfig,
    credentials: CredentialResolver | None,
) -> dict[str, str] | None:
    """header 凭据经 CredentialResolver 解析;解析失败仅丢弃该 header(fail-open)。"""
    if not config.header_credential_refs or credentials is None:
        return None
    headers: dict[str, str] = {}
    for header_name, credential_ref in config.header_credential_refs:
        try:
            headers[header_name] = credentials.resolve(credential_ref).value
        except Exception:
            continue
    return headers or None


def _compression_for(value: str) -> Compression:
    return Compression.NoCompression if value == "none" else Compression.Gzip


def _sampler_for(sample_ratio: float) -> Sampler:
    if sample_ratio >= 1.0:
        return ALWAYS_ON
    if sample_ratio <= 0.0:
        return ALWAYS_OFF
    return ParentBased(root=TraceIdRatioBased(sample_ratio))
