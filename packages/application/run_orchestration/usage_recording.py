"""任务完成后的确定性用量记录（entry_id 幂等）。"""

from __future__ import annotations

from packages.application.ports.budget_ledger import BudgetLedger
from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry
from packages.domain.core import Timestamp
from packages.domain.tasks import ResearchTask


def record_task_usage(budget: BudgetLedger | None, task: ResearchTask) -> None:
    """task 完成后的确定性用量记录（entry_id 幂等）。"""
    if budget is None:
        return
    budget.record_usage(
        UsageLedgerEntry(
            entry_id=f"usage:{task.id.value}:turns",
            resource_type=ResourceType.AGENT_TURNS,
            quantity=1,
            unit="turns",
            cost_status=LedgerCostStatus.UNKNOWN,
            source="run_orchestration",
            occurred_at=Timestamp.now().value,
            task_id=task.id.value,
        )
    )
