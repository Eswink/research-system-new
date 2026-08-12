"""phase → role → agent 绑定投影（RequiredRoles 的稳定解析结果）。"""

from __future__ import annotations

from packages.domain.activation import RoleActivationResult
from packages.domain.protocols import ProtocolDefinition
from packages.domain.team_plan import PhaseAssignment


def phase_assignments(
    protocol: ProtocolDefinition,
    agent_candidates: dict[str, list[str]],
    activation: RoleActivationResult,
) -> list[PhaseAssignment]:
    """按 phase 生成 role → agent 绑定；未激活 role 不分配 agent。"""
    decisions = {item.role_id: item for item in activation.decisions}
    assignments: list[PhaseAssignment] = []
    for phase in protocol.phases:
        role_assignments: dict[str, tuple[str, ...]] = {}
        for requirement in phase.required_roles:
            decision = decisions.get(requirement.role)
            if decision is not None and not decision.activated:
                continue
            candidates = agent_candidates.get(requirement.role, [])
            role_assignments[requirement.role] = tuple(candidates[: requirement.min_instances])
        assignments.append(PhaseAssignment(phase.id, role_assignments))
    return assignments
