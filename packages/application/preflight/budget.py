"""Preflight 预算聚合与预留决策。"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports import BudgetLedger
from packages.domain.budget import BudgetPolicy, BudgetReservation, ResourceType
from packages.domain.serialization import digest_of

_LIMIT_KEYS = {
    ResourceType.PARALLELISM: "agent_sessions",
    ResourceType.TOOL_REQUESTS: "tool_requests",
    ResourceType.WALL_CLOCK: "wall_clock_seconds",
}


@dataclass(frozen=True, slots=True)
class BudgetCheck:
    totals: dict[str, int]
    exceeded: dict[str, tuple[int, int]]
    unknown_limits: tuple[str, ...]
    unmapped_types: tuple[ResourceType, ...] = ()

    @property
    def allowed(self) -> bool:
        return not self.exceeded


@dataclass(frozen=True, slots=True)
class BudgetReservationResult:
    check: BudgetCheck
    reservation_ref: str | None


def _aggregate(reservations: tuple[BudgetReservation, ...]) -> dict[ResourceType, int]:
    totals: dict[ResourceType, int] = {}
    for reservation in reservations:
        current = totals.get(reservation.resource_type, 0)
        if reservation.resource_type is ResourceType.PARALLELISM:
            totals[reservation.resource_type] = max(current, reservation.quantity)
        else:
            totals[reservation.resource_type] = current + reservation.quantity
    return totals


def check_budget(
    reservations: tuple[BudgetReservation, ...],
    policy: BudgetPolicy,
) -> BudgetCheck:
    totals = _aggregate(reservations)
    rendered: dict[str, int] = {}
    exceeded: dict[str, tuple[int, int]] = {}
    unknown: list[str] = []
    unmapped: list[ResourceType] = []
    for resource_type, quantity in sorted(totals.items(), key=lambda item: item[0].value):
        key = _LIMIT_KEYS.get(resource_type)
        if key is None:
            # 未映射 ResourceType 不能静默放行：预算检查不完整必须显式暴露。
            unmapped.append(resource_type)
            continue
        rendered[key] = quantity
        limit = policy.hard_limits.get(key)
        if limit is None:
            unknown.append(key)
        elif quantity > limit:
            exceeded[key] = (quantity, limit)
    return BudgetCheck(rendered, exceeded, tuple(unknown), tuple(unmapped))


def _reservation_ref(policy: BudgetPolicy, reservations: tuple[BudgetReservation, ...]) -> str:
    digest = digest_of((policy, reservations))
    return f"budget-reservation:{digest.hex_value}"


def reserve_budget(
    reservations: tuple[BudgetReservation, ...],
    policy: BudgetPolicy,
    port: BudgetLedger | None = None,
) -> BudgetReservationResult:
    check = check_budget(reservations, policy)
    if not check.allowed:
        return BudgetReservationResult(check, None)
    reservation_ref: str | None = None
    if port is not None:
        reservation_ref = port.reserve(reservations, policy)
    else:
        reservation_ref = _reservation_ref(policy, reservations)
    return BudgetReservationResult(check, reservation_ref)
