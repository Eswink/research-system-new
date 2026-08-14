"""Team resolution 的纯辅助函数（service 会话解析的私有逻辑）。"""

from __future__ import annotations

from packages.domain.protocols import CompiledRunPlan
from packages.domain.team_plan import PhaseAssignment


def assigned_agents(assignment: PhaseAssignment) -> tuple[str, ...]:
    agents: list[str] = []
    for candidates in assignment.role_assignments.values():
        agents.extend(candidates)
    return tuple(agents)


def flatten_tool_providers(plan: CompiledRunPlan) -> tuple[str, ...]:
    """冻结 Tool Set：各 phase 全部 ToolRequirement 的 provider 并集。"""
    return tuple(
        sorted({
            provider for tool in plan.tool_requirements for provider in tool.provider_ids
        })
    )