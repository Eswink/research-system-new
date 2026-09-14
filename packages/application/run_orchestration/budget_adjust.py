"""Budget adjustment use case（PLAN-20260914-046 WP-A，EC-04 第一批）。

运行中的预算调整以 **reservation 生命周期**表达：release 既有预留引用 +
reserve 新额度（BudgetLedger 是 append-only 账本，无"原地改数"；释放+重留
与 WORKFLOW_RELIABILITY 的 non-idempotent compensation 语义一致）。

既有预留引用来自 RunOrchestrationService 的进程内记账
（`reservation_ref(run_id)`，run 启动时由 manifest 冻结写入）；策略沿用
run 启动时的 project budget policy（调用方解析后传入）。

语义边界：本模块只调整预算面（quantity/预留），不触碰协议/Agent 绑定——
那类变更必须走 Manifest Revision / Fork（保持诚实 501）。
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports.budget_ledger import BudgetLedger
from packages.domain.budget import BudgetPolicy, BudgetReservation, ResourceType


class BudgetAdjustmentError(RuntimeError):
    """预算调整无法执行（预算面缺失/无既有预留可释放）。"""


@dataclass(frozen=True, slots=True)
class AdjustmentLine:
    """一条调整：资源类型 + 新额度（相对整个 run 的目标值，非增量）。"""

    resource_type: ResourceType
    quantity: int
    unit: str

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("adjustment quantity must be non-negative")
        if not self.unit:
            raise ValueError("adjustment unit must not be empty")


@dataclass(frozen=True, slots=True)
class AdjustmentCommand:
    """一次 budget_adjust 干预的全部输入（参数对象，规避参数爆发）。"""

    run_id: str
    policy: BudgetPolicy
    existing_ref: str | None
    lines: tuple[AdjustmentLine, ...]

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must not be empty")
        if not self.lines:
            raise ValueError("budget_adjust requires at least one adjustment line")


@dataclass(frozen=True, slots=True)
class AdjustmentOutcome:
    """调整审计摘要（append-only 账本上的动作记录，不回写历史）。"""

    released_ref: str | None
    reservation_ref: str
    reservations: tuple[BudgetReservation, ...]


def execute_budget_adjustment(
    budget: BudgetLedger | None,
    command: AdjustmentCommand,
) -> AdjustmentOutcome:
    """release 既有预留（若有）+ reserve 新额度。

    预算面缺失 → BudgetAdjustmentError（调用方收敛 503）；无既有预留时
    直接 reserve（首留场景合法）。新预留 scope 固定为 `run:<id>`，id 带规划
    资源类型与 `adjusted` 标记，与 preflight 的 `budget:<phase>:<type>` 形状区分。
    """
    if budget is None:
        raise BudgetAdjustmentError("budget ledger not configured")
    if command.existing_ref is not None:
        budget.release(command.existing_ref)
    reservations = tuple(
        BudgetReservation(
            id=f"budget:{command.run_id}:{line.resource_type.value}:adjusted",
            scope=f"run:{command.run_id}",
            resource_type=line.resource_type,
            quantity=line.quantity,
            unit=line.unit,
        )
        for line in command.lines
    )
    reservation_ref = budget.reserve(reservations, command.policy)
    return AdjustmentOutcome(
        released_ref=command.existing_ref,
        reservation_ref=reservation_ref,
        reservations=reservations,
    )
