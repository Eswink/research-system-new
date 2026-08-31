"""Worker gateway authentication primitives (M16 WP1 / ADR-0027).

Trust model: workers are untrusted. Enrollment uses a pre-shared secret
(constant-time compare); after a successful handshake the gateway issues a
256-bit session token that is stored ONLY as a sha256 digest, bound to the
worker's current `registration_generation`. Re-registration mints a new
generation and voids the previous token (anti-replay).

No plaintext token is ever persisted, logged, or returned more than once.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def generate_session_token() -> str:
    """256-bit URL-safe session token (returned to the worker exactly once)."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """sha256 hex digest of a session token (the only form ever stored)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_enrollment(provided: str | None, expected: str) -> bool:
    """Constant-time enrollment secret check; missing/empty never matches."""
    if not provided or not expected:
        return False
    return hmac.compare_digest(provided, expected)


def extract_bearer(authorization: str | None) -> str | None:
    """Return the bearer token from an `Authorization: Bearer <t>` header."""
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def is_loopback_host(host: str) -> bool:
    """True for loopback/wildcard binds used by local tests."""
    return host in _LOOPBACK_HOSTS or host.startswith("127.")


class WorkerGatewayTlsError(RuntimeError):
    """Raised when a non-loopback bind is attempted without TLS (fail closed)."""


def assert_bind_allowed(host: str, *, require_tls: bool) -> None:
    """Refuse to start a non-loopback worker gateway without TLS.

    Mirrors the M15 collector loopback-only posture: plaintext worker traffic
    (which carries session tokens) may only bind loopback. Production sets
    `RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS=1` and terminates TLS upstream.
    """
    if not is_loopback_host(host) and not require_tls:
        raise WorkerGatewayTlsError(
            f"worker gateway bind {host!r} is non-loopback and TLS is not enabled; "
            "refusing to start (set RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS=1 with a "
            "TLS-terminating front-end, or bind loopback for local tests)"
        )
