"""Worker gateway request security helpers (M16 WP1/WP3).

Shared by the lifecycle routes (register/heartbeat) and the job routes
(claim/result): bearer-token authentication resolves the worker's current
generation identity, and enrollment gates registration only.
"""

from __future__ import annotations

from typing import cast

from fastapi import Request

from packages.application.ports.credential_resolver import CredentialResolver
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.worker_registry import WorkerRegistry
from packages.domain.workers import WorkerRegistration
from services.api.errors import ApiError
from services.api.worker_gateway import auth
from services.api.worker_gateway.deps import WorkerGatewayDeps


def deps_of(request: Request) -> WorkerGatewayDeps:
    return cast(WorkerGatewayDeps, request.app.state.worker_deps)


def registry_of(request: Request) -> WorkerRegistry:
    return deps_of(request).registry


def require_enrollment(request: Request, enrollment: str | None) -> None:
    deps = deps_of(request)
    resolver: CredentialResolver = deps.credentials
    try:
        expected = resolver.resolve(deps.settings.enrollment_credential_ref).value
    except InvalidInputError as exc:
        raise ApiError(
            503, "Enrollment Unavailable", "worker enrollment secret not configured"
        ) from exc
    if not auth.verify_enrollment(enrollment, expected):
        raise ApiError(401, "Unauthorized", "invalid worker enrollment secret")


def authenticate(request: Request, authorization: str | None) -> WorkerRegistration:
    """Resolve bearer token to the current-generation worker identity."""
    token = auth.extract_bearer(authorization)
    if token is None:
        raise ApiError(401, "Unauthorized", "missing bearer session token")
    stored = registry_of(request).authenticate(auth.hash_session_token(token))
    if stored is None:
        raise ApiError(401, "Unauthorized", "invalid or revoked session token")
    return stored
