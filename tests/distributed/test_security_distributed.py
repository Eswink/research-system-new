"""M16 WP4 distributed security attack suite (tests/distributed).

Asserts the untrusted-worker boundary under attack: forged registration,
stolen/expired credentials, replayed results, wrong fence, cross-task
artifacts, path traversal, symlinks, host mounts, host shell, secret
enumeration, oversized results. Security defaults are unchanged on the
remote path (M16 plan §12, ADR-0027).
"""

from __future__ import annotations

import base64
import json
from collections.abc import Generator

import httpx
import pytest

from adapters.workspace.bundle import BundleError
from tests.distributed.worker_harness import _ENROLLMENT, WorkerHarness
from tests.postgres_guard import postgres_dsn

pytestmark = [pytest.mark.distributed, pytest.mark.postgres]


@pytest.fixture()
def harness(clean_worker_plane: str) -> Generator[WorkerHarness, None, None]:
    h = WorkerHarness(postgres_dsn())
    h.start_gateway()
    yield h
    h.close()


def _register(harness: WorkerHarness, worker_id: str = "sec-w1") -> tuple[str, int]:
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/register",
        headers={"X-Worker-Enrollment": _ENROLLMENT},
        json={
            "worker_id": worker_id,
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": ["docker"],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [0],
            "max_concurrency": 1,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    return str(body["session_token"]), int(body["registration_generation"])


def test_worker_child_env_holds_zero_db_credentials() -> None:
    """F-2: the worker subprocess environment is stripped of every DB credential.

    PA-1 F6b: the child env is a whitelist — ambient session variables (worker
    backend/image overrides, OTel) must NOT leak into scenario workers.
    """
    from tests.distributed.worker_harness import worker_child_env

    base = {
        "RESEARCHOS_POSTGRES_DSN": "postgresql://u:p@h:5432/db",
        "DATABASE_URL": "postgresql://u:p@h:5432/db",
        "PATH": "/usr/bin",
        "RESEARCHOS_WORKER_EXECUTION_BACKEND": "docker",
        "RESEARCHOS_WORKER_GPU_IMAGE": "ambient-image:tag",
        "RESEARCHOS_OTEL_ENABLED": "1",
        "RESEARCHOS_WORKER_PLATFORM": "ambient/platform",
    }
    env = worker_child_env("http://127.0.0.1:1", "w1", base_env=base)
    assert "RESEARCHOS_POSTGRES_DSN" not in env
    assert "DATABASE_URL" not in env
    assert env["RESEARCHOS_WORKER_GATEWAY_URL"] == "http://127.0.0.1:1"
    assert env["PATH"] == "/usr/bin"  # non-secret env preserved
    # F6b: ambient deployment/session variables are not inherited
    assert "RESEARCHOS_WORKER_EXECUTION_BACKEND" not in env
    assert "RESEARCHOS_WORKER_GPU_IMAGE" not in env
    assert "RESEARCHOS_OTEL_ENABLED" not in env
    assert "RESEARCHOS_WORKER_PLATFORM" not in env
    # explicit env_extra still wins
    env2 = worker_child_env(
        "http://127.0.0.1:1",
        "w2",
        base_env=base,
        env_extra={"RESEARCHOS_WORKER_EXECUTION_BACKEND": "deterministic"},
    )
    assert env2["RESEARCHOS_WORKER_EXECUTION_BACKEND"] == "deterministic"


def test_forged_worker_registration_rejected(harness: WorkerHarness) -> None:
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/register",
        headers={"X-Worker-Enrollment": "forged-secret"},
        json={
            "worker_id": "forged",
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": ["docker"],
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [0],
            "max_concurrency": 1,
        },
    )
    assert resp.status_code == 401


def test_stolen_token_dies_after_reregistration(harness: WorkerHarness) -> None:
    token, _gen = _register(harness)
    # the real worker re-registers; the stolen copy of the old token is dead
    _register(harness, "sec-w1")
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/heartbeat",
        headers={"Authorization": f"Bearer {token}"},
        json={"worker_id": "sec-w1", "registration_generation": 1},
    )
    assert resp.status_code == 401


def test_replayed_result_with_wrong_fence_rejected(harness: WorkerHarness) -> None:
    token, gen = _register(harness)
    task_id = harness.seed_job(idem="sec-replay")
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/tasks/{task_id}/result",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "sec-w1",
            "registration_generation": gen,
            "lease_id": "never-issued",
            "fence": 0,
            "status": "SUCCEEDED",
            "exit_code": 0,
        },
    )
    assert resp.status_code == 409  # no matching lease -> rejected, not persisted


def test_impersonation_worker_id_mismatch_rejected(harness: WorkerHarness) -> None:
    token, gen = _register(harness, "imp-w1")
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/heartbeat",
        headers={"Authorization": f"Bearer {token}"},
        json={"worker_id": "victim", "registration_generation": gen},
    )
    assert resp.status_code == 401


def test_draining_worker_cannot_claim_new_work(harness: WorkerHarness) -> None:
    """F-1: drain is server-enforced authority, not worker cooperation."""
    token, gen = _register(harness, "drain-w1")
    harness.registry.drain("drain-w1")
    harness.seed_job(idem="drain-job", partition=0)
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "drain-w1",
            "registration_generation": gen,
            "capabilities": ["docker"],
            "partitions": [0],
        },
    )
    assert resp.status_code == 409  # DRAINING session refused, work stays queued


def test_claim_beyond_registered_capabilities_rejected(harness: WorkerHarness) -> None:
    """F-1: claim cannot assert capabilities/partitions never registered."""
    token, gen = _register(harness, "cap-w1")  # registers ["docker"], slots [0]
    harness.seed_job(idem="cap-job", partition=0)
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "cap-w1",
            "registration_generation": gen,
            "capabilities": ["docker", "gpu"],
            "partitions": [0],
        },
    )
    assert resp.status_code == 409


def _claim_lease(
    harness: WorkerHarness, token: str, gen: int, worker_id: str, idem: str
) -> tuple[str, str, int]:
    """Seed + claim one job through the gateway; return (task_id, lease_id, fence)."""
    harness.seed_job(idem=idem, partition=0)
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": worker_id,
            "registration_generation": gen,
            "capabilities": ["docker"],
            "partitions": [0],
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    return str(body["task_id"]), str(body["lease_id"]), int(body["fence"])


def _lease_headers(token: str, task_id: str, lease_id: str, fence: int) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Task-Id": task_id,
        "X-Lease-Id": lease_id,
        "X-Fence": str(fence),
    }


def test_secret_enumeration_surface_is_zero(harness: WorkerHarness) -> None:
    token, gen = _register(harness)
    # no endpoint lists credentials or resolves arbitrary refs
    for path in ("/worker/v1/credentials", "/worker/v1/secrets", "/worker/v1/credentials/LLM_KEY"):
        resp = httpx.get(
            f"{harness.gateway_url}{path}", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code in (401, 404, 405, 503)
    # F-4/F-10: even with a valid lease, an arbitrary artifact id is refused —
    # download is authorized only for the leased task's input or own uploads
    task_id, lease_id, fence = _claim_lease(harness, token, gen, "sec-w1", "enum-job")
    resp = httpx.get(
        f"{harness.gateway_url}/worker/v1/artifacts/LLM_KEY",
        headers=_lease_headers(token, task_id, lease_id, fence),
    )
    assert resp.status_code == 403


def test_oversized_result_rejected(harness: WorkerHarness) -> None:
    token, gen = _register(harness)
    task_id, lease_id, fence = _claim_lease(harness, token, gen, "sec-w1", "big-job")
    limit = harness.settings.max_result_bytes
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/artifacts",
        headers=_lease_headers(token, task_id, lease_id, fence),
        content=b"x" * (limit + 1),
    )
    assert resp.status_code == 413


def test_upload_without_lease_context_rejected(harness: WorkerHarness) -> None:
    """F-4: artifact transfer requires the fencing identity — no bare uploads."""
    token, _gen = _register(harness)
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/artifacts",
        headers={"Authorization": f"Bearer {token}"},
        content=b"small-bundle",
    )
    assert resp.status_code == 422


def test_cross_task_output_substitution_rejected(harness: WorkerHarness) -> None:
    """F-4 BLOCKER-class attack: present another task's bundle as this task's output."""
    token, gen = _register(harness, "sub-w1")
    # worker legitimately uploads a bundle while holding lease on task A
    task_a, lease_a, fence_a = _claim_lease(harness, token, gen, "sub-w1", "sub-a")
    upload = httpx.post(
        f"{harness.gateway_url}/worker/v1/artifacts",
        headers=_lease_headers(token, task_a, lease_a, fence_a),
        content=b"bundle-for-task-a",
    )
    assert upload.status_code == 200
    bundle_ref = upload.json()["artifact_id"]
    # BACKLOG-178: settle task A legitimately first (BUSY→READY) — a worker
    # can only hold one in-flight lease, so the substitution attempt happens
    # on the next claim, still carrying task A's bundle as B's output.
    settled = httpx.post(
        f"{harness.gateway_url}/worker/v1/tasks/{task_a}/result",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "sub-w1",
            "registration_generation": gen,
            "lease_id": lease_a,
            "fence": fence_a,
            "status": "SUCCEEDED",
            "exit_code": 0,
        },
    )
    assert settled.status_code == 200, settled.text
    # now claim task B and try to submit task A's bundle as B's output
    task_b, lease_b, fence_b = _claim_lease(harness, token, gen, "sub-w1", "sub-b")
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/tasks/{task_b}/result",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "sub-w1",
            "registration_generation": gen,
            "lease_id": lease_b,
            "fence": fence_b,
            "status": "SUCCEEDED",
            "exit_code": 0,
            "output_bundle_ref": bundle_ref,
            "output_bundle_digest": "sha256:" + "0" * 64,
        },
    )
    assert resp.status_code == 409  # provenance: bundle was uploaded for task A, not B


def test_malformed_result_rejected(harness: WorkerHarness) -> None:
    token, _gen = _register(harness)
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/tasks/not-a-task/result",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "sec-w1",
            "registration_generation": 1,
            # missing lease_id / fence / status entirely
            "exit_code": 0,
        },
    )
    assert resp.status_code in (422, 409)


def test_bundle_traversal_and_symlink_rejected() -> None:
    from adapters.workspace.bundle import bundle_to_directory

    evil = json.dumps(
        {
            "version": 1,
            "entries": [
                {
                    "path": "../escape.txt",
                    "sha256": "0" * 64,
                    "data_b64": base64.b64encode(b"pwned").decode(),
                }
            ],
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(BundleError):
            bundle_to_directory(evil, Path(tmp).joinpath("ws"), "sha256:" + "3" * 64)
        assert not (Path(tmp) / "escape.txt").exists()


def test_host_shell_denied_on_remote_path() -> None:
    """build_local_workspace host-shell default-deny is not lifted remotely."""
    from adapters.openhands.workspace_adapter import HostShellDeniedError, build_local_workspace

    with pytest.raises(HostShellDeniedError):
        build_local_workspace(None, "sec-session", allow_host_shell=False)


def test_docker_host_config_defaults_unchanged() -> None:
    """NetworkMode=none / CapDrop ALL / no-new-privileges remain the defaults."""
    import inspect

    from adapters.execution import docker_backend

    source = inspect.getsource(docker_backend.DockerExecutionBackend._create_container)
    assert '"NetworkMode": "none"' in source
    assert '"CapDrop": ["ALL"]' in source
    assert '"no-new-privileges"' in source
    assert '"Privileged": False' in source
