"""M15 Usage → Cost 投影(纯函数)。

唯一 usage 输入是 `BudgetLedger.snapshot()`(telemetry 绝不作为成本输入);
每个投影金额盖 `pricing_version` + `pricing_digest` 章,价格表后续变更产生
新版本,不能改写历史投影(CostAmount 不可变)。
五状态完备:`unknown` 绝不折叠为 0;未配置价格绝不伪造 0 成本。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from packages.application.cost.amount import (
    CostAmount,
    CostAmountStatus,
    _amount,
    _stamp_of,
)
from packages.application.cost.pricing import (
    PriceDimension,
    PricingTable,
    unpriced_table,
)
from packages.application.cost.pricing_resolution import (
    UNFROZEN_PRICING_VERSION,
    RunPricingResolution,
    resolve_run_pricing,
)
from packages.domain.budget import (
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)


@dataclass(frozen=True, slots=True)
class DimensionCost:
    """一个 (dimension, resource_key) 分组的投影结果。"""

    dimension: str
    resource_key: str
    amount: CostAmount
    entry_count: int


def _dimension_of(entry: UsageLedgerEntry) -> tuple[PriceDimension, str] | None:
    """entry → 定价维度与 resource key;不可定价维度返回 None。"""
    resource_type = entry.resource_type
    if resource_type in (ResourceType.MODEL_TOKENS, ResourceType.MODEL_REQUESTS):
        return (PriceDimension.MODEL, entry.model_id or "unknown")
    if resource_type is ResourceType.MODEL_COST:
        # Relay 上报的 provider monetary amount 是模型成本，不是 evaluation；
        # key 必须是 model_id，不能按 task_id 把可达价格变成不可达。
        return (PriceDimension.MODEL, entry.model_id or "unknown")
    if resource_type in (ResourceType.TOOL_REQUESTS, ResourceType.TOOL_COST):
        return (PriceDimension.TOOL, entry.tool_id or "unknown")
    if resource_type is ResourceType.CPU_TIME:
        return (PriceDimension.EXPERIMENT, entry.task_id or "unknown")
    if resource_type is ResourceType.EVALUATION_SCORER:
        return (PriceDimension.EVALUATION, entry.task_id or "unknown")
    return None


def project_entry_cost(
    entry: UsageLedgerEntry,
    pricing: PricingTable | None,
) -> CostAmount:
    """单条 ledger entry → CostAmount(状态判定树,见模块 docstring)。"""
    stamp = _stamp_of(pricing)

    if entry.quantity_status is LedgerQuantityStatus.UNKNOWN:
        return _amount(CostAmountStatus.USAGE_UNKNOWN, None, stamp)
    if entry.quantity == 0:
        return _amount(CostAmountStatus.ZERO, 0, stamp)
    if entry.actual_cost_minor is not None:
        # entry 自带币种时以它为准:金额与币种必须同源,否则聚合会把不同币种
        # 的数字相加(复审实测 [300 USD, 3000 JPY] 得 3300 USD,换序得 3300 JPY)。
        return _amount(
            CostAmountStatus.ACTUAL, entry.actual_cost_minor, stamp, currency=entry.currency
        )
    if entry.resource_type is ResourceType.MODEL_COST and entry.estimated_cost_minor is not None:
        # Relay 已上报的模型金额是可直接展示的上游货币事实；它不应再被
        # pricing table 的 unit 查找挡住，更不能被错误路由到 evaluation/task。
        return _amount(
            CostAmountStatus.ESTIMATED,
            entry.estimated_cost_minor,
            stamp,
            currency=entry.currency,
        )
    dimension_key = _dimension_of(entry)
    if dimension_key is None or pricing is None:
        return _amount(CostAmountStatus.MONETARY_UNAVAILABLE, None, stamp)
    price = pricing.price_for(dimension_key[0], dimension_key[1], entry.unit)
    if price is None:
        return _amount(CostAmountStatus.MONETARY_UNAVAILABLE, None, stamp)
    if entry.estimated_cost_minor is not None:
        return _amount(
            CostAmountStatus.ESTIMATED, entry.estimated_cost_minor, stamp, currency=entry.currency
        )
    return _amount(
        CostAmountStatus.ESTIMATED,
        # PA-1 W3: duration quantities may be fractional; money stays ints.
        int(entry.quantity * price.unit_price_minor),
        stamp,
    )


def unpriced_digest() -> str:
    """出厂 unpriced_v1 的固定 digest(与 unpriced_table().pricing_digest() 一致)。"""
    return unpriced_table().pricing_digest()


def project_dimensions(
    entries: Iterable[UsageLedgerEntry],
    pricing: PricingTable | None,
) -> tuple[DimensionCost, ...]:
    """按 (dimension, resource_key) 分组投影并聚合(确定性排序)。"""
    grouped: dict[tuple[str, str], list[UsageLedgerEntry]] = {}
    for entry in entries:
        dimension_key = _dimension_of(entry)
        key = (
            (dimension_key[0].value, dimension_key[1])
            if dimension_key is not None
            else ("unpriced", entry.resource_type.value)
        )
        grouped.setdefault(key, []).append(entry)
    results: list[DimensionCost] = []
    for (dimension, resource_key), group in sorted(grouped.items()):
        amounts = [project_entry_cost(entry, pricing) for entry in group]
        results.append(
            DimensionCost(
                dimension=dimension,
                resource_key=resource_key,
                amount=aggregate_costs(amounts, pricing),
                entry_count=len(group),
            )
        )
    return tuple(results)


def aggregate_costs(
    amounts: Iterable[CostAmount],
    pricing: PricingTable | None = None,
) -> CostAmount:
    """聚合规则:NO_DATA > 币种冲突 > 部分不可计量 > 求和 > 显式零。

    空集返回 `NO_DATA` 而不是 `ZERO 0`:"没有任何 usage 记录"与"已测量为零"
    是不同事实,复审实测前者被当作 `ZERO 0 USD` 报给 `/runs/{id}/cost`——一个
    刚启动、还没产生用量的 run 会显示确定的零成本。空集也不再硬编码
    `"USD"` / `"unpriced_v1"`:传入 `pricing` 时用真实上下文盖章。

    跨币种不做隐式换算:混合币种直接落 `CURRENCY_CONFLICT`,而不是取首项币种
    再无条件求和(那使结果依赖列表顺序)。存在已定价项目与不可计量项目时
    返回 `PARTIALLY_METERED` 和已知小计，避免单条 UNKNOWN 永久抹掉 run 的
    全部已知成本。"""
    items = list(amounts)
    if not items:
        stamp = _stamp_of(pricing)
        return _amount(CostAmountStatus.NO_DATA, None, stamp)
    head = items[0]
    if len({item.currency for item in items}) > 1:
        return replace(head, status=CostAmountStatus.CURRENCY_CONFLICT, minor_units=None)
    blocked = _blocking_status(items)
    if blocked is not None:
        return replace(head, status=blocked, minor_units=None)
    monetary = _monetary_amounts(items)
    if monetary and _has_unmeasured(items):
        total = sum(item.minor_units or 0 for item in monetary)
        return replace(head, status=CostAmountStatus.PARTIALLY_METERED, minor_units=total)
    unmeasurable = _unmeasurable_status(items)
    if unmeasurable is not None:
        return replace(head, status=unmeasurable, minor_units=None)
    if all(item.status is CostAmountStatus.ZERO for item in items):
        return replace(head, status=CostAmountStatus.ZERO, minor_units=0)
    total = sum(
        (item.minor_units or 0)
        for item in items
        if item.status in (CostAmountStatus.ACTUAL, CostAmountStatus.ESTIMATED)
    )
    all_actual = all(
        item.status in (CostAmountStatus.ACTUAL, CostAmountStatus.ZERO) for item in items
    )
    return replace(
        head,
        status=CostAmountStatus.ACTUAL if all_actual else CostAmountStatus.ESTIMATED,
        minor_units=total,
    )


def _monetary_amounts(items: list[CostAmount]) -> list[CostAmount]:
    return [
        item
        for item in items
        if item.status
        in (
            CostAmountStatus.ACTUAL,
            CostAmountStatus.ESTIMATED,
            CostAmountStatus.ZERO,
            CostAmountStatus.PARTIALLY_METERED,
        )
    ]


def _blocking_status(items: list[CostAmount]) -> CostAmountStatus | None:
    """立即阻断的聚合状态(NO_DATA / CURRENCY_CONFLICT 传播)。"""
    if any(item.status is CostAmountStatus.NO_DATA for item in items):
        return CostAmountStatus.NO_DATA
    if any(item.status is CostAmountStatus.CURRENCY_CONFLICT for item in items):
        return CostAmountStatus.CURRENCY_CONFLICT
    return None


def _has_unmeasured(items: list[CostAmount]) -> bool:
    return any(
        item.status
        in (
            CostAmountStatus.USAGE_UNKNOWN,
            CostAmountStatus.MONETARY_UNAVAILABLE,
            CostAmountStatus.PARTIALLY_METERED,
        )
        for item in items
    )


def _unmeasurable_status(items: list[CostAmount]) -> CostAmountStatus | None:
    if any(item.status is CostAmountStatus.USAGE_UNKNOWN for item in items):
        return CostAmountStatus.USAGE_UNKNOWN
    if any(item.status is CostAmountStatus.MONETARY_UNAVAILABLE for item in items):
        return CostAmountStatus.MONETARY_UNAVAILABLE
    return None


__all__ = [
    "CostAmount",
    "CostAmountStatus",
    "DimensionCost",
    "aggregate_costs",
    "project_dimensions",
    "project_entry_cost",
    # re-export（解析实现位于 cost/pricing_resolution.py 以控制文件长度）
    "RunPricingResolution",
    "UNFROZEN_PRICING_VERSION",
    "resolve_run_pricing",
]
