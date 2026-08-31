"""Worker gateway package (M16 WP1 / ADR-0027).

Public surface: `create_worker_app` + `WorkerGatewayDeps` + settings. Kept
separate from the Control Plane API so the worker trust domain has its own
auth dependency and DTOs.
"""

from __future__ import annotations

from services.api.worker_gateway.app import create_worker_app
from services.api.worker_gateway.deps import WorkerGatewayDeps
from services.api.worker_gateway.settings import WorkerGatewaySettings

__all__ = ["WorkerGatewayDeps", "WorkerGatewaySettings", "create_worker_app"]
