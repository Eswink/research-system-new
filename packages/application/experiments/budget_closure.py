"""M12 Budget / Usage Closure：四源用量闭环到 BudgetLedger（清偿 SA-1-M008）。

Model / Tool / Experiment / Evaluation 四类用量统一记录为
UsageLedgerEntry（append-only，幂等 entry_id，成本未知如实标 UNKNOWN
不伪造金额）；BudgetPolicy 阈值检查区分：
- 突破硬限 → BudgetExhaustedError（budget failure，非系统 FAILED）；
- reservation 与 actual 对账（reserve → usage → release 一致性）。

本 use case 只组合 BudgetLedger Port 与 Domain 类型；usage 采集由
各 adapter（ModelGateway / ToolProvider / ExecutionBackend）上报原始
数据，归账在本层完成。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from packages.application.ports.budget_ledger import BudgetLedger
from packages.domain.budget import (
    BudgetPolicy,
    LedgerCostStatus,
    ResourceType,
    UsageLedgerEntry,
)
from packages.domain.core import Timestamp


class BudgetExhaustedError(Exception):
    """预算硬限突破：budget failure，与基础设施/科学负结论分离。"""


@dataclass(frozen=True, slots=True)
class ModelUsage:
    """一次模型调用的原始用量（ModelGateway 上报）。"""

    model_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    calls: int = 1
    latency_ms: int | None = None
    estimated_cost_minor: int | None = None


@dataclass(frozen=True, slots=True)
class ToolUsage:
    """一次工具调用的原始用量（ToolProvider 上报）。"""

    tool_id: str
    requests: int = 1
    estimated_cost_minor: int | None = None


@dataclass(frozen=True, slots=True)
class ExperimentUsage:
    """一次实验执行的原始用量（ExecutionBackend compute_usage_summary）。"""

    run_id: str
    image_digest: str | None = None
    elapsed_seconds: int | None = None
    oom_killed: bool = False
    exit_code: int | None = None


@dataclass(frozen=True, slots=True)
class EvaluationUsage:
    """一次评测运行的原始用量（EvalRunner 上报）。"""

    eval_id: str
    cases: int = 0
    scorer_calls: int = 0


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


def _entry(  # noqa: PLR0913 - UsageLedgerEntry 字段映射，参数对象会降低可读性
    *,
    entry_id: str,
    resource_type: ResourceType,
    quantity: int,
    unit: str,
    source: str,
    occurred_at: datetime,
    estimated_cost_minor: int | None = None,
    task_id: str | None = None,
    agent_id: str | None = None,
    tool_id: str | None = None,
    model_id: str | None = None,
) -> UsageLedgerEntry:
    cost_status = (
        LedgerCostStatus.KNOWN
        if estimated_cost_minor is not None
        else LedgerCostStatus.UNKNOWN
    )
    return UsageLedgerEntry(
        entry_id=entry_id,
        resource_type=resource_type,
        quantity=quantity,
        unit=unit,
        cost_status=cost_status,
        source=source,
        occurred_at=occurred_at,
        estimated_cost_minor=estimated_cost_minor,
        task_id=task_id,
        agent_id=agent_id,
        tool_id=tool_id,
        model_id=model_id,
    )


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
    - Experiment：CPU_TIME / WALL_CLOCK + 资源摘要；
    - Evaluation：case/scorer 调用（MODEL_REQUESTS 之外独立计数）。
    """
    occurred_at = Timestamp.now().value
    run_id = input.run_id
    entries: list[UsageLedgerEntry] = []
    total_tokens = 0
    for usage in input.model_usage:
        tokens = usage.prompt_tokens + usage.completion_tokens
        total_tokens += tokens
        entries.append(
            _entry(
                entry_id=f"usage:{run_id}:model:{usage.model_id}",
                resource_type=ResourceType.MODEL_TOKENS,
                quantity=tokens,
                unit="tokens",
                source="m12:model_relay",
                occurred_at=occurred_at,
                estimated_cost_minor=usage.estimated_cost_minor,
                task_id=input.task_id,
                agent_id=input.agent_id,
                model_id=usage.model_id,
            )
        )
        entries.append(
            _entry(
                entry_id=f"usage:{run_id}:model:{usage.model_id}:calls",
                resource_type=ResourceType.MODEL_REQUESTS,
                quantity=usage.calls,
                unit="calls",
                source="m12:model_relay",
                occurred_at=occurred_at,
                task_id=input.task_id,
                agent_id=input.agent_id,
                model_id=usage.model_id,
            )
        )
    tool_requests = 0
    for tool_usage in input.tool_usage:
        tool_requests += tool_usage.requests
        entries.append(
            _entry(
                entry_id=f"usage:{run_id}:tool:{tool_usage.tool_id}",
                resource_type=ResourceType.TOOL_REQUESTS,
                quantity=tool_usage.requests,
                unit="requests",
                source="m12:tool_plane",
                occurred_at=occurred_at,
                estimated_cost_minor=tool_usage.estimated_cost_minor,
                task_id=input.task_id,
                tool_id=tool_usage.tool_id,
            )
        )
    experiment_seconds = 0
    for exp_usage in input.experiment_usage:
        experiment_seconds += exp_usage.elapsed_seconds or 0
        entries.append(
            _entry(
                entry_id=f"usage:{run_id}:experiment:{exp_usage.run_id}",
                resource_type=ResourceType.CPU_TIME,
                quantity=exp_usage.elapsed_seconds or 0,
                unit="seconds",
                source="m12:experiment",
                occurred_at=occurred_at,
                task_id=input.task_id,
            )
        )
    evaluation_cases = 0
    for eval_usage in input.evaluation_usage:
        evaluation_cases += eval_usage.cases
        entries.append(
            _entry(
                entry_id=f"usage:{run_id}:eval:{eval_usage.eval_id}",
                resource_type=ResourceType.MODEL_REQUESTS,
                quantity=eval_usage.scorer_calls,
                unit="scorer_calls",
                source="m12:evaluation",
                occurred_at=occurred_at,
            )
        )
    if policy is not None:
        _enforce_limits(policy, total_tokens, tool_requests, experiment_seconds)
    for entry in entries:
        ledger.record_usage(entry)
    return BudgetClosureResult(
        entries=tuple(entries),
        total_tokens=total_tokens,
        tool_requests=tool_requests,
        experiment_runs=len(input.experiment_usage),
        evaluation_cases=evaluation_cases,
        reservation_ref=reservation_ref,
        reservation_actual_consistent=_check_reservation(
            ledger, reservation_ref, total_tokens, tool_requests
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
    if "wall_clock_seconds" in limits and experiment_seconds > int(
        limits["wall_clock_seconds"]
    ):
        raise BudgetExhaustedError(
            f"wall clock budget exhausted: {experiment_seconds}s > "
            f"{limits['wall_clock_seconds']}s"
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
        item.quantity
        for item in reservations
        if item.resource_type is ResourceType.MODEL_TOKENS
    )
    reserved_tools = sum(
        item.quantity
        for item in reservations
        if item.resource_type is ResourceType.TOOL_REQUESTS
    )
    if reserved_tokens and tokens > reserved_tokens:
        return False
    if reserved_tools and tool_requests > reserved_tools:
        return False
    return True