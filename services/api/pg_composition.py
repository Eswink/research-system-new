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
from services.api.assembly import _endpoint_url_policy, _load_pricing
from services.api.composition import ApiDeps, demo_session_output


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
    eval_report_store: Any = None
    pricing_snapshot_store: Any = None
    worker_registry: Any = None
    gateway_override: Any = None
    credentials_override: Any = None
    preflight_override: Any = None
    telemetry: Any = None


def _pg_components(
    pg_dsn: str,
    connection: sqlite3.Connection,
    events_sink: Any,
    artifact_blob_dir: str | None = None,
) -> dict[str, Any]:
    """Instantiate PG connection + workflow + domain stores (helper, <50 lines)."""
    from adapters.postgres.approval_store import PostgresApprovalStore
    from adapters.postgres.artifact_store import PostgresArtifactStore
    from adapters.postgres.budget_ledger import PostgresBudgetLedger
    from adapters.postgres.db import connect as pg_connect
    from adapters.postgres.eval_report_store import PostgresEvalReportStore
    from adapters.postgres.evidence_ledger import PostgresEvidenceLedger
    from adapters.postgres.experiment_store import PostgresExperimentStore
    from adapters.postgres.memory_store import PostgresMemoryStore
    from adapters.postgres.pricing_snapshot_store import PostgresPricingSnapshotStore
    from adapters.postgres.run_projection import PostgresRunProjection
    from adapters.postgres.run_store import PostgresRunStore
    from adapters.postgres.worker_registry import PostgresWorkerRegistry
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
        "artifacts": PostgresArtifactStore(connection=pg_conn, blob_dir=artifact_blob_dir),
        "experiment_store": PostgresExperimentStore(connection=pg_conn),
        "memory": PostgresMemoryStore(connection=pg_conn),
        "eval_store": PostgresEvalReportStore(connection=pg_conn),
        "pricing_store": PostgresPricingSnapshotStore(connection=pg_conn),
        "worker_registry": PostgresWorkerRegistry(connection=pg_conn),
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
    telemetry: Any = None
    artifact_blob_dir: str | None = None


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

    c = _pg_components(pg_dsn, connection, config.events_sink, config.artifact_blob_dir)
    orchestration = _build_pg_orchestration(c, config)
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
        eval_report_store=c["eval_store"],
        pricing_snapshot_store=c["pricing_store"],
        worker_registry=c["worker_registry"],
        gateway_override=getattr(config, "gateway_override", None),
        credentials_override=getattr(config, "credentials_override", None),
        preflight_override=getattr(config, "preflight_override", None),
    )


def _build_pg_orchestration(c: dict[str, Any], config: PgAssemblyConfig) -> RunOrchestrationService:
    """PG 编排服务装配；与 ApiDeps 共享同一 approvals 实例（decide 读、执行循环写）。"""
    return RunOrchestrationService(
        OrchestrationDependencies(
            runtime=FakeAgentRuntime(structured_output=demo_session_output()),
            workflow=c["workflow"],
            artifacts=c["artifacts"],
            events=c["events"],
            budget=c["budget"],
            ledger=c["ledger"],
            telemetry=config.telemetry,
            pricing=_load_pricing(),
            pricing_store=c["pricing_store"],
            approvals=c["approvals"],
        )
    )


def _pg_config_stores(connection: sqlite3.Connection) -> dict[str, Any]:
    """配置面 store（WP-B PLAN-040 / WP-A PLAN-041：SQLite 两组成同侧）。

    PLAN-064（GOAL-003 / EC-02）：ToolPack 供应链状态与 tool provider 注册表同侧
    ——PG 路径的配置面同样是 SQLite，写面语义不因后端切换而分叉。

    PLAN-066（GOAL-003 / EC-03）：调度定义同理；`schedule_registry` 由同一 store
    构建，守护线程与 HTTP 写面共用（trigger 才找得到执行体）。
    """
    from adapters.sqlite.agent_store import SqliteAgentStore
    from adapters.sqlite.catalog_override_store import SqliteCatalogOverrideStore
    from adapters.sqlite.library_store import SqliteLibraryStore
    from adapters.sqlite.notification_read_store import SqliteNotificationReadStore
    from adapters.sqlite.ops_store import SqliteOpsStore
    from adapters.sqlite.project_settings_store import SqliteProjectSettingsStore
    from adapters.sqlite.project_store import SqliteProjectStore
    from adapters.sqlite.schedule_store import SqliteScheduleStore
    from adapters.sqlite.tool_pack_store import SqliteToolPackStore
    from adapters.sqlite.tool_provider_registry import SqliteToolProviderRegistry
    from services.api.schedule_support import build_registry

    schedule_store = SqliteScheduleStore(connection=connection)
    return {
        "agent_store": SqliteAgentStore(connection=connection),
        "catalog_overrides": SqliteCatalogOverrideStore(connection=connection),
        "project_settings_store": SqliteProjectSettingsStore(connection=connection),
        "project_store": SqliteProjectStore(connection=connection),
        "notification_reads": SqliteNotificationReadStore(connection=connection),
        "library_store": SqliteLibraryStore(connection=connection),
        "ops_store": SqliteOpsStore(connection=connection),
        "tool_provider_registry": SqliteToolProviderRegistry(connection=connection),
        "tool_pack_store": SqliteToolPackStore(connection=connection),  # EC-02 ToolPack 写面
        "schedule_store": schedule_store,  # EC-03 调度写面
        "schedule_registry": build_registry(schedule_store),
    }


def build_postgres_apideps(assembly: PostgresAssembly) -> ApiDeps:
    """PG assembly -> ApiDeps（composition root 装配点唯一）。"""
    from adapters.fakes.artifact_store import FakeArtifactStore
    from adapters.relay.gateway import OpenAIChatGateway
    from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
    from adapters.sqlite.approval_store import SqliteApprovalStore
    from adapters.sqlite.idempotency_store import SqliteIdempotencyStore
    from adapters.sqlite.run_store import SqliteRunStore
    from services.api.assembly import policy_bindings

    deps = ApiDeps(
        endpoint_store=assembly.endpoint_store,
        model_store=assembly.model_store,
        credentials=assembly.credentials_override or RegistryCredentialResolver(),
        gateway=assembly.gateway_override
        or OpenAIChatGateway(
            default_timeout_seconds=assembly.effective.endpoint_timeout_seconds,
            telemetry=assembly.telemetry,
        ),
        idempotency=SqliteIdempotencyStore(connection=assembly.connection),
        events=assembly.events,
        projection=assembly.projection,
        approvals=assembly.approvals_store or SqliteApprovalStore(connection=assembly.connection),
        runs=assembly.orchestration,
        workflow=assembly.workflow,
        runs_store=assembly.runs_store_pg or SqliteRunStore(connection=assembly.connection),
        artifacts=assembly.artifacts_pg or FakeArtifactStore(),
        # WP-E：实验计划存储（PG canonical state；PLAN-040 WP-A 起 SQLite 开发
        # 路径由 composition._assemble_sqlite 注入同 Port 实现，不再 503）。
        experiment_store=assembly.experiment_store,
        ledger=assembly.ledger,
        budget=assembly.budget,
        **_pg_config_stores(assembly.connection),
        endpoint_url_policy=_endpoint_url_policy(assembly.effective),
        memory=assembly.memory_store,
        preflight_override=assembly.preflight_override,
        telemetry=assembly.telemetry,
        eval_report_store=assembly.eval_report_store,
        pricing_snapshot_store=assembly.pricing_snapshot_store,
        worker_registry=assembly.worker_registry,
        protocol_draft_service=_build_pg_draft_service(assembly.pg_conn),
        **policy_bindings(),
        _connection=assembly.connection,
        _pg_connection=assembly.pg_conn,
    )
    deps.outbox_relay_enabled = True
    return deps


def _build_pg_draft_service(pg_conn: Any) -> Any:
    """构建协议草稿服务（PostgreSQL 生产路径；同一 Port/服务契约）。"""
    from adapters.contracts.protocol_text_loader import load_protocol_from_text
    from adapters.postgres.protocol_draft_store import PgProtocolDraftStore
    from packages.application.protocol_authoring.service import DraftService
    from services.api.routers.protocol_drafts import default_templates

    store = PgProtocolDraftStore(connection=pg_conn)
    return DraftService(store, default_templates(), text_loader=load_protocol_from_text)
