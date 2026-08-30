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
    """task 完成后的确定性用量记录（entry_id 幂等;attempt > 1 时作用域化）。

    与 `record_attempt_usage` **必须使用不同的 entry_id 基名**:两者记录的是
    不同事实(完成消耗 1 turn / 某次尝试消耗不可计量),共用基名会在
    "重试后成功" 这一最常见路径上碰撞。M15 复审只指出失败记账未接线;
    把 budget 接进生产路径后该碰撞立即暴露(F-01 retry-then-succeed 用例)。
    """
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
    """失败/重试路径的 attempt 作用域记账(M15)。

    该次尝试是否消费了完整 turn 不可观测 → quantity=0 且
    quantity_status=UNKNOWN(绝不伪造测量值);entry id 用独立基名
    `usage:{task}:attempt-{n}`,与完成记录的 `usage:{task}:turns` 不共享
    命名空间,retry 序列内部也互不碰撞。
    """
    if budget is None:
        return
    budget.record_usage(
        UsageLedgerEntry(
            entry_id=f"usage:{task.id.value}:attempt-{max(1, attempt)}",
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


def record_cancelled_usage(
    budget: BudgetLedger | None,
    run_id: str,
    task_ids: tuple[str, ...],
) -> None:
    """取消路径按真实 task 归属记账(M15)。

    旧实现把 `cancelled` 数量塞进 `usage:{run}:cancelled:{count}`：不同的
    取消事件只要数量相同就碰撞，且 entry 没有 task_id，run 级 usage/cost
    读取会过滤掉它。现在每个 canonical task 有自己的稳定 entry id 和
    task_id；重复 cancel 由 `record_usage_batch` 收敛为 no-op。
    """
    if budget is None or not task_ids:
        return
    entries = tuple(
        UsageLedgerEntry(
            entry_id=f"usage:{run_id}:task:{task_id}:cancelled",
            resource_type=ResourceType.AGENT_TURNS,
            quantity=0,
            unit="turns",
            cost_status=LedgerCostStatus.UNKNOWN,
            source="run_orchestration",
            occurred_at=Timestamp.now().value,
            run_id=run_id,
            task_id=task_id,
            quantity_status=LedgerQuantityStatus.UNKNOWN,
            unavailable_reason="cancellation observed; per-attempt turn usage not measurable",
        )
        for task_id in sorted(set(task_ids))
    )
    budget.record_usage_batch(entries)
