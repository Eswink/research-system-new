"""RemoteExecutionBackend: ExecutionBackend over the distributed job plane (M16).

Same Port as `DockerExecutionBackend`, so Application has zero local/remote
branching — the composition root picks the adapter. `execute` exports the
workspace as a content-addressed bundle, enqueues an EXECUTION job on the
single canonical queue, polls to a deadline, verifies the worker's output
bundle through ArtifactStore, materializes it back into the local workspace,
and normalizes an `ExecutionRun`. On timeout it requests cooperative cancel.

Honest scope note (M16 §9): `ExecutionSpec` carries no run/capability context,
so the job is enqueued under a generated job-scoped run id with capability
derived from `backend_kind` and partition from that run id. Phase-internal
parallel dispatch is M17; cross-run parallelism is what this enables.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from adapters.workspace.bundle import BundleError, bundle_from_directory, bundle_to_directory
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.execution_job_queue import (
    ExecutionJobOutcome,
    ExecutionJobQueue,
    ExecutionJobRequest,
)
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, Timestamp
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
        outcome = self._await(task_id, timeout_seconds, cancelled)
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
        run_id = str(uuid4())
        capability = spec.backend_kind.lower()
        idempotency_key = str(
            digest_of({
                "spec": spec.command,
                "input_bundle_digest": tree_digest,
                "workspace": str(workspace),
            })
        )
        request = ExecutionJobRequest(
            spec=spec,
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
        self, task_id: str, timeout_seconds: int | None, cancelled: Callable[[], bool] | None
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
                return ExecutionJobOutcome(task_id=task_id, status="TIMED_OUT")
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
        return ExecutionRun(
            run_id=f"remote-{outcome.task_id}",
            spec=spec,
            status=status,
            started_at=started,
            completed_at=Timestamp.now(),
            exit_code=outcome.exit_code,
            failure_category=self._map_failure(status, outcome),
            stdout_digest=Digest.parse(outcome.stdout_digest) if outcome.stdout_digest else None,
            stderr_digest=Digest.parse(outcome.stderr_digest) if outcome.stderr_digest else None,
            compute_usage_summary={
                "worker_ref": outcome.worker_id,
                "fence": outcome.fence,
                "remote": True,
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
        if status is not ExecutionStatus.FAILED:
            return None
        if outcome.failure_category:
            try:
                return FailureCategory(outcome.failure_category)
            except ValueError:
                return FailureCategory.EXECUTION_FAILURE
        return FailureCategory.EXECUTION_FAILURE
