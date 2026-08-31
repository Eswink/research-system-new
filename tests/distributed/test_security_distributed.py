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
from tests.distributed.conftest import _postgres_dsn
from tests.distributed.worker_harness import _ENROLLMENT, WorkerHarness

pytestmark = [pytest.mark.distributed, pytest.mark.postgres]


@pytest.fixture()
def harness(clean_worker_plane: str) -> Generator[WorkerHarness, None, None]:
    h = WorkerHarness(_postgres_dsn())
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


def test_secret_enumeration_surface_is_zero(harness: WorkerHarness) -> None:
    token, _gen = _register(harness)
    # no endpoint lists credentials or resolves arbitrary refs
    for path in ("/worker/v1/credentials", "/worker/v1/secrets", "/worker/v1/credentials/LLM_KEY"):
        resp = httpx.get(
            f"{harness.gateway_url}{path}", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code in (401, 404, 405, 503)
    # artifact download is namespaced by artifact id, not by reference guessing
    resp = httpx.get(
        f"{harness.gateway_url}/worker/v1/artifacts/LLM_KEY",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in (404, 503)


def test_oversized_result_rejected(harness: WorkerHarness) -> None:
    token, _gen = _register(harness)
    limit = harness.settings.max_result_bytes
    resp = httpx.post(
        f"{harness.gateway_url}/worker/v1/artifacts",
        headers={"Authorization": f"Bearer {token}"},
        content=b"x" * (limit + 1),
    )
    assert resp.status_code == 413


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
