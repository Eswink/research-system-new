"""Postgres parity: 任务身份读面 + run 装配来源 durability（GOAL-003 cycle 20）。

与 SQLite 侧逐条对应（`tests/adapters/sqlite/test_run_protocol_source_and_success_keys.py`）：

- `task_identities` 按 idempotency key 回答 (key, task_id, status)，与 SQLite 同判据；
- `protocol_source` 经 PG run store 往返一致，且早于来源登记的旧行显式留空。

Skipped automatically if PostgreSQL is not reachable (tests/postgres/conftest.py).
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.run_store import PostgresRunStore
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, TaskKind
from packages.domain.protocol_source import ProtocolSource
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, TaskContract

pytestmark = pytest.mark.postgres


def _dsn() -> str:
    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        os.environ.get(
            "DATABASE_URL",
            "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
        ),
    )


@pytest.fixture(autouse=True, scope="function")
def _clean_postgres() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events, runs CASCADE")
    conn.commit()
    conn.close()


@pytest.fixture(scope="function")
def _engine() -> Iterator[PostgresWorkflowEngine]:
    engine = PostgresWorkflowEngine(dsn=_dsn())
    yield engine
    engine.close()


def _task(run_id: ID, *, key: str) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=run_id,
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.AGENT_SESSION,
        idempotency_key=key,
    )


def _contract() -> TaskContract:
    return TaskContract(
        id="pg-identity-contract",
        version="1.0",
        purpose="pg parity for task identities",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
    )


def test_pg_task_identities_answer_the_stable_identity_and_status(
    _engine: PostgresWorkflowEngine,
) -> None:
    run_id = ID.generate()
    done_key = f"{run_id.value}:phase-a:agent-1"
    done = _task(run_id, key=done_key)
    _engine.submit(done, _contract())
    lease = _engine.acquire_lease(done.id.value)
    _engine.complete(lease, TaskCompletion(task_id=done.id.value, outcome="SUCCEEDED"))

    identities = _engine.task_identities(run_id.value)

    assert [(item.idempotency_key, item.task_id, item.status) for item in identities] == [
        (done_key, done.id.value, ResearchTaskState.State.SUCCEEDED)
    ]
    assert _engine.task_identities(ID.generate().value) == ()


def test_pg_run_store_round_trips_the_recorded_source() -> None:
    store = PostgresRunStore(dsn=_dsn())
    try:
        run_id = ID.generate()
        source = ProtocolSource(draft_id="draft-9", draft_revision=4)
        store.save_run(
            ResearchRun(
                id=run_id,
                project_id="project-1",
                protocol_id="protocol-1",
                protocol_source=source,
            )
        )
        legacy_id = ID.generate()
        store.save_run(ResearchRun(id=legacy_id, project_id="project-1", protocol_id="protocol-1"))

        reloaded = store.get_run(run_id.value)
        assert reloaded.protocol_source == source
        moved = reloaded.transition(ResearchRunState.Transition.START_COMPILE)
        assert moved.protocol_source == source, "状态迁移必须保留来源"
        assert store.get_run(legacy_id.value).protocol_source is None
    finally:
        store.close()
