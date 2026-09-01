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
        self.generation = 1
        self.registered = False
        self.register_calls: list[object] = []  # gpu_observation per register()
        self.heartbeats = 0
        self.results: list[tuple[str, WorkerResultPayload]] = []
        self.uploads: list[bytes] = []
        self.downloads: list[str] = []
        self.upload_context: tuple[str, str, int] | None = None
        self.renews = 0
        self.heartbeat_interval_seconds = 0.2

    def renew(self, task_id: str, lease_id: str, fence: int) -> None:
        self.renews += 1

    def register(
        self,
        gpu_observation: object | None = None,
        *,
        capabilities: tuple[str, ...] | None = None,
    ) -> dict[str, object]:
        self.registered = True
        self.register_calls.append(gpu_observation)
        self.generation += 1
        return {"session_token": "t", "registration_generation": self.generation}

    def heartbeat(self) -> dict[str, object]:
        self.heartbeats += 1
        return {"accepted": True, "state": "READY", "drain_requested": False}

    def claim(self) -> dict[str, object] | None:
        job, self._job = self._job, None
        return job

    def download_bundle(
        self, artifact_id: str, *, task_id: str, lease_id: str, fence: int
    ) -> bytes:
        self.downloads.append(artifact_id)
        return b""

    def upload_bundle(
        self, bundle: bytes, *, task_id: str, lease_id: str, fence: int
    ) -> dict[str, object]:
        self.uploads.append(bundle)
        self.upload_context = (task_id, lease_id, fence)
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
    # F-4: the loop binds artifact transfer to the job's fencing identity
    assert client.upload_context == ("task-1", "lease-1", 1)


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
            return httpx.Response(200, json={"session_token": "tok", "registration_generation": 3})
        if request.url.path.endswith("/heartbeat"):
            assert request.headers["Authorization"] == "Bearer tok"
            return httpx.Response(200, json={"accepted": True, "state": "READY"})
        return httpx.Response(404)

    config = WorkerClientConfig(base_url="http://gateway", enrollment_secret="s", worker_id="w1")
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


# --- M17 WP1: GPU probe freshness in the loop --------------------------------


def _observation(digest: str) -> object:
    from packages.domain.core import Timestamp
    from packages.domain.workers import WorkerGpuObservation

    return WorkerGpuObservation(
        device_name="NVIDIA GeForce RTX 4060 Laptop GPU",
        device_count=1,
        driver_version="581.80",
        cuda_runtime_version="12.8",
        total_vram_bytes=8_585_216_000,
        framework="torch-2.9.1+cu128",
        probed_at=Timestamp.now(),
        probe_digest=digest,
    )


def _prober(sequence: list[object]) -> object:
    """Probe stub returning sequence items in order (clamped at the last)."""
    calls = {"n": 0}

    def _probe() -> object:
        index = min(calls["n"], len(sequence) - 1)
        calls["n"] += 1
        return sequence[index]

    return _probe


def _idle_loop(client: object, prober: object, tmp_path: Path, iterations: int) -> WorkerLoop:
    return WorkerLoop(
        client,  # type: ignore[arg-type]
        FakeExecutionBackend(),
        config=WorkerLoopConfig(
            max_iterations=iterations,
            scratch_root=str(tmp_path / "s"),
            gpu_reprobe_every_idle_heartbeats=1,
        ),
        gpu_prober=prober,  # type: ignore[arg-type]
    )


def test_probe_failure_at_startup_registers_cpu_only(tmp_path: Path) -> None:
    client = _FakeClient(None)
    _idle_loop(client, _prober([None]), tmp_path, iterations=2).run()
    assert client.register_calls == [None]


def test_probe_success_at_startup_declares_gpu(tmp_path: Path) -> None:
    client = _FakeClient(None)
    observation = _observation("aaaaaaaaaaaaaaaa")
    _idle_loop(client, _prober([observation]), tmp_path, iterations=2).run()
    assert client.register_calls == [observation]


def test_probe_digest_change_triggers_reregister(tmp_path: Path) -> None:
    """Freshness layer 3: digest change → re-register with the new facts."""
    client = _FakeClient(None)
    first = _observation("1111111111111111")
    second = _observation("2222222222222222")
    _idle_loop(client, _prober([first, second]), tmp_path, iterations=3).run()
    assert client.register_calls == [first, second]


def test_gpu_disappearance_triggers_cpu_only_reregister(tmp_path: Path) -> None:
    client = _FakeClient(None)
    observation = _observation("1111111111111111")
    _idle_loop(client, _prober([observation, None]), tmp_path, iterations=3).run()
    assert client.register_calls == [observation, None]


def test_claim_409_selfheal_reregisters(tmp_path: Path) -> None:
    """A stale-observation 409 from claim triggers one re-probe/register."""

    class _RejectingClient(_FakeClient):
        def __init__(self) -> None:
            super().__init__(None)
            self.claims = 0

        def claim(self) -> dict[str, object] | None:
            self.claims += 1
            if self.claims == 1:
                request = httpx.Request("POST", "http://gateway/worker/v1/claim")
                response = httpx.Response(409, request=request)
                raise httpx.HTTPStatusError("conflict", request=request, response=response)
            return None

    client = _RejectingClient()
    observation = _observation("1111111111111111")
    _idle_loop(client, _prober([observation]), tmp_path, iterations=3).run()
    assert client.register_calls == [observation, observation]
