"""Team resolution 的纯辅助函数（service 会话解析的私有逻辑）。"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from packages.domain.core import ID
from packages.domain.models import LLMEndpoint, ModelDefinition
from packages.domain.protocols import CapabilityExecution, CompiledRunPlan
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


def run_chain_tool_ids(plan: CompiledRunPlan, phase_id: str) -> tuple[str, ...]:
    """该 phase **由运行链执行**（因而不暴露为会话工具）的 provider id（GOAL-011 EC-01）。

    只对显式声明 `capability_execution: run_chain` 的 phase 生效——声明缺席时返回空，
    会话工具列表因此逐字节等于**冻结集**（既有语义）。

    它**不**缩小任何检查面：这些 provider 仍在 `plan.tool_requirements` 里（preflight 的
    策略/凭据/健康判定一字不减）、仍在 `frozen_tool_set` 里（`require_frozen_tool_set`
    仍拦得住越权执行）——被拿掉的只有「会话工具」这一个面。
    """
    phase = next((item for item in plan.phases if item.id == phase_id), None)
    if phase is None or phase.capability_execution is not CapabilityExecution.RUN_CHAIN:
        return ()
    return tuple(
        sorted({
            provider
            for tool in plan.tool_requirements
            if tool.phase_id == phase_id
            for provider in tool.provider_ids
        })
    )


def execution_target(
    context: "RunContext", agent_id: str
) -> tuple[LLMEndpoint | None, ModelDefinition | None]:
    """Agent 的**执行目标**（endpoint + model）——EC-03 解析点。

    解析链：`plan.resolved_models[agent_id]`（编译期定下的 agent → model 绑定，与
    `RunManifest.resolved_models` 同源）→ `catalog.models[model_id]` →
    `catalog.endpoints[model.endpoint_id]`。

    三段**各自独立**收敛为 None：没有 model 时两者都是 None；有 model 但其 endpoint
    不在目录里时返回 `(None, model)`——保留已解析出的那一半，拒绝消息才能精确到
    「缺 endpoint」而不是含糊地说「缺目标」。**不**回退到别的 model、**不**编造
    endpoint：解析是纯映射，拒绝语义在 adapter 侧由门链给（点名缺哪条事实）。
    这样「编译期绑定」与「会话期实际调用」始终是同一份事实，不会漂移。
    """
    model_id = context.plan.resolved_models.get(agent_id)
    if model_id is None:
        return None, None
    model = context.catalog.models.get(model_id)
    if model is None:
        return None, None
    endpoint = context.catalog.endpoints.get(model.endpoint_id)
    return endpoint, model


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
            endpoint, model = execution_target(context, agent_id)
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
                    endpoint=endpoint,
                    model=model,
                    phase_id=phase.id,
                    # GOAL-011 EC-01：本 phase 由运行链执行的能力所属 provider——
                    # 它们**不在**会话工具列表里（冻结集与 preflight 判定不受影响）。
                    run_chain_tool_ids=run_chain_tool_ids(context.plan, phase.id),
                    # GOAL-010 EC-02：phase **声明**的输入制品随 spec 走到结果注册处，
                    # 在那里成为「非模型自述」的来源。声明在协议里（产品面），
                    # 校验在注册处（对象必须在库且内容可重算）——本层只搬运、不解释。
                    declared_input_artifacts=tuple(phase.inputs),
                ),
            ))
    return tuple(resolved)
