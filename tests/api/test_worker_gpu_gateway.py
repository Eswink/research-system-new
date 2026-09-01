"""M17 WP1 worker gateway GPU tests: handshake invariant + freshness TTL gate.

Fail-closed rules under test:
- declaring `gpu` requires a probe observation (and vice versa);
- bounded observation DTO rejects malformed input (422);
- a claim asserting `gpu` is refused with 409 `gpu_capability_stale` once the
  server-stamped observation age exceeds the TTL (server clock authority).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

from fastapi.testclient import TestClient

from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.credential_resolver import FakeCredentialResolver
from adapters.fakes.execution_job_queue import FakeExecutionJobQueue
from adapters.fakes.worker_registry import FakeWorkerRegistry
from adapters.fakes.workflow_engine import FakeWorkflowEngine
from services.api.worker_gateway.app import create_worker_app
from services.api.worker_gateway.deps import WorkerGatewayDeps
from services.api.worker_gateway.settings import WorkerGatewaySettings

_ENROLLMENT = "enroll-secret-xyz"
_OBSERVATION = {
    "device_name": "NVIDIA GeForce RTX 4060 Laptop GPU",
    "device_count": 1,
    "driver_version": "581.80",
    "cuda_runtime_version": "12.8",
    "total_vram_bytes": 8_585_216_000,
    "framework": "torch-2.9.1+cu128",
    "probed_at": "2026-09-02T00:00:00+00:00",
    "probe_digest": "aa11bb22cc33dd44",
}


def _as_dict(body: Any) -> dict[str, object]:
    return cast(dict[str, object], body)


def _deps(now: Any = None) -> WorkerGatewayDeps:
    return WorkerGatewayDeps(
        registry=FakeWorkerRegistry(now=now),
        credentials=FakeCredentialResolver({"WORKER_ENROLLMENT_SECRET": _ENROLLMENT}),
        settings=WorkerGatewaySettings(enrollment_credential_ref="WORKER_ENROLLMENT_SECRET"),
        workflow=FakeWorkflowEngine(),
        job_queue=FakeExecutionJobQueue(),
        artifacts=FakeArtifactStore(),
    )


def _register(client: TestClient, capabilities: list[str], gpu_observation: Any) -> Any:
    return client.post(
        "/worker/v1/register",
        headers={"X-Worker-Enrollment": _ENROLLMENT},
        json={
            "worker_id": "worker-a",
            "protocol_version": "1",
            "runtime_version": "0.1.0",
            "capabilities": capabilities,
            "backend_kinds": ["DOCKER"],
            "platform": "linux/amd64",
            "partition_slots": [0],
            "max_concurrency": 1,
            "gpu_observation": gpu_observation,
        },
    )


def _claim(client: TestClient, token: str, capabilities: list[str]) -> Any:
    return client.post(
        "/worker/v1/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "worker_id": "worker-a",
            "registration_generation": 1,
            "capabilities": capabilities,
            "partitions": [0],
        },
    )


def test_gpu_capability_without_observation_is_refused() -> None:
    resp = _register(TestClient(create_worker_app(_deps())), ["docker", "gpu"], None)
    assert resp.status_code == 409
    assert "gpu_observation probe result" in str(resp.json()["detail"])


def test_observation_without_gpu_capability_is_refused() -> None:
    resp = _register(TestClient(create_worker_app(_deps())), ["docker"], _OBSERVATION)
    assert resp.status_code == 409
    assert "gpu_observation requires the 'gpu' capability" in str(resp.json()["detail"])


def test_bounded_observation_rejects_malformed_fields() -> None:
    bad = dict(_OBSERVATION, device_count=0)
    resp = _register(TestClient(create_worker_app(_deps())), ["docker", "gpu"], bad)
    assert resp.status_code == 422


def test_gpu_registration_stores_observation_and_claim_passes_gate() -> None:
    deps = _deps()
    client = TestClient(create_worker_app(deps))
    resp = _register(client, ["docker", "gpu"], _OBSERVATION)
    assert resp.status_code == 200
    token = _as_dict(resp.json())["session_token"]
    stored = deps.registry.get("worker-a")
    assert stored is not None and stored.gpu_observation is not None
    assert stored.gpu_observation.device_name.endswith("RTX 4060 Laptop GPU")
    assert stored.gpu_observed_at is not None  # server-stamped
    # No queued jobs → 204 means the freshness gate did not refuse the claim.
    assert _claim(client, str(token), ["docker", "gpu"]).status_code == 204


def test_expired_observation_claim_is_refused_as_stale() -> None:
    """Registry clock at 2020 → observed_at is years old by real wall clock."""
    deps = _deps(now=lambda: datetime(2020, 1, 1, tzinfo=timezone.utc))
    client = TestClient(create_worker_app(deps))
    resp = _register(client, ["docker", "gpu"], _OBSERVATION)
    assert resp.status_code == 200
    token = _as_dict(resp.json())["session_token"]
    claim = _claim(client, str(token), ["docker", "gpu"])
    assert claim.status_code == 409
    detail = str(claim.json()["detail"])
    assert "re-probe required" in detail
    assert "TTL 900s" in detail


def test_expired_observation_does_not_block_cpu_claims() -> None:
    """A stale gpu observation must never take down the CPU path."""
    deps = _deps(now=lambda: datetime(2020, 1, 1, tzinfo=timezone.utc))
    client = TestClient(create_worker_app(deps))
    resp = _register(client, ["docker", "gpu"], _OBSERVATION)
    token = _as_dict(resp.json())["session_token"]
    assert _claim(client, str(token), ["docker"]).status_code == 204


def test_worker_without_gpu_can_never_claim_gpu_capability() -> None:
    """A CPU-only registration cannot self-assert `gpu` at claim time."""
    deps = _deps()
    client = TestClient(create_worker_app(deps))
    resp = _register(client, ["docker"], None)
    token = _as_dict(resp.json())["session_token"]
    claim = _claim(client, str(token), ["docker", "gpu"])
    assert claim.status_code == 409
    assert "exceed worker registration" in str(claim.json()["detail"])
