"""GOAL-026 EC-03（AC-3）：取消语义 —— 幂等、终止，且**取消后不再产生新副作用**。

既有判据（`tests/adapters/sqlite/test_workflow_engine.py:139-147`、
`test_workflow_cancel_run.py:72-78`）证了「第二次取消是 `deduped` / 0 条」。
本判据补三件它没有的事：

1. **取消释放租约**且任务**不再可被 claim**（结构化：状态串 + `claim_next` 为 `None`）；
2. **取消后的陈旧完成被结构化拒绝且不产生新副作用** —— 「完成已落账」的幂等集**不含**
   `CANCELLED`（`adapters/sqlite/workflow_ops.py:51-62`），故陈旧完成必须**响亮地被拒**
   （`InvalidInputError`），而**不是**被当成重放静默吞掉；且 outbox **零新增事件**；
3. **取消是终止态**：状态机里 `CANCELLED` 与 `DEAD_LETTER` 一样在 `terminal()` 集合里。
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

START = datetime(2026, 9, 29, 9, 0, 0, tzinfo=timezone.utc)


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
        id="cancel-contract",
        version="1.0",
        purpose="cancellation semantics",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=3, retryable_categories=[FailureCategory.MODEL_TIMEOUT]
        ),
    )


def _request() -> ClaimRequest:
    return ClaimRequest(
        worker_id="w1", capabilities=frozenset({"docker"}), partitions=frozenset({0})
    )


def _status(engine: SqliteWorkflowEngine, task: ResearchTask) -> str:
    rows = engine.list_tasks(task.run_id.value)
    return str(next(row.task.status for row in rows if row.task.id.value == task.id.value))


def _held_lease(engine: SqliteWorkflowEngine, task: ResearchTask) -> TaskLease:
    engine.submit(task, _contract())
    lease = engine.claim_next(_request())
    assert lease is not None
    assert _status(engine, task) == ResearchTaskState.State.LEASED
    return lease


def test_cancel_is_idempotent_and_releases_the_lease() -> None:
    """首次取消生效；**第二次取消**结论一致（结构化 `deduped`）；租约被释放、不再可 claim。"""
    engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=_Clock())
    task = _task()
    _held_lease(engine, task)

    engine.cancel(task.id.value)
    assert _status(engine, task) == ResearchTaskState.State.CANCELLED

    after_first = len(engine.pending_outbox())
    engine.cancel(task.id.value)  # 重复取消：结论一致，且**不产生新副作用**
    assert _status(engine, task) == ResearchTaskState.State.CANCELLED
    assert engine.calls[-1].result_summary == "deduped"
    assert engine.claim_next(_request()) is None, "取消后不得再被 claim"
    assert len(engine.pending_outbox()) == after_first, "重复取消不得再发事件（副作用计数）"


def test_stale_completion_after_cancel_is_rejected_without_new_event() -> None:
    """取消后的**陈旧完成**：结构化拒绝（`InvalidInputError`）且 **outbox 零新增**。"""
    engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=_Clock())
    task = _task()
    stale = _held_lease(engine, task)
    engine.cancel(task.id.value)

    before = len(engine.pending_outbox())
    with pytest.raises(InvalidInputError):
        engine.complete(stale, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))

    assert _status(engine, task) == ResearchTaskState.State.CANCELLED
    assert len(engine.pending_outbox()) == before, "被拒的陈旧完成不得产生新事件"


def test_cancel_is_terminal_in_the_state_machine() -> None:
    """结构化事实：`CANCELLED` 在 `terminal()` 集合里（与 `DEAD_LETTER` 同族）。"""
    assert ResearchTaskState.State.CANCELLED in ResearchTaskState.terminal()
    assert ResearchTaskState.State.DEAD_LETTER in ResearchTaskState.terminal()
