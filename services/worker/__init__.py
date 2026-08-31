"""Research OS worker process (M16). A worker is an untrusted execution party
that runs jobs through the Control Plane worker gateway. See ADR-0027."""

from __future__ import annotations

from services.worker.loop import WorkerLoop, WorkerLoopConfig

__all__ = ["WorkerLoop", "WorkerLoopConfig"]
