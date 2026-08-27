"""Control Plane API 测试夹具（基础装配；run 相关见 run_fixtures.py）。"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from adapters.fakes.credential_resolver import FakeCredentialResolver
from adapters.fakes.model_gateway import FakeModelGateway
from services.api.app import create_app
from services.api.composition import ApiDeps
from services.api.idempotency import InMemoryIdempotencyStore


def make_app_deps(
    *,
    gateway: FakeModelGateway | None = None,
    run_ready: bool = False,
) -> ApiDeps:
    """测试装配：Sqlite(:memory:) 配置存储 + Fakes + 内存幂等。

    run_ready=True 时装配可冻结 Manifest 的完整 preflight context
    （定义在 run_fixtures.py，避免本文件超行数阈值）。
    """
    from tests.api.run_fixtures import make_run_ready_deps

    if run_ready:
        return make_run_ready_deps(gateway=gateway)
    return make_base_deps(gateway=gateway)


def make_base_deps(*, gateway: FakeModelGateway | None = None) -> ApiDeps:
    """基础装配（endpoint/model CRUD + probe + run 测试用）。"""
    from adapters.fakes.agent_runtime import FakeAgentRuntime
    from adapters.fakes.artifact_store import FakeArtifactStore
    from adapters.fakes.budget_ledger import FakeBudgetLedger
    from adapters.sqlite.agent_store import SqliteAgentStore
    from adapters.sqlite.db import connect
    from adapters.sqlite.endpoint_store import SqliteEndpointStore
    from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
    from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
    from adapters.sqlite.model_store import SqliteModelStore
    from adapters.sqlite.project_settings_store import SqliteProjectSettingsStore
    from adapters.sqlite.run_projection import SqliteRunProjection
    from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
    from packages.application.run_orchestration.service import (
        OrchestrationDependencies,
        RunOrchestrationService,
    )
    from services.api.composition import demo_session_output

    connection = connect(":memory:")
    events = SqliteOutboxEventPublisher(connection=connection)
    workflow = SqliteWorkflowEngine(connection=connection)
    ledger = SqliteEvidenceLedger(connection=connection)
    budget = FakeBudgetLedger()
    runs = RunOrchestrationService(
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
        endpoint_store=SqliteEndpointStore(connection=connection),
        model_store=SqliteModelStore(connection=connection),
        credentials=FakeCredentialResolver(),
        gateway=gateway if gateway is not None else FakeModelGateway(),
        idempotency=InMemoryIdempotencyStore(),
        events=events,
        projection=SqliteRunProjection(connection, events),
        runs=runs,
        ledger=ledger,
        budget=budget,
        agent_store=SqliteAgentStore(connection=connection),
        project_settings_store=SqliteProjectSettingsStore(connection=connection),
        _connection=connection,
    )


@pytest.fixture
def app_deps() -> ApiDeps:
    return make_app_deps()


@pytest.fixture
def client(app_deps: ApiDeps) -> Iterator[TestClient]:
    app = create_app(app_deps)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def gateway(app_deps: ApiDeps) -> FakeModelGateway:
    gateway = app_deps.gateway
    assert isinstance(gateway, FakeModelGateway)
    return gateway


@pytest.fixture
def credentials(app_deps: ApiDeps) -> FakeCredentialResolver:
    credentials = app_deps.credentials
    assert isinstance(credentials, FakeCredentialResolver)
    return credentials


@pytest.fixture
def run_ready_deps() -> ApiDeps:
    """可冻结 Manifest 的 run 测试装配（受控 pin；定义见 run_fixtures.py）。"""
    from tests.api.run_fixtures import make_run_ready_deps

    return make_run_ready_deps()


@pytest.fixture
def run_ready_client(run_ready_deps: ApiDeps) -> Iterator[TestClient]:
    app = create_app(run_ready_deps)
    with TestClient(app) as test_client:
        yield test_client


def make_endpoint_payload(name: str = "relay-a", **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": name,
        "base_url": "https://relay.example.com/api/v1",
        "api_key": "sk-test-secret-1234",
        "api_style": "chat_completions",
    }
    payload.update(overrides)
    return payload


def create_endpoint(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {**make_endpoint_payload(), **overrides}
    response = client.post(
        "/llm-endpoints",
        json=payload,
        headers={"Idempotency-Key": f"k-{uuid.uuid4()}"},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())
