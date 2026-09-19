"""Control Plane API composition root。

仅本模块装配具体 adapter（依赖方向：services/api → packages/application
→ packages/domain；具体实现只由此处注入，routers 只消费 Port）。
SQLite 配置存储与 outbox 共享连接；凭据永不落盘；Run 编排用 Fake 全链（CI 一致）。
M14: database_url 指向 PostgreSQL 时自动选用 Postgres 引擎（同 Port）。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from adapters.relay.gateway import OpenAIChatGateway
from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
from adapters.sqlite.agent_store import SqliteAgentStore
from adapters.sqlite.approval_store import SqliteApprovalStore
from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.budget_ledger import SqliteBudgetLedger
from adapters.sqlite.catalog_override_store import SqliteCatalogOverrideStore
from adapters.sqlite.endpoint_store import SqliteEndpointStore
from adapters.sqlite.eval_report_store import SqliteEvalReportStore
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
from adapters.sqlite.experiment_store import SqliteExperimentStore
from adapters.sqlite.idempotency_store import SqliteIdempotencyStore
from adapters.sqlite.library_store import SqliteLibraryStore
from adapters.sqlite.memory_store import SqliteMemoryStore
from adapters.sqlite.model_store import SqliteModelStore
from adapters.sqlite.notification_read_store import SqliteNotificationReadStore
from adapters.sqlite.ops_store import SqliteOpsStore
from adapters.sqlite.pricing_snapshot_store import SqlitePricingSnapshotStore
from adapters.sqlite.project_settings_store import SqliteProjectSettingsStore
from adapters.sqlite.project_store import SqliteProjectStore
from adapters.sqlite.run_store import SqliteRunStore
from adapters.sqlite.schedule_store import SqliteScheduleStore
from adapters.sqlite.tool_pack_store import SqliteToolPackStore
from adapters.sqlite.tool_provider_registry import SqliteToolProviderRegistry
from adapters.sqlite.worker_registry import SqliteWorkerRegistry
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from adapters.workspace.snapshot_reader import FileSnapshotReader
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from packages.application.ports import (
    AgentStore,
    ApprovalStore,
    CatalogOverrideStore,
    LibraryStore,
    ProjectSettingsStore,
    ProjectStore,
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
from packages.application.ports.ops_store import OpsStore
from packages.application.ports.policy_evaluator import PolicyEvaluator
from packages.application.ports.resource_catalog import PreflightContext
from packages.application.ports.run_projection import RunProjection
from packages.application.ports.schedule_store import ScheduleStore
from packages.application.ports.telemetry_sink import NullTelemetrySink, TelemetrySink
from packages.application.ports.tool_pack_store import ToolPackStore
from packages.application.ports.tool_provider_registry import ToolProviderRegistry
from packages.application.ports.worker_registry import WorkerRegistry
from packages.application.ports.workspace_snapshot import WorkspaceSnapshotReader
from packages.application.run_orchestration.context import RunContext
from packages.application.run_orchestration.service import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from packages.domain.policy import PolicyDefinition
from packages.domain.run import ResearchRun
from services.api.assembly import (
    _endpoint_url_policy,
    _is_postgres_dsn,
    _load_pricing,
    _open_sqlite,
    build_sqlite_draft_service,
    policy_bindings,
    sqlite_artifact_blob_dir,
)
from services.api.demo import _default_events
from services.api.idempotency import IdempotencyStore
from services.api.runtime_support import build_agent_runtime
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
    # WP-B（PLAN-040）：用户自定义 Role/TeamTemplate 覆盖（SQLite 配置面；
    # 未配置时 merged_catalog 无 overrides、custom POST 诚实 503）。
    catalog_overrides: CatalogOverrideStore | None = field(default=None, repr=False)
    project_settings_store: ProjectSettingsStore | None = field(default=None, repr=False)
    # WP-A（PLAN-041）：项目注册表（单用户；SQLite 配置面，两组成同侧）。
    project_store: ProjectStore | None = field(default=None, repr=False)
    approvals: ApprovalStore | None = field(default=None, repr=False)
    memory: Any | None = field(default=None, repr=False)
    # WP-E（PLAN-037）：ExperimentStore（PG canonical state；PLAN-040 WP-A 起
    # SQLite 开发路径同 Port 实现，消灭 dev 路径诚实 503）。
    experiment_store: Any | None = field(default=None, repr=False)
    # WP-G：通知已读 view-state（控制面 SQLite；两路径同侧）。
    notification_reads: Any | None = field(default=None, repr=False)
    # WP-A（PLAN-044）：库目录（prompts/datasets/notebooks；配置面，两组成同侧）。
    library_store: LibraryStore | None = field(default=None, repr=False)
    # WP-D：provider_id → ToolProvider port 实例注册表（生产未注册时空 dict，
    # build_provider_health 对非 NATIVE provider 诚实返回 UNKNOWN）。
    tool_providers: Mapping[str, Any] = field(default_factory=dict, repr=False)
    preflight_override: PreflightContext | None = field(default=None, repr=False)
    endpoint_url_policy: EndpointUrlPolicy | None = field(default=None, repr=False)
    telemetry: TelemetrySink = field(default_factory=NullTelemetrySink, repr=False)
    exporter_config_digest: str | None = field(default=None, repr=False)
    eval_report_store: Any | None = field(default=None, repr=False)
    pricing_snapshot_store: Any | None = field(default=None, repr=False)
    pricing: Any | None = field(default=None, repr=False)
    worker_registry: WorkerRegistry | None = field(default=None, repr=False)
    protocol_draft_service: Any | None = field(default=None, repr=False)
    # WP-B（PLAN-049）：policy 面（examples/config/policy.yaml）与控制面求值器。
    # 两组成同侧装配；加载失败/缺文件时保持 None（调用方须按诚实缺口处理，
    # 不得假装存在默认策略）。
    policy: PolicyDefinition | None = field(default=None, repr=False)
    policy_evaluator: PolicyEvaluator | None = field(default=None, repr=False)
    # PLAN-059（EC-04）：ops 写面 store（告警规则 CRUD + 事故处置）。两组成同侧；
    # 缺失时 ops 读面 rules_available/workflow_available=False + 原因，写面诚实 503。
    ops_store: OpsStore | None = field(default=None, repr=False)
    # PLAN-060（EC-05）：tool provider 注册表（注册/更新/批准/吊销/健康复核）。
    # 两组成同侧；缺失时写面 503，读面目录只反映 examples 契约。
    tool_provider_registry: ToolProviderRegistry | None = field(default=None, repr=False)
    # PLAN-064（GOAL-003 / EC-02）：ToolPack 供应链状态（install/approve-update/revoke）。
    # 两组成同侧；缺失时 `/tool-packs` 读面给不可用原因、写面诚实 503。
    tool_pack_store: ToolPackStore | None = field(default=None, repr=False)
    # PLAN-066（GOAL-003 / EC-03）：调度定义（可写配置）与读/写共用 registry。
    # 两组成同侧；缺失时 `/ops/schedules` 回落静态事实、写面诚实 503。
    schedule_store: ScheduleStore | None = field(default=None, repr=False)
    schedule_registry: Any | None = field(default=None, repr=False)
    # PLAN-058：工作区快照只读读取器（仅 `RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT`
    # 显式配置时构建；None → 快照端点诚实 503，不猜默认路径、不冒充空树）。
    workspace_snapshots: WorkspaceSnapshotReader | None = field(default=None, repr=False)
    outbox_relay_enabled: bool = False
    _connection: sqlite3.Connection | None = field(default=None, repr=False)
    _pg_connection: Any | None = field(default=None, repr=False)

    def close(self) -> None:
        """关闭自持连接（app shutdown 钩子；注入连接不关闭）。

        每线程连接池（GOAL-004 cycle 5）要关**全部**线程的连接：`close()` 只关本线程
        那条，shutdown 时其余线程的连接会留在登记表里。
        """
        if self._connection is not None:
            close_all = getattr(self._connection, "close_all", None)
            if callable(close_all):
                close_all()
            else:
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
class _ControlFaces:
    """控制面装配的共享输入面（settings + 有状态凭据面 + policy 求值面）。

    PLAN-20260919-107（EC-01）：这三件必须**同一实例**贯穿 runtime 装配与 ApiDeps
    ——`RegistryCredentialResolver` 有状态（API 注册的 Key 只在该实例内存里），
    两套会让运行时解析不到凭据。
    """

    settings: ApiSettings
    credentials: RegistryCredentialResolver
    policy_evaluator: PolicyEvaluator | None


@dataclass(frozen=True, slots=True)
class _SqliteStoreParts:
    """SQLite 共享连接的 Port 面（类型化装配产物；编排服务另经 `_sqlite_orchestration` 装配）。"""

    events: SqliteOutboxEventPublisher
    workflow: SqliteWorkflowEngine
    projection: RunProjection
    ledger: EvidenceLedger
    budget: BudgetLedger
    pricing: Any
    pricing_store: SqlitePricingSnapshotStore
    artifacts: Any
    approvals: Any


def _sqlite_store_parts(
    connection: sqlite3.Connection,
    telemetry: TelemetrySink,
    blob_dir: str,
) -> _SqliteStoreParts:
    """SQLite 共享连接的 store 部分（helper 控制函数长度）。"""
    events = SqliteOutboxEventPublisher(connection=connection)
    workflow = SqliteWorkflowEngine(connection=connection, telemetry=telemetry)
    from adapters.sqlite.run_projection import SqliteRunProjection

    projection = SqliteRunProjection(connection, events)
    ledger = SqliteEvidenceLedger(connection=connection)
    budget = SqliteBudgetLedger(connection=connection)
    pricing = _load_pricing()
    pricing_store = SqlitePricingSnapshotStore(connection=connection)
    # WP-A（PLAN-040）：内容寻址持久存储替换进程内 FakeArtifactStore；
    # 单一实例共享给 orchestration 与控制面读取端点（两个独立实例会让 run
    # 产出的 artifact 对读取端永远为空）。
    artifacts = SqliteArtifactStore(connection=connection, blob_dir=blob_dir)
    # WP-H：同一审批存储实例（执行循环 register、decide/GET 读取）。
    approvals = SqliteApprovalStore(connection=connection)
    return _SqliteStoreParts(
        events=events,
        workflow=workflow,
        projection=projection,
        ledger=ledger,
        budget=budget,
        pricing=pricing,
        pricing_store=pricing_store,
        artifacts=artifacts,
        approvals=approvals,
    )


def _sqlite_orchestration(
    faces: _ControlFaces, ports: _SqliteStoreParts, telemetry: TelemetrySink
) -> RunOrchestrationService:
    """编排服务装配：runtime 经选择面（EC-01），其余 Port 显式注入。

    PLAN-20260919-107：runtime 不再硬编码——两个组合根同侧、都经
    `build_agent_runtime(faces.settings, ...)`；凭据/policy 面与 ApiDeps 同一实例。
    """
    runtime = build_agent_runtime(
        faces.settings,
        credentials=faces.credentials,
        policy_evaluator=faces.policy_evaluator,
        budget_ledger=ports.budget,
    )
    return RunOrchestrationService(
        OrchestrationDependencies(
            runtime=runtime,
            workflow=ports.workflow,
            artifacts=ports.artifacts,
            events=ports.events,
            budget=ports.budget,
            ledger=ports.ledger,
            telemetry=telemetry,
            pricing=ports.pricing,
            pricing_store=ports.pricing_store,
            approvals=ports.approvals,
        )
    )


def _sqlite_config_stores(connection: sqlite3.Connection) -> dict[str, Any]:
    """dev 路径配置/注册面 store（PLAN-040 WP-A / PLAN-041 WP-A；PG canonical
    仍是研究数据真相；store=None → 诚实 503 的边界保持）。

    PLAN-066（EC-03）：`schedule_registry` 与 `schedule_store` 一起装配——守护线程
    与 HTTP 写面必须共用同一个实例，否则 `trigger` 找不到执行体。
    """
    from services.api.schedule_support import build_registry

    schedule_store = SqliteScheduleStore(connection=connection)
    return {
        "agent_store": SqliteAgentStore(connection=connection),
        "catalog_overrides": SqliteCatalogOverrideStore(connection=connection),
        "project_settings_store": SqliteProjectSettingsStore(connection=connection),
        "project_store": SqliteProjectStore(connection=connection),
        "notification_reads": SqliteNotificationReadStore(connection=connection),
        "library_store": SqliteLibraryStore(connection=connection),
        "memory": SqliteMemoryStore(connection=connection),
        "experiment_store": SqliteExperimentStore(connection=connection),
        "ops_store": SqliteOpsStore(connection=connection),
        "tool_provider_registry": SqliteToolProviderRegistry(connection=connection),
        "tool_pack_store": SqliteToolPackStore(connection=connection),
        "worker_registry": SqliteWorkerRegistry(connection=connection),
        "schedule_store": schedule_store,
        "schedule_registry": build_registry(schedule_store),
    }


def _assemble_sqlite(
    effective: ApiSettings,
    connection: sqlite3.Connection,
    endpoint_store: EndpointStore,
    model_store: ModelStore,
    telemetry: TelemetrySink,
) -> ApiDeps:
    bindings = policy_bindings()
    credentials = RegistryCredentialResolver()
    parts = _sqlite_store_parts(connection, telemetry, sqlite_artifact_blob_dir(effective))
    return _sqlite_apideps(
        effective,
        connection,
        endpoint_store,
        model_store,
        telemetry,
        _ControlFaces(
            settings=effective,
            credentials=credentials,
            policy_evaluator=bindings["policy_evaluator"],
        ),
        parts,
        bindings,
    )


def _sqlite_apideps(  # noqa: PLR0913 - composition root 装配参数
    effective: ApiSettings,
    connection: sqlite3.Connection,
    endpoint_store: EndpointStore,
    model_store: ModelStore,
    telemetry: TelemetrySink,
    faces: _ControlFaces,
    parts: _SqliteStoreParts,
    bindings: dict[str, Any],
) -> ApiDeps:
    """ApiDeps 构造（helper 控制 `_assemble_sqlite` 长度）。"""
    return ApiDeps(
        endpoint_store=endpoint_store,
        model_store=model_store,
        credentials=faces.credentials,
        eval_report_store=SqliteEvalReportStore(connection=connection),
        pricing_snapshot_store=parts.pricing_store,
        pricing=parts.pricing,
        gateway=OpenAIChatGateway(
            default_timeout_seconds=effective.endpoint_timeout_seconds,
            telemetry=telemetry,
        ),
        idempotency=SqliteIdempotencyStore(connection=connection),
        events=parts.events,
        projection=parts.projection,
        approvals=parts.approvals,
        runs=_sqlite_orchestration(faces, parts, telemetry),
        workflow=parts.workflow,
        runs_store=SqliteRunStore(connection=connection),
        artifacts=parts.artifacts,
        ledger=parts.ledger,
        budget=parts.budget,
        **_sqlite_config_stores(connection),
        protocol_draft_service=build_sqlite_draft_service(connection),
        endpoint_url_policy=_endpoint_url_policy(effective),
        telemetry=telemetry,
        **bindings,
        _connection=connection,
    )


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
    deps.workspace_snapshots = _build_snapshot_reader(effective)
    return deps


def _build_snapshot_reader(effective: ApiSettings) -> WorkspaceSnapshotReader | None:
    """快照读取器：仅显式配置根目录时构建（未配置 → None → 端点诚实 503）。"""
    if not effective.workspace_snapshot_root:
        return None
    return FileSnapshotReader(effective.workspace_snapshot_root)
