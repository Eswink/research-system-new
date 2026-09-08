"""Control Plane API composition root。

仅本模块装配具体 adapter（依赖方向：services/api → packages/application
→ packages/domain；具体实现只由此处注入，routers 只消费 Port）。
SQLite 配置存储与 outbox 共享连接；凭据永不落盘；Run 编排用 Fake 全链（CI 一致）。
M14: database_url 指向 PostgreSQL 时自动选用 Postgres 引擎（同 Port）。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any

from adapters.fakes.agent_runtime import FakeAgentRuntime
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.relay.gateway import OpenAIChatGateway
from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
from adapters.sqlite.agent_store import SqliteAgentStore
from adapters.sqlite.approval_store import SqliteApprovalStore
from adapters.sqlite.budget_ledger import SqliteBudgetLedger
from adapters.sqlite.endpoint_store import SqliteEndpointStore
from adapters.sqlite.eval_report_store import SqliteEvalReportStore
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
from adapters.sqlite.idempotency_store import SqliteIdempotencyStore
from adapters.sqlite.model_store import SqliteModelStore
from adapters.sqlite.pricing_snapshot_store import SqlitePricingSnapshotStore
from adapters.sqlite.project_settings_store import SqliteProjectSettingsStore
from adapters.sqlite.run_store import SqliteRunStore
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from packages.application.ports import (
    AgentStore,
    ApprovalStore,
    ProjectSettingsStore,
    RunStore,
    WorkflowEngine,
)
from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.credential_resolver import CredentialResolver
from packages.application.ports.endpoint_store import EndpointStore
from packages.application.ports.event_publisher import EventPublisher
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.model_gateway import ModelGateway
from packages.application.ports.model_store import ModelStore
from packages.application.ports.resource_catalog import PreflightContext
from packages.application.ports.run_projection import RunProjection
from packages.application.ports.telemetry_sink import NullTelemetrySink, TelemetrySink
from packages.application.ports.worker_registry import WorkerRegistry
from packages.application.run_orchestration.context import RunContext
from packages.application.run_orchestration.service import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from packages.domain.run import ResearchRun
from services.api.assembly import (
    _endpoint_url_policy,
    _is_postgres_dsn,
    _load_pricing,
    _open_sqlite,
)
from services.api.demo import _default_events
from services.api.demo import demo_session_output as demo_session_output
from services.api.idempotency import IdempotencyStore
from services.api.settings import ApiSettings
from services.api.telemetry import build_api_telemetry, exporter_config_digest


@dataclass
class ApiDeps:
    """控制面依赖聚合（Port 面；由 composition root 注入具体实现）。"""

    endpoint_store: EndpointStore
    model_store: ModelStore
    credentials: CredentialResolver
    gateway: ModelGateway
    idempotency: IdempotencyStore
    events: EventPublisher = field(default_factory=_default_events)
    projection: RunProjection | None = field(default=None, repr=False)
    ledger: EvidenceLedger | None = field(default=None, repr=False)
    budget: BudgetLedger | None = field(default=None, repr=False)
    runs: RunOrchestrationService | None = None
    workflow: WorkflowEngine | None = field(default=None, repr=False)
    run_registry: dict[str, ResearchRun] = field(default_factory=dict)
    runs_store: RunStore | None = field(default=None, repr=False)
    run_contexts: dict[str, RunContext] = field(default_factory=dict)
    artifacts: ArtifactStore | None = field(default=None, repr=False)
    agent_store: AgentStore | None = field(default=None, repr=False)
    project_settings_store: ProjectSettingsStore | None = field(default=None, repr=False)
    approvals: ApprovalStore | None = field(default=None, repr=False)
    memory: Any | None = field(default=None, repr=False)
    preflight_override: PreflightContext | None = field(default=None, repr=False)
    endpoint_url_policy: EndpointUrlPolicy | None = field(default=None, repr=False)
    telemetry: TelemetrySink = field(default_factory=NullTelemetrySink, repr=False)
    exporter_config_digest: str | None = field(default=None, repr=False)
    eval_report_store: Any | None = field(default=None, repr=False)
    pricing_snapshot_store: Any | None = field(default=None, repr=False)
    pricing: Any | None = field(default=None, repr=False)
    worker_registry: WorkerRegistry | None = field(default=None, repr=False)
    protocol_draft_service: Any | None = field(default=None, repr=False)
    outbox_relay_enabled: bool = False
    _connection: sqlite3.Connection | None = field(default=None, repr=False)
    _pg_connection: Any | None = field(default=None, repr=False)

    def close(self) -> None:
        """关闭自持连接（app shutdown 钩子；注入连接不关闭）。"""
        if self._connection is not None:
            self._connection.close()
        if self._pg_connection is not None:
            try:
                self._pg_connection.close()
            except Exception:
                pass


def _assemble_postgres(  # noqa: PLR0913 - composition root 装配参数
    effective: ApiSettings,
    connection: sqlite3.Connection,
    endpoint_store: EndpointStore,
    model_store: ModelStore,
    pg_dsn: str,
    telemetry: TelemetrySink,
) -> ApiDeps:
    from services.api.pg_composition import (
        PgAssemblyConfig,
        build_postgres_apideps,
        build_postgres_assembly,
    )

    assembly = build_postgres_assembly(
        PgAssemblyConfig(
            effective=effective,
            connection=connection,
            endpoint_store=endpoint_store,
            model_store=model_store,
            pg_dsn=pg_dsn,
            ensure_schema=True,
            telemetry=telemetry,
            artifact_blob_dir=effective.artifact_blob_dir,
        )
    )
    return build_postgres_apideps(assembly)


@dataclass(frozen=True, slots=True)
class _SqliteStoreParts:
    """SQLite 共享连接的 store/orchestration 部分（类型化装配产物）。"""

    events: SqliteOutboxEventPublisher
    workflow: SqliteWorkflowEngine
    projection: RunProjection
    ledger: EvidenceLedger
    budget: BudgetLedger
    pricing: Any
    pricing_store: SqlitePricingSnapshotStore
    orchestration: RunOrchestrationService


def _sqlite_store_parts(
    connection: sqlite3.Connection,
    telemetry: TelemetrySink,
) -> _SqliteStoreParts:
    """SQLite 共享连接的 store/orchestration 部分（helper 控制函数长度）。"""
    events = SqliteOutboxEventPublisher(connection=connection)
    workflow = SqliteWorkflowEngine(connection=connection, telemetry=telemetry)
    from adapters.sqlite.run_projection import SqliteRunProjection

    projection = SqliteRunProjection(connection, events)
    ledger = SqliteEvidenceLedger(connection=connection)
    budget = SqliteBudgetLedger(connection=connection)
    pricing = _load_pricing()
    pricing_store = SqlitePricingSnapshotStore(connection=connection)
    orchestration = RunOrchestrationService(
        OrchestrationDependencies(
            runtime=FakeAgentRuntime(structured_output=demo_session_output()),
            workflow=workflow,
            artifacts=FakeArtifactStore(),
            events=events,
            budget=budget,
            ledger=ledger,
            telemetry=telemetry,
            pricing=pricing,
            pricing_store=pricing_store,
        )
    )
    return _SqliteStoreParts(
        events=events,
        workflow=workflow,
        projection=projection,
        ledger=ledger,
        budget=budget,
        pricing=pricing,
        pricing_store=pricing_store,
        orchestration=orchestration,
    )


def _assemble_sqlite(
    effective: ApiSettings,
    connection: sqlite3.Connection,
    endpoint_store: EndpointStore,
    model_store: ModelStore,
    telemetry: TelemetrySink,
) -> ApiDeps:
    parts = _sqlite_store_parts(connection, telemetry)
    events_sqlite = parts.events
    workflow_sqlite = parts.workflow
    projection_sqlite = parts.projection
    ledger_sqlite = parts.ledger
    budget_sqlite = parts.budget
    pricing_sqlite = parts.pricing
    pricing_store_sqlite = parts.pricing_store
    orchestration_sqlite = parts.orchestration
    eval_store = SqliteEvalReportStore(connection=connection)
    return ApiDeps(
        endpoint_store=endpoint_store,
        model_store=model_store,
        credentials=RegistryCredentialResolver(),
        eval_report_store=eval_store,
        pricing_snapshot_store=pricing_store_sqlite,
        pricing=pricing_sqlite,
        gateway=OpenAIChatGateway(
            default_timeout_seconds=effective.endpoint_timeout_seconds,
            telemetry=telemetry,
        ),
        idempotency=SqliteIdempotencyStore(connection=connection),
        events=events_sqlite,
        projection=projection_sqlite,
        approvals=SqliteApprovalStore(connection=connection),
        runs=orchestration_sqlite,
        workflow=workflow_sqlite,
        runs_store=SqliteRunStore(connection=connection),
        artifacts=FakeArtifactStore(),
        ledger=ledger_sqlite,
        budget=budget_sqlite,
        agent_store=SqliteAgentStore(connection=connection),
        project_settings_store=SqliteProjectSettingsStore(connection=connection),
        protocol_draft_service=_build_draft_service(connection),
        endpoint_url_policy=_endpoint_url_policy(effective),
        telemetry=telemetry,
        _connection=connection,
    )


def _build_draft_service(connection: sqlite3.Connection) -> Any:
    """构建协议草稿服务（SQLite 开发路径；PG 路径见 pg_composition）。"""
    from adapters.contracts.protocol_text_loader import load_protocol_from_text
    from adapters.sqlite.protocol_draft_store import SqliteProtocolDraftStore
    from packages.application.protocol_authoring.service import DraftService, DraftTemplates
    from services.api.routers.protocol_drafts import default_templates

    store = SqliteProtocolDraftStore(connection=connection)
    templates: DraftTemplates = default_templates()
    return DraftService(store, templates, text_loader=load_protocol_from_text)


def assemble(settings: ApiSettings | None = None) -> ApiDeps:
    """装配控制面（生产路径：SQLite 配置持久化 + Fake run 编排全链）。

    M14: 若 settings/database_url 为 postgresql://，workflow 使用 Postgres；
    配置存储仍为 SQLite（Postgres canonical state 仅 workflow 队列/lease/outbox）。
    """
    effective = settings if settings is not None else ApiSettings.from_env()
    pg_dsn = effective.effective_database_url()
    use_pg = _is_postgres_dsn(pg_dsn)
    connection = _open_sqlite(effective.db_path)
    endpoint_store = SqliteEndpointStore(connection=connection)
    model_store = SqliteModelStore(connection=connection)
    # M15: telemetry 默认 off(Null);RESEARCHOS_OTEL_ENABLED=1 时为 OTel 组合
    telemetry = build_api_telemetry(effective)
    if use_pg:
        assert pg_dsn is not None
        deps = _assemble_postgres(
            effective, connection, endpoint_store, model_store, pg_dsn, telemetry
        )
    else:
        deps = _assemble_sqlite(effective, connection, endpoint_store, model_store, telemetry)
    deps.pricing = _load_pricing()
    deps.exporter_config_digest = exporter_config_digest(effective)
    return deps
