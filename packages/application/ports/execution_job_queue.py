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
from decimal import Decimal
from typing import Protocol, runtime_checkable

from packages.application.ports.errors import InvalidInputError
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
    # M17: the worker's DockerExecutionBackend resolves the actual image digest
    # it ran; propagating it back binds remote reproducibility (the local
    # DockerExecutionBackend already carries it in compute_usage_summary).
    image_digest: str | None = None
    # M17: GPU observations (framework-reliable quantities only) flow back so
    # the remote path feeds the same single experiment usage ledger as local.
    gpu_elapsed_seconds: int | Decimal | None = None
    peak_gpu_memory_bytes: int | None = None
    execution_elapsed_seconds: int | Decimal | None = None


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
    image_digest: str | None = None
    gpu_elapsed_seconds: int | Decimal | None = None
    peak_gpu_memory_bytes: int | None = None
    execution_elapsed_seconds: int | Decimal | None = None


_TERMINAL_STATUSES = ("SUCCEEDED", "FAILED", "TIMED_OUT", "CANCELLED")


def canonical_task_status(status: str) -> str:
    """Closed-set terminal validation shared by every ExecutionJobQueue impl.

    `status` is worker-supplied and therefore untrusted (ADR-0027 §1): only
    terminal execution statuses may be persisted, so a fence-holding worker
    cannot resurrect a settled job as QUEUED or strand it in an unknown state.
    M17 WP4c: a worker-reported CANCELLED (cooperative cancel convergence) is
    preserved as CANCELLED — collapsing it into FAILED lost the cancellation
    semantic. TIMED_OUT records as FAILED (worker-side timeout, not a
    Control-Plane cancel).
    """
    if status not in _TERMINAL_STATUSES:
        raise InvalidInputError(f"invalid result status {status!r}: not a terminal execution state")
    if status == "SUCCEEDED":
        return "SUCCEEDED"
    if status == "CANCELLED":
        return "CANCELLED"
    return "FAILED"


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

    def claimed_by(self, task_id: str) -> str | None:
        """The worker currently holding (or that held) the job's lease.

        M17 timeout classification: a GPU job that times out while NEVER
        claimed is GPU_UNAVAILABLE (no worker could run it), while a
        claimed-then-slow job is a plain timeout. `None` means unclaimed
        or unknown.
        """
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
