"""M15 settings/装配 wiring 测试:telemetry 默认 off + fail-open。"""

from __future__ import annotations

from typing import Any

from adapters.fakes import NullTelemetrySink
from adapters.otel.failsafe import FailSafeTelemetrySink
from packages.application.ports.telemetry_sink import NullTelemetrySink as PortNullSink
from services.api.composition import ApiDeps
from services.api.settings import ApiSettings, OtelSettings
from services.api.telemetry import build_api_telemetry


def test_otel_defaults_to_off() -> None:
    settings = ApiSettings()
    assert settings.otel.enabled is False
    assert settings.otel.endpoint == "http://localhost:4318"
    assert settings.otel.sample_ratio == 1.0


def test_otel_settings_from_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("RESEARCHOS_OTEL_ENABLED", "1")
    monkeypatch.setenv("RESEARCHOS_OTEL_ENDPOINT", "http://collector:4318")
    monkeypatch.setenv("RESEARCHOS_OTEL_TIMEOUT", "9")
    monkeypatch.setenv("RESEARCHOS_OTEL_SAMPLE_RATIO", "0.25")
    monkeypatch.setenv("RESEARCHOS_OTEL_HEADER_CREDENTIAL_REF", "otel_auth")
    settings = ApiSettings.from_env()
    assert settings.otel == OtelSettings(
        enabled=True,
        endpoint="http://collector:4318",
        timeout_seconds=9.0,
        sample_ratio=0.25,
        header_credential_ref="otel_auth",
    )


def test_otel_settings_from_env_disabled_by_default(monkeypatch: Any) -> None:
    monkeypatch.delenv("RESEARCHOS_OTEL_ENABLED", raising=False)
    assert ApiSettings.from_env().otel.enabled is False


def test_apideps_default_telemetry_is_null() -> None:
    deps = ApiDeps(
        endpoint_store=None,  # type: ignore[arg-type]
        model_store=None,  # type: ignore[arg-type]
        credentials=None,  # type: ignore[arg-type]
        gateway=None,  # type: ignore[arg-type]
        idempotency=None,  # type: ignore[arg-type]
    )
    assert isinstance(deps.telemetry, NullTelemetrySink)
    assert deps.telemetry.calls == ()


def test_build_api_telemetry_disabled_returns_null_composition() -> None:
    failsafe = build_api_telemetry(ApiSettings(otel=OtelSettings(enabled=False)))
    assert isinstance(failsafe, FailSafeTelemetrySink)
    assert isinstance(failsafe.inner, PortNullSink)


def test_build_api_telemetry_malformed_endpoint_falls_back_to_null() -> None:
    """malformed endpoint → telemetry 保持 off,不抛出(qualification 行为表)。"""
    failsafe = build_api_telemetry(
        ApiSettings(otel=OtelSettings(enabled=True, endpoint="::not-a-url::"))
    )
    assert isinstance(failsafe, FailSafeTelemetrySink)
    assert isinstance(failsafe.inner, PortNullSink)
