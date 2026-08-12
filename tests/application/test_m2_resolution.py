"""M2 role、inheritance、binding 与 M3 eligibility 测试。"""

from __future__ import annotations

from dataclasses import replace

from packages.application.protocol_compile import compile_protocol
from packages.domain.core import Version
from packages.domain.enums import ModelBindingMode, ModelCapability
from packages.domain.models import ModelProfile
from packages.domain.protocols import (
    PhaseStrategy,
    ProtocolDefinition,
    ProtocolPhase,
    RoleRequirement,
)
from packages.domain.roles import AgentBinding, AgentSpec, RolePool, TeamTemplate
from tests.application import protocol_fixtures as fixtures


def test_team_template_inheritance_resolves_parent_role_pool() -> None:
    base = TeamTemplate(
        id="base",
        display_name="Base",
        roles={"researcher": RolePool(min_instances=1, max_instances=2)},
    )
    child = TeamTemplate(
        id="child",
        display_name="Child",
        roles={"reviewer": RolePool(min_instances=0, max_instances=1)},
        extends="base",
    )
    catalog = replace(fixtures.catalog(), team_templates={"base": base, "child": child})
    project = replace(fixtures.context().project, team_template_id="child")
    result = compile_protocol(fixtures.protocol(), catalog, project)
    assert result.plan is not None
    assert result.findings == ()
    assert result.plan.role_pools == {"researcher": 1}


def test_role_capacity_and_agent_shortage_are_findings() -> None:
    protocol = ProtocolDefinition(
        id="capacity_protocol_v0_4_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(
                id="collect",
                strategy=PhaseStrategy.SINGLE_AGENT,
                required_roles=[RoleRequirement("researcher", 2, 2)],
            )
        ],
    )
    result = compile_protocol(protocol, fixtures.catalog(), fixtures.context().project)
    assert result.plan is not None
    codes = {finding.code for finding in result.findings}
    assert {"ROLE_CAPACITY", "AGENT_MISSING"} <= codes
    assert result.plan.role_pools == {"researcher": 1}


def test_model_profile_hard_capability_is_consumed_by_m3_eligibility() -> None:
    catalog = fixtures.catalog()
    agent = AgentSpec(
        id="agent-1",
        role="researcher",
        model_binding=AgentBinding(mode=ModelBindingMode.MODEL_PROFILE, value="strong"),
    )
    catalog = replace(
        catalog,
        agents={"agent-1": agent},
        model_profiles={
            "strong": ModelProfile(
                id="strong",
                primary="model-1",
                hard_capabilities=[ModelCapability.REASONING],
            )
        },
    )
    result = compile_protocol(fixtures.protocol(), catalog, fixtures.context().project)
    assert result.plan is not None
    eligibility = result.plan.model_eligibility[0]
    assert not eligibility.eligible
    assert eligibility.missing_capabilities == (ModelCapability.REASONING,)


def test_missing_agent_model_profile_is_compile_finding() -> None:
    agent = AgentSpec(
        id="agent-1",
        role="researcher",
        model_binding=AgentBinding(mode=ModelBindingMode.MODEL_PROFILE, value="missing"),
    )
    catalog = replace(fixtures.catalog(), agents={"agent-1": agent})
    result = compile_protocol(fixtures.protocol(), catalog, fixtures.context().project)
    assert result.plan is not None
    assert "MODEL_PROFILE_MISSING" in {finding.code for finding in result.findings}
