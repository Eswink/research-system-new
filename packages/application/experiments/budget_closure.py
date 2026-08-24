"""M12 Budget / Usage Closure：四源用量闭环到 BudgetLedger（清偿 SA-1-M008）。

Model / Tool / Experiment / Evaluation 四类用量统一记录为
UsageLedgerEntry（append-only，幂等 entry_id，成本未知如实标 UNKNOWN
不伪造金额）；BudgetPolicy 阈值检查区分：
- 突破硬限 → BudgetExhaustedError（budget failure，非系统 FAILED）；
- reservation 与 actual 对账（reserve → usage → release 一致性）。

Usage 数据类型与条目构造在 budget_entries.py（模块规模阈值拆分）；
本 use case 只组合 BudgetLedger Port 与 Domain 类型。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.experiments.budget_entries import (
    EvaluationUsage,
    ExperimentUsage,
    ModelUsage,
    ToolUsage,
    evaluation_entries,
    experiment_entries,
    model_entries,
    summarize,
    tool_entries,
)
from packages.application.ports.budget_ledger import BudgetLedger
from packages.domain.budget import BudgetPolicy, ResourceType, UsageLedgerEntry
from packages.domain.core import Timestamp


class BudgetExhaustedError(Exception):
    """预算硬限突破：budget failure，与基础设施/科学负结论分离。"""


@dataclass(frozen=True, slots=True)
class BudgetClosureInput:
    """一次归账的聚合输入（参数对象）。"""

    run_id: str
    model_usage: tuple[ModelUsage, ...] = ()
    tool_usage: tuple[ToolUsage, ...] = ()
    experiment_usage: tuple[ExperimentUsage, ...] = ()
    evaluation_usage: tuple[EvaluationUsage, ...] = ()
    task_id: str | None = None
    agent_id: str | None = None


@dataclass(frozen=True, slots=True)
class BudgetClosureResult:
    """归账结果：entry 数、总量摘要、对账结论。"""

    entries: tuple[UsageLedgerEntry, ...]
    total_tokens: int
    tool_requests: int
    experiment_runs: int
    evaluation_cases: int
    reservation_ref: str | None = None
    reservation_actual_consistent: bool = False


def close_budget(
    ledger: BudgetLedger,
    *,
    input: BudgetClosureInput,
    policy: BudgetPolicy | None = None,
    reservation_ref: str | None = None,
) -> BudgetClosureResult:
    """把四源用量归账到 BudgetLedger；突破硬限抛 BudgetExhaustedError。

    归账粒度（M12 至少可回答）：
    - Model：token/call（MODEL_TOKENS / MODEL_REQUESTS，可带成本）；
    - Tool：请求数（TOOL_REQUESTS）；
    - Experiment：CPU_TIME（时长未知时如实记 UNKNOWN，不伪造秒数）；
    - Evaluation：case/scorer 调用（独立于 MODEL_REQUESTS 之外计数）。
    """
    occurred_at = Timestamp.now().value
    run_id = input.run_id
    entries = model_entries(run_id, input.model_usage, occurred_at, input.task_id, input.agent_id)
    entries += tool_entries(run_id, input.tool_usage, occurred_at, input.task_id)
    entries += experiment_entries(run_id, input.experiment_usage, occurred_at, input.task_id)
    entries += evaluation_entries(run_id, input.evaluation_usage, occurred_at)
    summary = summarize(entries)
    if policy is not None:
        _enforce_limits(
            policy, summary.total_tokens, summary.tool_requests, summary.experiment_seconds
        )
    for entry in entries:
        ledger.record_usage(entry)
    return BudgetClosureResult(
        entries=tuple(entries),
        total_tokens=summary.total_tokens,
        tool_requests=summary.tool_requests,
        experiment_runs=summary.experiment_runs,
        evaluation_cases=sum(usage.cases for usage in input.evaluation_usage),
        reservation_ref=reservation_ref,
        reservation_actual_consistent=_check_reservation(
            ledger, reservation_ref, summary.total_tokens, summary.tool_requests
        ),
    )


def _enforce_limits(
    policy: BudgetPolicy,
    tokens: int,
    tool_requests: int,
    experiment_seconds: int,
) -> None:
    limits = policy.hard_limits
    if "model_tokens" in limits and tokens > int(limits["model_tokens"]):
        raise BudgetExhaustedError(
            f"model token budget exhausted: {tokens} > {limits['model_tokens']}"
        )
    if "tool_requests" in limits and tool_requests > int(limits["tool_requests"]):
        raise BudgetExhaustedError(
            f"tool request budget exhausted: {tool_requests} > {limits['tool_requests']}"
        )
    if "wall_clock_seconds" in limits and experiment_seconds > int(limits["wall_clock_seconds"]):
        raise BudgetExhaustedError(
            f"wall clock budget exhausted: {experiment_seconds}s > {limits['wall_clock_seconds']}s"
        )


def _check_reservation(
    ledger: BudgetLedger,
    reservation_ref: str | None,
    tokens: int,
    tool_requests: int,
) -> bool:
    """reservation 与 actual 对账：ref 存在且 actual ≤ reservation 量。"""
    if reservation_ref is None:
        return False
    snapshot = ledger.snapshot()
    reservations = snapshot.reservations
    reserved_tokens = sum(
        item.quantity for item in reservations if item.resource_type is ResourceType.MODEL_TOKENS
    )
    reserved_tools = sum(
        item.quantity for item in reservations if item.resource_type is ResourceType.TOOL_REQUESTS
    )
    if reserved_tokens and tokens > reserved_tokens:
        return False
    if reserved_tools and tool_requests > reserved_tools:
        return False
    return True
