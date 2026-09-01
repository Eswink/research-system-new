"""Worker gateway job routes: claim + result (M16 WP3).

Mounted only when the gateway has the job plane (workflow + job_queue). The
worker claims its next EXECUTION job and submits a normalized result; the
Control Plane validates the fencing identity `(task_id, lease_id, fence)`
before any authoritative write (M16 §8). The job descriptor carries the spec +
input bundle only — never the session token or DB credentials.
"""

from __future__ import annotations

from fastapi import Header, Request, Response

from packages.application.ports.errors import InvalidInputError
from packages.application.ports.execution_job_queue import ExecutionJobResult
from packages.application.ports.workflow_engine import ClaimRequest
from packages.domain.workers import WorkerRegistration, WorkerState
from services.api.errors import ApiError
from services.api.worker_gateway import security
from services.api.worker_gateway.dto import (
    ClaimRequestDto,
    JobDescriptorDto,
    ResultAckDto,
    ResultSubmissionDto,
)


def _require_job_plane(request: Request) -> None:
    deps = security.deps_of(request)
    if deps.workflow is None or deps.job_queue is None:
        raise ApiError(503, "Job Plane Unavailable", "worker gateway job plane not configured")


def _authorized_identity(
    request: Request, authorization: str | None, worker_id: str, generation: int
) -> WorkerRegistration:
    identity = security.authenticate(request, authorization)
    if identity.worker_id != worker_id:
        raise ApiError(401, "Unauthorized", "worker_id does not match session identity")
    if identity.registration_generation != generation:
        raise ApiError(401, "Unauthorized", "stale registration generation")
    return identity


def _require_schedulable(identity: WorkerRegistration, payload: ClaimRequestDto) -> None:
    """Server-side scheduling authority (M16 re-audit F-1 / ADR-0027 §2).

    The Control Plane — not the worker — decides who may claim: a non-READY
    (DRAINING/LOST/OFFLINE/REGISTERING) session is refused, and a claim may
    never assert capabilities or partition slots beyond what the worker
    registered at handshake (fail closed, no silent clamping).
    """
    if identity.state not in WorkerState.schedulable():
        raise ApiError(
            409, "Worker Not Schedulable", f"worker state {identity.state!r} cannot claim work"
        )
    if not frozenset(payload.capabilities) <= identity.capabilities:
        raise ApiError(
            409, "Capability Mismatch", "claimed capabilities exceed worker registration"
        )
    if not frozenset(payload.partitions) <= identity.partition_slots:
        raise ApiError(409, "Partition Mismatch", "claimed partitions exceed worker registration")


def _require_output_provenance(
    request: Request, worker_id: str, task_id: str, output_bundle_ref: str
) -> None:
    """Server-side provenance gate (M16 re-audit F-4 / ADR-0027 §1).

    The worker's claimed `output_bundle_ref` is only accepted when the stored
    Artifact provenance shows THIS authenticated worker uploaded it for THIS
    exact task (see transfer.upload_bundle). A fence-holding worker cannot
    present another task's — or another worker's — bundle as its own output.
    """
    deps = security.deps_of(request)
    if deps.artifacts is None:
        raise ApiError(503, "Artifact Store Unavailable", "artifact store not configured")
    meta = deps.artifacts.meta(output_bundle_ref)
    expected = f"worker:{worker_id}:{task_id}"
    if meta is None or meta.created_by != expected:
        raise ApiError(
            409,
            "Artifact Provenance Rejected",
            "output bundle was not uploaded by this worker for this task",
        )


async def claim_job(
    request: Request,
    payload: ClaimRequestDto,
    authorization: str | None = Header(default=None),
) -> Response:
    _require_job_plane(request)
    identity = _authorized_identity(
        request, authorization, payload.worker_id, payload.registration_generation
    )
    _require_schedulable(identity, payload)
    deps = security.deps_of(request)
    workflow = deps.workflow
    job_queue = deps.job_queue
    assert workflow is not None and job_queue is not None  # guarded by _require_job_plane
    lease = workflow.claim_next(
        ClaimRequest(
            worker_id=payload.worker_id,
            capabilities=frozenset(payload.capabilities),
            partitions=frozenset(payload.partitions),
        )
    )
    if lease is None:
        return Response(status_code=204)
    descriptor = job_queue.describe(lease.task_id)
    if descriptor is None:
        raise ApiError(500, "Job Descriptor Missing", "claimed task has no execution payload")
    body = JobDescriptorDto(
        task_id=lease.task_id,
        lease_id=lease.lease_id,
        fence=lease.fence,
        spec_json=descriptor.spec_json,
        input_bundle_ref=descriptor.input_bundle_ref,
        input_bundle_digest=descriptor.input_bundle_digest,
        cancel_requested=job_queue.cancel_requested(lease.task_id),
    )
    return _json_response(body)


async def submit_result(
    request: Request,
    task_id: str,
    payload: ResultSubmissionDto,
    authorization: str | None = Header(default=None),
) -> ResultAckDto:
    _require_job_plane(request)
    identity = _authorized_identity(
        request, authorization, payload.worker_id, payload.registration_generation
    )
    deps = security.deps_of(request)
    job_queue = deps.job_queue
    assert job_queue is not None  # guarded by _require_job_plane
    if payload.output_bundle_ref:
        _require_output_provenance(request, identity.worker_id, task_id, payload.output_bundle_ref)
    try:
        job_queue.record_result(
            ExecutionJobResult(
                task_id=task_id,
                lease_id=payload.lease_id,
                fence=payload.fence,
                status=payload.status,
                # identity binding: the authenticated session identity (not a
                # client-asserted field) must equal leases.worker_id
                worker_id=identity.worker_id,
                exit_code=payload.exit_code,
                stdout_digest=payload.stdout_digest,
                stderr_digest=payload.stderr_digest,
                output_bundle_ref=payload.output_bundle_ref,
                output_bundle_digest=payload.output_bundle_digest,
                failure_category=payload.failure_category,
            )
        )
    except InvalidInputError as exc:
        # stale fence / lease: reject the late result (scenario C)
        raise ApiError(409, "Stale Result Rejected", str(exc)) from exc
    return ResultAckDto(accepted=True, task_id=task_id)


async def renew_job(
    request: Request,
    task_id: str,
    authorization: str | None = Header(default=None),
    x_lease_id: str | None = Header(default=None),
    x_fence: str | None = Header(default=None),
) -> Response:
    """Extend an in-flight EXECUTION lease (M16 re-audit F-7).

    A worker renews while executing a long job so its lease is not expired and
    reclaimed mid-flight. The renewal is gated on the same fencing identity as
    result writes and also refreshes the worker heartbeat (server time), so the
    reaper does not mark a busy-but-alive worker LOST. Returns 204 on success.
    """
    _require_job_plane(request)
    identity = security.authenticate(request, authorization)
    if not x_lease_id or x_fence is None:
        raise ApiError(422, "Unprocessable Entity", "renew requires lease/fence headers")
    try:
        fence_value = int(x_fence)
    except ValueError as exc:
        raise ApiError(422, "Unprocessable Entity", "fence header must be an integer") from exc
    deps = security.deps_of(request)
    workflow = deps.workflow
    assert workflow is not None  # guarded by _require_job_plane
    try:
        workflow.renew_lease(task_id, x_lease_id, fence_value, identity.worker_id)
    except InvalidInputError as exc:
        raise ApiError(409, "Stale Lease Rejected", str(exc)) from exc
    deps.registry.heartbeat(identity.worker_id, identity.registration_generation)
    return Response(status_code=204)


def _json_response(body: JobDescriptorDto) -> Response:
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=200, content=body.model_dump())
