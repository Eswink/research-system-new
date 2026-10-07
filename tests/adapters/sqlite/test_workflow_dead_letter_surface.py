"""GOAL-026 EC-03（AC-2）：死信的**终止面、可枚举面与「无出边」的结构化断言**。

既有判据（`tests/adapters/sqlite/test_workflow_retry_policy.py:121-133`）证了
「次数用尽 ⇒ `DEAD_LETTER` + 不再可 claim」。本判据补三件它没有的事：

1. **按 run 可枚举**：读面 `list_tasks(run_id)` 能列出死信行（含 `attempt`）；
2. **完成重放是幂等 no-op**：同一完成再放一次 ⇒ 状态不变且**不产生第二条事件**；
3. **状态机里 `DEAD_LETTER` 没有出边**：逐一遍历**全部**迁移事件并断言每一个都非法
   ⇒ 「**人工恢复路径不存在**」是**机械事实**而非散文。人工恢复属**新能力**
   （需用户拍板，见 GOAL-026 的 `R26-1`），本轮**只登记**。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import ClaimRequest, TaskCompletion, TaskLease
from packages.domain.core import ID
from packages.domain.enums import AcceptanceCriterionType, FailureCategory, TaskKind
from packages.domain.state_base import InvalidTransitionError
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
        id="dead-letter-contract",
        version="1.0",
        purpose="dead letter surface",
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


def _drive_to_dead_letter(
    engine: SqliteWorkflowEngine, task: ResearchTask, clock: _Clock
) -> TaskLease:
    """把任务打满重试预算（`max_attempts=2`）⇒ `DEAD_LETTER`；返回最后一次的租约。"""
    lease = None
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
    assert lease is not None
    return lease


def test_dead_letter_is_enumerable_and_not_claimable() -> None:
    """按 run 可枚举（含 `attempt`）+ 不再可 claim。"""
    clock = _Clock()
    engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=clock)
    task = _task()
    engine.submit(task, _contract())
    _drive_to_dead_letter(engine, task, clock)

    rows = engine.list_tasks(task.run_id.value)
    dead = [row for row in rows if row.task.status == ResearchTaskState.State.DEAD_LETTER]
    assert len(dead) == 1, "死信必须能从读面按 run 枚举到"
    assert dead[0].task.id.value == task.id.value
    assert int(dead[0].task.attempt) == 2
    assert engine.claim_next(_request()) is None


def test_dead_letter_completion_replay_is_idempotent() -> None:
    """重放同一完成 ⇒ 幂等 no-op：状态不变、**不产生第二条事件**。"""
    clock = _Clock()
    engine = SqliteWorkflowEngine(lease_ttl_seconds=60, now=clock)
    task = _task()
    engine.submit(task, _contract())
    lease = _drive_to_dead_letter(engine, task, clock)

    before = len(engine.pending_outbox())
    engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    assert _status(engine, task) == ResearchTaskState.State.DEAD_LETTER
    assert len(engine.pending_outbox()) == before, "重放不得产生新事件"


def test_dead_letter_has_exactly_one_manual_outgoing_transition() -> None:
    """**机械事实**：`DEAD_LETTER` 的**唯一**出边是 `REQUEUE`（人工恢复，ADR-0033）。

    GOAL-026 建档时这条判据断言「无出边」；ADR-0033 落地后事实**变了**，判据按新事实
    **重新定基**（受判面从「所有事件都非法」扩为「**恰有** `REQUEUE` 一条合法，其余
    仍非法」——**扩大**而不是缩小）。仍逐一遍历**全部**迁移事件 ⇒ 新增第二条出边会判红。
    """
    # 结构化枚举：迁移事件就是 `Transition` 上声明的那些常量（同名类属性）。
    events = [
        value
        for name, value in vars(ResearchTaskState.Transition).items()
        if not name.startswith("_") and isinstance(value, str)
    ]
    assert len(events) >= 8, f"受判面非空：迁移事件必须被真的枚举到（实测 {len(events)}）"
    legal: list[str] = []
    for event in events:
        try:
            target = ResearchTaskState.transition(ResearchTaskState.State.DEAD_LETTER, event)
        except InvalidTransitionError:
            continue
        legal.append(f"{event}->{target}")
    assert legal == [f"{ResearchTaskState.Transition.REQUEUE}->{ResearchTaskState.State.QUEUED}"], (
        f"DEAD_LETTER 的出边必须恰为 REQUEUE->QUEUED（实测 {legal}）"
    )
    assert ResearchTaskState.State.DEAD_LETTER in ResearchTaskState.terminal(), (
        "终态语义不变：DEAD_LETTER 仍对**自动路径**终态（人工恢复是唯一出边）"
    )
