"""TaskContract.retry_policy 被真正消费（GOAL-003 cycle 15 / PLAN-20260915-078）。

收口前：`complete()` 把任何非 SUCCEEDED 的完成一律写成 FAILED——
`retry_policy`（`max_attempts` 是必填字段）**零消费者**，Domain 状态机里的
`RETRY_SCHEDULED` / `DEAD_LETTER` 两个状态**没有任何生产调用方**，
`TaskCompletion` 也根本没有"失败类别"这个输入。

本文件把判据钉在**行为**上（不看实现）：成功照旧；可重试且还有次数 ⇒ 重排且能再被
claim；次数用尽 ⇒ 死信；不可重试 / 未分类 / 无策略 ⇒ 终态失败。
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


def _engine() -> SqliteWorkflowEngine:
    return SqliteWorkflowEngine(lease_ttl_seconds=60, now=lambda: START)


@dataclass
class _Clock:
    """可推进的时钟：让租约真的过期（recover 只回收已过期的租约）。"""

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


def _acceptance() -> list[AcceptanceCriterion]:
    return [AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)]


def _contract(max_attempts: int = 3, *categories: FailureCategory) -> TaskContract:
    return TaskContract(
        id="retry-contract",
        version="1.0",
        purpose="retry semantics",
        acceptance_criteria=_acceptance(),
        retry_policy=RetryPolicy(max_attempts=max_attempts, retryable_categories=list(categories)),
    )


def _request() -> ClaimRequest:
    return ClaimRequest(
        worker_id="w1", capabilities=frozenset({"docker"}), partitions=frozenset({0})
    )


def _status(engine: SqliteWorkflowEngine, task: ResearchTask) -> str:
    rows = engine.list_tasks(task.run_id.value)
    return str(next(row.task.status for row in rows if row.task.id.value == task.id.value))


def _fail(
    engine: SqliteWorkflowEngine,
    task: ResearchTask,
    *,
    category: FailureCategory | None,
    outcome: str = "FAILED",
) -> None:
    lease = engine.claim_next(_request())
    assert lease is not None
    engine.complete(
        lease,
        TaskCompletion(task_id=task.id.value, outcome=outcome, failure_category=category),
    )


def _events(engine: SqliteWorkflowEngine) -> list[EventType]:
    return [envelope.event_type for envelope in engine.pending_outbox()]


def _attempt(engine: SqliteWorkflowEngine, task: ResearchTask) -> int:
    row = next(r for r in engine.list_tasks(task.run_id.value) if r.task.id.value == task.id.value)
    return int(row.task.attempt)


def test_a_retryable_failure_is_rescheduled_and_claimable_again() -> None:
    """可重试 + 还有次数 ⇒ RETRY_SCHEDULED，且**能再被 claim**（下一次尝试才开始计数）。"""
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(3, FailureCategory.MODEL_TIMEOUT))

    _fail(engine, task, category=FailureCategory.MODEL_TIMEOUT)

    assert _status(engine, task) == ResearchTaskState.State.RETRY_SCHEDULED
    assert _attempt(engine, task) == 1, "attempt 计的是已开始的尝试；这次尝试已经跑完了"
    assert EventType.TASK_RETRY_SCHEDULED in _events(engine)
    lease = engine.claim_next(_request())
    assert lease is not None and lease.task_id == task.id.value
    assert _attempt(engine, task) == 2, "再次 claim = 第二次尝试开始，attempt 递增"


def test_attempts_exhausted_goes_to_dead_letter() -> None:
    """可重试但次数用尽 ⇒ DEAD_LETTER（不再自动重试，等人工恢复）。"""
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(2, FailureCategory.MODEL_TIMEOUT))

    _fail(engine, task, category=FailureCategory.MODEL_TIMEOUT)  # 第 1 次尝试失败 -> 重排
    assert _status(engine, task) == ResearchTaskState.State.RETRY_SCHEDULED
    _fail(engine, task, category=FailureCategory.MODEL_TIMEOUT)  # 第 2 次失败，max_attempts=2

    assert _status(engine, task) == ResearchTaskState.State.DEAD_LETTER
    assert _attempt(engine, task) == 2
    assert engine.claim_next(_request()) is None, "死信任务不该再被派发"


def test_a_non_retryable_category_still_fails_terminally() -> None:
    """类别不在 retryable_categories 里 ⇒ FAILED（与重试策略出现前一致）。"""
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(3, FailureCategory.MODEL_TIMEOUT))

    _fail(engine, task, category=FailureCategory.POLICY_DENIED)

    assert _status(engine, task) == ResearchTaskState.State.FAILED
    assert engine.claim_next(_request()) is None


def test_an_unclassified_failure_is_not_retried() -> None:
    """完成方没给类别 ⇒ FAILED（无从判断可不可能重试时**不**重试，保守）。"""
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(3, FailureCategory.MODEL_TIMEOUT))

    _fail(engine, task, category=None)

    assert _status(engine, task) == ResearchTaskState.State.FAILED


def test_no_retry_policy_keeps_the_old_behaviour() -> None:
    """契约没写 retry_policy ⇒ FAILED（既有契约一律不受影响）。"""
    engine = _engine()
    task = _task()
    contract = TaskContract(
        id="plain", version="1.0", purpose="no policy", acceptance_criteria=_acceptance()
    )
    engine.submit(task, contract)

    _fail(engine, task, category=FailureCategory.MODEL_TIMEOUT)

    assert _status(engine, task) == ResearchTaskState.State.FAILED


def test_a_successful_completion_is_untouched_by_the_retry_path() -> None:
    """回归：成功完成仍写 SUCCEEDED（判据只作用于失败）。"""
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(3, FailureCategory.MODEL_TIMEOUT))

    _fail(engine, task, category=None, outcome="SUCCEEDED")

    assert _status(engine, task) == ResearchTaskState.State.SUCCEEDED
    assert EventType.TASK_RETRY_SCHEDULED not in _events(engine)


def test_a_reclaimed_task_projection_advances_with_the_hand_out() -> None:
    """交付代次与投影必须同步：租约过期被回收后再交付，就是**第二次**尝试。

    这条不依赖 retry_policy：租约过期 + 回收（recover）本来就会让一个 QUEUED 任务被
    第二次交付。修好之前 task_json 里的 attempt 永远停在 1，于是重试产生的用量会一直
    记进第一次尝试的 entry id（`_attempt_scope` 的 attempt 后缀永不出现）。
    """
    clock = _Clock()
    engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=clock)
    task = _task()
    engine.submit(task, _contract(3))
    first = engine.claim_next(_request())
    assert first is not None and first.fence == 1
    clock.advance(seconds=3600)

    assert engine.recover_expired_leases() == 1
    second = engine.claim_next(_request())

    assert second is not None and second.fence == 2, "回收后再次交付 = 第二代"
    assert _attempt(engine, task) == 2, "投影的 attempt 跟着交付代次前进"


def test_replaying_a_completion_after_a_retry_is_still_idempotent() -> None:
    """at-least-once 回归：同一次完成重放必须是 noop，不能变成异常。

    重排之后任务不在终态、lease 又已删——如果重放判据只认 SUCCEEDED/FAILED，
    这里会抛 `no matching lease`。
    """
    engine = _engine()
    task = _task()
    engine.submit(task, _contract(3, FailureCategory.MODEL_TIMEOUT))
    lease = engine.claim_next(_request())
    assert lease is not None
    completion = TaskCompletion(
        task_id=task.id.value, outcome="FAILED", failure_category=FailureCategory.MODEL_TIMEOUT
    )

    engine.complete(lease, completion)
    engine.complete(lease, completion)  # 重放

    assert engine.calls[-1].result_summary == "deduped"
    assert _status(engine, task) == ResearchTaskState.State.RETRY_SCHEDULED
