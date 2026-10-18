"""GOAL-20261018-084 判据的**共享夹具**（EC-01…EC-03 两个判据文件共用）。

只放构造器与常量 —— 断言一律留在判据文件里，避免「夹具里藏着结论」。
"""

from __future__ import annotations

from dataclasses import replace

from packages.application.ports import (
    CatalogSnapshot,
    PreflightContext,
    ProjectSettings,
)
from packages.application.protocol_compile import compile_protocol
from packages.domain.core import Version
from packages.domain.enums import (
    ActivationPolicy,
    ModelBindingMode,
    ReviewPanelRole,
    RoleCategory,
    WorkspacePolicy,
)
from packages.domain.models import ModelDefinition, ModelProfile
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

#: 出厂目录的真实读数（**判据里写死**，不 import 产品常量当预言机）。
PRODUCER_MODEL_NAME = "deepseek-v4-flash-vision"
REVIEWER_MODEL_NAME = "glm-5.3"
SECOND_REVIEWER_MODEL_NAME = "kimi-k2.6"
FACTORY_ENDPOINT = "main"

WRITER_ROLE = "g084_writer_role"
REVIEWER_ROLE = "g084_reviewer_role"


def model(model_id: str, *, model_name: str, endpoint: str = "ep") -> ModelDefinition:
    return ModelDefinition(id=model_id, endpoint_id=endpoint, model_name=model_name)


def binding_explicit(model_id: str) -> AgentBinding:
    return AgentBinding(mode=ModelBindingMode.EXPLICIT_MODEL, value=model_id)


def binding_profile(profile_id: str) -> AgentBinding:
    return AgentBinding(mode=ModelBindingMode.MODEL_PROFILE, value=profile_id)


def agent(agent_id: str, role: str, binding: AgentBinding) -> AgentSpec:
    return AgentSpec(id=agent_id, role=role, model_binding=binding)


def catalog(
    *,
    models: dict[str, ModelDefinition],
    profiles: dict[str, ModelProfile],
    agents: dict[str, AgentSpec],
    roles: dict[str, RoleDefinition],
) -> CatalogSnapshot:
    return CatalogSnapshot(models=models, model_profiles=profiles, agents=agents, roles=roles)


def panel_role(role_id: str, panel: ReviewPanelRole) -> RoleDefinition:
    return RoleDefinition(
        id=role_id,
        role_type=role_id.title(),
        category=RoleCategory.EVALUATION,
        activation_default=ActivationPolicy.REQUIRED_BY_PROTOCOL,
        hard_model_capabilities=ModelCapabilityRequirement(all_of=["CHAT"]),
        workspace_policy=WorkspacePolicy.READ_ONLY,
        review_panel_role=panel,
    )


def protocol() -> ProtocolDefinition:
    return ProtocolDefinition(
        id="g084_panel_v0_4_0",
        version=Version("0.4.0"),
        phases=[
            ProtocolPhase(
                id="panel",
                strategy=PhaseStrategy.PARALLEL_AGENTS,
                required_roles=[
                    RoleRequirement(WRITER_ROLE, 1, 1),
                    RoleRequirement(REVIEWER_ROLE, 1, 1),
                ],
            )
        ],
    )


def project() -> ProjectSettings:
    return ProjectSettings(
        project_id="g084",
        team_template_id="none",
        default_model_profile_id=None,
        budget_policy_id="none",
        workspace_backend="openhands_docker",
    )


def compile_plan(snapshot: CatalogSnapshot) -> CompiledRunPlan:
    result = compile_protocol(protocol(), snapshot, project())
    assert result.plan is not None, result.findings
    return result.plan


def context(snapshot: CatalogSnapshot) -> PreflightContext:
    return PreflightContext(catalog=snapshot, project=project())


def panel_catalog(
    *, producer: str, reviewer: str, profiles: dict[str, ModelProfile]
) -> CatalogSnapshot:
    """(writer, reviewer) 的极小目录：两只 agent，各自绑给定 model id。"""
    models = {model_id: model(model_id, model_name=model_id) for model_id in {producer, reviewer}}
    return catalog(
        models=models,
        profiles=profiles,
        agents={
            "w": agent("w", WRITER_ROLE, binding_explicit(producer)),
            "r": agent("r", REVIEWER_ROLE, binding_explicit(reviewer)),
        },
        roles={
            WRITER_ROLE: panel_role(WRITER_ROLE, ReviewPanelRole.WRITER),
            REVIEWER_ROLE: panel_role(REVIEWER_ROLE, ReviewPanelRole.REVIEWER),
        },
    )


def with_model_names(snapshot: CatalogSnapshot, **names: str) -> CatalogSnapshot:
    """把指定 model id 的 `model_name` 换掉（保持 id / endpoint 不变）。"""
    return replace(
        snapshot,
        models={
            model_id: replace(item, model_name=names[model_id]) if model_id in names else item
            for model_id, item in snapshot.models.items()
        },
    )
