"""M4 Preflight 集成：role 激活与 agent 权限检查测试（异构评审见 test_m4_heterogeneity.py）。"""

from __future__ import annotations

from dataclasses import replace

from packages.application.ports import CatalogSnapshot
from packages.application.preflight.role_checks import (
    check_agent_permissions,
    check_role_activations,
)
from packages.application.protocol_compile import compile_protocol
from packages.domain.core import Version
from packages.domain.enums import (
    ActivationPolicy,
    ModelBindingMode,
    RoleCategory,
    WorkspacePolicy,
)
from packages.domain.protocols import (
    CompiledRunPlan,
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
)
from packages.domain.team_plan import PhaseAssignment, RoleActivationRecord
from packages.domain.tools import SkillSpec
from tests.application import protocol_fixtures as fixtures

_REVIEWER_ROLE_ID = "scientific_reviewer"


def _role(
    role_id: str,
    *,
    policy: ActivationPolicy = ActivationPolicy.REQUIRED_BY_PROTOCOL,
    capabilities: list[str] | None = None,
    forbidden: list[str] | None = None,
    skills: list[str] | None = None,
) -> RoleDefinition:
    return RoleDefinition(
        id=role_id,
        role_type=role_id.title(),
        category=RoleCategory.EVALUATION,
        activation_default=policy,
        requested_capabilities=list(capabilities or []),
        hard_model_capabilities=ModelCapabilityRequirement(all_of=["CHAT"]),
        forbidden_capabilities=list(forbidden or []),
        default_skills=list(skills or []),
        workspace_policy=WorkspacePolicy.READ_ONLY,
    )


def _agent(agent_id: str, role_id: str, *, skills: list[str] | None = None) -> AgentSpec:
    return AgentSpec(
        id=agent_id,
        role=role_id,
        model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        skill_refs=list(skills or []),
        capability_refs=["literature.search"],
    )


def _catalog_with(
    *,
    roles: dict[str, RoleDefinition] | None = None,
    agents: dict[str, AgentSpec] | None = None,
    skills: dict[str, SkillSpec] | None = None,
) -> CatalogSnapshot:
    return replace(
        fixtures.catalog(),
        roles=roles or {"researcher": _role("researcher", capabilities=["literature.search"])},
        agents=agents or {"agent-1": _agent("agent-1", "researcher")},
        skills=skills or {},
    )


def _protocol(requirements: list[RoleRequirement]) -> ProtocolDefinition:
    return ProtocolDefinition(
        id="m4_preflight_v0_4_0",
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


def _compile(catalog: CatalogSnapshot, protocol: ProtocolDefinition) -> CompiledRunPlan:
    result = compile_protocol(protocol, catalog, fixtures.context().project)
    assert result.plan is not None
    return result.plan


def test_permission_check_rejects_outside_capability() -> None:
    catalog = _catalog_with(
        roles={"researcher": _role("researcher", capabilities=["literature.search"])},
        agents={
            "agent-1": AgentSpec(
                id="agent-1",
                role="researcher",
                model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
                capability_refs=["code.execute"],
            )
        },
    )
    plan = _compile(catalog, _protocol([RoleRequirement("researcher", 1, 1)]))
    findings = check_agent_permissions(plan, fixtures.context(catalog))
    assert any(item.code == "AGENT_PERMISSION_DENIED" for item in findings)
    assert any("outside role" in item.message for item in findings)


def test_permission_check_rejects_forbidden_capability() -> None:
    catalog = _catalog_with(
        roles={
            _REVIEWER_ROLE_ID: _role(
                _REVIEWER_ROLE_ID,
                capabilities=["literature.search", "review.write"],
                forbidden=["evidence.write"],
            )
        },
        agents={
            "reviewer": AgentSpec(
                id="reviewer",
                role=_REVIEWER_ROLE_ID,
                model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
                capability_refs=["evidence.write"],
            )
        },
    )
    plan = _compile(catalog, _protocol([RoleRequirement(_REVIEWER_ROLE_ID, 1, 1)]))
    findings = check_agent_permissions(plan, fixtures.context(catalog))
    assert any("forbidden" in item.message for item in findings)


def test_permission_check_resolves_skill_capabilities() -> None:
    catalog = _catalog_with(
        roles={
            "researcher": _role("researcher", capabilities=["literature.search", "literature.read"])
        },
        agents={"agent-1": _agent("agent-1", "researcher", skills=["scout_skill"])},
        skills={
            "scout_skill": SkillSpec(
                id="scout_skill",
                version=Version("1.0.0"),
                capabilities=["literature.search", "literature.read"],
            )
        },
    )
    plan = _compile(catalog, _protocol([RoleRequirement("researcher", 1, 1)]))
    assert check_agent_permissions(plan, fixtures.context(catalog)) == []


def test_permission_check_reports_missing_skill() -> None:
    catalog = _catalog_with(
        roles={"researcher": _role("researcher", capabilities=["literature.search"])},
        agents={"agent-1": _agent("agent-1", "researcher", skills=["ghost_skill"])},
        skills={},
    )
    plan = _compile(catalog, _protocol([RoleRequirement("researcher", 1, 1)]))
    findings = check_agent_permissions(plan, fixtures.context(catalog))
    assert any("missing skill" in item.message for item in findings)


def test_role_activation_check_rejects_inactive_assignment() -> None:
    # 防御性检查：手工构造"未激活但被分配"的 plan（编译期不会产生这种状态）
    plan = fixtures.compiled()[0]
    plan = replace(
        plan,
        role_activations=[
            RoleActivationRecord(
                role_id="researcher", activated=False, policy="DISABLED", reason="disabled"
            )
        ],
        phase_assignments=[PhaseAssignment("collect", {"researcher": ("agent-1",)})],
    )
    findings = check_role_activations(plan, fixtures.context())
    assert any(item.code == "ROLE_DISABLED" for item in findings)
