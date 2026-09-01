"""M17 WP4c: real-GPU job cancellation over the cross-process plane.

distributed + postgres + requires_docker + requires_gpu: a genuine
`python -m services.worker` subprocess (real Docker GPU backend, real GPU
probe at startup) claims a long GPU job; the Control Plane cancels it; the
cooperative cancel probe kills the container and the settled result is
CANCELLED. A stale-fence late result replaying the released lease identity
is rejected (409). No containers may survive.
"""

from __future__ import annotations

import time
from collections.abc import Generator

import docker
import pytest

from tests.distributed.conftest import _postgres_dsn
from tests.distributed.test_scenarios import (
    _gateway_register,
    _is_leased_by,
    _wait_until,
)
from tests.distributed.worker_harness import WorkerHarness

pytestmark = [
    pytest.mark.distributed,
    pytest.mark.postgres,
    pytest.mark.requires_docker,
    pytest.mark.requires_gpu,
]

_IMAGE_TAG = "research-os-gpu-sandbox:m17-v1"
_EXEC_FILTER = {"name": "research-os-exec"}


def _exec_containers() -> list[dict[str, object]]:
    client = docker.from_env()
    return list(client.api.containers(filters=_EXEC_FILTER))


def _wait_for_new_container(baseline_ids: set[str], timeout: float = 20.0) -> bool:
    """Wait until a container started by THIS test appears (create/start race)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if {str(c["Id"]) for c in _exec_containers()} - baseline_ids:
            return True
        time.sleep(0.4)
    return False


def _no_new_containers(baseline_ids: set[str], timeout: float = 15.0) -> bool:
    """True once no container started by THIS test remains running.

    Baseline-relative: an unrelated orphan from a crashed earlier run must
    not mask the behavior under test (and is not ours to clean up).
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not ({str(c["Id"]) for c in _exec_containers()} - baseline_ids):
            return True
        time.sleep(0.5)
    return False


@pytest.fixture()
def gpu_harness(clean_worker_plane: str) -> Generator[WorkerHarness, None, None]:
    harness = WorkerHarness(_postgres_dsn(), lease_ttl_seconds=6, stale_seconds=4.0)
    harness.start_gateway()
    harness.start_schedulers()
    baseline_ids = {str(c["Id"]) for c in _exec_containers()}
    yield harness
    harness.close()
    # hygiene: force-remove containers THIS test started (never touch
    # orphans from earlier crashed runs — they are not ours to manage).
    for container in _exec_containers():
        if str(container["Id"]) not in baseline_ids:
            docker.from_env().api.remove_container(str(container["Id"]), force=True)


def test_gpu_job_cancel_kills_container_and_fences_late_result(
    gpu_harness: WorkerHarness,
) -> None:
    import httpx

    harness = gpu_harness
    baseline_ids = {str(c["Id"]) for c in _exec_containers()}
    task_id = harness.seed_job(
        idem="gpu-cancel-1",
        command="sleep 120",
        capability="gpu",
        resource_profile="gpu-small",
    )
    worker = harness.spawn_worker(
        "gpu-cancel-w1",
        env_extra={
            "RESEARCHOS_WORKER_EXECUTION_BACKEND": "docker",
            "RESEARCHOS_WORKER_GPU_IMAGE": _IMAGE_TAG,
        },
    )
    # the real GPU probe at worker startup gates the gpu capability — the
    # claim can only succeed once the probe-backed registration is in place.
    assert _wait_until(lambda: _is_leased_by(harness, task_id, "gpu-cancel-w1"), timeout=120)
    assert _wait_for_new_container(baseline_ids), "the GPU job container should be running"
    identity = harness.lease_identity(task_id)
    assert identity is not None
    lease_id, fence = identity

    # Control Plane cancels; the worker's probe kills the container.
    harness.job_queue.request_cancel(task_id)
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None, timeout=60)
    outcome = harness.job_queue.poll(task_id)
    assert outcome is not None and outcome.status == "CANCELLED"
    assert outcome.worker_id == "gpu-cancel-w1"
    assert harness.lease_identity(task_id) is None  # lease released
    assert _no_new_containers(baseline_ids), "cancelled GPU container must be force-removed"

    # GPU plane still healthy after cancellation: a fresh real probe passes.
    from adapters.execution.gpu_probe import GpuProbeConfig, probe_gpu

    observation = probe_gpu(GpuProbeConfig(image=_IMAGE_TAG))
    assert observation is not None and observation.device_count == 1

    # stale-fence injection: a valid session replaying the released lease
    # identity must be rejected (409), and nothing may overwrite CANCELLED.
    late_token, late_gen = _gateway_register(harness, "gpu-late-holder")
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/tasks/{task_id}/result",
        headers={"Authorization": f"Bearer {late_token}"},
        json={
            "worker_id": "gpu-late-holder",
            "registration_generation": late_gen,
            "lease_id": lease_id,
            "fence": fence,
            "status": "SUCCEEDED",
            "exit_code": 0,
        },
    )
    assert resp.status_code == 409
    settled = harness.job_queue.poll(task_id)
    assert settled is not None and settled.status == "CANCELLED"
    worker.terminate()
