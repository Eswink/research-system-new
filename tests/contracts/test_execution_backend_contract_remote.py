"""M16 re-audit F-8: RemoteExecutionBackend runs the formal ExecutionBackend
contract shape (mirrors TestExecutionBackendContract + the Docker mirror).

Application has zero local/remote branching, so the remote adapter must satisfy
the SAME terminal-state invariants as the Fake and Docker backends: every
settled run carries started_at + completed_at, and status maps faithfully.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.execution.remote_backend import RemoteExecutionBackend
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.execution_job_queue import FakeExecutionJobQueue
from packages.domain.workspace import ExecutionStatus
from tests.adapters.execution.test_remote_backend import (  # reuse fixtures
    _CompletingQueue,
    _make_backend,
    _output_bundle,
    _register,
    _run,
    _spec,
)


def _noop_monotonic() -> Any:
    ticks = {"n": 0}

    def _now() -> float:
        ticks["n"] += 1
        return float(ticks["n"])

    return _now


def test_remote_happy_path_returns_valid_run(tmp_path: Path) -> None:
    """P0 invariant: SUCCEEDED carries completed_at + started_at (domain rule)."""
    artifacts = FakeArtifactStore()
    bundle, digest = _output_bundle(tmp_path)
    out_ref = _register(artifacts, bundle)
    queue = _CompletingQueue(output_bundle_ref=out_ref, output_digest=digest)
    backend = _make_backend(queue, artifacts)
    run = _run(backend, _spec(tmp_path), timeout_seconds=5)
    assert run.status is ExecutionStatus.SUCCEEDED
    assert run.completed_at is not None
    assert run.started_at is not None
    assert run.exit_code == 0


def test_remote_timed_out_run_is_valid(tmp_path: Path) -> None:
    queue = FakeExecutionJobQueue()  # never settles
    backend = _make_backend(queue, FakeArtifactStore(), monotonic=_noop_monotonic())
    run = _run(backend, _spec(tmp_path), timeout_seconds=1)
    assert run.status is ExecutionStatus.TIMED_OUT
    assert run.completed_at is not None


def test_remote_cancelled_run_is_valid(tmp_path: Path) -> None:
    queue = FakeExecutionJobQueue()  # never settles
    backend = _make_backend(queue, FakeArtifactStore())
    run = _run(backend, _spec(tmp_path), timeout_seconds=None, cancelled=lambda: True)
    assert run.status is ExecutionStatus.CANCELLED
    assert run.completed_at is not None


def test_remote_backend_is_an_execution_backend() -> None:
    """The remote adapter satisfies the same Port as local (no branching)."""
    from packages.application.ports.execution_backend import ExecutionBackend

    backend = RemoteExecutionBackend(
        job_queue=FakeExecutionJobQueue(), artifacts=FakeArtifactStore()
    )
    assert isinstance(backend, ExecutionBackend)
