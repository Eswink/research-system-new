"""M4：INHERIT binding 解析与 Agent workspace policy 继承/边界测试。"""

from __future__ import annotations

from dataclasses import replace

from packages.application.preflight.preflight import compile_and_preflight
from packages.application.protocol_compile import compile_protocol
from packages.domain.core import Version
from packages.domain.enums import (
    ActivationPolicy,
    ModelBindingMode,
    RoleCategory,
    WorkspacePolicy,
)
from packages.domain.models import ModelProfile
from packages.domain.protocols import (
    FindingSeverity,
    PhaseStrategy,
    ProtocolDefinition,
    ProtocolPhase,
    RoleRequirement,
)
from packages.domain.roles import AgentBinding, AgentSpec, RoleDefinition
from tests.application import protocol_fixtures as fixtures


def _protocol_with_roles(requirements: list[RoleRequirement]) -> ProtocolDefinition:
    return ProtocolDefinition(
        id="m4_workspace_v0_4_0",
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


def _role(
    role_id: str,
    *,
    workspace_policy: WorkspacePolicy = WorkspacePolicy.READ_ONLY,
    default_model_profile: str | None = None,
) -> RoleDefinition:
    return RoleDefinition(
        id=role_id,
        role_type=role_id.title(),
        category=RoleCategory.DISCOVERY,
        activation_default=ActivationPolicy.REQUIRED_BY_PROTOCOL,
        requested_capabilities=["literature.search"],
        workspace_policy=workspace_policy,
        default_model_profile=default_model_profile,
    )


def _agent(
    agent_id: str,
    role_id: str,
    *,
    workspace_policy: WorkspacePolicy | None = None,
) -> AgentSpec:
    return AgentSpec(
        id=agent_id,
        role=role_id,
        model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value="model-1"),
        workspace_policy=workspace_policy,
    )


def test_inherit_binding_resolves_role_default_profile() -> None:
    catalog = replace(
        fixtures.catalog(),
        agents={
            "agent-1": AgentSpec(
                id="agent-1",
                role="researcher",
                model_binding=AgentBinding(mode=ModelBindingMode.INHERIT),
            )
        },
        roles={"researcher": _role("researcher", default_model_profile="strong")},
        model_profiles={"strong": ModelProfile(id="strong", primary="model-1")},
    )
    result = compile_protocol(fixtures.protocol(), catalog, fixtures.context().project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings), (
        result.findings
    )
    assert result.plan.resolved_models["agent-1"] == "model-1"


def test_inherit_binding_falls_back_to_project_default_profile() -> None:
    catalog = replace(
        fixtures.catalog(),
        agents={
            "agent-1": AgentSpec(
                id="agent-1",
                role="researcher",
                model_binding=AgentBinding(mode=ModelBindingMode.INHERIT),
            )
        },
        roles={"researcher": _role("researcher")},
        model_profiles={"strong": ModelProfile(id="strong", primary="model-1")},
    )
    project = replace(fixtures.context().project, default_model_profile_id="strong")
    result = compile_protocol(fixtures.protocol(), catalog, project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings), (
        result.findings
    )
    assert result.plan.resolved_models["agent-1"] == "model-1"


def test_workspace_policy_inherited_from_role_when_unset() -> None:
    catalog = replace(
        fixtures.catalog(),
        roles={"researcher": _role("researcher", workspace_policy=WorkspacePolicy.NOTES_ONLY)},
        agents={"agent-1": _agent("agent-1", "researcher")},
    )
    result = compile_protocol(fixtures.protocol(), catalog, fixtures.context().project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings), (
        result.findings
    )
    assert result.plan.agent_workspace_policies["agent-1"] == "notes_only"


def test_workspace_policy_explicit_within_role_boundary_is_allowed() -> None:
    # role notes_only，agent 显式收紧为 read_only → 合法
    catalog = replace(
        fixtures.catalog(),
        roles={"researcher": _role("researcher", workspace_policy=WorkspacePolicy.NOTES_ONLY)},
        agents={
            "agent-1": _agent("agent-1", "researcher", workspace_policy=WorkspacePolicy.READ_ONLY)
        },
    )
    result = compile_protocol(fixtures.protocol(), catalog, fixtures.context().project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings), (
        result.findings
    )
    assert result.plan.agent_workspace_policies["agent-1"] == "read_only"


def test_workspace_policy_exceeding_role_boundary_is_finding() -> None:
    # role read_only，agent 显式放宽为 isolated_writable → WORKSPACE_POLICY_VIOLATION
    catalog = replace(
        fixtures.catalog(),
        roles={"researcher": _role("researcher")},
        agents={
            "agent-1": _agent(
                "agent-1", "researcher", workspace_policy=WorkspacePolicy.ISOLATED_WRITABLE
            )
        },
    )
    result = compile_protocol(fixtures.protocol(), catalog, fixtures.context().project)
    assert result.plan is not None
    assert "WORKSPACE_POLICY_VIOLATION" in {finding.code for finding in result.findings}
    # 违规 agent 仍保留在 plan 中，由 Preflight 聚合为 FAIL
    assert result.plan.agent_workspace_policies["agent-1"] == "isolated_writable"


def test_workspace_policy_orthogonal_write_surfaces_are_not_mixed() -> None:
    # role deliverable_only，agent 显式 notes_only → 写面不同，判定违规
    catalog = replace(
        fixtures.catalog(),
        roles={
            "researcher": _role("researcher", workspace_policy=WorkspacePolicy.DELIVERABLE_ONLY)
        },
        agents={
            "agent-1": _agent("agent-1", "researcher", workspace_policy=WorkspacePolicy.NOTES_ONLY)
        },
    )
    result = compile_protocol(fixtures.protocol(), catalog, fixtures.context().project)
    assert result.plan is not None
    assert "WORKSPACE_POLICY_VIOLATION" in {finding.code for finding in result.findings}


def test_workspace_policy_violation_blocks_preflight() -> None:
    catalog = replace(
        fixtures.catalog(),
        roles={"researcher": _role("researcher")},
        agents={
            "agent-1": _agent(
                "agent-1", "researcher", workspace_policy=WorkspacePolicy.ISOLATED_WRITABLE
            )
        },
    )
    plan, report = compile_and_preflight(
        fixtures.protocol(),
        catalog,
        fixtures.context().project,
        fixtures.context(catalog),
    )
    assert plan is not None
    assert report.status.value == "FAIL"
    assert "WORKSPACE_POLICY_VIOLATION" in {finding.code for finding in report.findings}


def test_cost_aware_strategy_produces_degradation_finding() -> None:
    from packages.domain.enums import SelectionStrategy
    from packages.domain.protocols import FindingSeverity
    from packages.domain.roles import RolePool, TeamTemplate

    catalog = replace(
        fixtures.catalog(),
        team_templates={
            "team": TeamTemplate(
                id="team",
                display_name="Team",
                roles={
                    "researcher": RolePool(
                        min_instances=1,
                        max_instances=1,
                        selection_strategy=SelectionStrategy.COST_AWARE,
                    )
                },
            )
        },
    )
    result = compile_protocol(fixtures.protocol(), catalog, fixtures.context().project)
    assert result.plan is not None
    assert not any(finding.severity is FindingSeverity.ERROR for finding in result.findings)
    degraded = [
        finding for finding in result.findings if finding.code == "SELECTION_STRATEGY_DEGRADED"
    ]
    assert len(degraded) == 1
    assert degraded[0].severity is FindingSeverity.INFO
    assert degraded[0].subject_ref == "role:researcher"
    # INFO 不阻断 preflight（无其他问题时 PASS）
    report = compile_and_preflight(
        fixtures.protocol(),
        catalog,
        fixtures.context().project,
        fixtures.context(catalog),
    )[1]
    assert report.status.value == "PASS"


def test_eval_score_aware_strategy_produces_degradation_finding() -> None:
    from packages.domain.enums import SelectionStrategy
    from packages.domain.roles import RolePool, TeamTemplate

    catalog = replace(
        fixtures.catalog(),
        team_templates={
            "team": TeamTemplate(
                id="team",
                display_name="Team",
                roles={
                    "researcher": RolePool(
                        min_instances=1,
                        max_instances=1,
                        selection_strategy=SelectionStrategy.EVAL_SCORE_AWARE,
                    )
                },
            )
        },
    )
    result = compile_protocol(fixtures.protocol(), catalog, fixtures.context().project)
    assert result.plan is not None
    assert "SELECTION_STRATEGY_DEGRADED" in {finding.code for finding in result.findings}
