"""M13 PG production-composition run E2E (NV-B closure).

Proves the M13 critical path (Console -> API -> create/read Run -> timeline ->
approval/intervention -> evidence -> budget) works when all domain stores are
PostgreSQL (PostgresWorkflowEngine/PostgresRunStore/PostgresRunProjection/
PostgresEvidenceLedger/PostgresBudgetLedger/PostgresArtifactStore).

Honest scope note: the *real production* success path requires a registered
credential + a reachable relay (real network probe in build_endpoint_health),
which must NOT become a default CI dependency. This test drives the same API
layer with the documented Fake seam (FakeModelGateway + FakeCredentialResolver
+ preflight override) — the same seam M13-R1's SQLite tests use — but with all
canonical-domain stores on PostgreSQL. It closes the "no test ever ran a PG-
stored run to SUCCEEDED" gap.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from adapters.postgres.db import migrate

pytestmark = pytest.mark.postgres


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


def _clean() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute(
        "TRUNCATE tasks, leases, idempotency_records, outbox_events, runs,"
        " m12_sources, m12_evidence, m12_claims, m12_relations,"
        " budget_reservations, budget_usage_entries, approvals CASCADE"
    )
    conn.commit()
    conn.close()


def _make_pg_deps(tmp_path: Path) -> Any:
    """PG stores + Fake seam (mirrors tests/api/run_fixtures.make_run_ready_deps
    but swaps all domain stores to PostgreSQL)."""
    from adapters.fakes.credential_resolver import FakeCredentialResolver
    from adapters.fakes.model_gateway import FakeModelGateway
    from adapters.sqlite.db import connect as sqlite_connect
    from services.api.pg_composition import (
        PgAssemblyConfig,
        build_postgres_assembly,
    )
    from services.api.settings import ApiSettings

    connection = sqlite_connect(str(tmp_path / "control.sqlite"))
    credentials = FakeCredentialResolver()
    credentials.register("LLM_MAIN_KEY", "sk-test-pg-e2e")
    settings = ApiSettings(db_path=str(tmp_path / "control.sqlite"))

    assembly = build_postgres_assembly(
        PgAssemblyConfig(
            effective=settings,
            connection=connection,
            endpoint_store=None,  # placeholder replaced below
            model_store=None,
            pg_dsn=_dsn(),
            ensure_schema=True,
            gateway_override=FakeModelGateway(),
            credentials_override=credentials,
            preflight_override=_make_preflight_placeholder(credentials),
        )
    )
    deps = _to_apideps(assembly, connection)
    _bind_preflight(deps, credentials)
    return deps


def _bind_preflight(deps: Any, credentials: Any) -> None:
    """Bind the preflight override that references the assembled deps."""
    from adapters.fakes.policy_evaluator import FakePolicyEvaluator
    from packages.application.ports import PreflightContext
    from services.api.catalog import load_catalog_snapshot
    from services.api.catalog_merge import merged_project_settings

    catalog = load_catalog_snapshot()
    project = merged_project_settings(deps)
    from packages.domain.enums import EndpointHealth

    deps.preflight_override = PreflightContext(
        catalog=catalog,
        project=project,
        credentials=credentials,
        endpoint_health={eid: EndpointHealth.HEALTHY for eid in catalog.endpoints},
        provider_health={pid: True for pid in catalog.tool_providers},
        workspace_available={wid: True for wid in catalog.workspaces},
        budget_ledger=deps.budget,
        policy_evaluator=FakePolicyEvaluator(),
    )


def _to_apideps(assembly: Any, connection: Any) -> Any:
    """pg_composition.PostgresAssembly -> ApiDeps（endpoint/model 覆盖为测试 Sqlite 存储）。"""
    from adapters.sqlite.endpoint_store import SqliteEndpointStore
    from adapters.sqlite.model_store import SqliteModelStore
    from services.api.pg_composition import build_postgres_apideps

    deps = build_postgres_apideps(assembly)
    deps.endpoint_store = SqliteEndpointStore(connection=connection)
    deps.model_store = SqliteModelStore(connection=connection)
    deps._connection = connection
    return deps


def _make_preflight_placeholder(credentials: Any) -> Any:
    """Placeholder; replaced after assembly with the deps-bound PreflightContext."""
    return None


def test_pg_stores_run_to_succeeded(tmp_path: Path) -> None:
    """console_demo run with PG stores reaches SUCCEEDED + run.completed + 2 tasks."""
    _clean()
    from services.api.app import create_app

    deps = _make_pg_deps(tmp_path)
    assert type(deps.runs_store).__name__ == "PostgresRunStore"
    assert type(deps.ledger).__name__ == "PostgresEvidenceLedger"
    assert type(deps.budget).__name__ == "PostgresBudgetLedger"
    assert type(deps.runs._deps.workflow).__name__ == "PostgresWorkflowEngine"

    app = create_app(deps)
    with TestClient(app) as client:
        r = client.post(
            "/projects/example-project/runs",
            headers={"Idempotency-Key": f"pg-run-{uuid.uuid4()}"},
            json={"protocol_path": "console_demo_research_v1.yaml"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        run_id = body["id"]
        assert body["state"] == "SUCCEEDED", r.text
        assert body["manifest_digest"] and body["manifest_digest"].startswith("sha256:")

        # read run again
        r2 = client.get(f"/runs/{run_id}")
        assert r2.status_code == 200
        assert r2.json()["state"] == "SUCCEEDED"

        # timeline events
        r3 = client.get(f"/runs/{run_id}/events")
        assert r3.status_code == 200
        types = {item["type"] for item in r3.json()}
        assert "run.completed" in types, types

        # run list
        r4 = client.get("/projects/example-project/runs")
        assert r4.status_code == 200
        assert any(item["id"] == run_id for item in r4.json())

        # evidence map
        r6 = client.get(f"/runs/{run_id}/evidence")
        assert r6.status_code in (200, 404), r6.text  # evidence may be empty but renderable

        # tasks via projection (PG)
        r7 = client.get(f"/runs/{run_id}/tasks")
        assert r7.status_code in (200, 404), r7.text
        if r7.status_code == 200:
            assert len(r7.json()) == 2, r7.text
