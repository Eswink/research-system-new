"""统一派发读面契约（GOAL-004 cycle 6 = EC-05 ②）：三实现同一判据。

`dispatch_ownership(run_id)` 要回答运维读面的一个问题——"这条 run 现在有没有活的派发
方、是哪一个"——而两个派发方此前各持一半事实：retry dispatch 只看 `PAUSED` 的重排到期，
worker plane 的租约事实完全不在读面。这里钉**实现无关**的不变量：

1. 没有租约、没有重排 ⇒ `NONE`（未知 run 同形，不是异常）；
2. 一条被 claim 的租约 ⇒ `WORKER_CLAIM`，且持有者点名 task/worker/fence；
3. 持有者完成任务 ⇒ 租约消失 ⇒ 回到 `NONE`（读面跟着 canonical 事实走）；
4. 读面按 run 回答（另一条 run 的租约不串台）；
5. 重排 + 租约同时存在 ⇒ `BOTH`（**只在两个持久化实现上钉**：Fake 没有写
   `RETRY_SCHEDULED` 的路径，与 `test_retry_schedule_contract.py` 的边界同源）。

"活"的时钟判据（过期 / LOST worker）不在本文件：Fake 没有过期语义，三实现不同强度；
那两条由 SQLite 注入时钟单测（tests/adapters/sqlite/test_dispatch_ownership.py）与
PG parity（tests/postgres/test_dispatch_ownership_pg.py）覆盖。
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from adapters.fakes.workflow_engine import FakeWorkflowEngine
from packages.application.ports.workflow_engine import (
    DISPATCH_BOTH,
    DISPATCH_NONE,
    DISPATCH_WORKER_CLAIM,
    ClaimRequest,
    LeaseHolder,
    TaskCompletion,
    WorkflowEngine,
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
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_FACTORIES: list[Callable[[], object]] = list(PORT_IMPLEMENTATIONS["workflow_engine"])
_PERSISTENT_FACTORIES: list[Callable[[], object]] = [
    factory for factory in _FACTORIES if factory is not FakeWorkflowEngine
]
RUN_ID = "7c4e1b02-5d8a-4f31-8e6b-9a2d3c5f7e10"
_WORKER = "dispatch-ownership-worker"


def _contract(*, backoff: int | None = None) -> TaskContract:
    return TaskContract(
        id="dispatch-ownership-contract",
        version="1.0",
        purpose="one read answers who is dispatching this run",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )


def _execution_task(*, run_id: str = RUN_ID) -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID(RUN_ID if run_id == RUN_ID else run_id),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        idempotency_key=f"task-{ID.generate().value}",
        required_capability="python_exec",
    )


def _claim(engine: WorkflowEngine, task: ResearchTask) -> object:
    lease = engine.claim_next(
        ClaimRequest(
            worker_id=_WORKER,
            capabilities=frozenset({"python_exec"}),
            partitions=frozenset(),
        )
    )
    assert lease is not None and lease.task_id == task.id.value, "夹具必须先真的拿到租约"
    return lease


@pytest.mark.parametrize("factory", _FACTORIES)
def test_a_run_without_claims_or_retries_has_no_dispatch_owner(
    factory: Callable[[], object],
) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    engine.submit(_execution_task(), _contract())

    ownership = engine.dispatch_ownership(RUN_ID)

    assert ownership.kind == DISPATCH_NONE
    assert ownership.leases == (), "排队中、没人持有 ⇒ 没有持有者"
    assert ownership.retry.scheduled == 0 and ownership.retry.due == 0


@pytest.mark.parametrize("factory", _FACTORIES)
def test_an_unknown_run_is_the_same_answer_not_an_error(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]

    ownership = engine.dispatch_ownership(ID.generate().value)

    assert ownership.kind == DISPATCH_NONE
    assert ownership.leases == ()


@pytest.mark.parametrize("factory", _FACTORIES)
def test_a_worker_claim_names_the_holder(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task()
    engine.submit(task, _contract())
    lease = _claim(engine, task)

    ownership = engine.dispatch_ownership(RUN_ID)

    assert ownership.kind == DISPATCH_WORKER_CLAIM
    assert ownership.leases == (
        LeaseHolder(
            task_id=task.id.value,
            worker_id=_WORKER,
            fence=lease.fence,  # type: ignore[attr-defined]
            expires_at=lease.expires_at,  # type: ignore[attr-defined]
        ),
    ), "持有者要能点名：task / worker / fence / 到期（lease_id 不进读面）"


@pytest.mark.parametrize("factory", _FACTORIES)
def test_completing_the_task_releases_the_claim(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task()
    engine.submit(task, _contract())
    lease = _claim(engine, task)

    engine.complete(
        lease,  # type: ignore[arg-type]
        TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"),
    )

    assert engine.dispatch_ownership(RUN_ID).kind == DISPATCH_NONE, "完成后没人再持有它"


@pytest.mark.parametrize("factory", _FACTORIES)
def test_the_read_face_is_per_run(factory: Callable[[], object]) -> None:
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    mine = _execution_task()
    engine.submit(mine, _contract())
    _claim(engine, mine)
    other_run = ID.generate().value
    engine.submit(_execution_task(run_id=other_run), _contract())

    assert engine.dispatch_ownership(other_run).kind == DISPATCH_NONE, "别的 run 的租约不串台"
    assert engine.dispatch_ownership(RUN_ID).kind == DISPATCH_WORKER_CLAIM


@pytest.mark.parametrize("factory", _PERSISTENT_FACTORIES)
def test_a_retry_waiting_beside_a_claim_reads_as_both(factory: Callable[[], object]) -> None:
    """重排（等时钟）与租约（被持有）是两件事实，同时存在时读面两个都报。"""
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    retrying = _execution_task()
    engine.submit(retrying, _contract(backoff=600))
    lease = engine.acquire_lease(retrying.id.value)
    engine.complete(
        lease,
        TaskCompletion(
            task_id=retrying.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    claimed = _execution_task()
    engine.submit(claimed, _contract())
    _claim(engine, claimed)

    ownership = engine.dispatch_ownership(RUN_ID)

    assert ownership.kind == DISPATCH_BOTH
    assert ownership.retry.scheduled == 1 and ownership.retry.due == 0
    assert ownership.leases[0].task_id == claimed.id.value


@pytest.mark.parametrize("factory", _FACTORIES)
def test_the_batch_read_equals_the_per_run_read(factory: Callable[[], object]) -> None:
    """GOAL-005 cycle 5 = EC-05 ①：批量读面与逐 run 读**逐字同判**。

    这是列表路径（`GET /projects/{id}/runs`）放弃 N+1 的前提：批量读不是第二套判据，
    它就是"单 run 读"在同一次读里回答了整批（实现里两处共用同一段装配）。未知 run 也要
    有条目（与单 run 读同形 ⇒ `NONE`，不是缺项、不是异常）。
    """
    engine: WorkflowEngine = factory()  # type: ignore[assignment]
    task = _execution_task()
    engine.submit(task, _contract())
    _claim(engine, task)
    unknown = str(ID.generate().value)

    batch = engine.dispatch_ownership_many((RUN_ID, unknown))

    assert set(batch) == {RUN_ID, unknown}, "请求到的每条 run 都有条目"
    assert batch[RUN_ID].kind == DISPATCH_WORKER_CLAIM, "先钉住批量读真的答了"
    for run_id in (RUN_ID, unknown):
        assert batch[run_id] == engine.dispatch_ownership(run_id), run_id


@pytest.mark.parametrize("factory", _FACTORIES)
def test_an_empty_batch_reads_nothing(factory: Callable[[], object]) -> None:
    """空入参 ⇒ 空 dict（列表页没有 run 时不该为了空集合去读库）。"""
    engine: WorkflowEngine = factory()  # type: ignore[assignment]

    assert engine.dispatch_ownership_many(()) == {}


def test_the_fake_never_expires_a_lease_it_holds() -> None:
    """Fake 的"活"= 仍在租约表里（没有过期/回收路径）——这是它的边界，不是判据。

    与持久化实现同强度的判据（过期、LOST worker）由 SQLite 注入时钟单测与 PG parity
    覆盖；这里把 Fake 的限制钉成显式事实，避免"读到持有就以为有回收语义"。
    """
    engine = FakeWorkflowEngine()
    task = _execution_task()
    engine.submit(task, _contract())
    _claim(engine, task)

    ownership = engine.dispatch_ownership(RUN_ID)

    assert ownership.kind == DISPATCH_WORKER_CLAIM
    assert engine.recover_expired_leases() == 0, "Fake 没有可回收的租约（无过期语义）"
    assert engine.dispatch_ownership(RUN_ID).kind == DISPATCH_WORKER_CLAIM, "回收后仍然持有"
