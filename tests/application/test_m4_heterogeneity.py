"""M4：异构评审约束（HETEROGENEITY_VIOLATION）专项测试。

约束按 RoleDefinition.review_panel_role 属性聚合（支持自定义角色，不依赖 role id）。
"""

from __future__ import annotations

from dataclasses import replace

from packages.application.ports import CatalogSnapshot
from packages.application.preflight.role_checks import check_heterogeneity
from packages.application.protocol_compile import compile_protocol
from packages.domain.core import Version
from packages.domain.enums import (
    ActivationPolicy,
    ModelBindingMode,
    ReviewPanelRole,
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
from tests.application import protocol_fixtures as fixtures

_WRITER_ROLE_ID = "research_writer"
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


def _panel_role(role: RoleDefinition, panel: ReviewPanelRole) -> RoleDefinition:
    return replace(role, review_panel_role=panel)


def _agent(agent_id: str, role_id: str, model_id: str = "model-1") -> AgentSpec:
    return AgentSpec(
        id=agent_id,
        role=role_id,
        model_binding=AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value=model_id),
    )


def _catalog(roles: dict[str, RoleDefinition], agents: dict[str, AgentSpec]) -> CatalogSnapshot:
    return replace(
        fixtures.catalog(),
        roles=roles,
        agents=agents,
    )


def _protocol(requirements: list[RoleRequirement]) -> ProtocolDefinition:
    return ProtocolDefinition(
        id="m4_heterogeneity_v0_4_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(
                id="review",
                strategy=PhaseStrategy.PARALLEL_AGENTS,
                required_roles=requirements,
            )
        ],
    )


def _compile(catalog: CatalogSnapshot, protocol: ProtocolDefinition) -> CompiledRunPlan:
    result = compile_protocol(protocol, catalog, fixtures.context().project)
    assert result.plan is not None
    return result.plan


def test_heterogeneity_rejects_shared_writer_reviewer_model() -> None:
    catalog = _catalog(
        roles={
            _WRITER_ROLE_ID: _panel_role(
                _role(_WRITER_ROLE_ID, capabilities=["deliverable.write"]),
                ReviewPanelRole.WRITER,
            ),
            _REVIEWER_ROLE_ID: _panel_role(
                _role(_REVIEWER_ROLE_ID, capabilities=["review.write"]),
                ReviewPanelRole.REVIEWER,
            ),
        },
        agents={
            "writer": _agent("writer", _WRITER_ROLE_ID),
            "reviewer": _agent("reviewer", _REVIEWER_ROLE_ID),
        },
    )
    plan = _compile(
        catalog,
        _protocol([
            RoleRequirement(_WRITER_ROLE_ID, 1, 1),
            RoleRequirement(_REVIEWER_ROLE_ID, 1, 1),
        ]),
    )
    findings = check_heterogeneity(plan, fixtures.context(catalog))
    assert any(item.code == "HETEROGENEITY_VIOLATION" for item in findings)


def test_heterogeneity_allows_distinct_models() -> None:
    """**不同底层模型**（`model_name` 不同）⇒ 判绿。

    GOAL-20261018-084 收紧：本用例原先用「两个不同 model id、但 `model_name` 相同」的副本
    当作「不同模型」—— 按新口径那是**同一个底层模型**。这里把 `model-2` 改成
    **`model_name` 也不同**；谓词（`== []`）本身未变。
    """
    catalog = _catalog(
        roles={
            _WRITER_ROLE_ID: _panel_role(
                _role(_WRITER_ROLE_ID, capabilities=["deliverable.write"]),
                ReviewPanelRole.WRITER,
            ),
            _REVIEWER_ROLE_ID: _panel_role(
                _role(_REVIEWER_ROLE_ID, capabilities=["review.write"]),
                ReviewPanelRole.REVIEWER,
            ),
        },
        agents={
            "writer": _agent("writer", _WRITER_ROLE_ID),
            "reviewer": _agent("reviewer", _REVIEWER_ROLE_ID, model_id="model-2"),
        },
    )
    catalog = replace(
        catalog,
        models={
            **catalog.models,
            "model-2": replace(
                catalog.models["model-1"], id="model-2", model_name="other-underlying-model"
            ),
        },
    )
    plan = _compile(
        catalog,
        _protocol([
            RoleRequirement(_WRITER_ROLE_ID, 1, 1),
            RoleRequirement(_REVIEWER_ROLE_ID, 1, 1),
        ]),
    )
    assert check_heterogeneity(plan, fixtures.context(catalog)) == []


def test_a_model_with_the_same_underlying_name_is_not_distinct() -> None:
    """**反证**：两个 model id 不同、但 `(endpoint, model_name)` 相同 ⇒ **判违规**。

    这正是 GOAL-20261018-084 建档实测的出厂形态（`research_alpha` vs `reviewer_gamma`）：
    id 不同**不构成**独立性证据。本用例是「按 id 比」与「按解析目标比」的机械分界。
    """
    catalog = _catalog(
        roles={
            _WRITER_ROLE_ID: _panel_role(
                _role(_WRITER_ROLE_ID, capabilities=["deliverable.write"]),
                ReviewPanelRole.WRITER,
            ),
            _REVIEWER_ROLE_ID: _panel_role(
                _role(_REVIEWER_ROLE_ID, capabilities=["review.write"]),
                ReviewPanelRole.REVIEWER,
            ),
        },
        agents={
            "writer": _agent("writer", _WRITER_ROLE_ID),
            "reviewer": _agent("reviewer", _REVIEWER_ROLE_ID, model_id="model-2"),
        },
    )
    catalog = replace(
        catalog,
        models={
            **catalog.models,
            # 与 model-1 **同一个** model_name + endpoint，只是 id 不同
            "model-2": replace(catalog.models["model-1"], id="model-2"),
        },
    )
    plan = _compile(
        catalog,
        _protocol([
            RoleRequirement(_WRITER_ROLE_ID, 1, 1),
            RoleRequirement(_REVIEWER_ROLE_ID, 1, 1),
        ]),
    )
    findings = check_heterogeneity(plan, fixtures.context(catalog))
    assert [item.code for item in findings] == ["HETEROGENEITY_VIOLATION"], findings
    assert "endpoint-1/fixture-model" in findings[0].message, findings[0].message


def test_heterogeneity_applies_to_custom_role_ids_by_attribute() -> None:
    """异构约束按 review_panel_role 属性聚合，不依赖内置 role id。"""
    catalog = _catalog(
        roles={
            "draft_author": _panel_role(
                _role("draft_author", capabilities=["deliverable.write"]),
                ReviewPanelRole.WRITER,
            ),
            "independent_critic": _panel_role(
                _role("independent_critic", capabilities=["review.write"]),
                ReviewPanelRole.REVIEWER,
            ),
        },
        agents={
            "author": _agent("author", "draft_author"),
            "critic": _agent("critic", "independent_critic"),
        },
    )
    plan = _compile(
        catalog,
        _protocol([
            RoleRequirement("draft_author", 1, 1),
            RoleRequirement("independent_critic", 1, 1),
        ]),
    )
    findings = check_heterogeneity(plan, fixtures.context(catalog))
    assert any(item.code == "HETEROGENEITY_VIOLATION" for item in findings)


def test_heterogeneity_ignores_roles_without_panel_attribute() -> None:
    """review_panel_role=NONE 的角色不参与异构计算。"""
    catalog = _catalog(
        roles={
            _WRITER_ROLE_ID: _panel_role(
                _role(_WRITER_ROLE_ID, capabilities=["deliverable.write"]),
                ReviewPanelRole.WRITER,
            ),
            "assistant": _role("assistant", capabilities=["literature.search"]),
        },
        agents={
            "writer": _agent("writer", _WRITER_ROLE_ID),
            "assistant": _agent("assistant", "assistant"),
        },
    )
    plan = _compile(
        catalog,
        _protocol([
            RoleRequirement(_WRITER_ROLE_ID, 1, 1),
            RoleRequirement("assistant", 1, 1),
        ]),
    )
    assert check_heterogeneity(plan, fixtures.context(catalog)) == []
