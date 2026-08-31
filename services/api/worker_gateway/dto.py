"""Worker gateway DTOs (M16 WP1).

Independent from the Control Plane DTOs: worker input is treated as untrusted,
so every field is bounded and malformed payloads are rejected (422) before any
registry write.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from packages.domain.workers import (
    MAX_BACKEND_KINDS,
    MAX_CAPABILITIES,
    PARTITION_COUNT,
)


class WorkerRegisterRequest(BaseModel):
    """Registration handshake payload (bounded; not a hardware inventory)."""

    worker_id: str = Field(min_length=1, max_length=128)
    protocol_version: str = Field(min_length=1, max_length=64)
    runtime_version: str = Field(min_length=1, max_length=64)
    capabilities: list[str] = Field(default_factory=list, max_length=MAX_CAPABILITIES)
    backend_kinds: list[str] = Field(default_factory=list, max_length=MAX_BACKEND_KINDS)
    platform: str = Field(min_length=1, max_length=64)
    partition_slots: list[int] = Field(default_factory=list, max_length=PARTITION_COUNT)
    max_concurrency: int = Field(default=1, ge=1, le=64)


class WorkerRegisterResponse(BaseModel):
    """Returned once; `session_token` is never recoverable afterwards."""

    worker_id: str
    registration_generation: int
    state: str
    session_token: str
    heartbeat_interval_seconds: float
    stale_threshold_seconds: float


class HeartbeatRequest(BaseModel):
    worker_id: str = Field(min_length=1, max_length=128)
    registration_generation: int = Field(ge=0)


class HeartbeatResponse(BaseModel):
    accepted: bool
    state: str
    drain_requested: bool = False
