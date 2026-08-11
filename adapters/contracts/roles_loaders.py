"""Role / Agent / Team 契约加载器。"""

from __future__ import annotations

from adapters.contracts.base import load_flat_collection
from packages.domain.enums import (
    ActivationPolicy,
    ModelBindingMode,
    RoleCategory,
    SelectionStrategy,
    WorkspacePolicy,
)
from packages.domain.roles import (
    AgentBinding,
    AgentSpec,
    ModelCapabilityRequirement,
    RoleDefinition,
    RolePool,
    TeamTemplate,
)


def load_roles(relative_path: str) -> dict[str, RoleDefinition]:
    collection: dict[str, RoleDefinition] = {}
    for key, raw in load_flat_collection(
        relative_path, "roles", "role-definition.schema.json"
    ).items():
        hard = raw["hard_model_capabilities"]
        collection[key] = RoleDefinition(
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
        )
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
        collection[key] = AgentSpec(
            id=raw["id"],
            role=raw["role"],
            model_binding=agent_binding,
            workspace_policy=WorkspacePolicy(raw.get("workspace_policy", "read_only")),
        )
    return collection


def load_team_templates(relative_path: str) -> dict[str, TeamTemplate]:
    collection: dict[str, TeamTemplate] = {}
    for key, raw in load_flat_collection(
        relative_path, "team_templates", "team-template.schema.json"
    ).items():
        pools: dict[str, RolePool] = {}
        for role_name, pool in raw["roles"].items():
            pools[role_name] = RolePool(
                min_instances=pool["min_instances"],
                max_instances=pool["max_instances"],
                concurrency=pool.get("concurrency", 1),
                selection_strategy=SelectionStrategy(pool.get("selection_strategy", "FIXED")),
                model_profile=pool.get("model_profile"),
                activation_policy=ActivationPolicy(pool.get("activation_policy", "ON_DEMAND")),
            )
        collection[key] = TeamTemplate(
            id=raw["id"],
            display_name=raw["display_name"],
            roles=pools,
            extends=raw.get("extends"),
        )
    return collection
