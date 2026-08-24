"""M12 Budget 归账条目构造（与 budget_closure.py 拆分，保持模块规模阈值）。

四源（Model/Tool/Experiment/Evaluation）用量数据类型与
UsageLedgerEntry 确定性构造；幂等 entry_id 派生自真实事件标识
（retry/failure 不 double-count，由 BudgetLedger 契约拒绝重复 entry_id 保证）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from packages.domain.budget import (
    LedgerCostStatus,
    ResourceType,
    UsageLedgerEntry,
)


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
        LedgerCostStatus.KNOWN if estimated_cost_minor is not None else LedgerCostStatus.UNKNOWN
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


def model_entries(
    run_id: str,
    model_usage: tuple[ModelUsage, ...],
    occurred_at: datetime,
    task_id: str | None,
    agent_id: str | None,
) -> list[UsageLedgerEntry]:
    entries: list[UsageLedgerEntry] = []
    for usage in model_usage:
        tokens = usage.prompt_tokens + usage.completion_tokens
        entries.append(
            _entry(
                entry_id=f"usage:{run_id}:model:{usage.model_id}",
                resource_type=ResourceType.MODEL_TOKENS,
                quantity=tokens,
                unit="tokens",
                source="m12:model_relay",
                occurred_at=occurred_at,
                estimated_cost_minor=usage.estimated_cost_minor,
                task_id=task_id,
                agent_id=agent_id,
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
                task_id=task_id,
                agent_id=agent_id,
                model_id=usage.model_id,
            )
        )
    return entries


def tool_entries(
    run_id: str,
    tool_usage: tuple[ToolUsage, ...],
    occurred_at: datetime,
    task_id: str | None,
) -> list[UsageLedgerEntry]:
    return [
        _entry(
            entry_id=f"usage:{run_id}:tool:{usage.tool_id}",
            resource_type=ResourceType.TOOL_REQUESTS,
            quantity=usage.requests,
            unit="requests",
            source="m12:tool_plane",
            occurred_at=occurred_at,
            estimated_cost_minor=usage.estimated_cost_minor,
            task_id=task_id,
            tool_id=usage.tool_id,
        )
        for usage in tool_usage
    ]


def experiment_entries(
    run_id: str,
    experiment_usage: tuple[ExperimentUsage, ...],
    occurred_at: datetime,
    task_id: str | None,
) -> list[UsageLedgerEntry]:
    """CPU_TIME 入账：时长未知（None）时 quantity 记 0 + cost UNKNOWN。"""
    return [
        _entry(
            entry_id=f"usage:{run_id}:experiment:{usage.run_id}",
            resource_type=ResourceType.CPU_TIME,
            quantity=usage.elapsed_seconds or 0,
            unit="seconds",
            source="m12:experiment",
            occurred_at=occurred_at,
            task_id=task_id,
        )
        for usage in experiment_usage
    ]


def evaluation_entries(
    run_id: str,
    evaluation_usage: tuple[EvaluationUsage, ...],
    occurred_at: datetime,
) -> list[UsageLedgerEntry]:
    return [
        _entry(
            entry_id=f"usage:{run_id}:eval:{usage.eval_id}",
            resource_type=ResourceType.MODEL_REQUESTS,
            quantity=usage.scorer_calls,
            unit="scorer_calls",
            source="m12:evaluation",
            occurred_at=occurred_at,
        )
        for usage in evaluation_usage
    ]


def summarize(entries: list[UsageLedgerEntry]) -> Summary:
    """条目总量摘要（不落账，只读）。"""
    total_tokens = 0
    tool_requests = 0
    experiment_runs = 0
    experiment_seconds = 0
    for entry in entries:
        if entry.resource_type is ResourceType.MODEL_TOKENS:
            total_tokens += entry.quantity
        elif entry.resource_type is ResourceType.TOOL_REQUESTS:
            tool_requests += entry.quantity
        elif entry.resource_type is ResourceType.CPU_TIME:
            experiment_runs += 1
            experiment_seconds += entry.quantity
    return Summary(
        total_tokens=total_tokens,
        tool_requests=tool_requests,
        experiment_runs=experiment_runs,
        experiment_seconds=experiment_seconds,
    )


@dataclass(frozen=True, slots=True)
class Summary:
    total_tokens: int
    tool_requests: int
    experiment_runs: int
    experiment_seconds: int


__all__ = [
    "EvaluationUsage",
    "ExperimentUsage",
    "ModelUsage",
    "Summary",
    "ToolUsage",
    "evaluation_entries",
    "experiment_entries",
    "model_entries",
    "summarize",
    "tool_entries",
]
