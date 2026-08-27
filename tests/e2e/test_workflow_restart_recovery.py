"""M7 E2E：进程重启 / 恢复（Restart Recovery）。

模拟 process interruption → restart → load canonical state → continue：
- SqliteWorkflowEngine 落盘（tmp_path）；
- 第一个实例 acquire lease 后 close（等价进程中断，不清理 DB）；
- 第二个实例从同一 DB 恢复：recover_expired_leases 将超时任务重新 QUEUED；
- 二次 acquire → 完成。

恢复边界（诚实声明，docs/reliability/WORKFLOW_RELIABILITY.md）：
M7 提供"任务边界级"恢复——重启后从 SQLite canonical state 重新排队
未完成任务；run() 阻塞期间的会话内恢复、跨进程分布式调度属 Temporal
阶段（M7 之后），不在此伪造。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.task_state import ResearchTaskState
from tests.contracts.fixtures import research_task, task_contract

START = datetime(2026, 8, 13, 11, 0, 0, tzinfo=timezone.utc)


def test_restart_recovers_expired_lease_and_completes(tmp_path: object) -> None:
    """进程中断 → 重启 → 恢复 QUEUED → 二次投递完成。"""
    import os

    db_path = os.fspath(tmp_path / "queue.db")  # type: ignore[operator]
    clock = {"now": START}
    first = SqliteWorkflowEngine(db_path, lease_ttl_seconds=60, now=lambda: clock["now"])
    task = research_task()
    first.submit(task, task_contract())
    first.acquire_lease(task.id.value)
    first.close()  # 模拟进程中断：不清理 DB

    # 重启：从 canonical state 恢复
    clock["now"] = START + timedelta(seconds=120)
    second = SqliteWorkflowEngine(db_path, lease_ttl_seconds=60, now=lambda: clock["now"])
    try:
        recovered = second.recover_expired_leases()
        assert recovered == 1
        (row,) = second.list_tasks(task.run_id.value)
        assert row.task.status == ResearchTaskState.State.QUEUED
        lease = second.acquire_lease(task.id.value)
        renewed = second.heartbeat(lease)
        second.complete(
            renewed,
            TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"),
        )
        (row,) = second.list_tasks(task.run_id.value)
        assert row.task.status == ResearchTaskState.State.SUCCEEDED
    finally:
        second.close()


def test_restart_does_not_duplicate_completed_tasks(tmp_path: object) -> None:
    """已完成任务重启后不重复投递（idempotency 持久化）。"""
    import os

    db_path = os.fspath(tmp_path / "done.db")  # type: ignore[operator]
    clock = {"now": START}
    first = SqliteWorkflowEngine(db_path, lease_ttl_seconds=60, now=lambda: clock["now"])
    task = research_task()
    first.submit(task, task_contract())
    lease = first.acquire_lease(task.id.value)
    first.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
    first.close()

    clock["now"] = START + timedelta(seconds=120)
    second = SqliteWorkflowEngine(db_path, lease_ttl_seconds=60, now=lambda: clock["now"])
    try:
        assert second.recover_expired_leases() == 0
        rows = second.list_tasks(task.run_id.value)
        assert len(rows) == 1
        assert rows[0].task.status == ResearchTaskState.State.SUCCEEDED
        assert second.deliveries[task.idempotency_key or ""] == 1
    finally:
        second.close()


def test_outbox_survives_restart(tmp_path: object) -> None:
    """事务性 outbox 事件在重启后仍可读取（不依赖进程内存）。"""
    import os

    from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
    from packages.domain.events import EventType

    db_path = os.fspath(tmp_path / "outbox.db")  # type: ignore[operator]
    first = SqliteWorkflowEngine(db_path, lease_ttl_seconds=60)
    task = research_task()
    first.submit(task, task_contract())
    lease = first.acquire_lease(task.id.value)
    first.complete(lease, TaskCompletion(task_id=task.id.value, outcome="SUCCEEDED"))
    first.close()

    second = SqliteOutboxEventPublisher(db_path)
    try:
        kinds = [e.event_type for e in second.pending()]
        assert EventType.TASK_COMPLETED in kinds
        assert EventType.TASK_LEASED in kinds
    finally:
        second.close()
