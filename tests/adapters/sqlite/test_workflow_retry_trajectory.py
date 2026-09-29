"""GOAL-026 EC-02（AC-3 / AC-4 / AC-5）：退避**轨迹**与重试预算耗尽的终止态。

既有判据的缺口（建档实测）：`tests/domain/test_retry_backoff.py:29-56` 只在**纯函数层**采样
三点 + 上界；`tests/adapters/sqlite/test_workflow_retry_backoff.py:116-132` 只断言**第一次**
延迟的 `retry_at`。**没有**判据把「连续多次失败」的**实际落库**退避序列取出来，
证明它**单调不减且被上界封顶**，也没有把「轨迹的最后一步 = 死信」接起来。

本判据读的是 `tasks.retry_at`（**存储行**），比较对象是注入时钟 ⇒ 到期可确定性观测，
不依赖 sleep。分类一律按**结构化字段**（`FailureCategory` / 任务状态），不匹配错误文本。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from adapters.sqlite.db import connect, parse_iso
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import ClaimRequest, TaskCompletion
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, RetryPolicy, TaskContract

START = datetime(2026, 9, 29, 9, 0, 0, tzinfo=timezone.utc)
_BASE = 30
_CAP = 100
_MAX_ATTEMPTS = 5
#: 轨迹的期望形状（attempt 1..4 失败后落库的等长间隔）：增长两次后被上界封顶。
_EXPECTED_GAPS = [30, 60, 100, 100]


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


def _contract(*categories: FailureCategory) -> TaskContract:
    return TaskContract(
        id="trajectory-contract",
        version="1.0",
        purpose="retry trajectory",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=_MAX_ATTEMPTS,
            retryable_categories=list(categories),
            backoff_seconds=_BASE,
            max_backoff_seconds=_CAP,
        ),
    )


def _request() -> ClaimRequest:
    return ClaimRequest(
        worker_id="w1", capabilities=frozenset({"docker"}), partitions=frozenset({0})
    )


def _fail_with(engine: SqliteWorkflowEngine, task: ResearchTask, category: FailureCategory) -> None:
    lease = engine.claim_next(_request())
    assert lease is not None, "退避窗口已过时任务必须可被 claim"
    engine.complete(
        lease,
        TaskCompletion(task_id=task.id.value, outcome="FAILED", failure_category=category),
    )


def _retry_at(connection: sqlite3.Connection, task_id: str) -> datetime:
    row = connection.execute("SELECT retry_at FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    assert row is not None and row[0] is not None, "重排任务必须落库 retry_at"
    return parse_iso(str(row[0]))


def _status(engine: SqliteWorkflowEngine, task: ResearchTask) -> str:
    rows = engine.list_tasks(task.run_id.value)
    return str(next(row.task.status for row in rows if row.task.id.value == task.id.value))


def test_backoff_trajectory_is_monotonic_and_capped_then_dead_letters() -> None:
    """轨迹：`[30, 60, 100, 100]` —— 单调不减、被上界封顶、最后一步进入死信。"""
    clock = _Clock()
    connection = connect(":memory:")
    engine = SqliteWorkflowEngine(connection=connection, lease_ttl_seconds=3600, now=clock)
    try:
        task = _task()
        engine.submit(task, _contract(FailureCategory.MODEL_TIMEOUT))
        gaps: list[int] = []
        for _ in range(_MAX_ATTEMPTS - 1):
            _fail_with(engine, task, FailureCategory.MODEL_TIMEOUT)
            assert _status(engine, task) == ResearchTaskState.State.RETRY_SCHEDULED
            gap = int((_retry_at(connection, task.id.value) - clock.value).total_seconds())
            gaps.append(gap)
            clock.advance(seconds=gap)  # 走过退避窗口，让下一次尝试可以开始

        assert gaps == _EXPECTED_GAPS, f"退避轨迹实测: {gaps}"
        assert all(later >= earlier for earlier, later in zip(gaps, gaps[1:])), "单调不减"
        assert max(gaps) <= _CAP, "必须有上界（不得无限增长）"
        assert gaps[1] > gaps[0], "确实在增长 —— 常量退避会在这里判红"

        # 第 5 次尝试失败：次数用尽 ⇒ 终止态（不再自动重试）。
        _fail_with(engine, task, FailureCategory.MODEL_TIMEOUT)
        assert _status(engine, task) == ResearchTaskState.State.DEAD_LETTER
        assert engine.claim_next(_request()) is None, "死信任务不该再被派发"
    finally:
        engine.close()


def test_non_retryable_category_fails_without_any_reschedule() -> None:
    """对照：**不可重试**类别 ⇒ 直接终态失败，**不**重排、**不**留 `retry_at`。"""
    clock = _Clock()
    connection = connect(":memory:")
    engine = SqliteWorkflowEngine(connection=connection, lease_ttl_seconds=3600, now=clock)
    try:
        task = _task()
        engine.submit(task, _contract(FailureCategory.MODEL_TIMEOUT))
        _fail_with(engine, task, FailureCategory.VALIDATION_FAILURE)

        assert _status(engine, task) == ResearchTaskState.State.FAILED
        events = [envelope.event_type for envelope in engine.pending_outbox()]
        assert EventType.TASK_RETRY_SCHEDULED not in events, "不可重试类别不得被重排"
        assert engine.claim_next(_request()) is None
    finally:
        engine.close()
