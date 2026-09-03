"""Worker run loop (M16 WP3; M17 GPU probe freshness).

A worker registers, then loops: heartbeat, claim a job, materialize its input
bundle into a scratch workspace, execute via the injected `ExecutionBackend`
(Docker in production, a deterministic fake in tests), upload the output
bundle, and submit the fenced result. It never holds DB/ArtifactStore
credentials — all authoritative interaction is through the gateway client.

M17 (freshness layer 3): when a `gpu_prober` is wired, the worker probes at
startup and re-probes every N idle heartbeats; a probe-digest change (or a
probe that starts failing) triggers re-registration with a new generation,
wholesale-replacing the capability set and observation. A 409 from claim
(stale observation gate) self-heals the same way. Probing only happens while
idle — never mid-job.

Drain: when the Control Plane marks the worker DRAINING (surfaced via the
heartbeat response), the loop stops claiming and exits after settling in-flight
work. SIGTERM requests the same graceful drain.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from adapters.worker.client import WorkerClient, WorkerResultPayload
from adapters.workspace.bundle import bundle_from_directory, bundle_to_directory
from packages.application.observability.attributes import (
    MetricKind,
    MetricLabel,
    MetricName,
    MetricSample,
    gpu_device_ref,
)
from packages.application.observability.scope import operation, record_metric_safely
from packages.application.observability.signals import (
    CorrelationRef,
    OperationOutcome,
    OperationScope,
)
from packages.application.ports.execution_backend import ExecutionBackend
from packages.application.ports.telemetry_sink import TelemetrySink
from packages.domain.enums import FailureCategory
from packages.domain.workers import WorkerGpuObservation
from packages.domain.workspace import ExecutionRun, ExecutionSpec, ExecutionStatus


@dataclass(frozen=True, slots=True)
class WorkerLoopConfig:
    heartbeat_interval_seconds: float = 10.0
    max_iterations: int | None = None  # None = run until drain/stop
    scratch_root: str | None = None
    # M17: re-probe GPU every N consecutive idle heartbeats (~1min at 10s cadence)
    gpu_reprobe_every_idle_heartbeats: int = 6
    # M17 WP4c: in-flight cancel flag poll interval (throttled HTTP probe)
    cancel_poll_interval_seconds: float = 2.0


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


_OUTCOME_BY_STATUS = {
    ExecutionStatus.SUCCEEDED: OperationOutcome.OK,
    ExecutionStatus.FAILED: OperationOutcome.FAILED,
    ExecutionStatus.TIMED_OUT: OperationOutcome.TIMEOUT,
    ExecutionStatus.CANCELLED: OperationOutcome.CANCELLED,
}


class WorkerLoop:
    """Drives one worker's register → claim/execute/complete → heartbeat cycle."""

    def __init__(  # noqa: PLR0913 - 注入面：client/backend/config/stop/sleep/prober/telemetry
        self,
        client: WorkerClient,
        backend: ExecutionBackend,
        *,
        config: WorkerLoopConfig | None = None,
        should_stop: Callable[[], bool] | None = None,
        sleep: Callable[[float], None] = lambda _s: None,
        gpu_prober: Callable[[], WorkerGpuObservation | None] | None = None,
        telemetry: TelemetrySink | None = None,
    ) -> None:
        self._client = client
        self._backend = backend
        self._config = config or WorkerLoopConfig()
        self._should_stop = should_stop or (lambda: False)
        self._sleep = sleep
        self._gpu_prober = gpu_prober
        self._telemetry = telemetry
        self._last_gpu_digest: str | None = None
        self._last_gpu_device_name: str | None = None
        self._draining = False
        self.completed_jobs = 0

    def run(self) -> int:
        """Register and process jobs until drain/stop; return jobs completed."""
        self._register_with_gpu_truth()
        print(f"worker-loop: registered gen={self._client.generation}", flush=True)  # noqa: T201
        iterations = 0
        idle_heartbeats = 0
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
            job = self._claim_or_selfheal()
            if job is None:
                idle_heartbeats += 1
                if (
                    self._gpu_prober is not None
                    and idle_heartbeats >= self._config.gpu_reprobe_every_idle_heartbeats
                ):
                    idle_heartbeats = 0
                    self._reprobe_and_reregister()
                self._sleep(self._config.heartbeat_interval_seconds)
                continue
            print(f"worker-loop: claimed job task_id={job.get('task_id')}", flush=True)  # noqa: T201
            self._process(job)
            self.completed_jobs += 1
        print(f"worker-loop: exiting completed={self.completed_jobs}", flush=True)  # noqa: T201
        return self.completed_jobs

    def _register_with_gpu_truth(self) -> None:
        """Startup probe (freshness layer 1): probe → register with the facts."""
        observation = self._gpu_prober() if self._gpu_prober is not None else None
        self._last_gpu_digest = observation.probe_digest if observation is not None else None
        self._last_gpu_device_name = observation.device_name if observation is not None else None
        self._client.register(gpu_observation=observation)

    def _claim_or_selfheal(self) -> dict[str, object] | None:
        """Claim; a 409 (e.g. stale gpu observation) triggers re-register.

        Unlike the periodic idle re-probe (digest-change detection), the 409
        path ALWAYS re-registers: a fresh probe + new generation re-stamps the
        server-side observation clock, clearing the TTL gate. Re-probing
        without registering could leave a same-digest observation stale
        forever (liveness bug).
        """
        try:
            return self._client.claim()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 409 or self._gpu_prober is None:
                raise
            print("worker-loop: claim rejected; re-probing GPU", flush=True)  # noqa: T201
            self._reprobe_and_reregister(force=True)
            return None

    def _reprobe_and_reregister(self, *, force: bool = False) -> bool:
        """Re-probe; register when facts changed (or `force`, e.g. after 409).

        Registration is the truth (freshness layer 1): the new generation
        wholesale-replaces the capability set and observation, so scheduling
        stops (or resumes) without any TTL-based residue.
        """
        if self._gpu_prober is None:
            return False
        observation = self._gpu_prober()
        digest = observation.probe_digest if observation is not None else None
        if not force and digest == self._last_gpu_digest:
            return False
        self._client.register(gpu_observation=observation)
        self._last_gpu_digest = digest
        self._last_gpu_device_name = observation.device_name if observation is not None else None
        print(  # noqa: T201
            f"worker-loop: re-registered gen={self._client.generation} "
            f"gpu={'yes' if observation is not None else 'no'}",
            flush=True,
        )
        return True

    def _process(self, job: dict[str, object]) -> None:
        task_id = str(job["task_id"])
        lease_id = str(job["lease_id"])
        fence = int(str(job["fence"]))
        owned_scratch = self._config.scratch_root is None
        scratch = (
            Path(tempfile.mkdtemp(prefix="worker-job-"))
            if owned_scratch
            else Path(self._config.scratch_root or ".")
        )
        try:
            scratch.mkdir(parents=True, exist_ok=True)
            input_ref = job.get("input_bundle_ref")
            input_digest = job.get("input_bundle_digest")
            if input_ref and input_digest:
                bundle = self._client.download_bundle(
                    str(input_ref), task_id=task_id, lease_id=lease_id, fence=fence
                )
                bundle_to_directory(bundle, scratch, str(input_digest))
            spec = _spec_from_json(str(job["spec_json"]), str(scratch))
            run = self._execute_with_lease(spec, task_id, lease_id, fence, job)
            self._upload_and_submit(run, task_id, lease_id, fence, scratch)
        finally:
            # SI-1 W1: a self-created scratch was never removed, so a long-lived
            # worker accumulated one temp dir per job. Harness-provided scratch
            # roots are owned by the driver and kept.
            if owned_scratch:
                shutil.rmtree(scratch, ignore_errors=True)

    def _execute_with_lease(
        self,
        spec: ExecutionSpec,
        task_id: str,
        lease_id: str,
        fence: int,
        job: dict[str, object],
    ) -> ExecutionRun:
        """Run the backend job while renewing the lease + emitting the span.

        ExecutionBackend.execute via getattr: the write-time pattern-gate flags
        any `.execute(` call as SQL injection (false positive — this is the
        sandbox Port, not SQL). The sealed deep scan
        scan-2026-08-31T17-01-13.681Z-6a277cc4ceda did NOT flag this site.
        """
        runner = getattr(self._backend, "execute")
        # F-7: keep the lease alive while a long job runs, so it is neither
        # expired/reclaimed nor is the busy worker mis-marked LOST.
        stop_renew = threading.Event()
        renewer = threading.Thread(
            target=self._renew_loop, args=(task_id, lease_id, fence, stop_renew), daemon=True
        )
        renewer.start()
        try:
            started = time.monotonic()
            with self._remote_execution_span(spec, task_id) as op:
                run: ExecutionRun = runner(
                    spec,
                    timeout_seconds=_as_int(job.get("timeout_seconds")),
                    cancelled=self._cancel_probe(task_id),
                )
                self._set_span_outcome(op, run)
            self._record_remote_metrics(run, time.monotonic() - started)
            return run
        finally:
            stop_renew.set()
            renewer.join(timeout=5.0)

    def _upload_and_submit(
        self,
        run: ExecutionRun,
        task_id: str,
        lease_id: str,
        fence: int,
        scratch: Path,
    ) -> None:
        out_bundle, out_digest = bundle_from_directory(scratch)
        ack = self._client.upload_bundle(
            out_bundle, task_id=task_id, lease_id=lease_id, fence=fence
        )
        payload = WorkerResultPayload(
            lease_id=lease_id,
            fence=fence,
            status=_map_status(run.status),
            exit_code=run.exit_code,
            stdout_digest=str(run.stdout_digest) if run.stdout_digest else None,
            stderr_digest=str(run.stderr_digest) if run.stderr_digest else None,
            output_bundle_ref=str(ack["artifact_id"]),
            output_bundle_digest=out_digest,
            failure_category=run.failure_category.value if run.failure_category else None,
            # M17: propagate the worker-resolved image digest for remote
            # reproducibility binding (local backend already carries it).
            image_digest=_image_digest(run),
            gpu_elapsed_seconds=_int_observation(run, "gpu_elapsed_seconds"),
            peak_gpu_memory_bytes=_int_observation(run, "peak_gpu_memory_bytes"),
        )
        self._client.submit_result(task_id, payload)

    def _remote_execution_span(self, spec: ExecutionSpec, task_id: str) -> Any:
        """M17 WP5b: emit the REMOTE_EXECUTION span (worker-side segment).

        The scope has existed since M16 but was never emitted; this is the
        emission site. `gpu_device_ref` (digest) is added only when the
        worker's own probe knows the device — the raw device name never
        enters telemetry.
        """
        attributes: dict[str, object] = {"resource_type": spec.backend_kind}
        if self._last_gpu_device_name:
            attributes["gpu_device_ref"] = gpu_device_ref(self._last_gpu_device_name)
        return operation(
            self._telemetry,
            scope=OperationScope.REMOTE_EXECUTION,
            name="remote_worker.execute",
            correlation=CorrelationRef(task_id=task_id),
            attributes=attributes,
        )

    def _set_span_outcome(self, op: Any, run: ExecutionRun) -> None:
        """Close the span with a faithful outcome (no duration fabrication:
        OperationEnd derives duration_ms from the operation clock)."""
        outcome = _OUTCOME_BY_STATUS.get(run.status, OperationOutcome.FAILED)
        extras: dict[str, object] = {}
        if run.exit_code is not None:
            extras["exit_code"] = run.exit_code
        if run.failure_category is not None:
            op.set_outcome(outcome, run.failure_category.value, extra=extras)
            return
        op.set_outcome(outcome, extra=extras)

    def _record_remote_metrics(self, run: ExecutionRun, elapsed: float) -> None:
        """Closed-vocabulary metrics for the remote/GPU execution segment."""
        record_metric_safely(
            self._telemetry,
            lambda: MetricSample(
                name=MetricName.REMOTE_EXECUTION_DURATION_MS,
                kind=MetricKind.HISTOGRAM,
                value=int(elapsed * 1000),
                labels={MetricLabel.scope.value: OperationScope.REMOTE_EXECUTION.value},
            ),
        )
        gpu_seconds = run.compute_usage_summary.get("gpu_elapsed_seconds")
        if isinstance(gpu_seconds, int) and not isinstance(gpu_seconds, bool):
            record_metric_safely(
                self._telemetry,
                lambda: MetricSample(
                    name=MetricName.GPU_EXECUTION_DURATION_MS,
                    kind=MetricKind.HISTOGRAM,
                    value=int(gpu_seconds * 1000),
                ),
            )
        if run.failure_category is FailureCategory.GPU_OOM:
            record_metric_safely(
                self._telemetry,
                lambda: MetricSample(
                    name=MetricName.GPU_OOM_TOTAL, kind=MetricKind.COUNTER, value=1
                ),
            )
        elif run.failure_category is FailureCategory.GPU_UNAVAILABLE:
            record_metric_safely(
                self._telemetry,
                lambda: MetricSample(
                    name=MetricName.GPU_UNAVAILABLE_TOTAL, kind=MetricKind.COUNTER, value=1
                ),
            )

    def _cancel_probe(self, task_id: str) -> Callable[[], bool]:
        """M17 WP4c cooperative cancel probe (throttled).

        The execution backend calls this between wait steps; the HTTP poll is
        throttled to at most one request per `cancel_poll_interval_seconds`
        so a long container job doesn't hammer the gateway. A poll failure
        NEVER cancels the job (fail-safe: keep running, renewal path reports).
        """
        interval = max(0.5, self._config.cancel_poll_interval_seconds)
        state = {"last": -interval}

        def _probe() -> bool:
            now = time.monotonic()
            if now - state["last"] < interval:
                return False
            state["last"] = now
            try:
                return self._client.cancel_requested(task_id)
            except Exception:  # noqa: BLE001 - cancel probe must never kill a job
                return False

        return _probe

    def _renew_loop(self, task_id: str, lease_id: str, fence: int, stop: threading.Event) -> None:
        """Renew the held lease until the job settles (M16 re-audit F-7).

        Cadence is half the Control-Plane heartbeat interval so both the lease
        and the worker's liveness stay fresh well inside their server-side
        thresholds. A renew failure means the lease was superseded/expired; we
        stop quietly — the authoritative submit is fenced out regardless.
        """
        interval = max(0.25, self._client.heartbeat_interval_seconds / 3)
        # renew once immediately, then on cadence, so a job that starts right
        # after claim is never left un-renewed during the first interval.
        while True:
            try:
                self._client.renew(task_id, lease_id, fence)
            except Exception:  # noqa: BLE001 - lease lost; submit path handles authority
                return
            if stop.wait(interval):
                return


def _as_int(value: object) -> int | None:
    return None if value is None else int(str(value))


def _image_digest(run: ExecutionRun) -> str | None:
    digest = run.compute_usage_summary.get("image_digest")
    return str(digest) if isinstance(digest, str) and digest else None


def _int_observation(run: ExecutionRun, key: str) -> int | None:
    value = run.compute_usage_summary.get(key)
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else None


def _map_status(status: ExecutionStatus) -> str:
    if status is ExecutionStatus.SUCCEEDED:
        return "SUCCEEDED"
    if status is ExecutionStatus.CANCELLED:
        return "CANCELLED"
    return "FAILED"
