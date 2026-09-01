"""Worker gateway production composition (M16 re-audit F-3).

Assembles a deployable `/worker/v1` gateway from PostgreSQL adapters + the
shared CredentialResolver, mirroring `build_postgres_assembly` for the Control
Plane. Each adapter owns its own PG connection (the gateway serves concurrent
worker sessions; a single connection is not shareable across threads). TLS
fail-closed for non-loopback binds is enforced inside `create_worker_app`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from packages.application.ports.credential_resolver import CredentialResolver
from services.api.worker_gateway.app import create_worker_app
from services.api.worker_gateway.deps import WorkerGatewayDeps
from services.api.worker_gateway.settings import WorkerGatewaySettings


def build_worker_gateway_deps(  # noqa: PLR0913 - keyword-only composition inputs
    *,
    dsn: str,
    credentials: CredentialResolver,
    settings: WorkerGatewaySettings | None = None,
    bind_host: str = "127.0.0.1",
    blob_dir: str | Path | None = None,
    lease_ttl_seconds: int = 60,
) -> WorkerGatewayDeps:
    """Build the full job-plane gateway deps from a PG DSN (per-adapter conns)."""
    from adapters.postgres.artifact_store import PostgresArtifactStore
    from adapters.postgres.execution_job_queue import PostgresExecutionJobQueue
    from adapters.postgres.worker_registry import PostgresWorkerRegistry
    from adapters.postgres.workflow_engine import PostgresWorkflowEngine

    resolved_blob = blob_dir or os.environ.get("RESEARCHOS_WORKER_ARTIFACT_BLOB_DIR")
    return WorkerGatewayDeps(
        registry=PostgresWorkerRegistry(dsn=dsn),
        credentials=credentials,
        settings=settings or WorkerGatewaySettings.from_env(),
        bind_host=bind_host,
        workflow=PostgresWorkflowEngine(dsn=dsn, lease_ttl_seconds=lease_ttl_seconds),
        job_queue=PostgresExecutionJobQueue(dsn=dsn),
        artifacts=PostgresArtifactStore(dsn=dsn, blob_dir=resolved_blob),
    )


def build_gateway_from_env() -> tuple[Any, str, int]:
    """Resolve (asgi_app, host, port) from the environment for `python -m`."""
    from adapters.postgres.db import dsn_from_env
    from adapters.relay.registry_credential_resolver import RegistryCredentialResolver

    dsn = dsn_from_env()
    if not dsn:
        raise RuntimeError("worker gateway requires RESEARCHOS_POSTGRES_DSN / DATABASE_URL")
    host = os.environ.get("RESEARCHOS_WORKER_GATEWAY_HOST", "127.0.0.1")
    port = int(os.environ.get("RESEARCHOS_WORKER_GATEWAY_PORT", "8081"))
    deps = build_worker_gateway_deps(
        dsn=dsn, credentials=RegistryCredentialResolver(), bind_host=host
    )
    return create_worker_app(deps), host, port
