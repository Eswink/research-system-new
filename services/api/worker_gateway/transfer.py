"""Worker gateway artifact transfer routes (M16 WP3 / re-audit F-4, F-10).

The worker is untrusted and never holds ArtifactStore/DB credentials. Input
bundles are downloaded and output bundles uploaded through these authenticated
routes. Every transfer is gated on the SAME fencing identity as result writes
`(task_id, lease_id, fence)` + `leases.worker_id`, so a bundle can only be
moved by the worker that currently holds that job's lease (no cross-task or
cross-worker substitution). The ArtifactStore enforces content-addressing
(server-side digest verification) and the upload path enforces a body-size cap.
"""

from __future__ import annotations

from fastapi import Header, Request, Response

from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from services.api.errors import ApiError
from services.api.worker_gateway import security
from services.api.worker_gateway.dto import BundleUploadAckDto


def _lease_context(
    task_id: str | None, lease_id: str | None, fence: str | None
) -> tuple[str, str, int]:
    if not task_id or not lease_id or fence is None:
        raise ApiError(
            422, "Unprocessable Entity", "artifact transfer requires task/lease/fence headers"
        )
    try:
        fence_value = int(fence)
    except ValueError as exc:
        raise ApiError(422, "Unprocessable Entity", "fence header must be an integer") from exc
    return task_id, lease_id, fence_value


def _require_job_plane(request: Request) -> None:
    deps = security.deps_of(request)
    if deps.workflow is None or deps.job_queue is None:
        raise ApiError(503, "Job Plane Unavailable", "worker gateway job plane not configured")


async def _read_capped_body(request: Request, max_bytes: int) -> bytes:
    """Reject by Content-Length BEFORE buffering (memory DoS mitigation); a
    chunked request without a length still gets the post-buffer 413 below."""
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            length = int(declared)
        except ValueError:
            length = -1
        if length > max_bytes:
            raise ApiError(413, "Payload Too Large", "result bundle exceeds size limit")
    body = await request.body()
    if len(body) > max_bytes:
        raise ApiError(413, "Payload Too Large", "result bundle exceeds size limit")
    if not body:
        raise ApiError(422, "Unprocessable Entity", "empty bundle")
    return body


async def download_bundle(  # noqa: PLR0913 - FastAPI header/path parameters
    request: Request,
    artifact_id: str,
    authorization: str | None = Header(default=None),
    x_task_id: str | None = Header(default=None),
    x_lease_id: str | None = Header(default=None),
    x_fence: str | None = Header(default=None),
) -> Response:
    """Fetch a bundle only with an active lease on the owning task.

    Allowed: the leased task's declared input bundle, or an artifact this same
    worker uploaded (provenance `worker:{worker_id}:*`). Anything else is a
    cross-task/cross-worker read and is refused (F-4/F-10).
    """
    _require_job_plane(request)
    identity = security.authenticate(request, authorization)
    task_id, lease_id, fence = _lease_context(x_task_id, x_lease_id, x_fence)
    deps = security.deps_of(request)
    assert deps.job_queue is not None  # guarded by _require_job_plane
    try:
        deps.job_queue.assert_active_lease(task_id, lease_id, fence, identity.worker_id)
    except InvalidInputError as exc:
        raise ApiError(409, "Stale Lease Rejected", str(exc)) from exc
    if deps.artifacts is None:
        raise ApiError(503, "Artifact Store Unavailable", "artifact store not configured")
    descriptor = deps.job_queue.describe(task_id)
    meta = deps.artifacts.meta(artifact_id)
    allowed_input = descriptor is not None and descriptor.input_bundle_ref == artifact_id
    own_upload = meta is not None and str(meta.created_by or "").startswith(
        f"worker:{identity.worker_id}:"
    )
    if not (allowed_input or own_upload):
        raise ApiError(403, "Forbidden", "artifact not authorized for this lease")
    try:
        content = deps.artifacts.get(artifact_id)
    except Exception as exc:  # noqa: BLE001 - adapter raises many error types
        raise ApiError(404, "Artifact Not Found", "unknown or unreadable artifact") from exc
    return Response(content=content, media_type="application/octet-stream")


async def upload_bundle(
    request: Request,
    authorization: str | None = Header(default=None),
    x_task_id: str | None = Header(default=None),
    x_lease_id: str | None = Header(default=None),
    x_fence: str | None = Header(default=None),
) -> BundleUploadAckDto:
    """Store an output bundle bound to the caller's active lease (F-4).

    The stored provenance is `worker:{worker_id}:{task_id}`; `record_result`
    later refuses any `output_bundle_ref` not uploaded by this worker for this
    exact task, so one task's result cannot present another task's bundle.
    """
    _require_job_plane(request)
    identity = security.authenticate(request, authorization)
    task_id, lease_id, fence = _lease_context(x_task_id, x_lease_id, x_fence)
    deps = security.deps_of(request)
    assert deps.job_queue is not None  # guarded by _require_job_plane
    try:
        deps.job_queue.assert_active_lease(task_id, lease_id, fence, identity.worker_id)
    except InvalidInputError as exc:
        raise ApiError(409, "Stale Lease Rejected", str(exc)) from exc
    if deps.artifacts is None:
        raise ApiError(503, "Artifact Store Unavailable", "artifact store not configured")
    body = await _read_capped_body(request, deps.settings.max_result_bytes)
    digest = Digest.of_bytes(body)
    # Task-scoped id: content-addressing alone collides when two tasks produce
    # identical bytes, which would let the second upload overwrite the first's
    # provenance and break its result (M16 re-audit F-4). Binding the task keeps
    # each upload's provenance row unambiguous; dedup within one task still holds.
    artifact_id = f"bundle-{digest.hex_value[:32]}-{task_id}"
    deps.artifacts.put(
        Artifact(
            id=artifact_id,
            digest=digest,
            size_bytes=len(body),
            media_type="application/x-researchos-workspace-bundle",
            created_by=f"worker:{identity.worker_id}:{task_id}",
        ),
        body,
    )
    return BundleUploadAckDto(artifact_id=artifact_id, digest=str(digest))
