"""GOAL-026 EC-02（AC-1 / AC-2）：租约到期的回收与**心跳挡住回收**的两向取证。

既有判据的缺口（建档实测）：`tests/adapters/sqlite/test_workflow_engine.py:76-88` 只证
「心跳使 `expires_at` 变大 + 轮换 `lease_id`」；`test_workflow_retry_policy.py:185-204`
只证「到期 + 回收 ⇒ 可再 claim」。**没有人**把两件事接起来证「**心跳真的挡住了回收**
（过原 TTL 后回收 0 条、任务仍 `LEASED` 且抢不走）」，也没有证「**停止心跳后按新期限到期**」。

判据全部钉在**结构化字段 / 存储状态**上（`expires_at` / 任务 `status` / `fence` / 回收计数），
不靠散文或错误文本。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import ClaimRequest, TaskLease
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, TaskKind
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, RetryPolicy, TaskContract

START = datetime(2026, 9, 29, 9, 0, 0, tzinfo=timezone.utc)
_TTL_SECONDS = 60


@dataclass
class _Clock:
    """可推进时钟：`recover_expired_leases` 只回收**已过期**的租约 ⇒ 到期可确定性观测。"""

    value: datetime = field(default_factory=lambda: START)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, *, seconds: int) -> None:
        self.value = self.value + timedelta(seconds=seconds)


def _engine(clock: _Clock) -> SqliteWorkflowEngine:
    return SqliteWorkflowEngine(lease_ttl_seconds=_TTL_SECONDS, now=clock)


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
        id="lease-contract",
        version="1.0",
        purpose="lease lifecycle",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(max_attempts=3, retryable_categories=[]),
    )


def _claim(engine: SqliteWorkflowEngine, worker: str) -> TaskLease | None:
    return engine.claim_next(
        ClaimRequest(
            worker_id=worker, capabilities=frozenset({"docker"}), partitions=frozenset({0})
        )
    )


def _status(engine: SqliteWorkflowEngine, task: ResearchTask) -> str:
    rows = engine.list_tasks(task.run_id.value)
    return str(next(row.task.status for row in rows if row.task.id.value == task.id.value))


def test_expired_lease_is_reclaimed_and_claimable_by_another_worker() -> None:
    """持有者失效 ⇒ 回收 ⇒ **另一次 claim 取得**（fence 前进，不永久卡死）。"""
    clock = _Clock()
    engine = _engine(clock)
    task = _task()
    engine.submit(task, _contract())

    first = _claim(engine, "w1")
    assert first is not None and first.fence == 1
    # 正控制：**未**到期时回收不是空转（0 条），否则下面的「1 条」不说明问题。
    assert engine.recover_expired_leases() == 0
    assert _status(engine, task) == ResearchTaskState.State.LEASED
    assert _claim(engine, "w2") is None, "未到期的租约不得被抢"

    clock.advance(seconds=_TTL_SECONDS + 1)
    assert engine.recover_expired_leases() == 1
    assert _status(engine, task) == ResearchTaskState.State.QUEUED

    second = _claim(engine, "w2")
    assert second is not None
    assert second.task_id == task.id.value
    assert second.fence == 2, "回收后重新取得 = 新的围栏代次"


def test_heartbeat_keeps_the_lease_alive_past_its_original_ttl() -> None:
    """心跳续租 ⇒ 过**原** TTL 后仍不被回收、抢不走（**挡住回收**）。"""
    clock = _Clock()
    engine = _engine(clock)
    task = _task()
    engine.submit(task, _contract())
    lease = _claim(engine, "w1")
    assert lease is not None

    clock.advance(seconds=_TTL_SECONDS - 10)
    renewed = engine.heartbeat(lease)
    assert renewed.expires_at is not None and lease.expires_at is not None
    assert renewed.expires_at.value > lease.expires_at.value, "续租必须把到期推后（否则判据无意义）"

    clock.advance(seconds=20)  # 此刻已越过**原始** expires_at
    assert engine.recover_expired_leases() == 0, "心跳挡住了回收"
    assert _status(engine, task) == ResearchTaskState.State.LEASED
    assert _claim(engine, "w2") is None, "被续租的任务不得被抢"


def test_lease_expires_after_the_heartbeat_chain_stops() -> None:
    """停跳后**按预期**到期：过新 `expires_at` ⇒ 回收 ⇒ 可再 claim。"""
    clock = _Clock()
    engine = _engine(clock)
    task = _task()
    engine.submit(task, _contract())
    lease = _claim(engine, "w1")
    assert lease is not None

    clock.advance(seconds=_TTL_SECONDS - 10)
    renewed = engine.heartbeat(lease)
    assert renewed.expires_at is not None
    # 心跳停了：越过**新** expires_at（= 续租时刻 + TTL）。
    clock.advance(seconds=_TTL_SECONDS + 1)
    assert engine.recover_expired_leases() == 1
    assert _status(engine, task) == ResearchTaskState.State.QUEUED
    assert _claim(engine, "w2") is not None
