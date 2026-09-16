"""完成处置的事件发布（两个 adapter 共用，PLAN-20260915-078）。

判据在 Domain（`TaskContract.disposition`），这里只负责把它翻译成事件：
重排发 `task.retry_scheduled`，其余（成功 / 终态失败 / 死信）发 `task.completed`
并带上 `action` 与 `status`——附加字段，既有消费者按 outcome 读不受影响。
"""

from __future__ import annotations

from adapters.sqlite.outbox import OutboxWriter
from packages.application.ports.workflow_engine import TaskCompletion
from packages.domain.events import EventType
from packages.domain.tasks import FailureDisposition


def publish_completion_outcome(
    outbox: OutboxWriter,
    plan: FailureDisposition,
    *,
    run_id: str,
    completion: TaskCompletion,
    attempt: int,
) -> None:
    """按处置结果发事件（重排 ⇒ `task.retry_scheduled`；否则 `task.completed`）。"""
    if plan.retrying:
        outbox.publish(
            EventType.TASK_RETRY_SCHEDULED,
            {
                "task_id": completion.task_id,
                "reason": "failure_retry",
                "attempt": attempt + 1,
                "category": None
                if completion.failure_category is None
                else str(completion.failure_category),
            },
            run_id=run_id,
            task_id=completion.task_id,
        )
        return
    outbox.publish(
        EventType.TASK_COMPLETED,
        {
            "task_id": completion.task_id,
            "outcome": completion.outcome,
            "action": str(plan.action),
            "status": str(plan.status),
        },
        run_id=run_id,
        task_id=completion.task_id,
    )
