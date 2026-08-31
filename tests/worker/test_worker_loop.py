"""M16 WP3 worker loop + client tests (in-process, no subprocess).

The real cross-process HTTP path is exercised by the WP4 distributed E2E
harness; here the loop is driven by an in-memory fake client and the client's
request building is checked against an httpx MockTransport.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from adapters.fakes.execution_backend import FakeExecutionBackend
from adapters.worker.client import WorkerClient, WorkerClientConfig, WorkerResultPayload
from packages.domain.workspace import ExecutionStatus
from services.worker.loop import WorkerLoop, WorkerLoopConfig


class _FakeClient:
    """In-memory stand-in for WorkerClient driving one job through the loop."""

    def __init__(self, job: dict[str, object] | None) -> None:
        self._job = job
        self.registered = False
        self.heartbeats = 0
        self.results: list[tuple[str, WorkerResultPayload]] = []
        self.uploads: list[bytes] = []
        self.downloads: list[str] = []

    def register(self) -> dict[str, object]:
        self.registered = True
        return {"session_token": "t", "registration_generation": 1}

    def heartbeat(self) -> dict[str, object]:
        self.heartbeats += 1
        return {"accepted": True, "state": "READY", "drain_requested": False}

    def claim(self) -> dict[str, object] | None:
        job, self._job = self._job, None
        return job

    def download_bundle(self, artifact_id: str) -> bytes:
        self.downloads.append(artifact_id)
        return b""

    def upload_bundle(self, bundle: bytes) -> dict[str, object]:
        self.uploads.append(bundle)
        return {"artifact_id": "out-1", "digest": "sha256:x"}

    def submit_result(self, task_id: str, payload: WorkerResultPayload) -> dict[str, object]:
        self.results.append((task_id, payload))
        return {"accepted": True, "task_id": task_id}


def _job(tmp_path: Path) -> dict[str, object]:
    return {
        "task_id": "task-1",
        "lease_id": "lease-1",
        "fence": 1,
        "spec_json": '{"backend_kind":"DOCKER","command":"echo hi","workdir":"/workspace"}',
        "timeout_seconds": 5,
    }


def test_loop_processes_one_job(tmp_path: Path) -> None:
    client = _FakeClient(_job(tmp_path))
    loop = WorkerLoop(
        client,  # type: ignore[arg-type]
        FakeExecutionBackend(status=ExecutionStatus.SUCCEEDED),
        config=WorkerLoopConfig(max_iterations=2, scratch_root=str(tmp_path / "scratch")),
    )
    completed = loop.run()
    assert completed == 1
    assert client.registered is True
    assert len(client.results) == 1
    _task_id, payload = client.results[0]
    assert payload.status == "SUCCEEDED"
    assert payload.fence == 1
    assert payload.output_bundle_ref == "out-1"


def test_loop_stops_when_no_jobs(tmp_path: Path) -> None:
    client = _FakeClient(None)
    loop = WorkerLoop(
        client,  # type: ignore[arg-type]
        FakeExecutionBackend(),
        config=WorkerLoopConfig(max_iterations=3, scratch_root=str(tmp_path / "s")),
    )
    assert loop.run() == 0
    assert client.results == []


def test_loop_honours_drain() -> None:
    class _DrainingClient(_FakeClient):
        def heartbeat(self) -> dict[str, object]:
            self.heartbeats += 1
            return {"accepted": True, "state": "DRAINING", "drain_requested": True}

    client = _DrainingClient(_job(Path(".")))
    loop = WorkerLoop(client, FakeExecutionBackend(), config=WorkerLoopConfig())  # type: ignore[arg-type]
    assert loop.run() == 0  # drains before claiming
    assert client.results == []


def test_client_registers_and_stores_token() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path.endswith("/register"):
            return httpx.Response(
                200, json={"session_token": "tok", "registration_generation": 3}
            )
        if request.url.path.endswith("/heartbeat"):
            assert request.headers["Authorization"] == "Bearer tok"
            return httpx.Response(200, json={"accepted": True, "state": "READY"})
        return httpx.Response(404)

    config = WorkerClientConfig(
        base_url="http://gateway", enrollment_secret="s", worker_id="w1"
    )
    client = WorkerClient(config, transport=httpx.MockTransport(handler))
    client.register()
    assert client.generation == 3
    hb = client.heartbeat()
    assert hb["accepted"] is True
    client.close()


def test_client_claim_204_returns_none() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/register"):
            return httpx.Response(200, json={"session_token": "t", "registration_generation": 1})
        return httpx.Response(204)

    config = WorkerClientConfig(base_url="http://g", enrollment_secret="s", worker_id="w")
    client = WorkerClient(config, transport=httpx.MockTransport(handler))
    client.register()
    assert client.claim() is None
    client.close()


def test_client_requires_registration_for_auth() -> None:
    config = WorkerClientConfig(base_url="http://g", enrollment_secret="s", worker_id="w")
    client = WorkerClient(config, transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    with pytest.raises(RuntimeError):
        client.heartbeat()
    client.close()
