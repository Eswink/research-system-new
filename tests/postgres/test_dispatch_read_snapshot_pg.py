"""派发读面的一次读 = 一条语句 = 一个快照（PostgreSQL 侧；GOAL-20260918-006 cycle 1 = EC-01）。

与 `tests/adapters/sqlite/test_dispatch_read_snapshot.py` 同形判据（同一条 SQL 的两面在
同一个快照里），差别只在**快照的提供方**：PG 连接是 `autocommit=True`
（`adapters/postgres/db.py`）⇒ 每条语句各自取快照，两条语句之间别的会话可以提交，于是
"重排面已前移、租约面仍是旧值"的撕裂读就会出现在同一个 `kind` 组合里。

判据是**确定性**的（不靠线程调度）：连接代理在**第一条语句返回之后**用**另一条连接**
注入一次只影响租约面的写，然后断言三件事：

1. 整次读面调用**只发了一条语句**（结构判据）；
2. 答案仍是**该次调用开始时**的同一个快照（两件事实同刻 ⇒ `BOTH` + 持有者在列）；
3. 那次注入的写**确实生效**（事后新引擎读得到写后状态）——否则第 2 条无从谈起。

时钟是注入的（`now=...`）⇒ 读面调用里唯一的语句就是取数语句；生产路径上的
`server_now`（`SELECT now()`）在注入时钟下不发生。

反证：把实现拆回两条语句 ⇒ 第二次读拿到写后状态 ⇒ `kind` 掉成 `RETRY_DISPATCH`，
本用例红（实跑记录见 PLAN-20260918-100「证据」）。

Skipped automatically if PostgreSQL is not reachable (tests/postgres/conftest.py).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg
import pytest

from adapters.postgres.db import migrate
from adapters.postgres.workflow_engine import PostgresWorkflowEngine
from packages.application.ports.workflow_engine import (
    DISPATCH_BOTH,
    DISPATCH_RETRY,
    ClaimRequest,
    TaskCompletion,
)
from packages.domain.core import ID
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
_TTL = 600
_WORKER = "w-snapshot-pg"
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
    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE tasks, leases, idempotency_records, outbox_events, workers CASCADE")
    conn.commit()
    conn.close()


class _StatementProbe:
    """连接代理：数语句 + 在**第一条语句返回之后**注入一次外部写。

    语句入口不在此处重新声明——`__getattr__` 把里面的连接透出来，只在第一个语句面
    （`execute`）上包一层计数与注入。探针只记账，不留 SQL 文本，也不改写参数。
    """

    def __init__(self, inner: Any, after_first: Callable[[], None]) -> None:
        self._inner = inner
        self._after_first = after_first
        self.count = 0

    def __getattr__(self, name: str) -> Any:
        target = getattr(self._inner, name)
        if name != "execute":
            return target
        return self._counted(target)

    def _counted(self, target: Any) -> Any:
        def run(*args: Any, **kwargs: Any) -> Any:
            result = target(*args, **kwargs)
            self.count += 1
            if self.count == 1:
                self._after_first()
            return result

        return run


def _engine(*, now: datetime = START, ttl: int = _TTL) -> PostgresWorkflowEngine:
    return PostgresWorkflowEngine(dsn=_dsn(), lease_ttl_seconds=ttl, now=lambda: now)


def _contract(*, backoff: int | None = None) -> TaskContract:
    return TaskContract(
        id="dispatch-snapshot-contract",
        version="1.0",
        purpose="one statement answers both dispatch facts from one snapshot",
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


def _with_a_due_retry_and_a_live_lease(engine: PostgresWorkflowEngine, run_id: ID) -> None:
    """铺出 `BOTH`：一条任务停车等重排（到期）+ 另一条被 claim（租约活）。"""
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


def _expire_every_lease() -> Callable[[], None]:
    """外部写（另一条连接）：把租约改成已过期 ⇒ 只影响租约面，不动重排面。"""

    def _write() -> None:
        writer = psycopg.connect(_dsn(), autocommit=True)
        writer.execute(
            "UPDATE leases SET expires_at = %s",
            ((START - timedelta(seconds=1)),),
        )
        writer.close()

    return _write


def test_pg_the_read_face_answers_from_one_snapshot() -> None:
    run_id = ID.generate()
    setup = _engine()
    _with_a_due_retry_and_a_live_lease(setup, run_id)
    setup.close()

    read_at = START + timedelta(seconds=61)
    reader = PostgresWorkflowEngine(dsn=_dsn(), lease_ttl_seconds=_TTL, now=lambda: read_at)
    probe = _StatementProbe(reader._conn, _expire_every_lease())
    reader._conn = probe

    ownership = reader.dispatch_ownership(run_id.value)

    assert ownership.kind == DISPATCH_BOTH, "答案取的是该次调用开始时的快照，不是写后的状态"
    assert [holder.worker_id for holder in ownership.leases] == [_WORKER]
    assert ownership.retry.due == 1 and ownership.retry.scheduled == 0
    assert probe.count == 1, "一次读面调用只发一条语句（两件事实同一快照）"
    reader.close()

    after = PostgresWorkflowEngine(dsn=_dsn(), lease_ttl_seconds=_TTL, now=lambda: read_at)
    assert after.dispatch_ownership(run_id.value).kind == DISPATCH_RETRY, (
        "注入的写必须真的生效，否则上一条断言没有判别力"
    )
    after.close()
