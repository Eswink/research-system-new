"""PG 故障注入变体(postgres 标记,需 live PostgreSQL)。

telemetry 故障(exporter 500 / collector down)下,PG workflow 事务、
lease claim/heartbeat/complete 与 outbox 写入保持与 telemetry-off baseline
一致。PG 不可达时跳过(m0 离线不受影响)。
"""

from __future__ import annotations

import os

import pytest

from adapters.otel.config import OtelConfig
from adapters.otel.provider import build_telemetry_sink
from tests.contracts.fixtures import research_task, task_contract
from tests.observability.fault_collector import FaultyCollector

pytestmark = pytest.mark.postgres

_DSN_ENV = ("RESEARCHOS_POSTGRES_DSN", "DATABASE_URL", "POSTGRES_DSN")
_DEFAULT_DSN = "postgresql://research_os:research_os_m14_test@localhost:15432/research_os"


def _dsn() -> str:
    for key in _DSN_ENV:
        value = os.environ.get(key)
        if value and value.strip():
            return value.strip()
    return _DEFAULT_DSN


@pytest.fixture(scope="module", autouse=True)
def _pg_available() -> None:
    try:
        import psycopg

        conn = psycopg.connect(_dsn(), autocommit=True, connect_timeout=2)
        conn.close()
    except Exception:
        pytest.skip("PostgreSQL not reachable")


def _fresh_engine(dsn: str, telemetry: object = None) -> object:
    from adapters.postgres.db import connect as pg_connect
    from adapters.postgres.db import migrate as pg_migrate
    from adapters.postgres.workflow_engine import PostgresWorkflowEngine

    pg_migrate(dsn)
    conn = pg_connect(dsn)
    conn.autocommit = True
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events CASCADE")
    conn.commit()
    return PostgresWorkflowEngine(connection=conn, telemetry=telemetry)  # type: ignore[arg-type]


def _task(task_id: str, agent: str, idem: str) -> object:
    from dataclasses import replace

    from packages.domain.core import ID

    return replace(
        research_task(task_id), id=ID(task_id), assigned_agent_id=agent, idempotency_key=idem
    )


def _run(engine: object) -> list[tuple[str, str]]:
    task_a = _task("6f8f56a0-5c2a-4b3e-9f1d-2c7a4e8b6d90", "agent-1", "idem-a")
    task_b = _task("6f8f56a0-5c2a-4b3e-9f1d-2c7a4e8b6d91", "agent-2", "idem-b")
    engine.submit(task_a, task_contract())  # type: ignore[attr-defined]
    engine.submit(task_b, task_contract())  # type: ignore[attr-defined]
    lease_a = engine.acquire_lease(task_a.id.value)  # type: ignore[attr-defined]
    lease_b = engine.acquire_lease(task_b.id.value)  # type: ignore[attr-defined]
    lease_a = engine.heartbeat(lease_a)  # type: ignore[attr-defined]
    from packages.application.ports.workflow_engine import TaskCompletion

    engine.complete(lease_a, TaskCompletion(task_id=task_a.id.value, outcome="SUCCEEDED"))  # type: ignore[attr-defined]
    engine.complete(lease_b, TaskCompletion(task_id=task_b.id.value, outcome="FAILED"))  # type: ignore[attr-defined]
    rows = engine.list_tasks(str(task_a.run_id.value))  # type: ignore[attr-defined]
    return sorted((str(row.task.id.value), row.task.status) for row in rows)


@pytest.mark.parametrize("mode", ["500", "refused"])
def test_pg_workflow_state_equal_to_telemetry_off_baseline(mode: str) -> None:
    dsn = _dsn()
    baseline = _run(_fresh_engine(dsn))
    collector = FaultyCollector()
    if mode == "refused":
        # collector down:先取 endpoint 再停服务,端口保持连接拒绝
        collector.start()
        endpoint = collector.endpoint
        collector.stop()
    else:
        collector.start()
        collector.set_mode(mode)
        endpoint = collector.endpoint
    try:
        failsafe = build_telemetry_sink(OtelConfig(enabled=True, endpoint=endpoint))
        state = _run(_fresh_engine(dsn, failsafe))
        failsafe.shutdown()
        assert state == baseline
    finally:
        collector.stop()
