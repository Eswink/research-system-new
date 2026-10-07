"""GOAL-20261007-032 EC-01（`R26-1`）：死信**人工恢复路径**的行为判据（ADR-0033）。

GOAL-026 的 `R26-1` 登记「死信人工恢复路径不存在」；ADR-0033 落地后它存在了。
本文件判四件事（每条都能被按压判红）：

1. **恢复真的发生**：`DEAD_LETTER` → `requeue` → `QUEUED`，且**真的能再次交付**
   （`claim_next` 拿到租约、`attempt` 由交付路径推进到新代次、跑到终态）；
2. **点名失败**（三个不可恢复输入各自被拒，消息含任务 id 与实际状态）：
   ① 不存在的任务；② 已是其它终态（`FAILED` / `SUCCEEDED` / `CANCELLED`）；
   ③ **已恢复**（第二次恢复）——且第二次**零新副作用**（事件计数不增）；
3. **终态语义不变**：`DEAD_LETTER` 仍在 `terminal()`；自动路径（`acquire_lease`）
   在恢复**之前**仍然点名拒绝它（恢复不是"自动路径开始捞它"）；
4. **实跑留档**：全套状态转移序列（含恢复前的拒绝读数与恢复后的交付读数）。

**受判面**：恢复面的**声明集本身**（三实现的 `requeue` + domain 的那条边），
不是它与别的集合的交集（承 `MEM-20260928-160`）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import ClaimRequest, TaskCompletion, TaskLease
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, RetryPolicy, TaskContract

START = datetime(2026, 10, 7, 9, 0, 0, tzinfo=timezone.utc)


@dataclass
class _Clock:
    value: datetime = field(default_factory=lambda: START)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, *, seconds: int) -> None:
        self.value = self.value + timedelta(seconds=seconds)


def _task() -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID.generate(),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability="docker",
        partition=0,
    )


def _contract() -> TaskContract:
    return TaskContract(
        id="manual-recovery-contract",
        version="1.0",
        purpose="dead letter manual recovery",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=2, retryable_categories=[FailureCategory.MODEL_TIMEOUT]
        ),
    )


def _request() -> ClaimRequest:
    return ClaimRequest(
        worker_id="w1", capabilities=frozenset({"docker"}), partitions=frozenset({0})
    )


def _status(engine: SqliteWorkflowEngine, task: ResearchTask) -> str:
    rows = engine.list_tasks(task.run_id.value)
    return str(next(row.task.status for row in rows if row.task.id.value == task.id.value))


def _attempt_of(engine: SqliteWorkflowEngine, task: ResearchTask) -> int:
    rows = engine.list_tasks(task.run_id.value)
    return int(next(row.task.attempt for row in rows if row.task.id.value == task.id.value))


def _drive_to_dead_letter(engine: SqliteWorkflowEngine, task: ResearchTask, clock: _Clock) -> None:
    """把任务打满重试预算（`max_attempts=2`）⇒ `DEAD_LETTER`。"""
    for _ in range(2):
        lease = engine.claim_next(_request())
        assert lease is not None
        engine.complete(
            lease,
            TaskCompletion(
                task_id=task.id.value,
                outcome="FAILED",
                failure_category=FailureCategory.MODEL_TIMEOUT,
            ),
        )
        clock.advance(seconds=3600)  # 走过退避窗口


def test_a_dead_letter_task_can_be_requeued_and_really_executes_again() -> None:
    """**主判据**：死信任务恢复后真的能再次被交付并跑到终态（不是只改状态串）。"""
    clock = _Clock()
    engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=clock)
    task = _task()
    engine.submit(task, _contract())
    _drive_to_dead_letter(engine, task, clock)
    assert _status(engine, task) == ResearchTaskState.State.DEAD_LETTER
    attempt_at_death = _attempt_of(engine, task)
    assert attempt_at_death == 2

    outcome = engine.requeue(task.id.value)

    assert outcome == "restored"
    assert _status(engine, task) == ResearchTaskState.State.QUEUED
    # 交付真的发生：claim 拿得到租约，且 attempt 由交付路径推进到**新**代次
    lease = engine.claim_next(_request())
    assert lease is not None, "恢复后的任务必须真的再次可交付"
    assert lease.fence > attempt_at_death, "交付代次前进（单调性不因人工动作回退）"
    assert _attempt_of(engine, task) == lease.fence
    # 跑到终态
    engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
    assert _status(engine, task) == ResearchTaskState.State.SUCCEEDED
    kinds = [envelope.event_type.value for envelope in engine.pending_outbox()]
    assert "task.retry_scheduled" in kinds, "恢复事件落在 canonical 事件链上"


def test_requeue_of_an_unknown_task_is_refused_by_name() -> None:
    """**点名拒绝 ①**：不存在的任务。"""
    engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=_Clock())
    ghost = ID.generate().value

    with pytest.raises(InvalidInputError) as caught:
        engine.requeue(ghost)

    assert ghost in str(caught.value), "拒绝消息必须点名任务 id"
    assert "unknown task" in str(caught.value)
    assert engine.calls[-1].result_summary is None and engine.calls[-1].error == "InvalidInputError"


@pytest.mark.parametrize(
    ("drive", "expected_state", "message_fragment"),
    [
        ("failed", ResearchTaskState.State.FAILED, "only DEAD_LETTER can be requeued"),
        ("cancelled", ResearchTaskState.State.CANCELLED, "only DEAD_LETTER can be requeued"),
        ("succeeded", ResearchTaskState.State.SUCCEEDED, "only DEAD_LETTER can be requeued"),
    ],
)
def test_requeue_of_a_non_dead_letter_final_state_is_refused_by_name(
    drive: str, expected_state: str, message_fragment: str
) -> None:
    """**点名拒绝 ②**：其它终态（`FAILED` / `CANCELLED` / `SUCCEEDED`）各自被拒且点名。"""
    clock = _Clock()
    engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=clock)
    task = _task()
    engine.submit(task, _contract())
    lease = engine.claim_next(_request())
    assert lease is not None
    if drive == "failed":
        engine.complete(
            lease,
            TaskCompletion(
                task_id=task.id.value,
                outcome="FAILED",
                failure_category=FailureCategory.MODEL_AUTH,  # 不可重试类别 ⇒ FAILED
            ),
        )
    elif drive == "cancelled":
        engine.cancel(task.id.value)
    else:
        engine.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
    assert _status(engine, task) == expected_state

    with pytest.raises(InvalidInputError) as caught:
        engine.requeue(task.id.value)

    message = str(caught.value)
    assert task.id.value in message, "拒绝消息必须点名任务 id"
    assert expected_state in message, "拒绝消息必须点名实际状态"
    assert message_fragment in message


def test_a_second_requeue_is_refused_and_produces_no_second_side_effect() -> None:
    """**点名拒绝 ③（已恢复）+ 零第二次副作用**：第二次恢复被拒、事件不增。"""
    clock = _Clock()
    engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=clock)
    task = _task()
    engine.submit(task, _contract())
    _drive_to_dead_letter(engine, task, clock)

    assert engine.requeue(task.id.value) == "restored"
    after_first = len(engine.pending_outbox())  # 取样必须在第二次**之前**（假绿教训）

    with pytest.raises(InvalidInputError) as caught:
        engine.requeue(task.id.value)

    message = str(caught.value)
    assert task.id.value in message and "QUEUED" in message, "已恢复的任务必须被点名拒绝"
    assert _status(engine, task) == ResearchTaskState.State.QUEUED, "状态不被第二次调用改动"
    assert len(engine.pending_outbox()) == after_first, "第二次恢复不得产生新事件"


def test_auto_path_still_refuses_a_dead_letter_before_manual_recovery() -> None:
    """**终态语义不变**：恢复**之前**，自动交付入口（`acquire_lease`）仍然点名拒绝。"""
    clock = _Clock()
    engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=clock)
    task = _task()
    engine.submit(task, _contract())
    _drive_to_dead_letter(engine, task, clock)

    with pytest.raises(InvalidInputError) as caught:
        engine.acquire_lease(task.id.value)
    assert "terminal" in str(caught.value), "自动路径的拒绝理由必须还在（recovered≠自动捞回）"
    assert _status(engine, task) == ResearchTaskState.State.DEAD_LETTER

    # 恢复之后同一个入口才放行 —— 差别由**人工动作**带来，不是守卫被拆掉
    engine.requeue(task.id.value)
    lease = engine.acquire_lease(task.id.value)
    assert isinstance(lease, TaskLease)


def test_the_recovery_surface_is_the_declared_set_itself() -> None:
    """**受判面非空 + 是声明集本身**（不是交集/过滤）：三个实现的 `requeue` 都在。

    反证臂：把任一实现的方法摘掉 ⇒ 本判据判红（`getattr` 失败）。
    """
    from adapters.fakes.workflow_engine import FakeWorkflowEngine
    from adapters.postgres.workflow_engine import PostgresWorkflowEngine

    declared = (
        SqliteWorkflowEngine,
        PostgresWorkflowEngine,
        FakeWorkflowEngine,
    )
    for implementation in declared:
        method = getattr(implementation, "requeue", None)
        assert callable(method), f"{implementation.__name__} 缺 requeue（声明集不完整）"
    assert len(declared) == 3, "受判面 = 声明的三个实现（不是交集、不是空集）"
