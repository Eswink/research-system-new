"""Run 生命周期测试夹具：可冻结 Manifest 的完整装配（受控 pin + health）。"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from adapters.fakes.agent_runtime import FakeAgentRuntime
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.fakes.credential_resolver import FakeCredentialResolver
from adapters.fakes.evidence_ledger import FakeEvidenceLedger
from adapters.fakes.model_gateway import FakeModelGateway
from adapters.fakes.policy_evaluator import FakePolicyEvaluator
from adapters.fakes.pricing_snapshot_store import FakePricingSnapshotStore
from adapters.sqlite.endpoint_store import SqliteEndpointStore
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.model_store import SqliteModelStore
from adapters.sqlite.run_projection import SqliteRunProjection
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.cost.pricing import unpriced_table
from packages.application.ports import CatalogSnapshot, PreflightContext, ProjectSettings
from packages.application.run_orchestration.service import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from packages.domain.enums import AcceptanceCriterionType, EndpointHealth
from packages.domain.tasks import AcceptanceCriterion, TaskContract
from services.api.app import create_app
from services.api.catalog import load_catalog_snapshot
from services.api.composition import ApiDeps
from services.api.idempotency import InMemoryIdempotencyStore

_PROVIDERS = ("openhands_workspace", "m12_artifact", "ncbi_eutils")


def replace_catalog_with_pins(catalog: object) -> object:
    """测试夹具：注入显式 pin + sort_analysis 契约（受控环境）。

    - tool pack pin：避免 preflight SUPPLY_CHAIN_UNPINNED；
    - sort_analysis 契约：examples/protocols/sort_analysis_v1.yaml
      全 phase 有契约时 start_run 可走完整成功链（freeze → execute）。
    """
    from packages.application.ports import CatalogSnapshot

    assert isinstance(catalog, CatalogSnapshot)
    contracts = dict(catalog.task_contracts)
    contracts.setdefault(
        "sort_analysis_execution",
        TaskContract(
            id="sort_analysis_execution",
            version="1.0.0",
            purpose="Analyze the input repository and produce a report artifact.",
            required_capabilities=["workspace.read", "workspace.write.code", "code.execute"],
            acceptance_criteria=[
                AcceptanceCriterion(
                    type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact="analysis_report"
                )
            ],
            timeout_seconds=120,
        ),
    )
    contracts.setdefault(
        "sort_analysis_review",
        TaskContract(
            id="sort_analysis_review",
            version="1.0.0",
            purpose="Independently review the analysis report.",
            required_capabilities=["workspace.read", "evidence.read"],
            acceptance_criteria=[
                AcceptanceCriterion(
                    type=AcceptanceCriterionType.EVIDENCE_COVERAGE, minimum_sources=1
                )
            ],
            timeout_seconds=120,
        ),
    )
    return replace(
        catalog,
        task_contracts=contracts,
        tool_pack_digests={provider_id: "sha256:" + "1" * 64 for provider_id in _PROVIDERS},
    )


def make_run_ready_deps(*, gateway: FakeModelGateway | None = None) -> ApiDeps:
    """可冻结 Manifest 的 run 测试装配（受控 pin + 完整 preflight context）。"""
    from adapters.sqlite.db import connect
    from services.api.approvals import ApprovalRegistry

    credentials = FakeCredentialResolver()
    credentials.register("LLM_MAIN_KEY", "sk-test-e2e-secret")
    connection = connect(":memory:")
    events = SqliteOutboxEventPublisher(connection=connection)
    pricing_store = FakePricingSnapshotStore()
    runs = _build_orchestration(connection, events, pricing_store)
    preflight = _build_preflight(credentials)
    return ApiDeps(
        endpoint_store=SqliteEndpointStore(connection=connection),
        model_store=SqliteModelStore(connection=connection),
        credentials=credentials,
        gateway=gateway if gateway is not None else FakeModelGateway(),
        idempotency=InMemoryIdempotencyStore(),
        events=events,
        projection=SqliteRunProjection(connection, events),
        approvals=ApprovalRegistry(),
        runs=runs,
        workflow=runs._deps.workflow,
        pricing_snapshot_store=pricing_store,
        preflight_override=preflight,
        _connection=connection,
    )


def _build_orchestration(
    connection: object,
    events: object,
    pricing_store: FakePricingSnapshotStore,
) -> RunOrchestrationService:
    """装配正式编排链（Fake runtime + SQLite workflow/outbox，共享连接）。"""
    from sqlite3 import Connection

    from packages.application.ports import EventPublisher

    assert isinstance(connection, Connection)
    assert isinstance(events, EventPublisher)
    workflow = SqliteWorkflowEngine(connection=connection)
    pricing = unpriced_table()
    return RunOrchestrationService(
        OrchestrationDependencies(
            runtime=FakeAgentRuntime(),
            workflow=workflow,
            artifacts=FakeArtifactStore(),
            events=events,
            budget=FakeBudgetLedger(),
            ledger=FakeEvidenceLedger(),
            pricing=pricing,
            pricing_store=pricing_store,
        )
    )


def _build_preflight(credentials: FakeCredentialResolver) -> PreflightContext:
    """完整 preflight context：health/policy/ledger/pin 全注入（受控夹具）。"""

    catalog = load_catalog_snapshot()
    pinned = replace_catalog_with_pins(catalog)
    assert isinstance(pinned, CatalogSnapshot)
    project = ProjectSettings(
        project_id="example-project",
        team_template_id="standard",
        default_model_profile_id="research_strong",
        budget_policy_id="low_cost",
        workspace_backend="openhands_docker",
    )
    return PreflightContext(
        catalog=pinned,
        project=project,
        credentials=credentials,
        endpoint_health={key: EndpointHealth.HEALTHY for key in pinned.endpoints},
        provider_health={key: True for key in pinned.tool_providers},
        workspace_available={key: True for key in pinned.workspaces},
        budget_ledger=FakeBudgetLedger(),
        policy_evaluator=FakePolicyEvaluator(),
    )


@pytest.fixture
def run_ready_deps() -> ApiDeps:
    return make_run_ready_deps()


@pytest.fixture
def run_ready_client(run_ready_deps: ApiDeps) -> Iterator[TestClient]:
    app = create_app(run_ready_deps)
    with TestClient(app) as test_client:
        yield test_client
