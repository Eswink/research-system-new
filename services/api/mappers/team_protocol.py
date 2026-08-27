"""Team / Protocol / Preflight Domain → DTO 显式映射。"""

from __future__ import annotations

from packages.application.preflight.preflight import DryRunProjection
from packages.domain.models import ModelDefinition
from packages.domain.protocols import CompiledRunPlan, PreflightReport
from packages.domain.roles import AgentSpec, RoleDefinition, TeamTemplate
from packages.domain.serialization import digest_of
from services.api.dto.team_protocol import (
    AgentSpecDto,
    DryRunProjectionDto,
    PreflightReportDto,
    RoleDefinitionDto,
    TeamTemplateDto,
)


def role_dto(role: RoleDefinition) -> RoleDefinitionDto:
    requirement = role.hard_model_capabilities
    return RoleDefinitionDto(
        id=role.id,
        role_type=role.role_type,
        category=role.category.value,
        activation_default=role.activation_default.value,
        requested_capabilities=list(role.requested_capabilities),
        hard_model_capabilities={
            "all_of": list(requirement.all_of),
            "any_of": list(requirement.any_of),
        },
        default_model_profile=role.default_model_profile,
        workspace_policy=role.workspace_policy.value,
        default_skills=list(role.default_skills),
        review_panel_role=role.review_panel_role.value,
    )


def template_dto(template: TeamTemplate) -> TeamTemplateDto:
    return TeamTemplateDto(
        id=template.id,
        display_name=template.display_name,
        extends=template.extends,
        roles={
            role_id: {
                "min_instances": pool.min_instances,
                "max_instances": pool.max_instances,
            }
            for role_id, pool in template.roles.items()
        },
    )


def agent_dto(agent: AgentSpec) -> AgentSpecDto:
    context = agent.context
    return AgentSpecDto(
        id=agent.id,
        role=agent.role,
        model_binding={
            "mode": agent.model_binding.mode.value,
            "value": agent.model_binding.value,
        },
        workspace_policy=agent.workspace_policy.value if agent.workspace_policy else None,
        skill_refs=list(agent.skill_refs),
        capability_refs=list(agent.capability_refs),
        max_context_tokens=context.max_context_tokens if context else None,
        max_iterations=context.max_iterations if context else None,
        runtime_kind=agent.runtime_kind.value if agent.runtime_kind else None,
        budget_policy_ref=agent.budget_policy_ref,
        version=agent_version(agent),
    )


def model_version_of(model: ModelDefinition) -> str:
    from services.api.mappers.models import model_version

    return model_version(model)


def agent_version(agent: AgentSpec) -> str:
    """API resource version：全字段 canonical digest（If-Match 用）。"""
    context = agent.context
    binding = agent.model_binding
    canonical: dict[str, object] = {
        "id": agent.id,
        "role": agent.role,
        "model_binding": {"mode": binding.mode.value, "value": binding.value},
        "workspace_policy": agent.workspace_policy.value if agent.workspace_policy else None,
        "skill_refs": list(agent.skill_refs),
        "capability_refs": list(agent.capability_refs),
        "context": {
            "max_context_tokens": context.max_context_tokens,
            "max_iterations": context.max_iterations,
        }
        if context
        else None,
        "runtime_kind": agent.runtime_kind.value if agent.runtime_kind else None,
        "budget_policy_ref": agent.budget_policy_ref,
    }
    return str(digest_of(canonical))


def preflight_dto(report: PreflightReport) -> PreflightReportDto:
    estimated_cost = (
        report.estimated_cost.minor_units / 100 if report.estimated_cost is not None else None
    )
    return PreflightReportDto(
        status=report.status.value,
        findings=[
            {
                "code": finding.code,
                "severity": finding.severity.value,
                "message": finding.message,
                "subject_ref": finding.subject_ref,
            }
            for finding in report.findings
        ],
        estimated_cost=estimated_cost,
        reserved_budget_ref=report.reserved_budget_ref,
        unresolved_risks=list(report.unresolved_risks),
    )


def dry_run_dto(projection: DryRunProjection) -> DryRunProjectionDto:
    return DryRunProjectionDto(
        role_counts=dict(projection.role_counts),
        agent_models=dict(projection.agent_models),
        tools={key: list(value) for key, value in projection.tools.items()},
        workspaces=dict(projection.workspaces),
        compute_profiles=dict(projection.compute_profiles),
        budget_reservations=[
            {
                "id": item.id,
                "scope": item.scope,
                "resource_type": item.resource_type.value,
                "quantity": item.quantity,
                "unit": item.unit,
            }
            for item in projection.budget_reservations
        ],
        estimated_cost_minor=(
            projection.estimated_cost.minor_units if projection.estimated_cost else None
        ),
        approval_actions=list(projection.approval_actions),
    )


def plan_digest_of(plan: CompiledRunPlan) -> str:
    return str(plan.digest())
