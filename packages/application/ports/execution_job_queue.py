"""ExecutionJobQueue Port: submit / poll / settle remote EXECUTION jobs (M16).

This is the Control-Plane-side view of the single queue for remote execution.
It does NOT create a second queue: `enqueue` writes a `tasks` row with
`kind='EXECUTION'` (the one queue) plus an `execution_jobs` payload projection,
and `record_result` is called by the worker gateway only after it has validated
the `(task_id, lease_id, fence)` triple against the active lease. `poll` reads
the settled outcome so `RemoteExecutionBackend` can normalize an ExecutionRun.

Ownership/fencing authority stays in `WorkflowEngine`/`leases`; this port only
carries the execution-specific payload and the settle transition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from packages.domain.workspace import ExecutionSpec


@dataclass(frozen=True, slots=True)
class ExecutionJobRequest:
    """Enqueue payload for one remote execution job."""

    spec: ExecutionSpec
    run_id: str
    capability: str
    idempotency_key: str
    input_bundle_ref: str | None = None
    input_bundle_digest: str | None = None
    partition: int | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must not be empty")
        if not self.capability:
            raise ValueError("capability must not be empty")
        if not self.idempotency_key:
            raise ValueError("idempotency_key must not be empty")


@dataclass(frozen=True, slots=True)
class ExecutionJobResult:
    """A worker's settled execution result (gateway writes after fence check).

    `worker_id` is the authenticated session identity — the write is rejected
    unless it equals `leases.worker_id` (identity binding, ADR-0027 §1).
    """

    task_id: str
    lease_id: str
    fence: int
    status: str
    worker_id: str | None = None
    exit_code: int | None = None
    stdout_digest: str | None = None
    stderr_digest: str | None = None
    output_bundle_ref: str | None = None
    output_bundle_digest: str | None = None
    failure_category: str | None = None


@dataclass(frozen=True, slots=True)
class ExecutionJobOutcome:
    task_id: str
    status: str  # QUEUED / LEASED / SUCCEEDED / FAILED / CANCELLED / TIMED_OUT
    fence: int = 0
    worker_id: str | None = None
    exit_code: int | None = None
    stdout_digest: str | None = None
    stderr_digest: str | None = None
    output_bundle_ref: str | None = None
    output_bundle_digest: str | None = None
    failure_category: str | None = None


@dataclass(frozen=True, slots=True)
class ExecutionJobDescriptor:
    """Read-only view of a claimed job's inputs for the worker."""

    task_id: str
    spec_json: str
    input_bundle_ref: str | None = None
    input_bundle_digest: str | None = None
    timeout_seconds: int | None = None


@runtime_checkable
class ExecutionJobQueue(Protocol):
    """Remote execution job lifecycle on the single canonical queue."""

    def enqueue(self, request: ExecutionJobRequest) -> str:
        """Create an EXECUTION task + payload row; return the task_id.

        Idempotent on `request.idempotency_key`: re-enqueue returns the
        existing id.
        """
        ...

    def describe(self, task_id: str) -> ExecutionJobDescriptor | None:
        """Inputs for a claimed job (spec + input bundle), or None if unknown."""
        ...

    def poll(self, task_id: str) -> ExecutionJobOutcome | None:
        """Current settled outcome, or None while the job is still in flight."""
        ...

    def record_result(self, result: ExecutionJobResult) -> None:
        """Persist a worker's execution result (gateway calls after fence check)."""
        ...

    def assert_active_lease(self, task_id: str, lease_id: str, fence: int, worker_id: str) -> None:
        """Raise InvalidInputError unless (task_id, lease_id, fence) is the
        active lease AND `leases.worker_id == worker_id`.

        The gateway gates artifact transfer on the same fencing identity as
        result writes (M16 re-audit F-4), so a bundle can only be uploaded or
        fetched by the worker that currently holds the job's lease.
        """
        ...

    def request_cancel(self, task_id: str) -> None:
        """Cooperative cancel flag for an in-flight job."""
        ...

    def cancel_requested(self, task_id: str) -> bool:
        """Whether a cancel has been requested (worker polls this)."""
        ...
