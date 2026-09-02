"""M12 Usage 采集与 Budget 归账接线（M12-R1 WP6）。

从真实执行事件产生用量，禁止手工业务事实注入：
- Model：从 relay CompletionResult.usage（provider 返回的 token 明细）；
  缺字段显式记 UNKNOWN（usage_unavailable_reason），不伪造数字；
- Tool：从正式 ToolResultRecord 计数（已 spill 的成功结果）；
- Experiment：从 ExperimentRunResult 真实时长（非确定性但真实）；
- Evaluation：从 EvalReport 实际 cases/scorer_calls；本次仅 deterministic
  scorer，不虚构 LLM evaluation usage。

idempotency：entry_id 派生自真实事件标识，retry/failure 不 double-count
（ledger.append 拒绝重复 entry_id 由 BudgetLedger 契约保证）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.experiments.budget_closure import (
    BudgetClosureInput,
    close_budget,
)
from packages.application.experiments.budget_entries import (
    EvaluationUsage,
    ExperimentUsage,
    ModelUsage,
    ToolUsage,
)
from packages.application.ports.budget_ledger import BudgetLedger
from packages.application.ports.model_gateway import CompletionResult
from packages.domain.eval_result import EvalReport
from packages.domain.experiments import ExperimentRunResult
from packages.domain.tools import ToolResultRecord


@dataclass(frozen=True, slots=True)
class UsageCollection:
    """一次运行收集到的真实用量（参数对象）。"""

    run_id: str
    model_id: str | None = None
    model_completions: tuple[CompletionResult, ...] = ()
    tool_results: tuple[ToolResultRecord, ...] = ()
    experiment_result: ExperimentRunResult | None = None
    eval_report: EvalReport | None = None
    task_id: str | None = None
    agent_id: str | None = None
    # M15:attempt 作用于 entry id 作用域(retry 追加而非碰撞)与条目元数据
    attempt: int = 1


@dataclass(frozen=True, slots=True)
class CollectedUsage:
    """采集结果摘要：真实值或 UNKNOWN（不含伪造数字）。"""

    model_tokens: int = 0
    model_requests: int = 0
    tool_requests: int = 0
    experiment_seconds: int = 0
    gpu_seconds: int = 0
    eval_cases: int = 0
    eval_scorer_calls: int = 0
    model_usage_unknown: bool = False


def _model_usage(
    collection: UsageCollection,
) -> tuple[ModelUsage, ...]:
    """从真实 CompletionResult.usage 归集；无 usage 明细时记 UNKNOWN。"""
    if not collection.model_completions:
        return ()
    calls = len(collection.model_completions)
    prompt = sum(item.prompt_tokens or 0 for item in collection.model_completions)
    completion = sum(item.completion_tokens or 0 for item in collection.model_completions)
    unavailable = [
        item.usage_unavailable_reason
        for item in collection.model_completions
        if item.usage_unavailable_reason is not None
    ]
    unknown = bool(unavailable)
    usage = ModelUsage(
        model_id=collection.model_id or "unknown",
        prompt_tokens=prompt if not unknown else 0,
        completion_tokens=completion if not unknown else 0,
        calls=calls,
        usage_unavailable_reason=("; ".join(sorted(set(unavailable))) if unknown else None),
        attempt=collection.attempt,
    )
    return (usage,)


def _tool_usage(results: tuple[ToolResultRecord, ...], attempt: int = 1) -> tuple[ToolUsage, ...]:
    from collections import Counter

    counts = Counter(item.tool_id for item in results)
    return tuple(
        ToolUsage(tool_id=tool_id, requests=count, attempt=attempt)
        for tool_id, count in sorted(counts.items())
    )


def _experiment_usage(
    result: ExperimentRunResult | None, attempt: int = 1
) -> tuple[ExperimentUsage, ...]:
    if result is None:
        return ()
    return (
        ExperimentUsage(
            run_id=result.execution_run_id,
            image_digest=result.image_digest,
            elapsed_seconds=_elapsed_seconds(result),
            exit_code=0,
            attempt=attempt,
            gpu_elapsed_seconds=result.gpu_elapsed_seconds,
            peak_gpu_memory_bytes=result.peak_gpu_memory_bytes,
        ),
    )


def _elapsed_seconds(result: ExperimentRunResult) -> int | None:
    """真实时长：由 ExecutionBackend 观测写入 result.elapsed_seconds。

    ExperimentRunResult 无显式 duration 字段；调用方通过执行事件提供，
    本模块不伪造。无观测时返回 None（记 UNKNOWN）。
    """
    return result.elapsed_seconds


def _evaluation_usage(
    report: EvalReport | None,
    attempt: int,
) -> tuple[EvaluationUsage, ...]:
    if report is None:
        return ()
    scorer_calls = sum(len(result.scorer_findings) for result in report.results)
    return (
        EvaluationUsage(
            # eval_id 使用 eval run 唯一标识（report_id），重评产生独立条目，
            # retry 同一 run 保持幂等（entry_id 去重由 ledger 强制）
            eval_id=report.report_id,
            cases=len(report.results),
            scorer_calls=scorer_calls,
            attempt=attempt,
        ),
    )


def collect_usage(collection: UsageCollection) -> tuple[BudgetClosureInput, CollectedUsage]:
    """把真实事件转为 BudgetClosureInput 并附摘要（只读计算，不落账）。"""
    model_usage = _model_usage(collection)
    tool_usage = _tool_usage(collection.tool_results, collection.attempt)
    experiment_usage = _experiment_usage(collection.experiment_result, collection.attempt)
    evaluation_usage = _evaluation_usage(collection.eval_report, collection.attempt)
    summary = CollectedUsage(
        model_tokens=sum(item.prompt_tokens + item.completion_tokens for item in model_usage),
        model_requests=sum(item.calls for item in model_usage),
        tool_requests=sum(item.requests for item in tool_usage),
        experiment_seconds=sum(item.elapsed_seconds or 0 for item in experiment_usage),
        gpu_seconds=sum(item.gpu_elapsed_seconds or 0 for item in experiment_usage),
        eval_cases=sum(item.cases for item in evaluation_usage),
        eval_scorer_calls=sum(item.scorer_calls for item in evaluation_usage),
        model_usage_unknown=any(
            item.usage_unavailable_reason is not None for item in collection.model_completions
        ),
    )
    return (
        BudgetClosureInput(
            run_id=collection.run_id,
            model_usage=model_usage,
            tool_usage=tool_usage,
            experiment_usage=experiment_usage,
            evaluation_usage=evaluation_usage,
            task_id=collection.task_id,
            agent_id=collection.agent_id,
        ),
        summary,
    )


def record_collected_usage(
    ledger: BudgetLedger,
    collection: UsageCollection,
) -> CollectedUsage:
    """真实事件 → close_budget → BudgetLedger（幂等 entry_id 去重）。"""
    closure_input, summary = collect_usage(collection)
    close_budget(ledger, input=closure_input)
    return summary


__all__ = [
    "CollectedUsage",
    "UsageCollection",
    "collect_usage",
    "record_collected_usage",
]
