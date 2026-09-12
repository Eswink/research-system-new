"""Port 实现注册表：contract suite 的单一事实源。

M6 起真实 adapter（OpenHandsRuntimeAdapter）与 Fake 共享同一套 contract
suite：Fake 保持无参工厂语义；真实 adapter 经模块级工厂注入确定性依赖
（TestLLM 脚本化 LLM + 隔离临时目录，无网络/无真实凭据）。
"""

from __future__ import annotations

import os as _os
import tempfile
from collections.abc import Callable
from pathlib import Path

import pytest
from openhands.sdk.llm import Message, TextContent
from openhands.sdk.testing import TestLLM
from openhands.sdk.workspace.local import LocalWorkspace

from adapters.fakes import (
    FakeAgentRuntime,
    FakeArtifactStore,
    FakeBudgetLedger,
    FakeCredentialResolver,
    FakeEndpointStore,
    FakeEvalReportStore,
    FakeEventPublisher,
    FakeEvidenceLedger,
    FakeExecutionBackend,
    FakeExecutionJobQueue,
    FakeMemoryStore,
    FakeModelGateway,
    FakePolicyEvaluator,
    FakeResourceCatalog,
    FakeRetrievalIndex,
    FakeTelemetrySink,
    FakeToolPackStore,
    FakeToolProvider,
    FakeWorkerRegistry,
    FakeWorkflowEngine,
    FakeWorkspaceBackend,
    NullTelemetrySink,
)
from adapters.index.in_memory_index import InMemoryRetrievalIndex
from adapters.openhands.runtime_adapter import OpenHandsRuntimeAdapter
from adapters.openhands.session_types import AdapterDependencies
from adapters.postgres.artifact_store import PostgresArtifactStore
from adapters.postgres.budget_ledger import PostgresBudgetLedger
from adapters.postgres.evidence_ledger import PostgresEvidenceLedger
from adapters.postgres.execution_job_queue import PostgresExecutionJobQueue
from adapters.postgres.memory_store import PostgresMemoryStore
from adapters.postgres.worker_registry import PostgresWorkerRegistry
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.evidence_ledger import SqliteEvidenceLedger
from adapters.sqlite.memory_store import SqliteMemoryStore
from adapters.sqlite.worker_registry import SqliteWorkerRegistry
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from adapters.workspace.file_backend import FileWorkspaceBackend

Factory = Callable[[], object]

# 真实 adapter 的确定性装配（contract 级共享；测试进程退出自动清理）
_CONTRACT_WORKSPACE = Path(tempfile.mkdtemp(prefix="contract-openhands-ws-"))
_CONTRACT_PERSIST = tempfile.TemporaryDirectory(prefix="contract-openhands-persist-")


def _file_workspace_factory() -> FileWorkspaceBackend:
    """无参工厂：隔离临时根目录的 FileWorkspaceBackend。"""
    root = Path(tempfile.mkdtemp(prefix="contract-file-workspace-"))
    return FileWorkspaceBackend(root)


def _postgres_memory_factory() -> PostgresMemoryStore:
    """No-arg factory: reads DSN from env, skips if PG not available."""
    dsn = _os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )
    try:
        import psycopg

        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=2)
        conn.close()
    except Exception:
        pytest.skip("PostgreSQL not reachable")
    from adapters.postgres.db import migrate as pg_migrate

    pg_migrate(dsn)
    return PostgresMemoryStore(dsn=dsn)


def _postgres_workflow_factory() -> PostgresWorkflowEngine:
    """No-arg factory: PG engine against live DB; skip if PG not reachable.

    Lets the WorkflowEngine contract suite run the same scenarios against the
    production PostgreSQL adapter (M14 requirement), not only Fake/SQLite.
    The contract suite assumes per-engine clean state (Fake/SQLite are
    in-memory), so the PG factory truncates the shared task tables."""
    dsn = _os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )
    try:
        import psycopg

        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=2)
        conn.close()
    except Exception:
        pytest.skip("PostgreSQL not reachable")
    from adapters.postgres.db import migrate as pg_migrate

    pg_migrate(dsn)
    import psycopg

    conn = psycopg.connect(dsn, autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    conn.close()
    return PostgresWorkflowEngine(dsn=dsn)


def _pg_dsn_or_skip() -> str:
    """Resolve PG DSN; skip if unreachable (contract registry convention)."""
    dsn = _os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )
    try:
        import psycopg

        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=2)
        conn.close()
    except Exception:
        pytest.skip("PostgreSQL not reachable")
    from adapters.postgres.db import migrate as pg_migrate

    pg_migrate(dsn)
    return dsn


_TRUNCATE_STATEMENTS = {
    "m12_sources, m12_evidence, m12_claims, m12_relations, m12_memory": (
        "TRUNCATE m12_sources, m12_evidence, m12_claims, m12_relations, m12_memory CASCADE"
    ),
    "budget_reservations, budget_usage_entries": (
        "TRUNCATE budget_reservations, budget_usage_entries CASCADE"
    ),
    "workers": "TRUNCATE workers CASCADE",
    "tasks, leases, idempotency_records, outbox_events, execution_jobs": (
        "TRUNCATE tasks, leases, idempotency_records, outbox_events, execution_jobs CASCADE"
    ),
    "artifacts": "TRUNCATE artifacts CASCADE",
}


def _pg_truncate(tables: str) -> None:
    import psycopg

    dsn = _os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )
    conn = psycopg.connect(dsn, autocommit=True)
    # Literal dispatch: scanner-accepted form; fail closed on unknown sets.
    if tables == "m12_sources, m12_evidence, m12_claims, m12_relations, m12_memory":
        conn.execute(
            "TRUNCATE m12_sources, m12_evidence, m12_claims, m12_relations, m12_memory CASCADE"
        )
    elif tables == "budget_reservations, budget_usage_entries":
        conn.execute("TRUNCATE budget_reservations, budget_usage_entries CASCADE")
    elif tables == (
        "m12_sources, m12_evidence, m12_claims, m12_relations,"
        " m12_memory, approvals, budget_reservations, budget_usage_entries"
    ):
        conn.execute(
            "TRUNCATE m12_sources, m12_evidence, m12_claims, m12_relations,"
            " m12_memory, approvals, budget_reservations, budget_usage_entries"
            " CASCADE"
        )
    elif tables == "workers":
        conn.execute("TRUNCATE workers CASCADE")
    elif tables == "tasks, leases, idempotency_records, outbox_events, execution_jobs":
        conn.execute(
            "TRUNCATE tasks, leases, idempotency_records, outbox_events, execution_jobs CASCADE"
        )
    elif tables == "artifacts":
        conn.execute("TRUNCATE artifacts CASCADE")
    else:
        raise RuntimeError("unregistered truncate set: use a literal branch")
    conn.commit()
    conn.close()


def _postgres_evidence_factory() -> PostgresEvidenceLedger:
    dsn = _pg_dsn_or_skip()
    _pg_truncate(
        "m12_sources, m12_evidence, m12_claims, m12_relations,"
        " m12_memory, approvals, budget_reservations, budget_usage_entries"
    )
    return PostgresEvidenceLedger(dsn=dsn)


def _postgres_budget_factory() -> PostgresBudgetLedger:
    dsn = _pg_dsn_or_skip()
    _pg_truncate("budget_reservations, budget_usage_entries")
    return PostgresBudgetLedger(dsn=dsn)


def _postgres_worker_registry_factory() -> PostgresWorkerRegistry:
    dsn = _pg_dsn_or_skip()
    _pg_truncate("workers")
    return PostgresWorkerRegistry(dsn=dsn)


def _postgres_execution_job_queue_factory() -> PostgresExecutionJobQueue:
    dsn = _pg_dsn_or_skip()
    _pg_truncate("tasks, leases, idempotency_records, outbox_events, execution_jobs")
    return PostgresExecutionJobQueue(dsn=dsn)


def _postgres_artifact_factory() -> PostgresArtifactStore:
    dsn = _pg_dsn_or_skip()
    _pg_truncate("artifacts")
    root = Path(tempfile.mkdtemp(prefix="contract-pg-artifacts-"))
    return PostgresArtifactStore(dsn=dsn, blob_dir=root)


def _openhands_runtime_factory() -> OpenHandsRuntimeAdapter:
    """无参工厂：TestLLM 脚本化响应 + Fake 依赖 + 隔离 workspace。"""
    llm = TestLLM.from_messages([
        Message(role="assistant", content=[TextContent(text="Done.")]),
        Message(role="assistant", content=[TextContent(text="All set.")]),
    ])
    deps = AdapterDependencies(
        credential_resolver=FakeCredentialResolver({"LLM_KEY": "sk-contract"}),
        policy_evaluator=FakePolicyEvaluator(),
        build_llm=lambda spec: llm,
        build_workspace=lambda lease, session_id: LocalWorkspace(
            working_dir=str(_CONTRACT_WORKSPACE)
        ),
        persistence_dir=_CONTRACT_PERSIST.name,
    )
    return OpenHandsRuntimeAdapter(deps)


PORT_IMPLEMENTATIONS: dict[str, list[Factory]] = {
    "agent_runtime": [FakeAgentRuntime, _openhands_runtime_factory],
    "workflow_engine": [
        FakeWorkflowEngine,
        SqliteWorkflowEngine,
        _postgres_workflow_factory,
    ],
    "model_gateway": [FakeModelGateway],
    "tool_provider": [FakeToolProvider],
    "tool_pack_store": [FakeToolPackStore],
    "workspace_backend": [FakeWorkspaceBackend, _file_workspace_factory],
    "execution_backend": [FakeExecutionBackend],
    "artifact_store": [
        FakeArtifactStore,
        SqliteArtifactStore,
        _postgres_artifact_factory,
    ],
    "event_publisher": [FakeEventPublisher, SqliteOutboxEventPublisher],
    "eval_report_store": [FakeEvalReportStore],
    "evidence_ledger": [
        FakeEvidenceLedger,
        SqliteEvidenceLedger,
        _postgres_evidence_factory,
    ],
    "retrieval_index": [FakeRetrievalIndex, InMemoryRetrievalIndex],
    "policy_evaluator": [FakePolicyEvaluator],
    "credential_resolver": [FakeCredentialResolver],
    "memory_store": [FakeMemoryStore, SqliteMemoryStore, _postgres_memory_factory],
    "budget_ledger": [FakeBudgetLedger, _postgres_budget_factory],
    "endpoint_store": [FakeEndpointStore],
    "resource_catalog": [FakeResourceCatalog],
    "telemetry_sink": [FakeTelemetrySink, NullTelemetrySink],
    "worker_registry": [
        FakeWorkerRegistry,
        SqliteWorkerRegistry,
        _postgres_worker_registry_factory,
    ],
    "execution_job_queue": [
        FakeExecutionJobQueue,
        _postgres_execution_job_queue_factory,
    ],
}
