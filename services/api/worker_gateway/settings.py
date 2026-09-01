"""Worker gateway configuration (M16 WP1).

Independent configuration surface from the Control Plane API: the worker
gateway is a separate trust domain (ADR-0027). Enrollment secret is resolved
through the shared `CredentialResolver` under a WORKER-scoped ref, never
hardcoded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

_DEFAULT_ENROLLMENT_REF = "WORKER_ENROLLMENT_SECRET"
_DEFAULT_HEARTBEAT_INTERVAL = 10.0
_DEFAULT_STALE_THRESHOLD = 30.0
_DEFAULT_MAX_RESULT_BYTES = 1_000_000
# M17 WP1 freshness layer 2: GPU observations older than this (server clock)
# cannot claim `gpu` work. Re-probe cadence on the worker stays well inside it.
_DEFAULT_GPU_TTL_SECONDS = 900.0


def _env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True, slots=True)
class WorkerGatewaySettings:
    """Worker gateway settings; TLS is required for any non-loopback bind."""

    enrollment_credential_ref: str = _DEFAULT_ENROLLMENT_REF
    require_tls: bool = False
    heartbeat_interval_seconds: float = _DEFAULT_HEARTBEAT_INTERVAL
    stale_threshold_seconds: float = _DEFAULT_STALE_THRESHOLD
    max_result_bytes: int = _DEFAULT_MAX_RESULT_BYTES
    gpu_observation_ttl_seconds: float = _DEFAULT_GPU_TTL_SECONDS
    supported_protocol_versions: frozenset[str] = field(default_factory=lambda: frozenset({"1"}))
    supported_backend_kinds: frozenset[str] = field(default_factory=lambda: frozenset({"DOCKER"}))

    def __post_init__(self) -> None:
        if not self.enrollment_credential_ref:
            raise ValueError("enrollment_credential_ref must not be empty")
        if self.heartbeat_interval_seconds <= 0:
            raise ValueError("heartbeat_interval_seconds must be > 0")
        if self.stale_threshold_seconds <= self.heartbeat_interval_seconds:
            raise ValueError("stale_threshold_seconds must exceed heartbeat interval")
        if self.max_result_bytes <= 0:
            raise ValueError("max_result_bytes must be > 0")
        if self.gpu_observation_ttl_seconds <= 0:
            raise ValueError("gpu_observation_ttl_seconds must be > 0")
        if not self.supported_protocol_versions:
            raise ValueError("supported_protocol_versions must not be empty")

    @classmethod
    def from_env(cls) -> WorkerGatewaySettings:
        protocols = os.environ.get("RESEARCHOS_WORKER_PROTOCOL_VERSIONS", "1")
        backends = os.environ.get("RESEARCHOS_WORKER_BACKEND_KINDS", "DOCKER")
        return cls(
            enrollment_credential_ref=os.environ.get(
                "RESEARCHOS_WORKER_ENROLLMENT_REF", _DEFAULT_ENROLLMENT_REF
            ).strip(),
            require_tls=_env_flag("RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS"),
            heartbeat_interval_seconds=float(
                os.environ.get("RESEARCHOS_WORKER_HEARTBEAT_INTERVAL", _DEFAULT_HEARTBEAT_INTERVAL)
            ),
            stale_threshold_seconds=float(
                os.environ.get("RESEARCHOS_WORKER_STALE_THRESHOLD", _DEFAULT_STALE_THRESHOLD)
            ),
            max_result_bytes=int(
                os.environ.get("RESEARCHOS_WORKER_MAX_RESULT_BYTES", _DEFAULT_MAX_RESULT_BYTES)
            ),
            gpu_observation_ttl_seconds=float(
                os.environ.get(
                    "RESEARCHOS_WORKER_GPU_OBSERVATION_TTL", _DEFAULT_GPU_TTL_SECONDS
                )
            ),
            supported_protocol_versions=frozenset(
                p.strip() for p in protocols.split(",") if p.strip()
            ),
            supported_backend_kinds=frozenset(b.strip() for b in backends.split(",") if b.strip()),
        )
