"""M4：phase→agent 绑定投影、role 未注册、selection strategy、activation 投影测试。"""

from __future__ import annotations

from dataclasses import replace

from packages.application.protocol_compile import compile_protocol
from packages.domain.core import Version
from packages.domain.enums import (
    ActivationPolicy,
    ModelBindingMode,
    RoleCategory,
    SelectionStrategy,
    WorkspacePolicy,
)
from packages.domain.protocols import (
    FindingSeverity,
    PhaseStrategy,
    ProtocolDefinition,
    ProtocolPhase,
    RoleRequirement,
)
from packages.domain.roles import (
    AgentBinding,
    AgentSpec,
    ModelCapabilityRequirement,
    RoleDefinition,
    RolePool,
    TeamTemplate,
)
from tests.application import protocol_fixtures as fixtures


def _protocol_with_roles(requirements: list[RoleRequirement]) -> ProtocolDefinition:
    return ProtocolDefinition(
        id="m4_protocol_v0_4_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(
                id="collect",
                strategy=PhaseStrategy.PARALLEL_AGENTS,
                required_roles=requirements,
                required_capabilities=["literature.search"],
            )
        ],
    )


def _role(role_id: str, *, skills: list[str] | None = None) -> RoleDefinition:
    return RoleDefinition(
        id=role_id,
        role_type=role_id.title(),
        category=RoleCategory.DISCOVERY,
        activation_default=ActivationPolicy.REQUIRED_BY_PROTOCOL,
        requested_capabilities=["literature.search"],
        hard_model_capabilities=ModelCapabilityRequirement(all_of=["CHAT"]),
        default_skills=list(skills or []),
        workspace_policy=WorkspacePolicy.READ_ONLY,
    )


def _agent(agent_id: str, role_id: str, *, capability_refs: list[str] | None = None) -> AgentSpec:
    return AgentSpec(
        id=agent_id,
        role=role_id,
        model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        capability_refs=list(capability_refs or []),
    )


def test_phase_assignments_project_agents_per_role() -> None:
    catalog = replace(
        fixtures.catalog(),
        agents={
            "agent-1": _agent("agent-1", "researcher"),
            "agent-2": _agent("agent-2", "researcher"),
            "scout-1": _agent("scout-1", "scout"),
        },
        roles={
            "researcher": _role("researcher"),
            "scout": _role("scout"),
        },
        team_templates={
            "team": TeamTemplate(
                id="team",
                display_name="Team",
                roles={
                    "researcher": RolePool(min_instances=2, max_instances=2),
                    "scout": RolePool(min_instances=1, max_instances=1),
                },
            )
        },
    )
    project = replace(fixtures.context().project, team_template_id="team")
    protocol = _protocol_with_roles([
        RoleRequirement("researcher", 2, 2),
        RoleRequirement("scout", 1, 1),
    ])
    result = compile_protocol(protocol, catalog, project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings), (
        result.findings
    )
    assignments = result.plan.phase_assignments
    assert len(assignments) == 1
    role_assignments = assignments[0].role_assignments
    assert role_assignments["researcher"] == ("agent-1", "agent-2")
    assert role_assignments["scout"] == ("scout-1",)


def test_phase_assignments_respect_min_instances() -> None:
    result = compile_protocol(fixtures.protocol(), fixtures.catalog(), fixtures.context().project)
    assert result.plan is not None
    assignment = result.plan.phase_assignments[0]
    assert assignment.phase_id == "collect"
    # min=1 → 只分配 1 个 agent，尽管 pool 有 1 个候选
    assert assignment.role_assignments["researcher"] == ("agent-1",)


def test_unregistered_role_is_compile_finding() -> None:
    protocol = _protocol_with_roles([RoleRequirement("ghost", 1, 1)])
    result = compile_protocol(protocol, fixtures.catalog(), fixtures.context().project)
    assert result.plan is not None
    codes = {finding.code for finding in result.findings}
    assert "ROLE_CAPACITY" in codes
    assert any("not registered" in finding.message for finding in result.findings)
    assert result.plan.role_pools == {}


def test_role_activation_projection_reaches_plan() -> None:
    result = compile_protocol(fixtures.protocol(), fixtures.catalog(), fixtures.context().project)
    assert result.plan is not None
    activations = {item.role_id: item for item in result.plan.role_activations}
    assert activations["researcher"].activated is True
    assert activations["researcher"].policy == "REQUIRED_BY_PROTOCOL"


def test_round_robin_selection_rotates_candidates() -> None:
    catalog = replace(
        fixtures.catalog(),
        agents={
            "agent-a": _agent("agent-a", "researcher"),
            "agent-b": _agent("agent-b", "researcher"),
            "agent-c": _agent("agent-c", "researcher"),
        },
        team_templates={
            "team": TeamTemplate(
                id="team",
                display_name="Team",
                roles={
                    "researcher": RolePool(
                        min_instances=2,
                        max_instances=2,
                        selection_strategy=SelectionStrategy.ROUND_ROBIN,
                    )
                },
            )
        },
    )
    project = replace(fixtures.context().project, team_template_id="team")
    protocol = _protocol_with_roles([RoleRequirement("researcher", 2, 2)])
    result = compile_protocol(protocol, catalog, project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings), (
        result.findings
    )
    # 单 role 排序 offset=0 → 字典序前 2
    assert result.plan.agent_candidates["researcher"] == ["agent-a", "agent-b"]


def test_capability_best_fit_ranks_candidates() -> None:
    catalog = replace(
        fixtures.catalog(),
        agents={
            "agent-broad": _agent(
                "agent-broad", "researcher", capability_refs=["literature.search", "evidence.read"]
            ),
            "agent-narrow": _agent("agent-narrow", "researcher"),
        },
        team_templates={
            "team": TeamTemplate(
                id="team",
                display_name="Team",
                roles={
                    "researcher": RolePool(
                        min_instances=1,
                        max_instances=2,
                        selection_strategy=SelectionStrategy.CAPABILITY_BEST_FIT,
                    )
                },
            )
        },
    )
    project = replace(fixtures.context().project, team_template_id="team")
    protocol = _protocol_with_roles([RoleRequirement("researcher", 2, 2)])
    result = compile_protocol(protocol, catalog, project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings), (
        result.findings
    )
    candidates = result.plan.agent_candidates["researcher"]
    assert candidates[0] == "agent-broad"
    assert set(candidates) == {"agent-broad", "agent-narrow"}


def test_folded_role_gets_no_phase_assignment() -> None:
    catalog = replace(
        fixtures.catalog(),
        agents={
            "agent-1": _agent("agent-1", "researcher"),
            "scout-1": _agent("scout-1", "scout"),
        },
        roles={
            "researcher": _role("researcher"),
            # scout 未要求，且声明等价 Skill → 折叠
            "scout": _role("scout", skills=["literature_scouting"]),
        },
        team_templates={
            "team": TeamTemplate(
                id="team",
                display_name="Team",
                roles={
                    "researcher": RolePool(min_instances=1, max_instances=1),
                    "scout": RolePool(min_instances=1, max_instances=1),
                },
            )
        },
    )
    project = replace(fixtures.context().project, team_template_id="team")
    protocol = _protocol_with_roles([RoleRequirement("researcher", 1, 1)])
    result = compile_protocol(protocol, catalog, project)
    assert result.plan is not None
    activations = {item.role_id: item for item in result.plan.role_activations}
    assert activations["scout"].activated is False
    assert activations["scout"].folded_skill == "literature_scouting"
    assert result.plan.phase_assignments[0].role_assignments == {"researcher": ("agent-1",)}
