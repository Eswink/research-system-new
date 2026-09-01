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
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)


def _attempt_scope(entry_id: str, attempt: int) -> str:
    """attempt > 1 时为 entry id 追加 attempt 后缀(retry 追加而非碰撞)。"""
    return entry_id if attempt <= 1 else f"{entry_id}:attempt-{attempt}"


@dataclass(frozen=True, slots=True)
class ModelUsage:
    """一次模型调用的原始用量（ModelGateway 上报）。

    M15:`usage_unavailable_reason` 非空 → quantity_status=UNKNOWN
    (token 计数不可信,绝不解释为 0);`attempt` 用于 attempt-scoped entry id。
    """

    model_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    calls: int = 1
    latency_ms: int | None = None
    estimated_cost_minor: int | None = None
    usage_unavailable_reason: str | None = None
    attempt: int = 1


@dataclass(frozen=True, slots=True)
class ToolUsage:
    """一次工具调用的原始用量（ToolProvider 上报）。"""

    tool_id: str
    requests: int = 1
    estimated_cost_minor: int | None = None
    attempt: int = 1


@dataclass(frozen=True, slots=True)
class ExperimentUsage:
    """一次实验执行的原始用量（ExecutionBackend compute_usage_summary）。"""

    run_id: str
    image_digest: str | None = None
    elapsed_seconds: int | None = None
    oom_killed: bool = False
    exit_code: int | None = None
    attempt: int = 1


@dataclass(frozen=True, slots=True)
class EvaluationUsage:
    """一次评测运行的原始用量（EvalRunner 上报）。

    deterministic scorer 与模型调用是不同资源：写入专用
    `EVALUATION_SCORER`，而不是伪装为 `MODEL_REQUESTS`。评测与其触发
    task 的归属由 close_budget 的 task_id 统一传递，保证 run 级视图可达。
    """

    eval_id: str
    cases: int = 0
    scorer_calls: int = 0
    attempt: int = 1


def _entry(  # noqa: PLR0913 - UsageLedgerEntry 字段映射，参数对象会降低可读性
    *,
    entry_id: str,
    resource_type: ResourceType,
    quantity: int,
    unit: str,
    source: str,
    occurred_at: datetime,
    estimated_cost_minor: int | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
    agent_id: str | None = None,
    tool_id: str | None = None,
    model_id: str | None = None,
    quantity_status: LedgerQuantityStatus = LedgerQuantityStatus.KNOWN,
    unavailable_reason: str | None = None,
    attempt: int = 1,
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
        run_id=run_id,
        task_id=task_id,
        agent_id=agent_id,
        tool_id=tool_id,
        model_id=model_id,
        quantity_status=quantity_status,
        unavailable_reason=unavailable_reason,
        attempt=attempt,
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
        unknown = usage.usage_unavailable_reason is not None
        entries.append(
            _entry(
                entry_id=_attempt_scope(f"usage:{run_id}:model:{usage.model_id}", usage.attempt),
                resource_type=ResourceType.MODEL_TOKENS,
                quantity=0 if unknown else tokens,
                unit="tokens",
                source="m12:model_relay",
                occurred_at=occurred_at,
                estimated_cost_minor=usage.estimated_cost_minor,
                run_id=run_id,
                task_id=task_id,
                agent_id=agent_id,
                model_id=usage.model_id,
                quantity_status=(
                    LedgerQuantityStatus.UNKNOWN if unknown else LedgerQuantityStatus.KNOWN
                ),
                unavailable_reason=usage.usage_unavailable_reason,
                attempt=usage.attempt,
            )
        )
        entries.append(
            _entry(
                entry_id=_attempt_scope(
                    f"usage:{run_id}:model:{usage.model_id}:calls", usage.attempt
                ),
                resource_type=ResourceType.MODEL_REQUESTS,
                quantity=usage.calls,
                unit="calls",
                source="m12:model_relay",
                occurred_at=occurred_at,
                run_id=run_id,
                task_id=task_id,
                agent_id=agent_id,
                model_id=usage.model_id,
                attempt=usage.attempt,
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
            entry_id=_attempt_scope(f"usage:{run_id}:tool:{usage.tool_id}", usage.attempt),
            resource_type=ResourceType.TOOL_REQUESTS,
            quantity=usage.requests,
            unit="requests",
            source="m12:tool_plane",
            occurred_at=occurred_at,
            estimated_cost_minor=usage.estimated_cost_minor,
            run_id=run_id,
            task_id=task_id,
            tool_id=usage.tool_id,
            attempt=usage.attempt,
        )
        for usage in tool_usage
    ]


def experiment_entries(
    run_id: str,
    experiment_usage: tuple[ExperimentUsage, ...],
    occurred_at: datetime,
    task_id: str | None,
) -> list[UsageLedgerEntry]:
    """CPU_TIME 入账：时长未知（None）→ quantity_status=UNKNOWN,绝不假测量零。"""
    return [
        _entry(
            entry_id=_attempt_scope(f"usage:{run_id}:experiment:{usage.run_id}", usage.attempt),
            resource_type=ResourceType.CPU_TIME,
            quantity=usage.elapsed_seconds or 0,
            unit="seconds",
            source="m12:experiment",
            occurred_at=occurred_at,
            run_id=run_id,
            task_id=task_id,
            quantity_status=(
                LedgerQuantityStatus.UNKNOWN
                if usage.elapsed_seconds is None
                else LedgerQuantityStatus.KNOWN
            ),
            unavailable_reason=None
            if usage.elapsed_seconds is not None
            else "elapsed_seconds not observed",
            attempt=usage.attempt,
        )
        for usage in experiment_usage
    ]


def evaluation_entries(
    run_id: str,
    evaluation_usage: tuple[EvaluationUsage, ...],
    occurred_at: datetime,
    task_id: str | None,
    agent_id: str | None,
) -> list[UsageLedgerEntry]:
    """评测用量有 run task 归属，deterministic scorer 不是模型调用。"""
    return [
        _entry(
            entry_id=_attempt_scope(f"usage:{run_id}:eval:{usage.eval_id}", usage.attempt),
            resource_type=ResourceType.EVALUATION_SCORER,
            quantity=usage.scorer_calls,
            unit="scorer_calls",
            source="m12:evaluation",
            occurred_at=occurred_at,
            run_id=run_id,
            task_id=task_id,
            agent_id=agent_id,
            attempt=usage.attempt,
        )
        for usage in evaluation_usage
    ]


# M16 re-audit F-5: remote execution has NO separate usage namespace. Its wall
# clock is server-measured (RemoteExecutionBackend.compute_usage_summary
# ["elapsed_seconds"]) and flows through the single experiment path
# (usage_collection → close_budget → experiment_entries). A second
# `usage:{run}:remote-exec:{task}` counter would be a second usage truth.


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
