"""成本预测视图域：只读派生投影（PLAN-20260914-046 WP-B，EC-04 第一批）。

本模块只定义**派生视图**并做纯函数聚合，不含持久化、不写账本：

- 输入 = BudgetLedger snapshot 中归属本 run 的 reservations（已预留）与
  usage entries（已消耗）；
- 输出 = 按 (resource_type, unit) 分组的 reserved / consumed / remaining，
  以及已消耗金额的诚实摘要。

诚实边界：

- **不外推未预留开销**：只有在账本里真实存在的预留额度才参与"剩余"计算；
  未预留的未来用量不预测（没有 burn-rate 外推，页面如实标注）。
- **UNKNOWN ≠ 0**：组内任一条目 quantity_status=UNKNOWN 时，consumed 与
  remaining 均为 None（不可计量），绝不降级为 0。
- **不跨币种求和**：多币种并存时金额状态为 CURRENCY_CONFLICT，不隐式换算。
- remaining 为负表示"消耗超出预留"——如实呈现，不截断为 0。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from packages.domain.budget import (
    BudgetReservation,
    LedgerCostStatus,
    LedgerQuantityStatus,
    ResourceType,
    UsageLedgerEntry,
)

FORECAST_SCOPE_RESERVED_ONLY = "RESERVED_ONLY"
SCOPE_NOTE_RESERVED_ONLY = (
    "forecast covers reserved quota minus recorded usage only; "
    "un-reserved future spend is not extrapolated"
)


class ReservationAttribution(StrEnum):
    """预留归属方式：run 与预留的关联必须来自权威引用，不能按作用域猜。"""

    RESERVATION_REF = "RESERVATION_REF"  # 冻结 manifest / 调整登记的 ref 解析成功
    RUN_SCOPE = "RUN_SCOPE"  # ref 不可解析时退化为作用域匹配（显式标注）
    NONE = "NONE"  # 无可归属预留


class ForecastLineStatus(StrEnum):
    """单组消耗计量的完备状态（三态，避免把"无数据"伪装成 0）。"""

    KNOWN = "KNOWN"  # 组内条目全部可计量 → consumed 已计算
    UNKNOWN = "UNKNOWN"  # 组内含 quantity_status=UNKNOWN 条目 → 不可计量
    NO_DATA = "NO_DATA"  # 组内无 usage 条目（预留存在但尚无消耗记录）


class ForecastCostStatus(StrEnum):
    """已消耗金额的完备状态（None 金额不等于 0）。"""

    NO_DATA = "NO_DATA"  # 本 run 无 usage entry：与"已测量为零"严格区分
    ACTUAL = "ACTUAL"  # 全部条目为实测金额
    ESTIMATED = "ESTIMATED"  # 全部条目为估计金额
    PARTIALLY_METERED = "PARTIALLY_METERED"  # 混合 actual/estimated
    MONETARY_UNAVAILABLE = "MONETARY_UNAVAILABLE"  # 有 UNKNOWN 成本条目
    CURRENCY_CONFLICT = "CURRENCY_CONFLICT"  # 跨币种：不求和，也不换算


@dataclass(frozen=True, slots=True)
class ForecastLine:
    """单组 (resource_type, unit) 的预留/消耗/剩余。

    `consumed` 与 `remaining` 为 None 表示不可计量或尚无消耗记录
    （由 `data_status` 区分 UNKNOWN / NO_DATA）；`remaining` 可为负
    （消耗超出预留）。quantity 类型为 int | Decimal：时长类资源可为小数
    （与 UsageLedgerEntry.quantity 同口径）。
    """

    resource_type: ResourceType
    unit: str
    reserved: int
    consumed: int | Decimal | None
    remaining: int | Decimal | None
    data_status: ForecastLineStatus
    entry_count: int
    unknown_entry_count: int

    def __post_init__(self) -> None:
        if self.reserved < 0:
            raise ValueError("reserved quantity must be non-negative")
        if self.entry_count < 0 or self.unknown_entry_count < 0:
            raise ValueError("entry counts must be non-negative")
        if self.unknown_entry_count > self.entry_count:
            raise ValueError("unknown entries cannot exceed total entries")
        if self.data_status is ForecastLineStatus.KNOWN and self.consumed is None:
            raise ValueError("KNOWN line must carry a consumed amount")
        if self.data_status is not ForecastLineStatus.KNOWN and self.consumed is not None:
            raise ValueError("non-KNOWN line must not carry a consumed amount")
        if self.data_status is ForecastLineStatus.NO_DATA and self.entry_count != 0:
            raise ValueError("NO_DATA line must not carry entries")


@dataclass(frozen=True, slots=True)
class CostForecast:
    """run 级成本预测视图（只读；外推边界见模块 docstring）。

    `attribution` 记录预留是怎么归到本 run 的：正式 preflight 预留的作用域是
    `phase:<id>`（不含 run id），只有冻结 manifest / 调整登记返回的 ref 能证明
    归属；按作用域匹配只是退化路径，必须显式标注。`unattributed_reserved` 是
    账本里存在、但无权威引用可归到本 run 的预留条数（不为 0 时说明该 run 的
    预留总量不完整）。
    """

    run_id: str
    lines: tuple[ForecastLine, ...]
    consumed_cost_minor: int | None
    currency: str | None
    cost_status: ForecastCostStatus
    unknown_cost_entries: int
    attribution: ReservationAttribution = ReservationAttribution.NONE
    unattributed_reserved: int = 0
    forecast_scope: str = FORECAST_SCOPE_RESERVED_ONLY
    scope_note: str = SCOPE_NOTE_RESERVED_ONLY


def build_cost_forecast(
    run_id: str,
    reservations: tuple[BudgetReservation, ...],
    entries: tuple[UsageLedgerEntry, ...],
    *,
    attribution: ReservationAttribution = ReservationAttribution.RUN_SCOPE,
    unattributed_reserved: int = 0,
) -> CostForecast:
    """纯函数：由既有账本快照派生预测视图（不修改任何输入）。

    调用方负责归属：`reservations` 只应包含可归到本 run 的预留（由 ref 解析
    或显式退化作用域匹配得到），归属方式与未归属条数如实传入。
    """
    reserved_by_key = _reserved_by_key(run_id, reservations)
    groups = _consume_groups(entries)
    keys = sorted(set(reserved_by_key) | set(groups), key=lambda item: (item[0].value, item[1]))
    lines = tuple(
        _line_of(resource_type, unit, reserved_by_key, groups) for resource_type, unit in keys
    )
    unknown_cost = sum(
        1
        for entry in entries
        if entry.cost_status is LedgerCostStatus.UNKNOWN
        or entry.quantity_status is LedgerQuantityStatus.UNKNOWN
    )
    total, currency, cost_status = _cost_summary(entries)
    return CostForecast(
        run_id=run_id,
        lines=lines,
        consumed_cost_minor=total,
        currency=currency,
        cost_status=cost_status,
        unknown_cost_entries=unknown_cost,
        attribution=attribution,
        unattributed_reserved=unattributed_reserved,
    )


def _reserved_by_key(
    run_id: str, reservations: tuple[BudgetReservation, ...]
) -> dict[tuple[ResourceType, str], int]:
    """按 (resource_type, unit) 聚合本 run 的预留额度。

    归属已由调用方决定（ref 解析或显式退化匹配）；`run:<id>` 作用域的检查
    仍在此执行：声称归到本 run 的预留若作用域指向别的 run，属调用方错误。
    """
    scope = f"run:{run_id}"
    reserved: dict[tuple[ResourceType, str], int] = {}
    for item in reservations:
        if item.scope.startswith("run:") and item.scope != scope:
            raise ValueError(
                f"reservation {item.id} is scoped to {item.scope}, not to run {run_id}"
            )
        key = (item.resource_type, item.unit)
        reserved[key] = reserved.get(key, 0) + item.quantity
    return reserved


def _consume_groups(
    entries: tuple[UsageLedgerEntry, ...],
) -> dict[tuple[ResourceType, str], list[UsageLedgerEntry]]:
    groups: dict[tuple[ResourceType, str], list[UsageLedgerEntry]] = {}
    for entry in entries:
        groups.setdefault((entry.resource_type, entry.unit), []).append(entry)
    return groups


def _line_of(
    resource_type: ResourceType,
    unit: str,
    reserved_by_key: dict[tuple[ResourceType, str], int],
    groups: dict[tuple[ResourceType, str], list[UsageLedgerEntry]],
) -> ForecastLine:
    key = (resource_type, unit)
    reserved = reserved_by_key.get(key, 0)
    items = groups.get(key, [])
    unknown = sum(1 for item in items if item.quantity_status is LedgerQuantityStatus.UNKNOWN)
    if not items:
        status, consumed = ForecastLineStatus.NO_DATA, None
    elif unknown:
        status, consumed = ForecastLineStatus.UNKNOWN, None
    else:
        status, consumed = ForecastLineStatus.KNOWN, sum((item.quantity for item in items), start=0)
    return ForecastLine(
        resource_type=resource_type,
        unit=unit,
        reserved=reserved,
        consumed=consumed,
        remaining=None if consumed is None else reserved - consumed,
        data_status=status,
        entry_count=len(items),
        unknown_entry_count=unknown,
    )


def _cost_summary(
    entries: tuple[UsageLedgerEntry, ...],
) -> tuple[int | None, str | None, ForecastCostStatus]:
    """已消耗金额摘要：不跨币种求和，UNKNOWN 不解释为 0。"""
    if not entries:
        return None, None, ForecastCostStatus.NO_DATA
    known = [entry for entry in entries if _amount_of(entry) is not None]
    if any(entry.cost_status is LedgerCostStatus.UNKNOWN for entry in entries):
        return None, None, ForecastCostStatus.MONETARY_UNAVAILABLE
    currencies = {entry.currency for entry in known}
    if len(currencies) > 1:
        return None, None, ForecastCostStatus.CURRENCY_CONFLICT
    currency = next(iter(currencies)) if currencies else None
    if len(known) < len(entries):
        return None, currency, ForecastCostStatus.MONETARY_UNAVAILABLE
    subtotal = sum(amount for entry in known if (amount := _amount_of(entry)) is not None)
    kinds = {_amount_kind(entry) for entry in entries}
    status = (
        ForecastCostStatus.ACTUAL
        if kinds == {"actual"}
        else ForecastCostStatus.ESTIMATED
        if kinds == {"estimated"}
        else ForecastCostStatus.PARTIALLY_METERED
    )
    return subtotal, currency, status


def _amount_of(entry: UsageLedgerEntry) -> int | None:
    if entry.actual_cost_minor is not None:
        return entry.actual_cost_minor
    return entry.estimated_cost_minor


def _amount_kind(entry: UsageLedgerEntry) -> str:
    return "actual" if entry.actual_cost_minor is not None else "estimated"
