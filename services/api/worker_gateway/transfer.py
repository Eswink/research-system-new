"""Worker gateway artifact transfer routes (M16 WP3).

The worker is untrusted and never holds ArtifactStore/DB credentials. Input
bundles are downloaded and output bundles uploaded through these authenticated
routes; the ArtifactStore enforces content-addressing (server-side digest
verification) and the upload path enforces a body-size cap.
"""

from __future__ import annotations

from fastapi import Header, Request, Response

from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from services.api.errors import ApiError
from services.api.worker_gateway import security
from services.api.worker_gateway.dto import BundleUploadAckDto


async def download_bundle(
    request: Request, artifact_id: str, authorization: str | None = Header(default=None)
) -> Response:
    security.authenticate(request, authorization)  # any valid worker session may fetch inputs
    deps = security.deps_of(request)
    if deps.artifacts is None:
        raise ApiError(503, "Artifact Store Unavailable", "artifact store not configured")
    try:
        content = deps.artifacts.get(artifact_id)
    except Exception as exc:  # noqa: BLE001 - adapter raises many error types
        raise ApiError(404, "Artifact Not Found", "unknown or unreadable artifact") from exc
    return Response(content=content, media_type="application/octet-stream")


async def upload_bundle(
    request: Request, authorization: str | None = Header(default=None)
) -> BundleUploadAckDto:
    security.authenticate(request, authorization)
    deps = security.deps_of(request)
    if deps.artifacts is None:
        raise ApiError(503, "Artifact Store Unavailable", "artifact store not configured")
    # Reject by Content-Length BEFORE buffering the body (memory DoS mitigation;
    # chunked requests without a length still get the post-buffer 413 below).
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            length = int(declared)
        except ValueError:
            length = -1
        if length > deps.settings.max_result_bytes:
            raise ApiError(413, "Payload Too Large", "result bundle exceeds size limit")
    body = await request.body()
    if len(body) > deps.settings.max_result_bytes:
        raise ApiError(413, "Payload Too Large", "result bundle exceeds size limit")
    if not body:
        raise ApiError(422, "Unprocessable Entity", "empty bundle")
    digest = Digest.of_bytes(body)
    artifact_id = f"bundle-{digest.hex_value[:32]}"
    deps.artifacts.put(
        Artifact(
            id=artifact_id,
            digest=digest,
            size_bytes=len(body),
            media_type="application/x-researchos-workspace-bundle",
            created_by="worker",
        ),
        body,
    )
    return BundleUploadAckDto(artifact_id=artifact_id, digest=str(digest))
