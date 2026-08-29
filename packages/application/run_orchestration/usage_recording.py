"""任务完成/失败/取消后的确定性用量记录（entry_id 幂等,attempt 作用域）。"""

from __future__ import annotations

from packages.application.ports.budget_ledger import BudgetLedger
from packages.domain.budget import (
    LedgerCostStatus,
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.core import Timestamp
from packages.domain.tasks import ResearchTask


def _attempt_scoped(entry_id: str, attempt: int) -> str:
    return entry_id if attempt <= 1 else f"{entry_id}:attempt-{attempt}"


def record_task_usage(budget: BudgetLedger | None, task: ResearchTask) -> None:
    """task 完成后的确定性用量记录（entry_id 幂等;attempt > 1 时作用域化）。"""
    if budget is None:
        return
    budget.record_usage(
        UsageLedgerEntry(
            entry_id=_attempt_scoped(f"usage:{task.id.value}:turns", task.attempt),
            resource_type=ResourceType.AGENT_TURNS,
            quantity=1,
            unit="turns",
            cost_status=LedgerCostStatus.UNKNOWN,
            source="run_orchestration",
            occurred_at=Timestamp.now().value,
            task_id=task.id.value,
            attempt=task.attempt,
        )
    )


def record_attempt_usage(
    budget: BudgetLedger | None,
    task: ResearchTask,
    attempt: int,
    reason: str | None,
) -> None:
    """失败/重试耗尽路径的 attempt 作用域记账(M15)。

    该次尝试是否消费了完整 turn 不可观测 → quantity=0 且
    quantity_status=UNKNOWN(绝不伪造测量值);entry id 按 attempt 作用域,
    retry 序列追加而非碰撞。
    """
    if budget is None:
        return
    budget.record_usage(
        UsageLedgerEntry(
            entry_id=_attempt_scoped(f"usage:{task.id.value}:turns", attempt),
            resource_type=ResourceType.AGENT_TURNS,
            quantity=0,
            unit="turns",
            cost_status=LedgerCostStatus.UNKNOWN,
            source="run_orchestration",
            occurred_at=Timestamp.now().value,
            task_id=task.id.value,
            quantity_status=LedgerQuantityStatus.UNKNOWN,
            unavailable_reason=reason or "attempt outcome not fully observable",
            attempt=max(1, attempt),
        )
    )


def record_cancelled_usage(budget: BudgetLedger | None, run_id: str, cancelled: int) -> None:
    """取消路径记账(M15):取消任务数 KNOWN,turn 消耗不可观测 → UNKNOWN。"""
    if budget is None:
        return
    budget.record_usage(
        UsageLedgerEntry(
            entry_id=f"usage:{run_id}:cancelled:{cancelled}",
            resource_type=ResourceType.AGENT_TURNS,
            quantity=cancelled,
            unit="tasks",
            cost_status=LedgerCostStatus.UNKNOWN,
            source="run_orchestration",
            occurred_at=Timestamp.now().value,
            quantity_status=LedgerQuantityStatus.UNKNOWN,
            unavailable_reason="cancellation observed; per-attempt turn usage not measurable",
        )
    )
