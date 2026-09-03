"""M16 re-audit F-3: production composition for the worker plane.

Covers the Control-Plane reaper wiring (LOST detection must run in production,
not only in the test harness) and the gateway composition factory.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any, cast

import pytest

from adapters.fakes.worker_registry import FakeWorkerRegistry
from packages.application.ports.credential_resolver import CredentialResolver
from services.api.app import _start_worker_reaper
from services.api.scheduler import WorkerReaperScheduler
from services.api.worker_gateway.composition import (
    build_gateway_from_env,
    build_worker_gateway_deps,
)
from services.api.worker_gateway.settings import WorkerGatewaySettings


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
        ),
    )


def test_reaper_not_started_without_worker_registry() -> None:
    deps = SimpleNamespace(worker_registry=None, telemetry=None)
    assert _start_worker_reaper(deps) is None  # type: ignore[arg-type]


def test_reaper_started_when_registry_present() -> None:
    deps = SimpleNamespace(worker_registry=FakeWorkerRegistry(), telemetry=None)
    sched = _start_worker_reaper(deps)  # type: ignore[arg-type]
    assert isinstance(sched, WorkerReaperScheduler)
    sched.stop()


def test_gateway_from_env_requires_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    import adapters.postgres.db as pgdb

    monkeypatch.setattr(pgdb, "dsn_from_env", lambda: None)
    monkeypatch.delenv("RESEARCHOS_POSTGRES_DSN", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="RESEARCHOS_POSTGRES_DSN"):
        build_gateway_from_env()


@pytest.mark.postgres
def test_gateway_deps_composition_builds_job_plane() -> None:
    from services.api.worker_gateway.app import create_worker_app

    creds = SimpleNamespace()  # resolver only consulted on register; not here
    deps: Any = build_worker_gateway_deps(
        dsn=_dsn(),
        credentials=cast(CredentialResolver, creds),
        settings=WorkerGatewaySettings(enrollment_credential_ref="WORKER_ENROLLMENT_SECRET"),
        bind_host="127.0.0.1",
    )
    assert deps.workflow is not None and deps.job_queue is not None and deps.artifacts is not None
    app = create_worker_app(deps)
    assert app is not None
    for adapter in (deps.registry, deps.workflow, deps.job_queue, deps.artifacts):
        adapter.close()


@pytest.mark.postgres
def test_gateway_composition_reads_blob_dir_env(monkeypatch: pytest.MonkeyPatch) -> None:
    import tempfile

    blob = os.path.join(tempfile.mkdtemp(prefix="gw-blobs-"), "blobs")
    monkeypatch.setenv("RESEARCHOS_WORKER_ARTIFACT_BLOB_DIR", blob)
    deps: Any = build_worker_gateway_deps(
        dsn=_dsn(), credentials=cast(CredentialResolver, SimpleNamespace())
    )
    assert str(deps.artifacts._blob_root) == blob  # noqa: SLF001 - composition assertion
    for adapter in (deps.registry, deps.workflow, deps.job_queue, deps.artifacts):
        adapter.close()


@pytest.mark.postgres
def test_api_assembly_reads_artifact_blob_dir_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """PA-1: the control-plane ArtifactStore blob root is configurable via
    RESEARCHOS_ARTIFACT_BLOB_DIR (settings → PgAssemblyConfig → store)."""
    import tempfile

    from services.api.composition import assemble
    from services.api.settings import ApiSettings

    blob = os.path.join(tempfile.mkdtemp(prefix="api-blobs-"), "blobs")
    monkeypatch.setenv("RESEARCHOS_ARTIFACT_BLOB_DIR", blob)
    monkeypatch.setenv("RESEARCHOS_DATABASE_URL", _dsn())
    settings = ApiSettings.from_env()
    assert settings.artifact_blob_dir == blob
    deps: Any = assemble(settings)
    try:
        assert str(deps.artifacts._blob_root) == blob  # noqa: SLF001 - composition assertion
    finally:
        deps.close()
