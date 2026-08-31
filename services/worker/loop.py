"""Worker run loop (M16 WP3).

A worker registers, then loops: heartbeat, claim a job, materialize its input
bundle into a scratch workspace, execute via the injected `ExecutionBackend`
(Docker in production, a deterministic fake in tests), upload the output
bundle, and submit the fenced result. It never holds DB/ArtifactStore
credentials — all authoritative interaction is through the gateway client.

Drain: when the Control Plane marks the worker DRAINING (surfaced via the
heartbeat response), the loop stops claiming and exits after settling in-flight
work. SIGTERM requests the same graceful drain.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.worker.client import WorkerClient, WorkerResultPayload
from adapters.workspace.bundle import bundle_from_directory, bundle_to_directory
from packages.application.ports.execution_backend import ExecutionBackend
from packages.domain.workspace import ExecutionSpec, ExecutionStatus


@dataclass(frozen=True, slots=True)
class WorkerLoopConfig:
    heartbeat_interval_seconds: float = 10.0
    max_iterations: int | None = None  # None = run until drain/stop
    scratch_root: str | None = None


def _spec_from_json(spec_json: str, workspace_path: str) -> ExecutionSpec:
    data: dict[str, Any] = json.loads(spec_json)
    return ExecutionSpec(
        backend_kind=str(data["backend_kind"]),
        command=str(data["command"]),
        resource_profile=data.get("resource_profile"),
        environment_digest=data.get("environment_digest"),
        workspace_path=workspace_path,
        environment=dict(data.get("environment") or {}),
        workdir=str(data.get("workdir") or "/workspace"),
    )


class WorkerLoop:
    """Drives one worker's register → claim/execute/complete → heartbeat cycle."""

    def __init__(
        self,
        client: WorkerClient,
        backend: ExecutionBackend,
        *,
        config: WorkerLoopConfig | None = None,
        should_stop: Callable[[], bool] | None = None,
        sleep: Callable[[float], None] = lambda _s: None,
    ) -> None:
        self._client = client
        self._backend = backend
        self._config = config or WorkerLoopConfig()
        self._should_stop = should_stop or (lambda: False)
        self._sleep = sleep
        self._draining = False
        self.completed_jobs = 0

    def run(self) -> int:
        """Register and process jobs until drain/stop; return jobs completed."""
        self._client.register()
        print(f"worker-loop: registered gen={self._client.generation}", flush=True)  # noqa: T201
        iterations = 0
        while not self._should_stop() and not self._draining:
            if (
                self._config.max_iterations is not None
                and iterations >= self._config.max_iterations
            ):
                break
            iterations += 1
            hb = self._client.heartbeat()
            if hb.get("drain_requested"):
                self._draining = True
                break
            job = self._client.claim()
            if job is None:
                self._sleep(self._config.heartbeat_interval_seconds)
                continue
            print(f"worker-loop: claimed job task_id={job.get('task_id')}", flush=True)  # noqa: T201
            self._process(job)
            self.completed_jobs += 1
        print(f"worker-loop: exiting completed={self.completed_jobs}", flush=True)  # noqa: T201
        return self.completed_jobs

    def _process(self, job: dict[str, object]) -> None:
        task_id = str(job["task_id"])
        scratch = Path(self._config.scratch_root or tempfile.mkdtemp(prefix="worker-job-"))
        scratch.mkdir(parents=True, exist_ok=True)
        input_ref = job.get("input_bundle_ref")
        input_digest = job.get("input_bundle_digest")
        if input_ref and input_digest:
            bundle = self._client.download_bundle(str(input_ref))
            bundle_to_directory(bundle, scratch, str(input_digest))
        spec = _spec_from_json(str(job["spec_json"]), str(scratch))
        runner = getattr(self._backend, "execute")
        run = runner(spec, timeout_seconds=_as_int(job.get("timeout_seconds")))
        out_bundle, out_digest = bundle_from_directory(scratch)
        ack = self._client.upload_bundle(out_bundle)
        payload = WorkerResultPayload(
            lease_id=str(job["lease_id"]),
            fence=int(str(job["fence"])),
            status=_map_status(run.status),
            exit_code=run.exit_code,
            stdout_digest=str(run.stdout_digest) if run.stdout_digest else None,
            stderr_digest=str(run.stderr_digest) if run.stderr_digest else None,
            output_bundle_ref=str(ack["artifact_id"]),
            output_bundle_digest=out_digest,
            failure_category=run.failure_category.value if run.failure_category else None,
        )
        self._client.submit_result(task_id, payload)


def _as_int(value: object) -> int | None:
    return None if value is None else int(str(value))


def _map_status(status: ExecutionStatus) -> str:
    if status is ExecutionStatus.SUCCEEDED:
        return "SUCCEEDED"
    if status is ExecutionStatus.CANCELLED:
        return "CANCELLED"
    return "FAILED"
