"""Control Plane API composition root。

仅本模块装配具体 adapter（依赖方向：services/api → packages/application
→ packages/domain；具体实现只由此处注入，routers 只消费 Port）。
SQLite 配置存储与 outbox 共享连接；凭据注册表永不落盘。
Run 编排使用 Fake Port 全链（无真实付费 LLM；E2E 与 CI 一致）。
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from adapters.fakes.agent_runtime import FakeAgentRuntime
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.relay.gateway import OpenAIChatGateway
from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
from adapters.sqlite.agent_store import SqliteAgentStore
from adapters.sqlite.approval_store import SqliteApprovalStore
from adapters.sqlite.budget_ledger import SqliteBudgetLedger
from adapters.sqlite.db import connect
from adapters.sqlite.endpoint_store import SqliteEndpointStore
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
from adapters.sqlite.idempotency_store import SqliteIdempotencyStore
from adapters.sqlite.model_store import SqliteModelStore
from adapters.sqlite.project_settings_store import SqliteProjectSettingsStore
from adapters.sqlite.run_store import SqliteRunStore
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.model_relay.endpoint_policy import EndpointUrlPolicy
from packages.application.ports import AgentStore, ApprovalStore, ProjectSettingsStore, RunStore
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
from packages.application.run_orchestration.context import RunContext
from packages.application.run_orchestration.service import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from packages.domain.run import ResearchRun
from services.api.idempotency import IdempotencyStore
from services.api.settings import ApiSettings


class FakeEventPublisherFactory:
    """占位（dataclass default 惰性构造用）；真实装配走 assemble()。"""

    def __call__(self) -> EventPublisher:
        from adapters.fakes.event_publisher import FakeEventPublisher

        return FakeEventPublisher()


def demo_session_output() -> dict[str, object]:
    """控制面 demo 会话输出（受控 Fake agent loop；UI 如实披露执行体性质）。

    只用于 console_demo 协议：使验收标准（ARTIFACT_EXISTS analysis_report +
    EVIDENCE_COVERAGE 1）可被正式 gate 求值通过，不冒充真实研究结果；
    其他协议照常按各自契约执行/拒绝。
    """
    return {
        "analysis_report": {
            "summary": "controlled fake session output (M13-R1 console demo)",
            "status": "ok",
        }
    }


def _default_events() -> EventPublisher:
    """ApiDeps events 字段默认值工厂（dataclass default_factory 用）。"""
    return FakeEventPublisherFactory()()


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
    run_registry: dict[str, ResearchRun] = field(default_factory=dict)
    runs_store: RunStore | None = field(default=None, repr=False)
    run_contexts: dict[str, RunContext] = field(default_factory=dict)
    artifacts: ArtifactStore | None = field(default=None, repr=False)
    agent_store: AgentStore | None = field(default=None, repr=False)
    project_settings_store: ProjectSettingsStore | None = field(default=None, repr=False)
    approvals: ApprovalStore | None = field(default=None, repr=False)
    preflight_override: PreflightContext | None = field(default=None, repr=False)
    endpoint_url_policy: EndpointUrlPolicy | None = field(default=None, repr=False)
    _connection: sqlite3.Connection | None = field(default=None, repr=False)

    def close(self) -> None:
        """关闭自持连接（app shutdown 钩子；注入连接不关闭）。"""
        if self._connection is not None:
            self._connection.close()


def assemble(settings: ApiSettings | None = None) -> ApiDeps:
    """装配控制面（生产路径：SQLite 配置持久化 + Fake run 编排全链）。"""
    effective = settings if settings is not None else ApiSettings.from_env()
    db_path = Path(effective.db_path)
    if str(db_path) != ":memory:":
        os.makedirs(db_path.parent, exist_ok=True)
    connection = connect(effective.db_path)
    endpoint_store = SqliteEndpointStore(connection=connection)
    model_store = SqliteModelStore(connection=connection)
    events = SqliteOutboxEventPublisher(connection=connection)
    workflow = SqliteWorkflowEngine(connection=connection)
    from adapters.sqlite.run_projection import SqliteRunProjection

    projection = SqliteRunProjection(connection, events)
    ledger = SqliteEvidenceLedger(connection=connection)
    budget = SqliteBudgetLedger(connection=connection)
    orchestration = RunOrchestrationService(
        OrchestrationDependencies(
            runtime=FakeAgentRuntime(structured_output=demo_session_output()),
            workflow=workflow,
            artifacts=FakeArtifactStore(),
            events=events,
            budget=budget,
            ledger=ledger,
        )
    )
    return ApiDeps(
        endpoint_store=endpoint_store,
        model_store=model_store,
        credentials=RegistryCredentialResolver(),
        gateway=OpenAIChatGateway(default_timeout_seconds=effective.endpoint_timeout_seconds),
        idempotency=SqliteIdempotencyStore(connection=connection),
        events=events,
        projection=projection,
        approvals=SqliteApprovalStore(connection=connection),
        runs=orchestration,
        runs_store=SqliteRunStore(connection=connection),
        artifacts=FakeArtifactStore(),
        ledger=ledger,
        budget=budget,
        agent_store=SqliteAgentStore(connection=connection),
        project_settings_store=SqliteProjectSettingsStore(connection=connection),
        endpoint_url_policy=EndpointUrlPolicy(
            allow_localhost=effective.allow_localhost_endpoints,
            allow_private=effective.allow_localhost_endpoints,
            allow_link_local=effective.allow_localhost_endpoints,
        ),
        _connection=connection,
    )
