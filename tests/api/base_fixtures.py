"""基础 API 测试装配（`conftest.make_base_deps` 的实现在这里）。

拆出来的原因和 `run_fixtures.py` 一样：`tests/api/conftest.py` 受 50 行/函数硬上限约束，
而基础装配（~30 个 SQLite store + 编排服务）本来就不适合塞在一个函数里。

连接布局（GOAL-004 cycle 5 = EC-05）：统一走 `ThreadLocalConnection`——`:memory:` 时它
退化成一条共享连接（与既有行为逐字一致），文件路径时才真的每线程一条。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.fakes.credential_resolver import FakeCredentialResolver
from adapters.fakes.model_gateway import FakeModelGateway
from services.api.composition import ApiDeps
from services.api.idempotency import InMemoryIdempotencyStore

if TYPE_CHECKING:
    from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
    from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
    from adapters.sqlite.run_projection import SqliteRunProjection
    from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
    from packages.application.ports.agent_runtime import AgentRuntime
    from packages.application.protocol_authoring.service import DraftService
    from packages.application.run_orchestration.service import RunOrchestrationService


@dataclass(frozen=True, slots=True)
class _SharedParts:
    """`_base_sqlite_parts` 的产物（参数对象：六个部件的元组注解不该占掉函数行数预算）。"""

    events: SqliteOutboxEventPublisher
    workflow: SqliteWorkflowEngine
    ledger: SqliteEvidenceLedger
    budget: FakeBudgetLedger
    runs: RunOrchestrationService
    projection: SqliteRunProjection


def _base_sqlite_parts(
    connection: sqlite3.Connection,
    *,
    runtime: AgentRuntime | None = None,
) -> _SharedParts:
    """Build shared SQLite stores + orchestration for base test deps."""
    from adapters.fakes.agent_runtime import FakeAgentRuntime
    from adapters.fakes.artifact_store import FakeArtifactStore
    from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
    from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
    from adapters.sqlite.run_projection import SqliteRunProjection
    from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
    from packages.application.run_orchestration.service import (
        OrchestrationDependencies,
        RunOrchestrationService,
    )
    from services.api.demo import demo_session_output, seed_declared_inputs

    events = SqliteOutboxEventPublisher(connection=connection)
    workflow = SqliteWorkflowEngine(connection=connection)
    ledger = SqliteEvidenceLedger(connection=connection)
    budget = FakeBudgetLedger()
    # GOAL-010 EC-02：协议**声明**的输入制品必须真的在库里；`EVIDENCE_COVERAGE`
    # 收紧后只认非模型自述的来源，声明的输入就是那个来源。
    artifacts = FakeArtifactStore()
    seed_declared_inputs(artifacts)
    runs = RunOrchestrationService(
        OrchestrationDependencies(
            # GOAL-010 EC-04：允许调用方换受控执行体（驱动「执行体报告了 model 名」的
            # 链路）；默认仍是与接线前逐字一致的 demo Fake。
            runtime=runtime or FakeAgentRuntime(structured_output=demo_session_output()),
            workflow=workflow,
            artifacts=artifacts,
            events=events,
            budget=budget,
            ledger=ledger,
        )
    )
    projection = SqliteRunProjection(connection, events)
    return _SharedParts(events, workflow, ledger, budget, runs, projection)


def build_base_deps(
    *,
    gateway: FakeModelGateway | None = None,
    db_path: str = ":memory:",
    runtime: AgentRuntime | None = None,
) -> ApiDeps:
    """基础装配（endpoint/model CRUD + probe + run 测试用）。"""
    from adapters.sqlite.pool import ThreadLocalConnection

    # 代理面与 sqlite3.Connection 同形（execute/cursor/commit/with 块/row_factory），
    # 但类型上不是它的子类：装配边界显式 cast，覆盖由池单测 + 整库 API 套件提供。
    connection = cast("sqlite3.Connection", ThreadLocalConnection(db_path))
    return _base_api_deps(connection, _base_sqlite_parts(connection, runtime=runtime), gateway)


def _base_api_deps(
    connection: sqlite3.Connection,
    parts: _SharedParts,
    gateway: FakeModelGateway | None,
) -> ApiDeps:
    """共享部件 → ApiDeps（端口逐个接线；从 `build_base_deps` 拆出守 50 行函数上限）。"""
    from adapters.fakes.policy_evaluator import FakePolicyEvaluator
    from adapters.sqlite.agent_store import SqliteAgentStore
    from adapters.sqlite.catalog_override_store import SqliteCatalogOverrideStore
    from adapters.sqlite.endpoint_store import SqliteEndpointStore
    from adapters.sqlite.library_store import SqliteLibraryStore
    from adapters.sqlite.model_store import SqliteModelStore
    from adapters.sqlite.ops_store import SqliteOpsStore
    from adapters.sqlite.project_settings_store import SqliteProjectSettingsStore
    from adapters.sqlite.project_store import SqliteProjectStore
    from adapters.sqlite.schedule_store import SqliteScheduleStore
    from adapters.sqlite.tool_pack_store import SqliteToolPackStore
    from adapters.sqlite.tool_provider_registry import SqliteToolProviderRegistry
    from services.api.schedule_support import build_registry

    events, workflow, ledger, budget = parts.events, parts.workflow, parts.ledger, parts.budget
    runs, projection = parts.runs, parts.projection
    schedule_store = SqliteScheduleStore(connection=connection)
    return ApiDeps(
        endpoint_store=SqliteEndpointStore(connection=connection),
        model_store=SqliteModelStore(connection=connection),
        credentials=FakeCredentialResolver(),
        gateway=gateway if gateway is not None else FakeModelGateway(),
        idempotency=InMemoryIdempotencyStore(),
        events=events,
        projection=projection,
        runs=runs,
        workflow=workflow,
        ledger=ledger,
        budget=budget,
        agent_store=SqliteAgentStore(connection=connection),
        catalog_overrides=SqliteCatalogOverrideStore(connection=connection),
        project_settings_store=SqliteProjectSettingsStore(connection=connection),
        project_store=SqliteProjectStore(connection=connection),
        library_store=SqliteLibraryStore(connection=connection),
        ops_store=SqliteOpsStore(connection=connection),
        tool_provider_registry=SqliteToolProviderRegistry(connection=connection),
        tool_pack_store=SqliteToolPackStore(connection=connection),
        schedule_store=schedule_store,
        schedule_registry=build_registry(schedule_store),
        policy_evaluator=FakePolicyEvaluator(),
        protocol_draft_service=make_draft_service(connection),
        _connection=connection,
    )


def make_draft_service(connection: sqlite3.Connection) -> DraftService:
    """测试装配的草稿服务（与生产 SQLite 路径同构造，含 text_loader）。"""
    from adapters.contracts.protocol_text_loader import load_protocol_from_text
    from adapters.sqlite.protocol_draft_store import SqliteProtocolDraftStore
    from packages.application.protocol_authoring.service import DraftService
    from services.api.routers.protocol_drafts import default_templates

    return DraftService(
        SqliteProtocolDraftStore(connection=connection),
        default_templates(),
        text_loader=load_protocol_from_text,
    )
