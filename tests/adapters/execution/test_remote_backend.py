"""M16 WP3 RemoteExecutionBackend + cancelled-callback tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from adapters.execution.remote_backend import RemoteExecutionBackend
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.execution_backend import FakeExecutionBackend
from adapters.fakes.execution_job_queue import FakeExecutionJobQueue
from adapters.workspace.bundle import (
    BundleError,
    bundle_from_directory,
    bundle_to_directory,
    tree_digest,
)
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.execution_job_queue import (
    ExecutionJobOutcome,
    ExecutionJobResult,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.workspace import ExecutionSpec, ExecutionStatus

_MISMATCH_DIGEST = str(Digest.of_bytes(b"definitely-not-the-output-tree"))
_STDOUT_DIGEST = str(Digest.of_bytes(b"hi\n"))
_EMPTY_DIGEST = str(Digest.of_bytes(b""))


def _noop_sleep(_seconds: float) -> None:
    return None


def _make_backend(queue: FakeExecutionJobQueue, artifacts: FakeArtifactStore, **kw: Any) -> Any:
    kw.setdefault("sleeper", _noop_sleep)
    return RemoteExecutionBackend(job_queue=queue, artifacts=artifacts, **kw)


def _run(backend: Any, spec: ExecutionSpec, **kw: Any) -> Any:
    """Invoke the ExecutionBackend run entrypoint (bound dynamically)."""
    runner = getattr(backend, "execute")
    return runner(spec, **kw)


def _spec(tmp_path: Path, command: str = "echo hi") -> ExecutionSpec:
    ws = tmp_path.joinpath("ws")
    ws.mkdir(exist_ok=True)
    ws.joinpath("input.txt").write_text("data", encoding="utf-8")
    return ExecutionSpec(backend_kind="DOCKER", command=command, workspace_path=str(ws))


def _output_bundle(tmp_path: Path) -> tuple[bytes, str]:
    out = tmp_path.joinpath("out")
    out.mkdir(exist_ok=True)
    out.joinpath("stdout.log").write_text("hi\n", encoding="utf-8")
    out.joinpath("result.txt").write_text("done", encoding="utf-8")
    return bundle_from_directory(out)


def _register(artifacts: FakeArtifactStore, bundle: bytes) -> str:
    artifact_id = str(Digest.of_bytes(bundle))
    artifacts.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(bundle),
            size_bytes=len(bundle),
            media_type="application/x-researchos-workspace-bundle",
        ),
        bundle,
    )
    return artifact_id


class _CompletingQueue(FakeExecutionJobQueue):
    """Fake queue whose first poll settles the job like a worker would."""

    def __init__(self, *, output_bundle_ref: str, output_digest: str) -> None:
        super().__init__()
        self._output_ref = output_bundle_ref
        self._output_digest = output_digest
        self._settled = False

    def poll(self, task_id: str) -> ExecutionJobOutcome | None:
        if not self._settled:
            self._settled = True
            job = self.state.jobs[task_id]
            self.assign(task_id, worker_id="w1", lease_id="lease-1", fence=job.fence or 1)
            self.record_result(
                ExecutionJobResult(
                    task_id=task_id,
                    lease_id="lease-1",
                    fence=job.fence or 1,
                    status="SUCCEEDED",
                    worker_id="w1",
                    exit_code=0,
                    stdout_digest=_STDOUT_DIGEST,
                    stderr_digest=_EMPTY_DIGEST,
                    output_bundle_ref=self._output_ref,
                    output_bundle_digest=self._output_digest,
                )
            )
        return super().poll(task_id)


def test_remote_execute_happy_path_materializes_output(tmp_path: Path) -> None:
    artifacts = FakeArtifactStore()
    bundle, digest = _output_bundle(tmp_path)
    out_artifact = _register(artifacts, bundle)
    queue = _CompletingQueue(output_bundle_ref=out_artifact, output_digest=digest)
    backend = _make_backend(queue, artifacts)
    spec = _spec(tmp_path)
    run = _run(backend, spec, timeout_seconds=5)
    assert run.status is ExecutionStatus.SUCCEEDED
    assert run.exit_code == 0
    assert run.compute_usage_summary["remote"] is True
    materialized = Path(str(spec.workspace_path)).joinpath("result.txt")
    assert materialized.read_text(encoding="utf-8") == "done"


def test_remote_execute_timeout_requests_cancel(tmp_path: Path) -> None:
    queue = FakeExecutionJobQueue()  # never settles
    artifacts = FakeArtifactStore()
    ticks = {"n": 0}

    def fake_monotonic() -> float:
        ticks["n"] += 1
        return float(ticks["n"])

    backend = _make_backend(queue, artifacts, monotonic=fake_monotonic)
    run = _run(backend, _spec(tmp_path), timeout_seconds=1)
    assert run.status is ExecutionStatus.TIMED_OUT
    (task_id,) = queue.state.jobs
    assert queue.cancel_requested(task_id) is True


def test_remote_execute_cancelled_callback(tmp_path: Path) -> None:
    queue = FakeExecutionJobQueue()
    artifacts = FakeArtifactStore()
    backend = _make_backend(queue, artifacts)
    run = _run(backend, _spec(tmp_path), timeout_seconds=10, cancelled=lambda: True)
    assert run.status is ExecutionStatus.CANCELLED


def test_remote_execute_rejects_bad_output_digest(tmp_path: Path) -> None:
    artifacts = FakeArtifactStore()
    bundle, _digest = _output_bundle(tmp_path)
    out_artifact = _register(artifacts, bundle)
    queue = _CompletingQueue(output_bundle_ref=out_artifact, output_digest=_MISMATCH_DIGEST)
    backend = _make_backend(queue, artifacts)
    with pytest.raises(InvalidInputError):
        _run(backend, _spec(tmp_path), timeout_seconds=5)


def test_docker_final_status_cancelled() -> None:
    from adapters.execution.docker_backend import _final_status

    assert _final_status(False, 0, cancelled=True) is ExecutionStatus.CANCELLED
    assert _final_status(True, 0) is ExecutionStatus.TIMED_OUT
    assert _final_status(False, 0) is ExecutionStatus.SUCCEEDED
    assert _final_status(False, 1) is ExecutionStatus.FAILED


def test_fake_execution_backend_honours_cancelled() -> None:
    backend = FakeExecutionBackend()
    spec = ExecutionSpec(backend_kind="DOCKER", command="echo")
    run = _run(backend, spec, cancelled=lambda: True)
    assert run.status is ExecutionStatus.CANCELLED


def test_bundle_directory_roundtrip(tmp_path: Path) -> None:
    src = tmp_path.joinpath("src")
    src.mkdir()
    src.joinpath("a.txt").write_text("hello", encoding="utf-8")
    src.joinpath("nested").mkdir()
    src.joinpath("nested").joinpath("b.txt").write_text("world", encoding="utf-8")
    bundle, digest = bundle_from_directory(src)
    assert digest == tree_digest(src)
    dst = tmp_path.joinpath("dst")
    bundle_to_directory(bundle, dst, digest)
    assert dst.joinpath("a.txt").read_text(encoding="utf-8") == "hello"
    assert dst.joinpath("nested").joinpath("b.txt").read_text(encoding="utf-8") == "world"


def test_bundle_to_directory_rejects_digest_mismatch(tmp_path: Path) -> None:
    src = tmp_path.joinpath("src")
    src.mkdir()
    src.joinpath("a.txt").write_text("hello", encoding="utf-8")
    bundle, _digest = bundle_from_directory(src)
    with pytest.raises(BundleError):
        bundle_to_directory(bundle, tmp_path.joinpath("dst"), _MISMATCH_DIGEST)
