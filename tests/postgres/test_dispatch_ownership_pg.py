"""Postgres parity: 统一派发读面与 SQLite/Fake 同判据、同时钟源（GOAL-004 cycle 6 = EC-05 ②）。

与 `tests/adapters/sqlite/test_dispatch_ownership.py` 逐条对应：未过期的 claim ⇒ 持有者
（点名 task/worker/fence）；过期或持有者 LOST ⇒ 不算持有，且**回收方在同一次断言里
被要求同判**；重排 + 持有 ⇒ `BOTH`。

差别只在时钟来源——PG 的租约到期写入与分类都走 `server_now`（生产=数据库时钟、测试=注入
时钟），所以这里同样是注入固定时钟、不推进墙钟。

Skipped automatically if PostgreSQL is not reachable (tests/postgres/conftest.py).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.ports.worker_registry import WorkerRegistration
from packages.application.ports.workflow_engine import (
    DISPATCH_BOTH,
    DISPATCH_NONE,
    DISPATCH_WORKER_CLAIM,
    ClaimRequest,
    TaskCompletion,
)
from packages.domain.core import ID, Timestamp
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import (
    AcceptanceCriterion,
    ResearchTask,
    RetryPolicy,
    TaskContract,
)

pytestmark = pytest.mark.postgres

START = datetime(2026, 9, 18, 9, 0, 0, tzinfo=timezone.utc)
_TTL = 60
_WORKER = "w-dispatch-pg"
_CAPABILITY = "python_exec"


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
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events, workers CASCADE")
    conn.commit()
    conn.close()


def _engine(*, now: datetime = START, ttl: int = _TTL) -> PostgresWorkflowEngine:
    return PostgresWorkflowEngine(dsn=_dsn(), lease_ttl_seconds=ttl, now=lambda: now)


def _contract(*, backoff: int | None = None) -> TaskContract:
    return TaskContract(
        id="dispatch-ownership-contract",
        version="1.0",
        purpose="pg parity for the unified dispatch read face",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )


def _execution_task(run_id: ID) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=run_id,
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        idempotency_key=f"task-{ID.generate().value}",
        required_capability=_CAPABILITY,
    )


def _claimed(engine: PostgresWorkflowEngine, run_id: ID) -> str:
    task = _execution_task(run_id)
    engine.submit(task, _contract())
    lease = engine.claim_next(
        ClaimRequest(
            worker_id=_WORKER,
            capabilities=frozenset({_CAPABILITY}),
            partitions=frozenset({0}),
        )
    )
    assert lease is not None, "夹具必须先真的拿到租约"
    return task.id.value


def _register_worker(worker_id: str) -> None:
    from adapters.postgres.worker_registry import PostgresWorkerRegistry

    registry = PostgresWorkerRegistry(dsn=_dsn())
    registry.register(
        WorkerRegistration(
            worker_id=worker_id,
            protocol_version="1",
            runtime_version="0.1.0",
            capabilities=frozenset({_CAPABILITY}),
            backend_kinds=frozenset({"DOCKER"}),
            platform="linux/amd64",
            partition_slots=frozenset({0}),
            max_concurrency=1,
        )
    )
    registry.transition(worker_id, "HANDSHAKE_OK")
    registry.close()


def test_pg_an_unexpired_claim_names_its_holder() -> None:
    run_id = ID.generate()
    task_id = _claimed(_engine(), run_id)

    ownership = _engine().dispatch_ownership(run_id.value)

    assert ownership.kind == DISPATCH_WORKER_CLAIM
    assert [(holder.task_id, holder.worker_id, holder.fence) for holder in ownership.leases] == [
        (task_id, _WORKER, 1)
    ]
    assert ownership.leases[0].expires_at == Timestamp(START + timedelta(seconds=_TTL))


def test_pg_an_expired_lease_is_not_live_and_recovery_agrees() -> None:
    run_id = ID.generate()
    _claimed(_engine(), run_id)

    after = START + timedelta(seconds=_TTL + 1)
    assert _engine(now=after).dispatch_ownership(run_id.value).kind == DISPATCH_NONE
    assert _engine(now=after).recover_expired_leases() == 1, "读面说不活的，回收方必须动手"
    assert _engine(now=after).dispatch_ownership(run_id.value).kind == DISPATCH_NONE


def test_pg_a_lost_workers_lease_is_not_live() -> None:
    from adapters.postgres.worker_registry import PostgresWorkerRegistry
    from packages.domain.workers import WorkerState

    run_id = ID.generate()
    _claimed(_engine(), run_id)
    _register_worker(_WORKER)

    assert _engine().dispatch_ownership(run_id.value).kind == DISPATCH_WORKER_CLAIM

    # 租约的 worker 身份来自 claim 的真实路径（claim_next 写 worker_id），这里只把那个
    # worker 判成 LOST —— 回收判据的第二半。时钟不动：租约还没到期。
    registry = PostgresWorkerRegistry(dsn=_dsn())
    lost = registry.mark_lost(_WORKER)
    registry.close()
    assert lost.state == WorkerState.State.LOST

    ownership = _engine().dispatch_ownership(run_id.value)
    assert ownership.kind == DISPATCH_NONE, "持有者已 LOST ⇒ 不算活（哪怕还没到期）"
    assert _engine().recover_expired_leases() == 1, "回收方同样按 LOST 判据动手"


def test_pg_a_due_retry_beside_a_live_claim_reads_as_both() -> None:
    run_id = ID.generate()
    # 租约 TTL 长过重排退避，否则到期的重排把"活的持有者"也熬过期
    engine = _engine(ttl=600)
    retrying = _execution_task(run_id)
    engine.submit(retrying, _contract(backoff=60))
    lease = engine.acquire_lease(retrying.id.value)
    engine.complete(
        lease,
        TaskCompletion(
            task_id=retrying.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    _claimed(engine, run_id)

    ownership = _engine(now=START + timedelta(seconds=61), ttl=600).dispatch_ownership(run_id.value)

    assert ownership.kind == DISPATCH_BOTH
    assert ownership.retry.due == 1 and ownership.retry.scheduled == 0
    assert len(ownership.leases) == 1
