"""PostgreSQL composition helpers (M14).

Kept out of `services/api/composition.py` to honor the 300-line source
limit while remaining inside the allowed composition boundary (adapters
imports permitted only here and in composition root).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

from adapters.fakes.agent_runtime import FakeAgentRuntime
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from packages.application.run_orchestration.context import RunContext  # noqa: F401 (re-export)
from packages.application.run_orchestration.service import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from services.api.composition import (
    ApiDeps,
    demo_session_output,
)


@dataclass(frozen=True, slots=True)
class PostgresAssembly:
    """Postgres 路径装配所需依赖聚合（避免超参数阈值）。"""

    effective: Any
    connection: sqlite3.Connection
    endpoint_store: Any
    model_store: Any
    pg_conn: Any
    workflow: Any
    events: Any
    projection: Any
    ledger: Any
    budget: Any
    orchestration: RunOrchestrationService
    approvals_store: Any = None
    runs_store_pg: Any = None
    artifacts_pg: Any = None
    experiment_store: Any = None
    memory_store: Any = None
    gateway_override: Any = None
    credentials_override: Any = None
    preflight_override: Any = None


def _pg_components(pg_dsn: str, connection: sqlite3.Connection, events_sink: Any) -> dict[str, Any]:
    """Instantiate PG connection + workflow + domain stores (helper, <50 lines)."""
    from adapters.postgres.approval_store import PostgresApprovalStore
    from adapters.postgres.artifact_store import PostgresArtifactStore
    from adapters.postgres.budget_ledger import PostgresBudgetLedger
    from adapters.postgres.db import connect as pg_connect
    from adapters.postgres.evidence_ledger import PostgresEvidenceLedger
    from adapters.postgres.experiment_store import PostgresExperimentStore
    from adapters.postgres.memory_store import PostgresMemoryStore
    from adapters.postgres.run_projection import PostgresRunProjection
    from adapters.postgres.run_store import PostgresRunStore
    from adapters.postgres.workflow_engine import PostgresWorkflowEngine

    pg_conn = pg_connect(pg_dsn)
    workflow: Any = PostgresWorkflowEngine(connection=pg_conn)
    if events_sink is None:
        events_sink = SqliteOutboxEventPublisher(connection=connection)
    projection: Any = PostgresRunProjection(connection=pg_conn)
    projection.bind_events(events_sink)
    return {
        "pg_conn": pg_conn,
        "workflow": workflow,
        "events": events_sink,
        "projection": projection,
        "ledger": PostgresEvidenceLedger(connection=pg_conn),
        "budget": PostgresBudgetLedger(connection=pg_conn),
        "approvals": PostgresApprovalStore(connection=pg_conn),
        "runs_store": PostgresRunStore(connection=pg_conn),
        "artifacts": PostgresArtifactStore(connection=pg_conn),
        "experiment_store": PostgresExperimentStore(connection=pg_conn),
        "memory": PostgresMemoryStore(connection=pg_conn),
    }


@dataclass(frozen=True, slots=True)
class PgAssemblyConfig:
    """Inputs for build_postgres_assembly (arg-count hygiene)."""

    effective: Any
    connection: sqlite3.Connection
    endpoint_store: Any
    model_store: Any
    pg_dsn: str
    ensure_schema: bool = True
    events_sink: Any = None
    gateway_override: Any = None
    credentials_override: Any = None
    preflight_override: Any = None


def build_postgres_assembly(config: PgAssemblyConfig) -> PostgresAssembly:
    """Assemble PG stores + workflow + orchestration (composition root calls this)."""
    effective = config.effective
    connection = config.connection
    endpoint_store = config.endpoint_store
    model_store = config.model_store
    pg_dsn = config.pg_dsn
    if config.ensure_schema:
        from adapters.postgres.db import migrate as pg_migrate

        pg_migrate(pg_dsn)

    c = _pg_components(pg_dsn, connection, config.events_sink)
    orchestration = RunOrchestrationService(
        OrchestrationDependencies(
            runtime=FakeAgentRuntime(structured_output=demo_session_output()),
            workflow=c["workflow"],
            artifacts=c["artifacts"],
            events=c["events"],
            budget=c["budget"],
            ledger=c["ledger"],
        )
    )
    return PostgresAssembly(
        effective=effective,
        connection=connection,
        endpoint_store=endpoint_store,
        model_store=model_store,
        pg_conn=c["pg_conn"],
        workflow=c["workflow"],
        events=c["events"],
        projection=c["projection"],
        ledger=c["ledger"],
        budget=c["budget"],
        orchestration=orchestration,
        approvals_store=c["approvals"],
        runs_store_pg=c["runs_store"],
        artifacts_pg=c["artifacts"],
        experiment_store=c["experiment_store"],
        memory_store=c["memory"],
        gateway_override=getattr(config, "gateway_override", None),
        credentials_override=getattr(config, "credentials_override", None),
        preflight_override=getattr(config, "preflight_override", None),
    )


def build_postgres_apideps(assembly: PostgresAssembly) -> ApiDeps:
    """PG assembly -> ApiDeps (mirrors _build_postgres_apideps)."""
    from services.api.composition import PostgresAssembly as BaseAssembly
    from services.api.composition import _build_postgres_apideps

    base = BaseAssembly(
        effective=assembly.effective,
        connection=assembly.connection,
        endpoint_store=assembly.endpoint_store,
        model_store=assembly.model_store,
        pg_conn=assembly.pg_conn,
        workflow=assembly.workflow,
        events=assembly.events,
        projection=assembly.projection,
        ledger=assembly.ledger,
        budget=assembly.budget,
        orchestration=assembly.orchestration,
        approvals_store=assembly.approvals_store,
        runs_store_pg=assembly.runs_store_pg,
        artifacts_pg=assembly.artifacts_pg,
        memory_store=assembly.memory_store,
        gateway_override=assembly.gateway_override,
        credentials_override=assembly.credentials_override,
        preflight_override=assembly.preflight_override,
    )
    deps = _build_postgres_apideps(base)
    deps.outbox_relay_enabled = True
    return deps
