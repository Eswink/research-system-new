"""Worker-side adapters (M16): the HTTP client a worker process uses to reach
the Control Plane worker gateway. Kept separate from `adapters.execution` so
the worker trust domain has its own import-linter boundary (`.importlinter.worker`).
"""

from __future__ import annotations

from adapters.worker.client import WorkerClient, WorkerClientConfig

__all__ = ["WorkerClient", "WorkerClientConfig"]
