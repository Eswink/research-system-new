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
from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.relay.gateway import OpenAIChatGateway
from adapters.relay.registry_credential_resolver import RegistryCredentialResolver
from adapters.sqlite.db import connect
from adapters.sqlite.endpoint_store import SqliteEndpointStore
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
from adapters.sqlite.model_store import SqliteModelStore
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
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
from services.api.approvals import ApprovalRegistry
from services.api.idempotency import IdempotencyStore, InMemoryIdempotencyStore
from services.api.settings import ApiSettings


class FakeEventPublisherFactory:
    """占位（dataclass default 惰性构造用）；真实装配走 assemble()。"""

    def __call__(self) -> EventPublisher:
        from adapters.fakes.event_publisher import FakeEventPublisher

        return FakeEventPublisher()


def _default_events() -> EventPublisher:
    """ApiDeps events 字段默认值工厂（dataclass default_factory 用）。"""
    return FakeEventPublisherFactory()()


def _default_approvals() -> ApprovalRegistry:
    """ApiDeps approvals 默认注册表（dataclass default_factory 用）。"""
    from services.api.approvals import ApprovalRegistry

    return ApprovalRegistry()


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
    approvals: ApprovalRegistry | None = field(default=None, repr=False)
    ledger: EvidenceLedger | None = field(default=None, repr=False)
    budget: BudgetLedger | None = field(default=None, repr=False)
    runs: RunOrchestrationService | None = None
    run_registry: dict[str, ResearchRun] = field(default_factory=dict)
    run_contexts: dict[str, RunContext] = field(default_factory=dict)
    preflight_override: PreflightContext | None = field(default=None, repr=False)
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
    budget = FakeBudgetLedger()
    orchestration = RunOrchestrationService(
        OrchestrationDependencies(
            runtime=FakeAgentRuntime(),
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
        idempotency=InMemoryIdempotencyStore(),
        events=events,
        projection=projection,
        approvals=_default_approvals(),
        runs=orchestration,
        ledger=ledger,
        budget=budget,
        _connection=connection,
    )
