"""Team resolution 的纯辅助函数（service 会话解析的私有逻辑）。"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from packages.domain.core import ID
from packages.domain.models import LLMEndpoint, ModelDefinition
from packages.domain.protocols import CapabilityExecution, CompiledPhase, CompiledRunPlan
from packages.domain.roles import AgentSpec, RoleDefinition
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


def session_tool_face(plan: CompiledRunPlan, phase_id: str) -> tuple[str, ...]:
    """本 phase 的**会话工具面** = 冻结集 − run-chain 排除（GOAL-028 EC-01）。

    与 `adapters/openhands/tool_mapping.session_tool_ids` 同一语义，但**不依赖 adapter**
    （application 层不能 import adapter）；adapter 侧对同一输入做同一次减法，
    两处由 `tests/architecture/python/test_session_tool_bindings_exposure.py` 逐字对齐。
    """
    excluded = set(run_chain_tool_ids(plan, phase_id))
    return tuple(name for name in flatten_tool_providers(plan) if name not in excluded)


def session_tool_bindings(plan: CompiledRunPlan, phase_id: str) -> tuple[tuple[str, str], ...]:
    """该 phase 的**会话工具绑定** `(provider_id, tool_name)`（GOAL-028 EC-01）。

    这是绑定的**唯一解释点**（域内声明 → 编译透传 → 这里解释 → adapter 消费）。
    返回序列与声明顺序一致，并做两条**点名拒绝**（不猜、不静默取其 一）：

    - 绑定的 provider id 必须在本 phase 的**会话工具面**内（冻结集 − run-chain 排除）：
      越界即装配期错误，点名越界的名字——拿一份不描述本次装配的声明去改工具面是不允许的。
    - 同一个 provider 绑定到**两个**工具名 ⇒ 点名拒绝（一次会话里一个 provider 不该有两个
      身份；静默取其一会让「声明」与实际装配分叉）。

    缺省（未声明）⇒ 空元组 ⇒ adapter 侧逐字保持既有语义（provider id 直接交给 SDK）。
    """
    phase = next((item for item in plan.phases if item.id == phase_id), None)
    if phase is None or not phase.session_tool_bindings:
        return ()
    allowed = set(session_tool_face(plan, phase_id))
    outside = sorted({item.provider_id for item in phase.session_tool_bindings} - allowed)
    if outside:
        raise ValueError(
            "session tool bindings reference providers outside this phase's session "
            f"tool face: {', '.join(outside)}"
        )
    pairs: list[tuple[str, str]] = []
    seen: dict[str, str] = {}
    for binding in phase.session_tool_bindings:
        previous = seen.get(binding.provider_id)
        if previous is not None and previous != binding.tool_name:
            raise ValueError(
                f"provider {binding.provider_id} is bound to two tool names: "
                f"{previous!r} and {binding.tool_name!r}"
            )
        seen[binding.provider_id] = binding.tool_name
        pairs.append((binding.provider_id, binding.tool_name))
    return tuple(pairs)


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


def _spec_context(  # noqa: PLR0913 - 装配面：context + phase/agent/role/目标，逐项来自调用点
    context: "RunContext",
    *,
    phase: CompiledPhase,
    agent: AgentSpec,
    role: RoleDefinition,
    endpoint: LLMEndpoint | None,
    model: ModelDefinition | None,
) -> "SessionSpecContext":
    """本 phase 的 `SessionSpecContext`（`resolve_sessions` 的装配细节，单列以守住函数长度门）。"""
    from packages.application.run_orchestration.task_executor import SessionSpecContext

    return SessionSpecContext(
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
        # GOAL-028 EC-01：本 phase 的会话工具绑定（唯一解释点在这里；adapter 侧消费）。
        # 越界 / 一 provider 两名字 ⇒ 点名的 ValueError。
        session_tool_bindings=session_tool_bindings(context.plan, phase.id),
        # GOAL-010 EC-02：phase **声明**的输入制品随 spec 走到结果注册处，在那里成为
        # 「非模型自述」的来源。声明在协议里（产品面），校验在注册处（对象必须在库且
        # 内容可重算）——本层只搬运、不解释。
        declared_input_artifacts=tuple(phase.inputs),
    )


def resolve_sessions(
    context: "RunContext",
    *,
    contract_for: _ContractFor,
) -> "tuple[SessionSpec, ...]":
    """M4 team resolution：phase assignments → ResearchTask + session spec。"""
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
                _spec_context(
                    context, phase=phase, agent=agent, role=role, endpoint=endpoint, model=model
                ),
            ))
    return tuple(resolved)
