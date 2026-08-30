"""控制面 telemetry 装配(composition root 私有 helper)。

fail-open:`OtelConfig` 校验失败(如 malformed endpoint)→ FailSafe(Null),
telemetry 保持 off,不阻断 API 启动(qualification:collector failure behavior)。
OTLP header 凭据经 RegistryCredentialResolver 按引用解析,永不落盘。
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from adapters.otel.config import OtelConfig
from adapters.otel.failsafe import FailSafeTelemetrySink
from adapters.otel.provider import build_telemetry_sink
from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
from packages.application.ports.telemetry_sink import NullTelemetrySink, TelemetrySink
from packages.domain.serialization import digest_of
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


def exporter_config_digest(effective: ApiSettings) -> str:
    """Return a stable, non-secret digest of the configured exporter surface."""
    otel = effective.otel
    endpoint = _endpoint_identity(otel.endpoint)
    payload = {
        "enabled": otel.enabled,
        "endpoint": endpoint,
        "timeout_seconds": repr(otel.timeout_seconds),
        "sample_ratio": repr(otel.sample_ratio),
        "header_names": ["authorization"] if otel.header_credential_ref is not None else [],
        "service_name": "research-os",
        "service_version": _service_version(),
    }
    return str(digest_of(payload))


def _endpoint_identity(endpoint: str) -> str:
    """Keep exporter config provenance free of URL userinfo and query secrets."""
    try:
        parsed = urlsplit(endpoint)
        port = parsed.port
    except ValueError:
        return "invalid-endpoint"
    value = f"{parsed.scheme}://{parsed.hostname or ''}"
    if port is not None:
        value += f":{port}"
    return value + parsed.path


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
