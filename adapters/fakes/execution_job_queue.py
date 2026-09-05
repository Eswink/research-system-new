"""FakeExecutionJobQueue: in-memory remote execution jobs (M16 WP3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from adapters.fakes.base import FakeBase
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.execution_job_queue import (
    ExecutionJobDescriptor,
    ExecutionJobOutcome,
    ExecutionJobRequest,
    ExecutionJobResult,
    canonical_task_status,
)
from packages.domain.serialization import canonical_json_bytes
from packages.domain.task_state import ResearchTaskState
from packages.domain.workspace import ExecutionSpec


@dataclass(slots=True)
class _Job:
    task_id: str
    spec: ExecutionSpec
    run_id: str
    capability: str
    partition: int | None
    status: str = ResearchTaskState.State.QUEUED
    fence: int = 0
    lease_id: str | None = None
    worker_id: str | None = None
    input_bundle_ref: str | None = None
    input_bundle_digest: str | None = None
    cancel: bool = False
    outcome: ExecutionJobOutcome | None = None
    idempotency_key: str = ""


@dataclass(slots=True)
class FakeExecutionJobQueueState:
    """Shared mutable state so a queue + gateway view the same jobs."""

    jobs: dict[str, _Job] = field(default_factory=dict)
    by_idem: dict[str, str] = field(default_factory=dict)


class FakeExecutionJobQueue(FakeBase):
    """Deterministic job queue for contract + unit tests (no cross-process)."""

    def __init__(self, state: FakeExecutionJobQueueState | None = None) -> None:
        super().__init__("execution_job_queue")
        self._state = state if state is not None else FakeExecutionJobQueueState()

    @property
    def state(self) -> FakeExecutionJobQueueState:
        return self._state

    def enqueue(self, request: ExecutionJobRequest) -> str:
        self._enter("enqueue", request.idempotency_key)
        existing = self._state.by_idem.get(request.idempotency_key)
        if existing is not None:
            self._record("enqueue", request.idempotency_key, result="deduped")
            return existing
        task_id = f"exec-{uuid4().hex}"
        self._state.jobs[task_id] = _Job(
            task_id=task_id,
            spec=request.spec,
            run_id=request.run_id,
            capability=request.capability,
            partition=request.partition,
            input_bundle_ref=request.input_bundle_ref,
            input_bundle_digest=request.input_bundle_digest,
            idempotency_key=request.idempotency_key,
        )
        self._state.by_idem[request.idempotency_key] = task_id
        self._record("enqueue", request.idempotency_key, result=task_id)
        return task_id

    def describe(self, task_id: str) -> ExecutionJobDescriptor | None:
        self._enter("describe", task_id)
        job = self._state.jobs.get(task_id)
        if job is None:
            return None
        return ExecutionJobDescriptor(
            task_id=task_id,
            spec_json=canonical_json_bytes(job.spec).decode("utf-8"),
            input_bundle_ref=job.input_bundle_ref,
            input_bundle_digest=job.input_bundle_digest,
        )

    def poll(self, task_id: str) -> ExecutionJobOutcome | None:
        self._enter("poll", task_id)
        job = self._state.jobs.get(task_id)
        if job is None:
            return None
        if job.outcome is not None:
            return job.outcome
        if job.status in (
            ResearchTaskState.State.SUCCEEDED,
            ResearchTaskState.State.FAILED,
            ResearchTaskState.State.CANCELLED,
        ):
            return ExecutionJobOutcome(task_id=task_id, status=job.status, fence=job.fence)
        return None

    def record_result(self, result: ExecutionJobResult) -> None:
        self._enter("record_result", result.task_id)
        # shared closed-set terminal validation + canonicalization (Fake must
        # mirror the PostgreSQL adapter: CANCELLED stays CANCELLED, M17 WP4c)
        canonical_task_status(result.status)
        job = self._state.jobs.get(result.task_id)
        if job is None:
            raise InvalidInputError(f"unknown job: {result.task_id}")
        # fencing: mirror the PostgreSQL lease gate (M16 §8), including the
        # identity binding (the caller must BE the claim holder).
        if (
            result.worker_id is None
            or job.worker_id != result.worker_id
            or job.lease_id != result.lease_id
            or job.fence != result.fence
        ):
            self._record("record_result", result.task_id, error="InvalidInputError")
            raise InvalidInputError(
                f"stale or missing lease for task {result.task_id}: result rejected"
            )
        job.status = canonical_task_status(result.status)
        job.outcome = ExecutionJobOutcome(
            task_id=result.task_id,
            status=result.status,
            fence=result.fence,
            worker_id=job.worker_id,
            exit_code=result.exit_code,
            stdout_digest=result.stdout_digest,
            stderr_digest=result.stderr_digest,
            output_bundle_ref=result.output_bundle_ref,
            output_bundle_digest=result.output_bundle_digest,
            failure_category=result.failure_category,
            image_digest=result.image_digest,
            gpu_elapsed_seconds=result.gpu_elapsed_seconds,
            peak_gpu_memory_bytes=result.peak_gpu_memory_bytes,
            execution_elapsed_seconds=result.execution_elapsed_seconds,
        )
        job.lease_id = None  # lease released on settle
        self._record("record_result", result.task_id, result=result.status)

    def assert_active_lease(self, task_id: str, lease_id: str, fence: int, worker_id: str) -> None:
        """Artifact-transfer gate mirroring the PostgreSQL fencing check (F-4)."""
        self._enter("assert_active_lease", task_id)
        job = self._state.jobs.get(task_id)
        if (
            job is None
            or job.lease_id is None
            or job.lease_id != lease_id
            or job.fence != fence
            or job.worker_id != worker_id
        ):
            self._record("assert_active_lease", task_id, error="InvalidInputError")
            raise InvalidInputError(f"stale or missing lease for task {task_id}: result rejected")
        self._record("assert_active_lease", task_id, result="ok")

    def request_cancel(self, task_id: str) -> None:
        self._enter("request_cancel", task_id)
        job = self._state.jobs.get(task_id)
        if job is not None:
            job.cancel = True
        self._record("request_cancel", task_id)

    def cancel_requested(self, task_id: str) -> bool:
        self._enter("cancel_requested", task_id)
        job = self._state.jobs.get(task_id)
        return bool(job and job.cancel)

    def claimed_by(self, task_id: str) -> str | None:
        """M17 timeout classification input: worker holding/that held the job."""
        self._enter("claimed_by", task_id)
        job = self._state.jobs.get(task_id)
        return job.worker_id if job is not None else None

    # --- test helpers (not part of the Port) ---
    def seed(self, task_id: str, spec: ExecutionSpec, *, capability: str = "docker") -> None:
        """Register a job under an existing task_id (mirrors PG enqueue writing
        the shared `tasks` row that claim_next reads)."""
        self._state.jobs[task_id] = _Job(
            task_id=task_id,
            spec=spec,
            run_id=task_id,
            capability=capability,
            partition=None,
            idempotency_key=f"seed-{task_id}",
        )

    def assign(self, task_id: str, *, worker_id: str, lease_id: str, fence: int) -> None:
        job = self._state.jobs.get(task_id)
        if job is not None:
            job.worker_id = worker_id
            job.lease_id = lease_id
            job.fence = fence
            job.status = ResearchTaskState.State.LEASED
