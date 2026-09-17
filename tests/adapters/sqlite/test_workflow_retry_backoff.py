"""重排后的退避在 claim 上真的生效（GOAL-003 cycle 16 / PLAN-20260915-079）。

判据钉在**行为**上：声明了退避的重排任务在 deadline 之前**不能被 claim**（哪怕
worker 就在那里等着），到点后与首次排队同权；没声明退避的契约行为与今天完全一致
（立即重排、立即可 claim）——既有契约不受影响。

这里用的是可推进时钟：`retry_at` 的比较对象是"claim 时刻的 now"，所以退避是否生效
可以用时间推进直接观测，不依赖 sleep。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import ClaimRequest, TaskCompletion
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.events import EventType
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


def _engine(clock: _Clock) -> SqliteWorkflowEngine:
    return SqliteWorkflowEngine(lease_ttl_seconds=3600, now=clock)


def _task() -> ResearchTask:
    return ResearchTask(
        id=ID.generate(),
        run_id=ID.generate(),
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability="docker",
        partition=0,
    )


def _contract(*, backoff_seconds: int | None, max_attempts: int = 3) -> TaskContract:
    return TaskContract(
        id="backoff-contract",
        version="1.0",
        purpose="retry backoff",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=max_attempts,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff_seconds,
        ),
    )


def _request() -> ClaimRequest:
    return ClaimRequest(
        worker_id="w1", capabilities=frozenset({"docker"}), partitions=frozenset({0})
    )


def _status(engine: SqliteWorkflowEngine, task: ResearchTask) -> str:
    rows = engine.list_tasks(task.run_id.value)
    return str(next(row.task.status for row in rows if row.task.id.value == task.id.value))


def _fail_once(engine: SqliteWorkflowEngine, task: ResearchTask) -> None:
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


def _rescheduled(backoff_seconds: int | None) -> tuple[SqliteWorkflowEngine, _Clock, ResearchTask]:
    clock = _Clock()
    engine = _engine(clock)
    task = _task()
    engine.submit(task, _contract(backoff_seconds=backoff_seconds))
    _fail_once(engine, task)
    assert _status(engine, task) == ResearchTaskState.State.RETRY_SCHEDULED
    return engine, clock, task


def test_a_rescheduled_task_is_not_claimable_before_its_deadline() -> None:
    """声明了 60s 退避：重排后立刻 claim 拿不到东西，时钟推过 deadline 才拿得到。"""
    engine, clock, task = _rescheduled(backoff_seconds=60)

    assert engine.claim_next(_request()) is None, "deadline 之前不该被派发"

    clock.advance(seconds=59)
    assert engine.claim_next(_request()) is None, "差一秒也不行"

    clock.advance(seconds=1)
    lease = engine.claim_next(_request())
    assert lease is not None and lease.task_id == task.id.value, "到点后与首次排队同权"
    assert lease.fence == 2, "这是第二次交付"


def test_the_deadline_is_written_and_cleared_not_left_behind() -> None:
    """deadline 是可读的事实（事件里带 `retry_at`），交付后被清掉不留残留。"""
    engine, clock, task = _rescheduled(backoff_seconds=60)
    scheduled = [
        e for e in engine.pending_outbox() if e.event_type == EventType.TASK_RETRY_SCHEDULED
    ]

    retry_at = scheduled[-1].payload.get("retry_at")
    assert retry_at is not None, "重排事件要能解释'为什么还没被取走'"
    assert str(retry_at).startswith("2026-09-17T09:01"), f"deadline = now + 60s，实际 {retry_at}"

    clock.advance(seconds=60)
    assert engine.claim_next(_request()) is not None
    stored = engine._conn.execute(  # noqa: SLF001 - 直读列，确认交付把 deadline 清掉
        "SELECT retry_at FROM tasks WHERE task_id = ?", (task.id.value,)
    ).fetchone()
    assert stored["retry_at"] is None, "交付即清"


def test_a_task_without_backoff_is_still_claimable_immediately() -> None:
    """向后兼容：没写退避字段的契约，重排后立即可 claim（与退避出现之前一致）。"""
    engine, _clock, task = _rescheduled(backoff_seconds=None)

    lease = engine.claim_next(_request())

    assert lease is not None and lease.task_id == task.id.value


def test_an_unexpired_retry_does_not_block_another_claimable_task() -> None:
    """退避过滤在**扫描内**：一个没到期的重试不占候选窗口，别的任务照常被取走。"""
    engine, _clock, cooling = _rescheduled(backoff_seconds=3600)
    other = _task()
    engine.submit(other, _contract(backoff_seconds=None))

    lease = engine.claim_next(_request())

    assert lease is not None and lease.task_id == other.id.value
