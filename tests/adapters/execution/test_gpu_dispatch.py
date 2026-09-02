"""M17 WP2 dispatch tests: capability derivation + GPU timeout classification.

The M17 defect fix: `RemoteExecutionBackend._submit` previously derived the
scheduling capability from `spec.backend_kind.lower()` → `"sandbox"`, which
no real worker declares — real-experiment remote dispatch could never be
claimed. Derivation now comes from the resource profile.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.execution.profiles import (
    DOCKER_CAPABILITY,
    GpuRequirements,
    derive_required_capability,
    is_gpu_profile,
    resolve_gpu_requirements,
    resolve_resource_profile,
)
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.execution_job_queue import FakeExecutionJobQueue
from packages.application.ports.errors import InvalidInputError
from packages.domain.enums import FailureCategory
from packages.domain.workspace import ExecutionSpec, ExecutionStatus
from tests.adapters.execution.test_remote_backend import _make_backend, _run


def _noop_monotonic() -> object:
    ticks = {"n": 0}

    def _now() -> float:
        ticks["n"] += 1
        return float(ticks["n"])

    return _now


def _spec(tmp_path: Path, *, profile: str | None, backend_kind: str = "sandbox") -> ExecutionSpec:
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    return ExecutionSpec(
        backend_kind=backend_kind,
        command="echo hi",
        resource_profile=profile,
        workspace_path=str(ws),
    )


def _enqueue(
    tmp_path: Path, *, profile: str | None, backend_kind: str = "sandbox"
) -> tuple[FakeExecutionJobQueue, str]:
    queue = FakeExecutionJobQueue()
    backend = _make_backend(queue, FakeArtifactStore())
    task_id = backend._submit(
        _spec(tmp_path, profile=profile, backend_kind=backend_kind), Path(tmp_path)
    )
    return queue, task_id


def test_real_experiment_spec_claims_as_docker(tmp_path: Path) -> None:
    """Regression: the real experiment path (`execute.py`) uses
    backend_kind="sandbox" — dispatch must derive `docker`, not `sandbox`."""
    queue, task_id = _enqueue(tmp_path, profile=None, backend_kind="sandbox")
    job = queue.state.jobs[task_id]
    assert job.capability == DOCKER_CAPABILITY == "docker"


def test_gpu_profile_spec_claims_as_gpu(tmp_path: Path) -> None:
    queue, task_id = _enqueue(tmp_path, profile="gpu-small", backend_kind="sandbox")
    assert queue.state.jobs[task_id].capability == "gpu"


@pytest.mark.parametrize(
    ("profile", "expected"),
    [
        (None, "docker"),
        ("default", "docker"),
        ("small", "docker"),
        ("large", "docker"),
        ("gpu-small", "gpu"),
        ("gpu-oom-probe", "gpu"),
    ],
)
def test_derive_required_capability_table(
    tmp_path: Path, profile: str | None, expected: str
) -> None:
    assert derive_required_capability(_spec(tmp_path, profile=profile)) == expected


def test_derive_required_capability_unknown_profile_fails_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(InvalidInputError):
        derive_required_capability(_spec(tmp_path, profile="gpu-huge"))


def test_gpu_profile_unclaimed_timeout_is_gpu_unavailable(tmp_path: Path) -> None:
    """No GPU worker ever claims → TIMED_OUT classified GPU_UNAVAILABLE,
    never a silent CPU fallback (the job required `gpu` until the end)."""
    queue = FakeExecutionJobQueue()
    backend = _make_backend(queue, FakeArtifactStore(), monotonic=_noop_monotonic())
    run = _run(backend, _spec(tmp_path, profile="gpu-small"), timeout_seconds=1)
    assert run.status is ExecutionStatus.TIMED_OUT
    assert run.failure_category is FailureCategory.GPU_UNAVAILABLE
    (task_id,) = queue.state.jobs
    assert queue.state.jobs[task_id].capability == "gpu"


def test_cpu_profile_unclaimed_timeout_has_no_gpu_category(tmp_path: Path) -> None:
    queue = FakeExecutionJobQueue()
    backend = _make_backend(queue, FakeArtifactStore(), monotonic=_noop_monotonic())
    run = _run(backend, _spec(tmp_path, profile="small"), timeout_seconds=1)
    assert run.status is ExecutionStatus.TIMED_OUT
    assert run.failure_category is None


def test_gpu_profile_limits_and_requirements_resolve() -> None:
    for name in ("gpu-small", "gpu-oom-probe"):
        limits = resolve_resource_profile(name)
        assert limits.cpu_nanos > 0 and limits.memory_bytes >= 4 * 1024**3
        reqs = resolve_gpu_requirements(name)
        assert isinstance(reqs, GpuRequirements)
        assert reqs.device_count == 1
        assert reqs.framework == "torch"
    assert is_gpu_profile("gpu-small") and is_gpu_profile("gpu-oom-probe")
    assert not is_gpu_profile("small") and not is_gpu_profile(None)


def test_resolve_gpu_requirements_rejects_cpu_profile() -> None:
    with pytest.raises(InvalidInputError):
        resolve_gpu_requirements("small")


def test_resolve_resource_profile_still_fail_closed_for_unknown() -> None:
    with pytest.raises(InvalidInputError):
        resolve_resource_profile("gpu-huge")
