"""控制面 telemetry 装配(composition root 私有 helper)。

fail-open:`OtelConfig` 校验失败(如 malformed endpoint)→ FailSafe(Null),
telemetry 保持 off,不阻断 API 启动(qualification:collector failure behavior)。
OTLP header 凭据经 RegistryCredentialResolver 按引用解析,永不落盘。
"""

from __future__ import annotations

from pathlib import Path

from adapters.otel.config import OtelConfig
from adapters.otel.failsafe import FailSafeTelemetrySink
from adapters.otel.provider import build_telemetry_sink
from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
from packages.application.ports.telemetry_sink import NullTelemetrySink, TelemetrySink
from services.api.settings import ApiSettings


def build_api_telemetry(effective: ApiSettings) -> TelemetrySink:
    """settings → telemetry sink;配置错误回退 Null 组合(fail-open)。"""
    try:
        config = OtelConfig(
            enabled=effective.otel.enabled,
            endpoint=effective.otel.endpoint,
            timeout_seconds=effective.otel.timeout_seconds,
            sample_ratio=effective.otel.sample_ratio,
            service_version=_service_version(),
            header_credential_refs=_header_refs(effective),
        )
    except Exception:
        return FailSafeTelemetrySink(NullTelemetrySink())
    return build_telemetry_sink(config, RegistryCredentialResolver())


def _header_refs(effective: ApiSettings) -> tuple[tuple[str, str], ...]:
    ref = effective.otel.header_credential_ref
    if ref is None:
        return ()
    return (("authorization", ref),)


def _service_version() -> str | None:
    try:
        version_file = Path(__file__).resolve().parents[2].joinpath("VERSION")
        return version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
