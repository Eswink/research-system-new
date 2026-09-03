"""Worker telemetry assembly (PA-1 debt #6): default off → Null fail-open;
enabled → FailSafe sink; construction never raises."""

from __future__ import annotations

from adapters.otel.failsafe import FailSafeTelemetrySink
from packages.application.ports.telemetry_sink import NullTelemetrySink
from services.worker.telemetry import build_worker_telemetry


def test_builder_defaults_to_null_fail_open(monkeypatch: object) -> None:
    for key in (
        "RESEARCHOS_OTEL_ENABLED",
        "RESEARCHOS_OTEL_ENDPOINT",
        "RESEARCHOS_OTEL_TIMEOUT",
        "RESEARCHOS_OTEL_SAMPLE_RATIO",
    ):
        monkeypatch.delenv(key, raising=False)  # type: ignore[attr-defined]
    sink = build_worker_telemetry("w1")
    assert isinstance(sink, FailSafeTelemetrySink)
    assert isinstance(sink._inner, NullTelemetrySink)  # noqa: SLF001


def test_builder_enabled_wraps_failsafe_sink(monkeypatch: object) -> None:
    monkeypatch.setenv("RESEARCHOS_OTEL_ENABLED", "1")  # type: ignore[attr-defined]
    sink = build_worker_telemetry("w2")
    assert isinstance(sink, FailSafeTelemetrySink)
    # sink must accept the sink protocol (no-op or real, never raises)
    from packages.application.observability.attributes import MetricKind, MetricName, MetricSample

    sink.record_metric(
        MetricSample(
            name=MetricName.REMOTE_EXECUTION_DURATION_MS, kind=MetricKind.HISTOGRAM, value=1
        )
    )


def test_builder_never_raises_on_bad_config(monkeypatch: object) -> None:
    monkeypatch.setenv("RESEARCHOS_OTEL_ENABLED", "1")  # type: ignore[attr-defined]
    monkeypatch.setenv("RESEARCHOS_OTEL_ENDPOINT", "http://[::1")  # type: ignore[attr-defined]
    sink = build_worker_telemetry("w3")
    assert isinstance(sink, FailSafeTelemetrySink)
