"""统一派发读面的"活"判据（GOAL-004 cycle 6 = EC-05 ②，注入时钟）。

契约套件钉的是三实现共同的部分（有没有持有者、按 run 回答）；本文件钉**只有持久化
实现才有的强度**：读面说的"活"必须与 `recover_expired_leases` 的回收判据互补——

- 租约行还在但已过期 ⇒ **不算持有**（回收方马上会动手：用例同时断言这一点，
  避免读面与回收方各说各话）；
- 持有者 worker 已 LOST ⇒ 不算持有（同样与回收方同判）；
- 未过期 ⇒ 持有；控制面自己持有的租约（`acquire_lease`，无 worker_id）同样算持有，
  且持有者如实回答 `worker_id=None`（不编一个 worker 出来）。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from adapters.sqlite.db import connect as sqlite_connect
from adapters.sqlite.worker_registry import SqliteWorkerRegistry
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.worker_registry import WorkerRegistration
from packages.application.ports.workflow_engine import (
    DISPATCH_BOTH,
    DISPATCH_NONE,
    DISPATCH_RETRY,
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

START = datetime(2026, 9, 18, 9, 0, 0, tzinfo=timezone.utc)
_TTL = 60
_WORKER = "w-dispatch"
_CAPABILITY = "python_exec"


class _Clock:
    def __init__(self, value: datetime = START) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


def _contract(*, backoff: int | None = None) -> TaskContract:
    return TaskContract(
        id="dispatch-ownership-contract",
        version="1.0",
        purpose="liveness must match the recovery rule",
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


def _registry(connection: sqlite3.Connection, clock: _Clock) -> SqliteWorkerRegistry:
    registry = SqliteWorkerRegistry(connection=connection, now=clock)
    registry.register(
        WorkerRegistration(
            worker_id=_WORKER,
            protocol_version="1",
            runtime_version="0.1.0",
            capabilities=frozenset({_CAPABILITY}),
            backend_kinds=frozenset({"DOCKER"}),
            platform="linux/amd64",
            partition_slots=frozenset({0}),
            max_concurrency=1,
        )
    )
    registry.transition(_WORKER, "HANDSHAKE_OK")
    return registry


def _claimed(engine: SqliteWorkflowEngine, run_id: ID) -> str:
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


def test_an_unexpired_claim_reads_as_a_live_holder() -> None:
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=_TTL, now=_Clock())
    run_id = ID.generate()
    task_id = _claimed(engine, run_id)

    ownership = engine.dispatch_ownership(run_id.value)

    assert ownership.kind == DISPATCH_WORKER_CLAIM
    assert [(holder.task_id, holder.worker_id, holder.fence) for holder in ownership.leases] == [
        (task_id, _WORKER, 1)
    ]
    assert ownership.leases[0].expires_at == Timestamp(START + timedelta(seconds=_TTL)), (
        "到期时刻来自 canonical 租约行，不是读面自己算的"
    )
    engine.close()


def test_an_expired_lease_is_not_a_live_holder_and_recovery_agrees() -> None:
    """读面与回收方必须同判：读面说"不活"的，回收就该动手（判据互补）。"""
    clock = _Clock()
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=_TTL, now=clock)
    run_id = ID.generate()
    _claimed(engine, run_id)

    clock.value = START + timedelta(seconds=_TTL + 1)
    ownership = engine.dispatch_ownership(run_id.value)

    assert ownership.kind == DISPATCH_NONE, "过期租约不是持有者"
    assert engine.recover_expired_leases() == 1, "同一时刻回收方必须把它算作该回收"
    assert engine.dispatch_ownership(run_id.value).kind == DISPATCH_NONE, "回收后仍无人持有"
    engine.close()


def test_the_boundary_second_is_still_live() -> None:
    """`expires_at == now` 仍算活：回收判据是 `expires_at < now`（严格小于）。"""
    clock = _Clock()
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=_TTL, now=clock)
    run_id = ID.generate()
    _claimed(engine, run_id)

    clock.value = START + timedelta(seconds=_TTL)

    assert engine.dispatch_ownership(run_id.value).kind == DISPATCH_WORKER_CLAIM
    assert engine.recover_expired_leases() == 0, "回收方也不能在边界秒动手"
    engine.close()


def test_a_lost_workers_lease_is_not_a_live_holder() -> None:
    clock = _Clock()
    connection = sqlite_connect(":memory:")
    engine = SqliteWorkflowEngine(connection=connection, lease_ttl_seconds=_TTL, now=clock)
    run_id = ID.generate()
    _claimed(engine, run_id)
    registry = _registry(connection, clock)

    assert engine.dispatch_ownership(run_id.value).kind == DISPATCH_WORKER_CLAIM, (
        "先确认它本来是活的"
    )

    registry.mark_lost(_WORKER)

    ownership = engine.dispatch_ownership(run_id.value)
    assert ownership.kind == DISPATCH_NONE, "持有者已 LOST ⇒ 不算活（哪怕还没到期）"
    assert engine.recover_expired_leases() == 1, "回收方同样按 LOST 判据动手"
    engine.close()
    registry.close()
    connection.close()


def test_a_control_plane_lease_has_no_worker_but_still_counts() -> None:
    """`acquire_lease`（agent session 投递）也是派发方：持有者如实回答"没有 worker"。"""
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=_TTL, now=_Clock())
    run_id = ID.generate()
    task = _execution_task(run_id)
    engine.submit(task, _contract())
    engine.acquire_lease(task.id.value)

    ownership = engine.dispatch_ownership(run_id.value)

    assert ownership.kind == DISPATCH_WORKER_CLAIM
    assert ownership.leases[0].worker_id is None, "控制面持有 ⇒ 不编造 worker 身份"
    assert ownership.leases[0].task_id == task.id.value
    engine.close()


def test_a_waiting_retry_alone_reads_as_retry_dispatch() -> None:
    clock = _Clock()
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=_TTL, now=clock)
    run_id = ID.generate()
    task = _execution_task(run_id)
    engine.submit(task, _contract(backoff=600))
    lease = engine.acquire_lease(task.id.value)
    engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )

    ownership = engine.dispatch_ownership(run_id.value)

    assert ownership.kind == DISPATCH_RETRY
    assert ownership.retry.scheduled == 1
    assert ownership.retry.next_retry_at == Timestamp(START + timedelta(seconds=600))
    assert ownership.leases == (), "完成即释放租约 ⇒ 只剩重排这一件事实"
    engine.close()


def test_a_due_retry_beside_a_live_claim_reads_as_both() -> None:
    clock = _Clock()
    # 租约 TTL 必须长过重排退避，否则到期的重排正好把"活的持有者"也熬过期
    engine = SqliteWorkflowEngine(":memory:", lease_ttl_seconds=600, now=clock)
    run_id = ID.generate()
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

    clock.value = START + timedelta(seconds=61)
    ownership = engine.dispatch_ownership(run_id.value)

    assert ownership.kind == DISPATCH_BOTH
    assert ownership.retry.due == 1 and ownership.retry.scheduled == 0
    assert len(ownership.leases) == 1
    engine.close()
