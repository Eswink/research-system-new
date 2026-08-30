"""Usage 归一化：SDK ConversationStats → Research OS UsageLedgerEntry。

用量原始数据从 OpenHands 采集（ConversationStats.usage_to_metrics 结构化
Metrics：accumulated_token_usage/accumulated_cost/response_latencies），
记账/归账由 Research OS BudgetLedger 拥有（M5_PORT_COMPATIBILITY_MATRIX §11）；
SDK 不是预算真值源。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from openhands.sdk.conversation.conversation_stats import ConversationStats

from packages.domain.budget import LedgerCostStatus, ResourceType, UsageLedgerEntry


@dataclass(frozen=True, slots=True)
class UsageContext:
    """记账上下文（避免参数爆炸）。"""

    source: str
    task_id: str | None = None
    agent_id: str | None = None
    model_id: str | None = None
    now: datetime | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _tokens_entry(usage_id: str, total: int, context: UsageContext) -> UsageLedgerEntry:
    return UsageLedgerEntry(
        entry_id=f"{usage_id}:tokens",
        resource_type=ResourceType.MODEL_TOKENS,
        quantity=total,
        unit="tokens",
        cost_status=LedgerCostStatus.UNKNOWN,
        source=context.source,
        occurred_at=context.now or _utc_now(),
        task_id=context.task_id,
        agent_id=context.agent_id,
        model_id=context.model_id,
    )


def _requests_entry(usage_id: str, count: int, context: UsageContext) -> UsageLedgerEntry:
    return UsageLedgerEntry(
        entry_id=f"{usage_id}:requests",
        resource_type=ResourceType.MODEL_REQUESTS,
        quantity=count,
        unit="requests",
        cost_status=LedgerCostStatus.UNKNOWN,
        source=context.source,
        occurred_at=context.now or _utc_now(),
        task_id=context.task_id,
        agent_id=context.agent_id,
        model_id=context.model_id,
    )


def _cost_entry(usage_id: str, cost_cents: int, context: UsageContext) -> UsageLedgerEntry:
    return UsageLedgerEntry(
        entry_id=f"{usage_id}:cost",
        resource_type=ResourceType.MODEL_COST,
        quantity=1,
        unit="usd-cents",
        cost_status=LedgerCostStatus.KNOWN,
        source=context.source,
        occurred_at=context.now or _utc_now(),
        task_id=context.task_id,
        agent_id=context.agent_id,
        model_id=context.model_id,
        estimated_cost_minor=cost_cents,
    )


def usage_entries_from_stats(
    stats: ConversationStats,
    context: UsageContext,
) -> tuple[UsageLedgerEntry, ...]:
    """ConversationStats → 归一化 UsageLedgerEntry 元组（token/request/cost）。

    entry_id 使用 usage_id 前缀 + 资源类型，保证幂等可去重。
    """
    entries: list[UsageLedgerEntry] = []
    for usage_id, metrics in stats.usage_to_metrics.items():
        usage = getattr(metrics, "accumulated_token_usage", None)
        prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion = int(getattr(usage, "completion_tokens", 0) or 0)
        total = prompt + completion
        if total > 0:
            entries.append(_tokens_entry(usage_id, total, context))
        requests = len(getattr(metrics, "response_latencies", []) or [])
        if requests > 0:
            entries.append(_requests_entry(usage_id, requests, context))
        cost = float(getattr(metrics, "accumulated_cost", 0.0) or 0.0)
        if cost > 0:
            entries.append(_cost_entry(usage_id, max(1, round(cost * 100)), context))
    return tuple(entries)


def publish_usage(
    stats: ConversationStats,
    ledger: Any,
    context: UsageContext,
) -> tuple[UsageLedgerEntry, ...]:
    """归一化并写入 BudgetLedger（Research OS 拥有最终业务记录）。

    usage 是 signal：ledger 为 None 或写入失败时返回已归一化条目但不抛错，
    run() 结果不受影响（记账失败由调用方从返回值/审计日志发现）。
    """
    entries = usage_entries_from_stats(stats, context)
    if ledger is None:
        return entries
    for entry in entries:
        ledger.record_usage(entry)
    return entries


__all__ = ["UsageContext", "usage_entries_from_stats", "publish_usage"]
