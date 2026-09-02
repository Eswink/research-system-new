"""M17 WP5b tests: GPU telemetry vocabulary + privacy canary coverage.

- the REMOTE_EXECUTION span (M16-defined, never emitted) is emitted by the
  worker-side execution segment;
- GPU closed-set metrics: GPU_EXECUTION_DURATION_MS, GPU_OOM_TOTAL,
  GPU_UNAVAILABLE_TOTAL;
- `gpu_device_ref` is a digest short-code — the raw device name never
  reaches any telemetry surface (privacy canary, GPU path).
"""

from __future__ import annotations

from typing import Any

from adapters.fakes.execution_backend import FakeExecutionBackend
from adapters.fakes.telemetry_sink import FakeTelemetrySink
from packages.application.observability.attributes import (
    AttributeKey,
    MetricKind,
    MetricName,
    gpu_device_ref,
    sanitize_attributes,
)
from packages.domain.workspace import ExecutionStatus
from services.worker.loop import WorkerLoop, WorkerLoopConfig
from tests.worker.test_worker_loop import _FakeClient

_DEVICE_NAME = "NVIDIA GeForce RTX 4060 Laptop GPU"


def _observation() -> Any:
    from packages.domain.core import Timestamp
    from packages.domain.workers import WorkerGpuObservation

    return WorkerGpuObservation(
        device_name=_DEVICE_NAME,
        device_count=1,
        driver_version="581.80",
        cuda_runtime_version="12.8",
        total_vram_bytes=8_585_216_000,
        framework="torch-2.9.1+cu128",
        probed_at=Timestamp.now(),
        probe_digest="1111111111111111",
    )


def _job() -> dict[str, object]:
    return {
        "task_id": "t1",
        "lease_id": "l1",
        "fence": 1,
        "spec_json": '{"backend_kind":"DOCKER","command":"echo hi","workdir":"/workspace"}',
        "timeout_seconds": 5,
    }


def _fake_client(job: dict[str, object]) -> _FakeClient:
    return _FakeClient(job)


def test_remote_execution_span_is_emitted_worker_side() -> None:
    client = _fake_client(_job())
    sink = FakeTelemetrySink()
    WorkerLoop(
        client,  # type: ignore[arg-type]
        FakeExecutionBackend(status=ExecutionStatus.SUCCEEDED),
        config=WorkerLoopConfig(max_iterations=1),
        telemetry=sink,
    ).run()
    scopes = [b.scope.value for b in sink.begins]
    assert "remote_execution" in scopes


def test_gpu_metrics_emit_from_run_facts() -> None:
    client = _fake_client(_job())
    sink = FakeTelemetrySink()
    WorkerLoop(
        client,  # type: ignore[arg-type]
        FakeExecutionBackend(
            status=ExecutionStatus.FAILED,
            exit_code=1,
            failure_category=None,
            compute_usage_summary={"gpu_elapsed_seconds": 3},
        ),
        config=WorkerLoopConfig(max_iterations=1),
        telemetry=sink,
    ).run()
    names = [m.name for m in sink.metrics]
    assert MetricName.GPU_EXECUTION_DURATION_MS in names
    assert MetricName.REMOTE_EXECUTION_DURATION_MS in names


def test_gpu_oom_counter_emits() -> None:
    from packages.domain.enums import FailureCategory

    client = _fake_client(_job())
    sink = FakeTelemetrySink()
    WorkerLoop(
        client,  # type: ignore[arg-type]
        FakeExecutionBackend(
            status=ExecutionStatus.FAILED,
            exit_code=1,
            failure_category=FailureCategory.GPU_OOM,
        ),
        config=WorkerLoopConfig(max_iterations=1),
        telemetry=sink,
    ).run()
    counters = [m.name for m in sink.metrics if m.kind is MetricKind.COUNTER]
    assert MetricName.GPU_OOM_TOTAL in counters


def test_gpu_unavailable_counter_emits() -> None:
    from packages.domain.enums import FailureCategory

    client = _fake_client(_job())
    sink = FakeTelemetrySink()
    WorkerLoop(
        client,  # type: ignore[arg-type]
        FakeExecutionBackend(
            status=ExecutionStatus.FAILED,
            exit_code=1,
            failure_category=FailureCategory.GPU_UNAVAILABLE,
        ),
        config=WorkerLoopConfig(max_iterations=1),
        telemetry=sink,
    ).run()
    counters = [m.name for m in sink.metrics if m.kind is MetricKind.COUNTER]
    assert MetricName.GPU_UNAVAILABLE_TOTAL in counters


def test_raw_device_name_never_enters_telemetry() -> None:
    """Privacy canary (GPU path): only the digest reaches the span, never
    the device name — and unknown keys are structurally dropped."""
    client = _fake_client(_job())
    sink = FakeTelemetrySink()
    WorkerLoop(
        client,  # type: ignore[arg-type]
        FakeExecutionBackend(),
        config=WorkerLoopConfig(max_iterations=1),
        gpu_prober=lambda: _observation(),
        telemetry=sink,
    ).run()
    exported = str(sink.begins) + str(sink.ends) + str(sink.metrics)
    assert _DEVICE_NAME not in exported
    assert "torch-2.9.1" not in exported
    ref = gpu_device_ref(_DEVICE_NAME)
    spans = [b for b in sink.begins if b.scope.value == "remote_execution"]
    assert spans, "REMOTE_EXECUTION span expected with prober present"
    assert any(b.attributes.get("gpu_device_ref") == ref for b in spans)


def test_gpu_device_ref_attribute_key_is_closed_vocabulary() -> None:
    sanitized = sanitize_attributes({"gpu_device_ref": gpu_device_ref(_DEVICE_NAME)})
    assert sanitized == {"gpu_device_ref": gpu_device_ref(_DEVICE_NAME)}
    assert AttributeKey("gpu_device_ref").value == "gpu_device_ref"
    # 原文设备名即使塞进该键也会被 redact/截断处理，键仍闭合
    assert sanitize_attributes({"prompt": _DEVICE_NAME}) == {}
