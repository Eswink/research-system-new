"""Worker-side HTTP client for the Control Plane worker gateway (M16 WP3).

The only place a worker process talks to the Control Plane. It never touches
PostgreSQL or ArtifactStore directly — every authoritative interaction goes
through the authenticated `/worker/v1` gateway. `httpx` is the pinned client
(already an ADOPTED dependency; no new upstream).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import httpx

if TYPE_CHECKING:
    from packages.domain.workers import WorkerGpuObservation


def _json(resp: httpx.Response) -> dict[str, object]:
    return cast(dict[str, object], resp.json())


@dataclass(frozen=True, slots=True)
class WorkerClientConfig:
    base_url: str
    enrollment_secret: str
    worker_id: str
    protocol_version: str = "1"
    runtime_version: str = "0.1.0"
    platform: str = "unknown/unknown"
    capabilities: tuple[str, ...] = ()
    backend_kinds: tuple[str, ...] = ()
    partition_slots: tuple[int, ...] = ()
    max_concurrency: int = 1
    request_timeout_seconds: float = 30.0
    heartbeat_interval_seconds: float = 10.0


@dataclass(frozen=True, slots=True)
class WorkerResultPayload:
    """A worker's execution result for one claimed job (typed, not a dict).

    The gateway derives worker identity from the authenticated session (not
    from this payload), so no identity field is carried here.
    """

    lease_id: str
    fence: int
    status: str
    exit_code: int | None = None
    stdout_digest: str | None = None
    stderr_digest: str | None = None
    output_bundle_ref: str | None = None
    output_bundle_digest: str | None = None
    failure_category: str | None = None
    image_digest: str | None = None
    gpu_elapsed_seconds: int | None = None
    peak_gpu_memory_bytes: int | None = None

    def to_body(self, worker_id: str, generation: int) -> dict[str, object]:
        return {
            "worker_id": worker_id,
            "registration_generation": generation,
            "lease_id": self.lease_id,
            "fence": self.fence,
            "status": self.status,
            "exit_code": self.exit_code,
            "stdout_digest": self.stdout_digest,
            "stderr_digest": self.stderr_digest,
            "output_bundle_ref": self.output_bundle_ref,
            "output_bundle_digest": self.output_bundle_digest,
            "failure_category": self.failure_category,
            "image_digest": self.image_digest,
            "gpu_elapsed_seconds": self.gpu_elapsed_seconds,
            "peak_gpu_memory_bytes": self.peak_gpu_memory_bytes,
        }


class WorkerClient:
    """Thin, testable gateway client (session token held in-memory only)."""

    def __init__(self, config: WorkerClientConfig, transport: httpx.BaseTransport | None = None):
        self._config = config
        self._token: str | None = None
        self._generation: int = 0
        self._heartbeat_interval: float = config.heartbeat_interval_seconds
        # effective capabilities of the CURRENT registration (register() may
        # derive 'gpu' from the probe observation; claims must advertise the
        # same set that was registered, or the engine will never match).
        self._capabilities: tuple[str, ...] = tuple(config.capabilities)
        self._http = httpx.Client(
            base_url=config.base_url, timeout=config.request_timeout_seconds, transport=transport
        )

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self._capabilities

    @property
    def heartbeat_interval_seconds(self) -> float:
        return self._heartbeat_interval

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "WorkerClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def generation(self) -> int:
        return self._generation

    def _auth_headers(self) -> dict[str, str]:
        if self._token is None:
            raise RuntimeError("worker not registered; no session token")
        return {"Authorization": f"Bearer {self._token}"}

    def register(
        self,
        gpu_observation: WorkerGpuObservation | None = None,
        *,
        capabilities: tuple[str, ...] | None = None,
    ) -> dict[str, object]:
        """Registration handshake; `gpu_observation` present ⇔ `gpu` capability.

        M17: when a probe observation is supplied, the `gpu` capability is
        added automatically; without one it is never declared (probe failure
        ⇒ CPU-only registration, never a guess).
        """
        caps = list(capabilities) if capabilities is not None else list(self._config.capabilities)
        body: dict[str, object] = {
            "worker_id": self._config.worker_id,
            "protocol_version": self._config.protocol_version,
            "runtime_version": self._config.runtime_version,
            "capabilities": caps,
            "backend_kinds": list(self._config.backend_kinds),
            "platform": self._config.platform,
            "partition_slots": list(self._config.partition_slots),
            "max_concurrency": self._config.max_concurrency,
        }
        if gpu_observation is not None:
            if "gpu" not in caps:
                caps.append("gpu")
            body["capabilities"] = caps
            body["gpu_observation"] = gpu_observation.to_json_dict()
        self._capabilities = tuple(caps)
        resp = self._http.post(
            "/worker/v1/register",
            headers={"X-Worker-Enrollment": self._config.enrollment_secret},
            json=body,
        )
        resp.raise_for_status()
        response_body = _json(resp)
        self._token = str(response_body["session_token"])
        self._generation = int(str(response_body["registration_generation"]))
        interval = response_body.get("heartbeat_interval_seconds")
        if interval is not None:
            self._heartbeat_interval = float(str(interval))
        return response_body

    def heartbeat(self) -> dict[str, object]:
        resp = self._http.post(
            "/worker/v1/heartbeat",
            headers=self._auth_headers(),
            json={"worker_id": self._config.worker_id, "registration_generation": self._generation},
        )
        resp.raise_for_status()
        return _json(resp)

    def claim(self) -> dict[str, object] | None:
        resp = self._http.post(
            "/worker/v1/claim",
            headers=self._auth_headers(),
            json={
                "worker_id": self._config.worker_id,
                "registration_generation": self._generation,
                # current registration's effective capabilities (M17: register
                # may have derived 'gpu' from the probe observation)
                "capabilities": list(self._capabilities),
                "partitions": list(self._config.partition_slots),
            },
        )
        if resp.status_code == 204:
            return None
        resp.raise_for_status()
        return _json(resp)

    def submit_result(self, task_id: str, payload: WorkerResultPayload) -> dict[str, object]:
        resp = self._http.post(
            f"/worker/v1/tasks/{task_id}/result",
            headers=self._auth_headers(),
            json=payload.to_body(self._config.worker_id, self._generation),
        )
        resp.raise_for_status()
        return _json(resp)

    def renew(self, task_id: str, lease_id: str, fence: int) -> None:
        """Extend the in-flight lease (M16 re-audit F-7); raises on stale lease."""
        resp = self._http.post(
            f"/worker/v1/tasks/{task_id}/renew",
            headers=self._lease_headers(task_id, lease_id, fence),
        )
        resp.raise_for_status()

    def cancel_requested(self, task_id: str) -> bool:
        """M17 WP4c: poll the cooperative cancel flag for an in-flight job.

        Only the lease holder is authorized (403 otherwise); a 404 (lease
        already released) maps to False — the job is over either way.
        """
        resp = self._http.get(
            f"/worker/v1/tasks/{task_id}/cancel",
            headers=self._auth_headers(),
        )
        if resp.status_code == 404:
            return False
        resp.raise_for_status()
        return bool(_json(resp).get("cancel_requested"))

    def _lease_headers(self, task_id: str, lease_id: str, fence: int) -> dict[str, str]:
        """Fencing identity for artifact transfer (M16 re-audit F-4).

        Uploads/downloads are gated server-side on the same
        `(task_id, lease_id, fence)` triple as result writes.
        """
        return {
            **self._auth_headers(),
            "X-Task-Id": task_id,
            "X-Lease-Id": lease_id,
            "X-Fence": str(fence),
        }

    def download_bundle(
        self, artifact_id: str, *, task_id: str, lease_id: str, fence: int
    ) -> bytes:
        resp = self._http.get(
            f"/worker/v1/artifacts/{artifact_id}",
            headers=self._lease_headers(task_id, lease_id, fence),
        )
        resp.raise_for_status()
        return resp.content

    def upload_bundle(
        self, bundle: bytes, *, task_id: str, lease_id: str, fence: int
    ) -> dict[str, object]:
        resp = self._http.post(
            "/worker/v1/artifacts",
            headers=self._lease_headers(task_id, lease_id, fence),
            content=bundle,
        )
        resp.raise_for_status()
        return _json(resp)
