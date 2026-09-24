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

from tests.distributed.test_scenarios import (
    _expire_lease,
    _gateway_register,
    _is_leased_by,
    _lease_count,
    _wait_until,
)
from tests.distributed.worker_harness import WorkerHarness
from tests.postgres_guard import postgres_dsn

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
    harness = WorkerHarness(postgres_dsn(), lease_ttl_seconds=6, stale_seconds=4.0)
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
    status_code = _submit_stale_result(harness, task_id, lease_id, fence)
    assert status_code == 409
    settled = harness.job_queue.poll(task_id)
    assert settled is not None and settled.status == "CANCELLED"
    worker.terminate()


def _submit_stale_result(harness: WorkerHarness, task_id: str, lease_id: str, fence: int) -> int:
    """A fresh valid session replaying a released (lease_id, fence) → status."""
    import httpx

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
    return int(resp.status_code)


def _gateway_register_gpu(harness: WorkerHarness, worker_id: str) -> tuple[str, int]:
    """Register a gpu-capable session (probe observation attached) via gateway."""
    import httpx

    from tests.distributed.worker_harness import _ENROLLMENT

    reg = httpx.post(
        f"{harness.gateway_url}/worker/v1/register",
        headers={"X-Worker-Enrollment": _ENROLLMENT},
        json={
            "worker_id": worker_id,
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": ["docker", "gpu"],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": list(range(16)),
            "max_concurrency": 1,
            "gpu_observation": {
                "device_name": "NVIDIA GeForce RTX 4060 Laptop GPU",
                "device_count": 1,
                "driver_version": "581.80",
                "cuda_runtime_version": "12.8",
                "total_vram_bytes": 8_585_216_000,
                "framework": "torch-2.9.1+cu128",
                "probed_at": "2026-09-02T00:00:00+00:00",
                "probe_digest": "aa11bb22cc33dd44",
            },
        },
    )
    assert reg.status_code == 200
    return str(reg.json()["session_token"]), int(reg.json()["registration_generation"])


def test_gpu_long_job_survives_lease_renewal(gpu_harness: WorkerHarness) -> None:
    """A GPU job longer than the lease TTL completes ONCE by the same worker.

    The renewal loop keeps the lease alive (M16 F-7); without it the lease
    would expire mid-job and the job would be requeued (duplicate execution).
    Longer GPU jobs widen the race window — this is the fencing regression
    variant the M17 plan calls out.
    """
    harness = gpu_harness
    task_id = harness.seed_job(
        idem="gpu-renew-1", command="sleep 15", capability="gpu", resource_profile="gpu-small"
    )
    worker = harness.spawn_worker(
        "gpu-renew-w1",
        env_extra={
            "RESEARCHOS_WORKER_EXECUTION_BACKEND": "docker",
            "RESEARCHOS_WORKER_GPU_IMAGE": _IMAGE_TAG,
            "RESEARCHOS_WORKER_DOCKER_IMAGE": _IMAGE_TAG,
        },
    )
    assert _wait_until(lambda: _is_leased_by(harness, task_id, "gpu-renew-w1"), timeout=120)
    # the job runs ~15s; the lease TTL is 8s — renewal must carry it across
    assert _wait_until(lambda: harness.job_queue.poll(task_id) is not None, timeout=90)
    outcome = harness.job_queue.poll(task_id)
    assert outcome is not None and outcome.status == "SUCCEEDED"
    # exactly one settle by the original worker; no requeue/duplicate
    assert outcome.worker_id == "gpu-renew-w1"
    assert _lease_count(harness, task_id) == 0
    worker.terminate()


def test_gpu_stale_fence_artifact_upload_rejected(gpu_harness: WorkerHarness) -> None:
    """A superseded GPU worker cannot upload its output bundle (fence gate)."""
    import httpx

    harness = gpu_harness
    task_id = harness.seed_job(
        idem="gpu-fence-1", command="echo hi", capability="gpu", resource_profile="gpu-small"
    )
    old_token, old_gen = _gateway_register_gpu(harness, "gpu-fence-old")
    claim = httpx.post(
        f"{harness.gateway_url}/worker/v1/claim",
        headers={"Authorization": f"Bearer {old_token}"},
        json={
            "worker_id": "gpu-fence-old",
            "registration_generation": old_gen,
            "capabilities": ["docker", "gpu"],
            "partitions": list(range(16)),
        },
    )
    assert claim.status_code == 200
    lease_id = str(claim.json()["lease_id"])
    fence = int(claim.json()["fence"])
    # supersede: expire + recover + a new claim advances the fence
    _expire_lease(harness, task_id)
    harness.workflow.recover_expired_leases()
    new_token, new_gen = _gateway_register_gpu(harness, "gpu-fence-new")
    httpx.post(
        f"{harness.gateway_url}/worker/v1/claim",
        headers={"Authorization": f"Bearer {new_token}"},
        json={
            "worker_id": "gpu-fence-new",
            "registration_generation": new_gen,
            "capabilities": ["docker", "gpu"],
            "partitions": list(range(16)),
        },
    )
    # the OLD worker's artifact upload with its stale fence must be rejected
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/artifacts",
        headers={
            "Authorization": f"Bearer {old_token}",
            "X-Task-Id": task_id,
            "X-Lease-Id": lease_id,
            "X-Fence": str(fence),
        },
        content=b"bundle-bytes",
    )
    assert resp.status_code == 409
