"""Team resolution 的纯辅助函数（service 会话解析的私有逻辑）。"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from packages.domain.core import ID
from packages.domain.protocols import CompiledRunPlan
from packages.domain.tasks import ResearchTask, TaskContract
from packages.domain.team_plan import PhaseAssignment

if TYPE_CHECKING:
    from packages.application.run_orchestration.context import RunContext
    from packages.application.run_orchestration.task_executor import SessionSpecContext

    SessionSpec = tuple[ResearchTask, TaskContract, SessionSpecContext]

_ContractFor = Callable[["RunContext", tuple[str, ...]], TaskContract]


def assigned_agents(assignment: PhaseAssignment) -> tuple[str, ...]:
    agents: list[str] = []
    for candidates in assignment.role_assignments.values():
        agents.extend(candidates)
    return tuple(agents)


def flatten_tool_providers(plan: CompiledRunPlan) -> tuple[str, ...]:
    """冻结 Tool Set：各 phase 全部 ToolRequirement 的 provider 并集。"""
    return tuple(
        sorted({provider for tool in plan.tool_requirements for provider in tool.provider_ids})
    )


def resolve_sessions(
    context: "RunContext",
    *,
    contract_for: _ContractFor,
) -> "tuple[SessionSpec, ...]":
    """M4 team resolution：phase assignments → ResearchTask + session spec。"""
    from packages.application.run_orchestration.task_executor import SessionSpecContext

    resolved: list[SessionSpec] = []
    assignments = {item.phase_id: item for item in context.plan.phase_assignments}
    for phase in context.plan.phases:
        assignment = assignments.get(phase.id)
        if assignment is None:
            continue
        for agent_id in assigned_agents(assignment):
            agent = context.catalog.agents[agent_id]
            role = context.catalog.roles[agent.role]
            contract = contract_for(context, phase.task_contract_refs)
            task = ResearchTask(
                id=ID.generate(),
                run_id=context.run.id,
                contract_id=contract.id,
                assigned_agent_id=agent_id,
                status="CREATED",
                idempotency_key=f"{context.run.id.value}:{phase.id}:{agent_id}",
            )
            resolved.append((
                task,
                contract,
                SessionSpecContext(
                    role=role,
                    agent=agent,
                    frozen_manifest_digest=context.frozen_manifest_digest,
                    frozen_tool_set=flatten_tool_providers(context.plan),
                    phase_id=phase.id,
                ),
            ))
    return tuple(resolved)
