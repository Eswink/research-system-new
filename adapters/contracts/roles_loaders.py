"""Role / Agent / Team / Skill 契约加载器。"""

from __future__ import annotations

from typing import Any

from adapters.contracts.base import load_flat_collection
from packages.domain.core import Digest, Version
from packages.domain.enums import (
    ActivationPolicy,
    BackendKind,
    ModelBindingMode,
    ReviewPanelRole,
    RoleCategory,
    SelectionStrategy,
    SkillStatus,
    WorkspacePolicy,
)
from packages.domain.roles import (
    AgentBinding,
    AgentContextConfig,
    AgentSpec,
    ModelCapabilityRequirement,
    RoleDefinition,
    RolePool,
    TeamTemplate,
)
from packages.domain.tools import SkillSpec


def role_from_mapping(raw: Any) -> RoleDefinition:
    """从契约映射（examples/config/roles.yaml 子项同形）构造 RoleDefinition。

    schema 校验由调用方负责（`load_roles` 经 `load_flat_collection`；控制面
    自定义创建经 `validate_instance` + 本构造，失败抛 ValueError 族）。
    """
    hard = raw["hard_model_capabilities"]
    return RoleDefinition(
        id=raw["id"],
        role_type=raw["role_type"],
        category=RoleCategory(raw["category"]),
        activation_default=ActivationPolicy(raw["activation_default"]),
        requested_capabilities=list(raw["requested_capabilities"]),
        hard_model_capabilities=ModelCapabilityRequirement(
            all_of=list(hard.get("all_of", [])),
            any_of=list(hard.get("any_of", [])),
        ),
        default_model_profile=raw.get("default_model_profile"),
        workspace_policy=WorkspacePolicy(raw["workspace_policy"]),
        default_skills=list(raw.get("default_skills", [])),
        forbidden_capabilities=list(raw.get("forbidden_capabilities", [])),
        review_panel_role=ReviewPanelRole(raw.get("review_panel_role", "NONE")),
    )


def load_roles(relative_path: str) -> dict[str, RoleDefinition]:
    collection: dict[str, RoleDefinition] = {}
    for key, raw in load_flat_collection(
        relative_path, "roles", "role-definition.schema.json"
    ).items():
        collection[key] = role_from_mapping(raw)
    return collection


def load_agents(relative_path: str) -> dict[str, AgentSpec]:
    collection: dict[str, AgentSpec] = {}
    for key, raw in load_flat_collection(relative_path, "agents", "agent-spec.schema.json").items():
        binding = raw["model_binding"]
        if binding["type"] == "INHERIT":
            agent_binding = AgentBinding(mode=ModelBindingMode.INHERIT)
        elif binding["type"] == "EXPLICIT_MODEL":
            agent_binding = AgentBinding(
                mode=ModelBindingMode.EXPLICIT_MODEL, value=binding["value"]
            )
        else:
            agent_binding = AgentBinding(
                mode=ModelBindingMode.MODEL_PROFILE, value=binding["value"]
            )
        context = raw.get("context")
        runtime = raw.get("runtime_kind")
        collection[key] = AgentSpec(
            id=raw["id"],
            role=raw["role"],
            model_binding=agent_binding,
            workspace_policy=(
                WorkspacePolicy(raw["workspace_policy"]) if raw.get("workspace_policy") else None
            ),
            skill_refs=list(raw.get("skill_refs", [])),
            capability_refs=list(raw.get("capability_refs", [])),
            context=(
                AgentContextConfig(
                    max_context_tokens=context.get("max_context_tokens"),
                    max_iterations=context.get("max_iterations"),
                )
                if context
                else None
            ),
            runtime_kind=BackendKind(runtime) if runtime else None,
            budget_policy_ref=raw.get("budget_policy_ref"),
        )
    return collection


def team_template_from_mapping(raw: Any) -> TeamTemplate:
    """从契约映射（examples/config/team_templates.yaml 子项同形）构造 TeamTemplate。"""
    pools: dict[str, RolePool] = {}
    for role_name, pool in raw["roles"].items():
        pools[role_name] = RolePool(
            min_instances=pool["min_instances"],
            max_instances=pool["max_instances"],
            concurrency=pool.get("concurrency", 1),
            selection_strategy=SelectionStrategy(pool.get("selection_strategy", "FIXED")),
            model_profile=pool.get("model_profile"),
            activation_policy=(
                ActivationPolicy(pool["activation_policy"])
                if pool.get("activation_policy")
                else None
            ),
        )
    return TeamTemplate(
        id=raw["id"],
        display_name=raw["display_name"],
        roles=pools,
        extends=raw.get("extends"),
    )


def load_team_templates(relative_path: str) -> dict[str, TeamTemplate]:
    collection: dict[str, TeamTemplate] = {}
    for key, raw in load_flat_collection(
        relative_path, "team_templates", "team-template.schema.json"
    ).items():
        collection[key] = team_template_from_mapping(raw)
    return collection


def load_skills(relative_path: str) -> dict[str, SkillSpec]:
    collection: dict[str, SkillSpec] = {}
    for key, raw in load_flat_collection(relative_path, "skills", "skill.schema.json").items():
        digest_raw = raw.get("digest")
        collection[key] = SkillSpec(
            id=raw["id"],
            version=Version(raw["version"]),
            capabilities=list(raw["capabilities"]),
            description=raw.get("description", ""),
            status=SkillStatus(raw.get("status", SkillStatus.ACTIVE.value)),
            digest=Digest.parse(digest_raw) if digest_raw else None,
        )
    return collection
