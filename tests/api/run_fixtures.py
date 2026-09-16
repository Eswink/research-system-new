"""Run 生命周期测试夹具：可冻结 Manifest 的完整装配（受控 pin + health）。"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, replace
from typing import Any

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
from packages.application.ports import (
    ApprovalStore,
    ArtifactStore,
    CatalogSnapshot,
    EvidenceLedger,
    PreflightContext,
    ProjectSettings,
)
from packages.application.protocol_authoring.service import DraftService
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


@dataclass(frozen=True)
class _RunReadyContext:
    """make_run_ready_deps 的构建中间态（规避单函数超行数阈值）。"""

    credentials: FakeCredentialResolver
    connection: sqlite3.Connection
    events: SqliteOutboxEventPublisher
    pricing_store: FakePricingSnapshotStore
    shared: _RunReadyStores
    runs: RunOrchestrationService
    preflight: PreflightContext
    # 预算账本：与生产同侧——编排链、preflight 上下文与控制面读取共享同一实例
    # （分开装配会让 preflight 预留写进 A、API 读 B，预算/预测永远为空）。
    budget: FakeBudgetLedger


def _run_ready_context() -> _RunReadyContext:
    from adapters.sqlite.db import connect
    from services.api.approvals import ApprovalRegistry

    credentials = FakeCredentialResolver()
    credentials.register("LLM_MAIN_KEY", "sk-test-e2e-secret")
    connection = connect(":memory:")
    events = SqliteOutboxEventPublisher(connection=connection)
    pricing_store = FakePricingSnapshotStore()
    # WP-C：编排产出与控制面读取共享同一 artifact store。
    # WP-H：编排链与 ApiDeps 共享同一审批 registry（注册与裁决同实例）。
    # WP-D：同一 evidence ledger（编排写、inspection 读）。
    shared = _RunReadyStores(
        registry=ApprovalRegistry(),
        artifacts=FakeArtifactStore(),
        ledger=FakeEvidenceLedger(),
    )
    budget = FakeBudgetLedger()
    runs = _build_orchestration(connection, events, pricing_store, shared, budget)
    return _RunReadyContext(
        credentials=credentials,
        connection=connection,
        events=events,
        pricing_store=pricing_store,
        shared=shared,
        runs=runs,
        preflight=_build_preflight(credentials, budget),
        budget=budget,
    )


def make_run_ready_deps(*, gateway: FakeModelGateway | None = None) -> ApiDeps:
    """可冻结 Manifest 的 run 测试装配（受控 pin + 完整 preflight context）。

    WP-D（PLAN-040）：与生产 SQLite 开发组成对齐——agent/settings/override/
    project/worker-registry/experiment store 用同连接 SQLite 实现，evidence
    ledger 为编排与读取端共享的受控 Fake（修正旧注释漂移：ledger 此前未注入
    ApiDeps，导致 live e2e 从未走过 evidence/claims/experiments 真实读链）。
    """
    from adapters.fakes.memory_store import FakeMemoryStore
    from adapters.sqlite.notification_read_store import SqliteNotificationReadStore
    from services.api.assembly import policy_bindings

    ctx = _run_ready_context()
    return ApiDeps(
        endpoint_store=SqliteEndpointStore(connection=ctx.connection),
        model_store=SqliteModelStore(connection=ctx.connection),
        credentials=ctx.credentials,
        gateway=gateway if gateway is not None else FakeModelGateway(),
        idempotency=InMemoryIdempotencyStore(),
        events=ctx.events,
        projection=SqliteRunProjection(ctx.connection, ctx.events),
        approvals=ctx.shared.registry,
        runs=ctx.runs,
        workflow=ctx.runs._deps.workflow,
        pricing_snapshot_store=ctx.pricing_store,
        preflight_override=ctx.preflight,
        protocol_draft_service=_make_draft_service(ctx.connection),
        # WP-Z live e2e 只读链装配：ledger/通知读状态/memory/artifact 均为受控 Fake。
        budget=ctx.budget,
        notification_reads=SqliteNotificationReadStore(connection=ctx.connection),
        memory=FakeMemoryStore(),
        artifacts=ctx.shared.artifacts,
        ledger=ctx.shared.ledger,
        **policy_bindings(),  # PLAN-049：策略面与生产同源（缺文件 → None）
        **_run_ready_sqlite_stores(ctx.connection),
        _connection=ctx.connection,
    )


def _run_ready_sqlite_stores(connection: sqlite3.Connection) -> dict[str, Any]:
    """live e2e 与生产 SQLite 组成同侧的配置/注册/实验存储（共享连接）。"""
    from adapters.sqlite.agent_store import SqliteAgentStore
    from adapters.sqlite.catalog_override_store import SqliteCatalogOverrideStore
    from adapters.sqlite.experiment_store import SqliteExperimentStore
    from adapters.sqlite.library_store import SqliteLibraryStore
    from adapters.sqlite.ops_store import SqliteOpsStore
    from adapters.sqlite.project_settings_store import SqliteProjectSettingsStore
    from adapters.sqlite.project_store import SqliteProjectStore
    from adapters.sqlite.run_store import SqliteRunStore
    from adapters.sqlite.tool_pack_store import SqliteToolPackStore
    from adapters.sqlite.tool_provider_registry import SqliteToolProviderRegistry
    from adapters.sqlite.worker_registry import SqliteWorkerRegistry

    return {
        "agent_store": SqliteAgentStore(connection=connection),
        "project_settings_store": SqliteProjectSettingsStore(connection=connection),
        "project_store": SqliteProjectStore(connection=connection),
        "library_store": SqliteLibraryStore(connection=connection),
        "catalog_overrides": SqliteCatalogOverrideStore(connection=connection),
        "worker_registry": SqliteWorkerRegistry(connection=connection),
        "experiment_store": SqliteExperimentStore(connection=connection),
        # ops 写面（PLAN-059）：live e2e 要真的走 HTTP 写链，不能只断言"能力不可用"。
        "ops_store": SqliteOpsStore(connection=connection),
        # 供应链治理写面（PLAN-060）：live e2e 要真的登记→批准→吊销。
        "tool_provider_registry": SqliteToolProviderRegistry(connection=connection),
        # ToolPack 供应链写面（PLAN-064 / EC-02）：install / approve-update / revoke。
        "tool_pack_store": SqliteToolPackStore(connection=connection),
        # 与生产 composition 同侧：run 行落在共享连接上，派发面（claim_next）
        # 才读得到 canonical state —— 协作式暂停的事实来源（PLAN-20260914-048）。
        "runs_store": SqliteRunStore(connection=connection),
    }


def _make_draft_service(
    connection: sqlite3.Connection,
) -> DraftService:
    """run 装配的草稿服务（与 base deps 同构造）。"""
    from adapters.contracts.protocol_text_loader import load_protocol_from_text
    from adapters.sqlite.protocol_draft_store import SqliteProtocolDraftStore
    from services.api.routers.protocol_drafts import default_templates

    return DraftService(
        SqliteProtocolDraftStore(connection=connection),
        default_templates(),
        text_loader=load_protocol_from_text,
    )


@dataclass(frozen=True)
class _RunReadyStores:
    """编排链与控制面共享的 store 实例（registry/artifacts/ledger 同对象）。"""

    registry: ApprovalStore
    artifacts: ArtifactStore
    ledger: EvidenceLedger


def _build_orchestration(
    connection: object,
    events: object,
    pricing_store: FakePricingSnapshotStore,
    shared: _RunReadyStores,
    budget: FakeBudgetLedger,
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
            artifacts=shared.artifacts,
            events=events,
            budget=budget,
            ledger=shared.ledger,
            pricing=pricing,
            pricing_store=pricing_store,
            approvals=shared.registry,
        )
    )


def _build_preflight(
    credentials: FakeCredentialResolver, budget: FakeBudgetLedger
) -> PreflightContext:
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
        provider_health={key: EndpointHealth.HEALTHY for key in pinned.tool_providers},
        workspace_available={key: True for key in pinned.workspaces},
        budget_ledger=budget,
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
