"""RemoteExecutionBackend: ExecutionBackend over the distributed job plane (M16).

Same Port as `DockerExecutionBackend`, so Application has zero local/remote
branching — the composition root picks the adapter. `execute` exports the
workspace as a content-addressed bundle, enqueues an EXECUTION job on the
single canonical queue, polls to a deadline, verifies the worker's output
bundle through ArtifactStore, materializes it back into the local workspace,
and normalizes an `ExecutionRun`. On timeout it requests cooperative cancel.

M17: the scheduling capability is derived from the spec's resource profile
(`derive_required_capability`), never from `backend_kind` — the old
`backend_kind.lower()` derivation produced `"sandbox"`, which no real worker
declares, so remote dispatch could never be claimed. A GPU-profile job that
times out while never claimed is classified GPU_UNAVAILABLE (GPU
infrastructure failure — never a silent CPU fallback).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from adapters.execution.profiles import derive_required_capability, is_gpu_profile
from adapters.workspace.bundle import BundleError, bundle_from_directory, bundle_to_directory
from packages.application.observability.attributes import worker_ref
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.execution_job_queue import (
    ExecutionJobOutcome,
    ExecutionJobQueue,
    ExecutionJobRequest,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.enums import FailureCategory
from packages.domain.serialization import digest_of
from packages.domain.task_state import ResearchTaskState
from packages.domain.workers import compute_partition
from packages.domain.workspace import ExecutionRun, ExecutionSpec, ExecutionStatus

_BUNDLE_MEDIA = "application/x-researchos-workspace-bundle"
_POLL_STEP_SECONDS = 0.2


class RemoteExecutionBackend:
    """ExecutionBackend that dispatches work to remote workers via the queue."""

    def __init__(
        self,
        *,
        job_queue: ExecutionJobQueue,
        artifacts: ArtifactStore,
        poll_step_seconds: float = _POLL_STEP_SECONDS,
        sleeper: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._jobs = job_queue
        self._artifacts = artifacts
        self._poll_step = poll_step_seconds
        self._sleep = sleeper
        self._monotonic = monotonic
        self._closed = False
        self._run_id: str | None = None

    @classmethod
    def for_run(
        cls,
        run_id: str,
        *,
        job_queue: ExecutionJobQueue,
        artifacts: ArtifactStore,
    ) -> RemoteExecutionBackend:
        """Bind production dispatch to its owning ResearchRun at composition."""
        backend = cls(job_queue=job_queue, artifacts=artifacts)
        backend._run_id = ID(run_id).value
        return backend

    def close(self) -> None:
        self._closed = True

    def execute(
        self,
        spec: ExecutionSpec,
        timeout_seconds: int | None = None,
        *,
        cancelled: Callable[[], bool] | None = None,
    ) -> ExecutionRun:
        if self._closed:
            raise InvalidInputError("remote execution backend is closed")
        if not spec.command:
            raise InvalidInputError("execution command must not be empty")
        workspace = Path(spec.workspace_path) if spec.workspace_path else Path(".")
        started = Timestamp.now()
        task_id = self._submit(spec, workspace)
        outcome = self._await(spec, task_id, timeout_seconds, cancelled)
        return self._normalize(spec, workspace, started, outcome)

    # --- submit ---
    def _submit(self, spec: ExecutionSpec, workspace: Path) -> str:
        bundle, tree_digest = bundle_from_directory(workspace)
        artifact = Artifact(
            id=f"wsbundle-{uuid4().hex}",
            digest=Digest.of_bytes(bundle),
            size_bytes=len(bundle),
            media_type=_BUNDLE_MEDIA,
            created_by="remote-execution-backend",
        )
        self._artifacts.put(artifact, bundle)
        run_id = self._run_id or str(uuid4())
        job_spec = replace(spec, workspace_path=None) if self._run_id is not None else spec
        # M17 fix: capability from the resource profile ("gpu" / "docker"),
        # matching what real workers declare. The previous
        # `spec.backend_kind.lower()` produced "sandbox" — unclaimable.
        capability = derive_required_capability(spec)
        idempotency_key = str(
            digest_of({
                "run_id": self._run_id,
                "spec": job_spec,
                "input_bundle_digest": tree_digest,
                "workspace": str(workspace) if self._run_id is None else None,
            })
        )
        request = ExecutionJobRequest(
            spec=job_spec,
            run_id=run_id,
            capability=capability,
            idempotency_key=idempotency_key,
            input_bundle_ref=artifact.id,
            input_bundle_digest=tree_digest,
            partition=compute_partition(run_id),
        )
        return self._jobs.enqueue(request)

    # --- poll ---
    def _await(
        self,
        spec: ExecutionSpec,
        task_id: str,
        timeout_seconds: int | None,
        cancelled: Callable[[], bool] | None,
    ) -> ExecutionJobOutcome:
        deadline = self._monotonic() + timeout_seconds if timeout_seconds is not None else None
        while True:
            outcome = self._jobs.poll(task_id)
            if outcome is not None:
                return outcome
            if cancelled is not None and cancelled():
                self._jobs.request_cancel(task_id)
                return ExecutionJobOutcome(task_id=task_id, status="CANCELLED")
            if deadline is not None and self._monotonic() >= deadline:
                self._jobs.request_cancel(task_id)
                # M17: a GPU job that timed out while never claimed is a GPU
                # infrastructure failure (no worker could run it) — never a
                # silent CPU fallback.
                timeout_failure = (
                    FailureCategory.GPU_UNAVAILABLE.value
                    if is_gpu_profile(spec.resource_profile)
                    and getattr(self._jobs, "claimed_by", lambda _t: None)(task_id) is None
                    else None
                )
                return ExecutionJobOutcome(
                    task_id=task_id, status="TIMED_OUT", failure_category=timeout_failure
                )
            self._sleep(self._poll_step)

    # --- normalize ---
    def _normalize(
        self,
        spec: ExecutionSpec,
        workspace: Path,
        started: Timestamp,
        outcome: ExecutionJobOutcome,
    ) -> ExecutionRun:
        status = self._map_status(outcome.status)
        if outcome.output_bundle_ref and outcome.output_bundle_digest:
            self._materialize(workspace, outcome)
        completed = Timestamp.now()
        return ExecutionRun(
            run_id=f"remote-{outcome.task_id}",
            spec=spec,
            status=status,
            started_at=started,
            completed_at=completed,
            exit_code=outcome.exit_code,
            failure_category=self._map_failure(status, outcome),
            stdout_digest=Digest.parse(outcome.stdout_digest) if outcome.stdout_digest else None,
            stderr_digest=Digest.parse(outcome.stderr_digest) if outcome.stderr_digest else None,
            compute_usage_summary={
                "worker_ref": worker_ref(outcome.worker_id) if outcome.worker_id else None,
                "fence": outcome.fence,
                "remote": True,
                # M17: the worker resolved and reported the actual image digest
                # it ran — bind remote reproducibility to it.
                "image_digest": outcome.image_digest,
                # M17: GPU observations flow back so the remote path feeds the
                # same single experiment usage ledger (GPU_TIME) as local.
                "gpu_elapsed_seconds": outcome.gpu_elapsed_seconds,
                "peak_gpu_memory_bytes": outcome.peak_gpu_memory_bytes,
                # server-measured wall clock (started→completed); consumed by the
                # single experiment usage path (M16 re-audit F-5: no second truth)
                "elapsed_seconds": (
                    float(outcome.execution_elapsed_seconds)
                    if outcome.execution_elapsed_seconds is not None
                    else max(0, int((completed.value - started.value).total_seconds()))
                ),
            },
        )

    def _materialize(self, workspace: Path, outcome: ExecutionJobOutcome) -> None:
        bundle = self._artifacts.get(str(outcome.output_bundle_ref))
        if not self._artifacts.verify(str(outcome.output_bundle_ref)):
            raise InvalidInputError(f"output bundle failed verification: {outcome.task_id}")
        try:
            bundle_to_directory(bundle, workspace, str(outcome.output_bundle_digest))
        except BundleError as exc:
            raise InvalidInputError(f"output bundle integrity failure: {exc}") from exc

    @staticmethod
    def _map_status(status: str) -> ExecutionStatus:
        if status == ResearchTaskState.State.SUCCEEDED:
            return ExecutionStatus.SUCCEEDED
        if status == "TIMED_OUT":
            return ExecutionStatus.TIMED_OUT
        if status == "CANCELLED" or status == ResearchTaskState.State.CANCELLED:
            return ExecutionStatus.CANCELLED
        return ExecutionStatus.FAILED

    @staticmethod
    def _map_failure(
        status: ExecutionStatus, outcome: ExecutionJobOutcome
    ) -> FailureCategory | None:
        if status is ExecutionStatus.SUCCEEDED:
            return None
        if outcome.failure_category:
            try:
                return FailureCategory(outcome.failure_category)
            except ValueError:
                return FailureCategory.EXECUTION_FAILURE
        if status is ExecutionStatus.FAILED:
            return FailureCategory.EXECUTION_FAILURE
        return None
