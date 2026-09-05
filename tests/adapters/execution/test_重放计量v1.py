"""Replay returns the original worker duration, not new polling latency."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from adapters.execution.remote_backend import RemoteExecutionBackend
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.execution_job_queue import FakeExecutionJobQueue
from packages.application.ports.execution_job_queue import ExecutionJobOutcome
from packages.domain.core import Timestamp
from packages.domain.workspace import ExecutionSpec


def test_completed_job_preserves_original_duration_on_replay(tmp_path: Path) -> None:
    backend = RemoteExecutionBackend(
        job_queue=FakeExecutionJobQueue(), artifacts=FakeArtifactStore()
    )
    outcome = ExecutionJobOutcome(
        task_id="completed-task",
        status="SUCCEEDED",
        exit_code=0,
        execution_elapsed_seconds=Decimal("12.5"),
        gpu_elapsed_seconds=Decimal("1.7"),
    )
    spec = ExecutionSpec(backend_kind="DOCKER", command="true")
    first = backend._normalize(spec, tmp_path, Timestamp.now(), outcome)
    replay = backend._normalize(spec, tmp_path, Timestamp.now(), outcome)
    assert first.compute_usage_summary["elapsed_seconds"] == 12.5
    assert replay.compute_usage_summary["elapsed_seconds"] == 12.5
    assert replay.compute_usage_summary["gpu_elapsed_seconds"] == Decimal("1.7")
