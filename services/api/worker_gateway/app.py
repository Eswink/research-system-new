"""Worker gateway ASGI app (M16 WP1/WP3 / ADR-0027).

A standalone FastAPI app exposing `/worker/v1`. It can be mounted into the
main Control Plane app for single-process dev, or bound to its own address in
production. Workers authenticate with a session token issued at registration;
the enrollment secret gates only the registration handshake.

Authorization stays in the Control Plane: this app never executes work itself.
The lifecycle routes record facts into the `WorkerRegistry`; the job routes
(claim/result) are mounted only when the gateway has the job plane
(workflow + job_queue) and validate fencing before any authoritative write.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, Header, Request

from packages.domain.core import Timestamp
from packages.domain.workers import (
    GPU_CAPABILITY,
    WorkerGpuObservation,
    WorkerRegistration,
    WorkerState,
)
from services.api.errors import ApiError, register_error_handlers
from services.api.worker_gateway import auth, jobs, security, transfer
from services.api.worker_gateway.deps import WorkerGatewayDeps
from services.api.worker_gateway.dto import (
    BundleUploadAckDto,
    HeartbeatRequest,
    HeartbeatResponse,
    JobDescriptorDto,
    ResultAckDto,
    WorkerRegisterRequest,
    WorkerRegisterResponse,
)
from services.api.worker_gateway.settings import WorkerGatewaySettings


def _gpu_observation_of(payload: WorkerRegisterRequest) -> WorkerGpuObservation | None:
    """M17 fail-closed handshake: declaring `gpu` REQUIRES a probe observation.

    An observation without the `gpu` capability is also refused — the worker
    either publishes its probe as a schedulable capability, or registers
    CPU-only without any observation (probe failed → never guessed).
    """
    if payload.gpu_observation is None:
        if GPU_CAPABILITY in set(payload.capabilities):
            raise ApiError(
                409,
                "GPU Observation Required",
                f"capability {GPU_CAPABILITY!r} requires a gpu_observation probe result",
            )
        return None
    if GPU_CAPABILITY not in set(payload.capabilities):
        raise ApiError(
            409,
            "GPU Capability Mismatch",
            "gpu_observation requires the 'gpu' capability in this registration",
        )
    try:
        dto = payload.gpu_observation
        return WorkerGpuObservation(
            device_name=dto.device_name,
            device_count=dto.device_count,
            driver_version=dto.driver_version,
            cuda_runtime_version=dto.cuda_runtime_version,
            total_vram_bytes=dto.total_vram_bytes,
            framework=dto.framework,
            probed_at=Timestamp(datetime.fromisoformat(dto.probed_at)),
            probe_digest=dto.probe_digest,
        )
    except (TypeError, ValueError) as exc:
        raise ApiError(422, "Unprocessable Entity", f"invalid gpu_observation: {exc}") from exc


def _handshake_and_build(
    payload: WorkerRegisterRequest, settings: WorkerGatewaySettings
) -> WorkerRegistration:
    """Fail-closed protocol/backend handshake + bounded registration build."""
    if payload.protocol_version not in settings.supported_protocol_versions:
        raise ApiError(
            409,
            "Protocol Mismatch",
            f"worker protocol_version {payload.protocol_version!r} unsupported",
        )
    unsupported = set(payload.backend_kinds) - set(settings.supported_backend_kinds)
    if unsupported or not payload.backend_kinds:
        raise ApiError(
            409,
            "Protocol Mismatch",
            f"worker backend kinds unsupported: {sorted(unsupported) or payload.backend_kinds}",
        )
    try:
        return WorkerRegistration(
            worker_id=payload.worker_id,
            protocol_version=payload.protocol_version,
            runtime_version=payload.runtime_version,
            capabilities=frozenset(payload.capabilities),
            backend_kinds=frozenset(payload.backend_kinds),
            platform=payload.platform,
            partition_slots=frozenset(payload.partition_slots),
            max_concurrency=payload.max_concurrency,
            gpu_observation=_gpu_observation_of(payload),
        )
    except ValueError as exc:  # bounded-field violation → 422
        raise ApiError(422, "Unprocessable Entity", str(exc)) from exc


async def _register_body(
    request: Request,
    payload: WorkerRegisterRequest,
    x_worker_enrollment: str | None = Header(default=None),
) -> WorkerRegisterResponse:
    security.require_enrollment(request, x_worker_enrollment)
    settings = security.deps_of(request).settings
    registration = _handshake_and_build(payload, settings)
    registry = security.registry_of(request)
    stored = registry.register(registration)
    token = auth.generate_session_token()
    registry.set_session_token(
        stored.worker_id, stored.registration_generation, auth.hash_session_token(token)
    )
    ready = registry.transition(stored.worker_id, WorkerState.Transition.HANDSHAKE_OK)
    return WorkerRegisterResponse(
        worker_id=ready.worker_id,
        registration_generation=ready.registration_generation,
        state=ready.state,
        session_token=token,
        heartbeat_interval_seconds=settings.heartbeat_interval_seconds,
        stale_threshold_seconds=settings.stale_threshold_seconds,
    )


async def _heartbeat_body(
    request: Request,
    payload: HeartbeatRequest,
    authorization: str | None = Header(default=None),
) -> HeartbeatResponse:
    identity = security.authenticate(request, authorization)
    if payload.worker_id != identity.worker_id:
        raise ApiError(401, "Unauthorized", "worker_id does not match session identity")
    if payload.registration_generation != identity.registration_generation:
        raise ApiError(401, "Unauthorized", "stale registration generation")
    registry = security.registry_of(request)
    accepted = registry.heartbeat(payload.worker_id, payload.registration_generation)
    current = registry.get(payload.worker_id)
    state = current.state if current is not None else "UNKNOWN"
    drain = current.drain_requested if current is not None else False
    return HeartbeatResponse(accepted=accepted, state=state, drain_requested=drain)


async def _health() -> dict[str, str]:
    return {"status": "ok"}


def create_worker_app(deps: WorkerGatewayDeps) -> FastAPI:
    """Build the worker gateway app; refuses non-loopback bind without TLS."""
    auth.assert_bind_allowed(deps.bind_host, require_tls=deps.settings.require_tls)
    app = FastAPI(
        title="Research OS Worker Gateway",
        description="Untrusted worker lifecycle + job plane (M16 / ADR-0027)",
        version="v1",
    )
    app.state.worker_deps = deps
    register_error_handlers(app)
    app.add_api_route("/worker/v1/health", _health, methods=["GET"])
    app.add_api_route(
        "/worker/v1/register",
        _register_body,
        methods=["POST"],
        response_model=WorkerRegisterResponse,
    )
    app.add_api_route(
        "/worker/v1/heartbeat",
        _heartbeat_body,
        methods=["POST"],
        response_model=HeartbeatResponse,
    )
    if deps.workflow is not None and deps.job_queue is not None:
        app.add_api_route(
            "/worker/v1/claim", jobs.claim_job, methods=["POST"], response_model=JobDescriptorDto
        )
        app.add_api_route(
            "/worker/v1/tasks/{task_id}/result",
            jobs.submit_result,
            methods=["POST"],
            response_model=ResultAckDto,
        )
        app.add_api_route("/worker/v1/tasks/{task_id}/renew", jobs.renew_job, methods=["POST"])
    if deps.artifacts is not None:
        app.add_api_route(
            "/worker/v1/artifacts/{artifact_id}", transfer.download_bundle, methods=["GET"]
        )
        app.add_api_route(
            "/worker/v1/artifacts",
            transfer.upload_bundle,
            methods=["POST"],
            response_model=BundleUploadAckDto,
        )
    return app
