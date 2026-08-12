"""Budget、Policy、Workspace、ToolProvider 与 Project 配置加载器。"""

from __future__ import annotations

from decimal import ROUND_CEILING, Decimal
from typing import Any

from adapters.contracts.base import (
    load_json_schema,
    load_yaml,
    mapping_under,
    validate_instance,
)
from packages.domain.budget import BudgetPolicy
from packages.domain.core import Version
from packages.domain.enums import (
    EffectClass,
    PolicyDecision,
    ProviderType,
    TrustLevel,
    TrustProfile,
)
from packages.domain.policy import PolicyDefinition, PolicyRule
from packages.domain.tools import ToolProviderSpec
from packages.domain.workspace import Workspace


def _scaled_limit(value: object, factor: int = 1) -> int | None:
    if value is None:
        return None
    scaled = Decimal(str(value)) * factor
    return int(scaled.to_integral_value(rounding=ROUND_CEILING))


def load_budget_policies(relative_path: str) -> dict[str, BudgetPolicy]:
    policies: dict[str, BudgetPolicy] = {}
    section = mapping_under(load_yaml(relative_path), "budgets", relative_path)
    schema = load_json_schema("budget-policy.schema.json")
    for policy_id, body in section.items():
        if not isinstance(body, dict):
            raise ValueError(f"{relative_path}/{policy_id} must be a mapping")
        raw = {"id": policy_id, **body}
        validate_instance(schema, raw, f"{relative_path}/{policy_id}")
        model = body.get("model", {})
        compute = body.get("compute", {})
        tools = body.get("tools", {})
        wall_clock = body.get("wall_clock", {})
        parallelism = body.get("parallelism", {})
        limits: dict[str, int] = {}
        values = {
            "model_input_tokens": model.get("max_input_tokens"),
            "model_output_tokens": model.get("max_output_tokens"),
            "model_requests": model.get("max_requests"),
            "model_cost_minor": _scaled_limit(model.get("max_cost_usd"), 100),
            "cpu_seconds": _scaled_limit(compute.get("max_cpu_hours"), 3600),
            "gpu_seconds": _scaled_limit(compute.get("max_gpu_hours"), 3600),
            "tool_requests": tools.get("max_requests"),
            "wall_clock_seconds": _scaled_limit(wall_clock.get("max_hours"), 3600),
            "agent_sessions": parallelism.get("max_agent_sessions"),
        }
        for key, value in values.items():
            if value is not None:
                limits[key] = int(value)
        threshold_values = body.get("thresholds", {})
        policies[policy_id] = BudgetPolicy(
            id=policy_id,
            hard_limits=limits,
            threshold_ratios={key: Decimal(str(value)) for key, value in threshold_values.items()},
        )
    return policies


def _rules(raw_rules: list[dict[str, Any]] | None) -> tuple[PolicyRule, ...]:
    return tuple(
        PolicyRule(
            capability=item.get("capability"),
            action=item.get("action"),
            scope=item.get("scope"),
            constraints=dict(item.get("constraints", {})),
        )
        for item in (raw_rules or [])
    )


def load_policy(relative_path: str) -> PolicyDefinition:
    data = load_yaml(relative_path)
    if not isinstance(data, dict):
        raise ValueError(f"{relative_path} must be a mapping")
    body = data.get("policy")
    if not isinstance(body, dict):
        raise ValueError(f"{relative_path} must declare `policy:` mapping")
    raw = {
        "id": body.get("id", "project-policy"),
        "version": body.get("version", "0.4.0"),
        **body,
    }
    validate_instance(load_json_schema("policy.schema.json"), raw, relative_path)
    return PolicyDefinition(
        id=raw["id"],
        version=Version(raw["version"]),
        default_effect=PolicyDecision(raw["default_effect"]),
        allow=_rules(raw.get("allow")),
        allow_with_constraints=_rules(raw.get("allow_with_constraints")),
        require_approval=_rules(raw.get("require_approval")),
        deny=_rules(raw.get("deny")),
    )


def load_workspaces(relative_path: str) -> dict[str, Workspace]:
    workspaces: dict[str, Workspace] = {}
    section = mapping_under(load_yaml(relative_path), "workspace_backends", relative_path)
    schema = load_json_schema("workspace.schema.json")
    for workspace_id, body in section.items():
        if not isinstance(body, dict):
            raise ValueError(f"{relative_path}/{workspace_id} must be a mapping")
        raw = {"id": workspace_id, **body}
        validate_instance(schema, raw, f"{relative_path}/{workspace_id}")
        workspaces[workspace_id] = Workspace(
            id=workspace_id,
            name=workspace_id,
            backend_type=raw["type"],
            trust_profile=TrustProfile(raw["trust_profile"]),
        )
    return workspaces


def load_tool_providers(relative_path: str) -> dict[str, ToolProviderSpec]:
    providers: dict[str, ToolProviderSpec] = {}
    section = mapping_under(load_yaml(relative_path), "tool_providers", relative_path)
    schema = load_json_schema("tool-provider.schema.json")
    for provider_id, body in section.items():
        if not isinstance(body, dict):
            raise ValueError(f"{relative_path}/{provider_id} must be a mapping")
        raw = {"id": provider_id, **body}
        validate_instance(schema, raw, f"{relative_path}/{provider_id}")
        providers[provider_id] = ToolProviderSpec(
            id=provider_id,
            kind=ProviderType(raw["kind"]),
            trust_level=TrustLevel(raw["trust_level"]),
            capabilities=list(raw.get("capabilities", [])),
            effect_class=EffectClass(raw["effect_class"]),
            transport=raw.get("transport"),
            endpoint_env=raw.get("endpoint_env"),
            network_domains=list(raw.get("network_domains", [])),
            protocol_version=raw.get("protocol_version"),
            health_check=bool(raw.get("health_check", False)),
        )
    return providers


def load_project(relative_path: str) -> dict[str, Any]:
    data = load_yaml(relative_path)
    project = data.get("project") if isinstance(data, dict) else None
    if not isinstance(project, dict):
        raise ValueError(f"{relative_path} must declare `project:` mapping")
    return dict(project)
