"""acquire 入口也守退避 deadline（GOAL-003 cycle 17 / PLAN-20260915-080）。

cycle 16 只在 `claim_next` 的候选扫描里过滤了 `retry_at`；按 task_id 直接 `acquire_lease`
仍能把没到期的重试任务租出去——"deadline 之前不得交付"这个不变量必须在**每个交付入口**
成立（同 cycle 13/14 的枚举手法）。本文件把 acquire 侧钉住：未到期拒绝、到期放行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.errors import InvalidInputError
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, RetryPolicy, TaskContract

START = datetime(2026, 9, 17, 9, 0, 0, tzinfo=timezone.utc)


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
        kind=TaskKind.AGENT_SESSION,
        required_capability="workspace.read",
    )


def _contract(*, backoff: int | None) -> TaskContract:
    return TaskContract(
        id="acquire-backoff-contract",
        version="1.0",
        purpose="acquire must respect the retry deadline",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )


def _rescheduled(*, backoff: int | None) -> tuple[SqliteWorkflowEngine, _Clock, ResearchTask]:
    clock = _Clock()
    engine = SqliteWorkflowEngine(lease_ttl_seconds=3600, now=clock)
    task = _task()
    engine.submit(task, _contract(backoff=backoff))
    lease = engine.acquire_lease(task.id.value)
    engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    return engine, clock, task


def test_acquire_refuses_a_task_that_is_still_waiting_for_its_backoff() -> None:
    engine, clock, task = _rescheduled(backoff=600)

    with pytest.raises(InvalidInputError, match="waiting for its retry backoff"):
        engine.acquire_lease(task.id.value)

    clock.advance(seconds=599)
    with pytest.raises(InvalidInputError, match="waiting for its retry backoff"):
        engine.acquire_lease(task.id.value)

    clock.advance(seconds=1)
    lease = engine.acquire_lease(task.id.value)

    assert lease.fence == 2, "到期后是可租的第二次交付"


def test_acquire_without_a_declared_backoff_is_unchanged() -> None:
    """向后兼容：没写退避字段的任务，失败后立刻可以再租（既有行为）。"""
    engine, _clock, task = _rescheduled(backoff=None)

    lease = engine.acquire_lease(task.id.value)

    assert lease.fence == 2
