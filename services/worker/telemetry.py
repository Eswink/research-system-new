"""Worker-side telemetry assembly (PA-1 debt #6: production workers emitted
no telemetry — the REMOTE_EXECUTION span path existed but was never fed).

Mirrors services.api.telemetry.build_api_telemetry against the shared
RESEARCHOS_OTEL_* env (OtelSettings.from_env); service_name distinguishes
the worker in the collector. Any misconfiguration fails open to a
FailSafe(Null) sink — telemetry can never break a job.
"""

from __future__ import annotations

from pathlib import Path

from adapters.otel.config import OtelConfig
from adapters.otel.failsafe import FailSafeTelemetrySink
from adapters.otel.provider import build_telemetry_sink
from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
from packages.application.ports.telemetry_sink import NullTelemetrySink, TelemetrySink
from services.api.settings import OtelSettings


def _service_version() -> str:
    try:
        return (
            Path(__file__).resolve().parents[2].joinpath("VERSION").read_text(encoding="utf-8").strip()
        )
    except OSError:
        return "unknown"


def build_worker_telemetry(worker_id: str) -> TelemetrySink:
    """OtelSettings.from_env → worker sink; fail-open on any error."""
    try:
        settings = OtelSettings.from_env()
        config = OtelConfig(
            enabled=settings.enabled,
            endpoint=settings.endpoint,
            timeout_seconds=settings.timeout_seconds,
            sample_ratio=settings.sample_ratio,
            service_name=f"research-os-worker/{worker_id}",
            service_version=_service_version(),
        )
    except Exception:
        return FailSafeTelemetrySink(NullTelemetrySink())
    return build_telemetry_sink(config, RegistryCredentialResolver())
