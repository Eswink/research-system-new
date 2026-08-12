"""Compile 阶段的 Role/Agent/Model 解析。"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.application.model_relay.eligibility import decide_eligibility
from packages.application.ports import CatalogSnapshot, ProjectSettings
from packages.application.protocol_compile.assignments import phase_assignments
from packages.application.protocol_compile.requirements import (
    aggregate_required_roles,
    merged_team_roles,
)
from packages.application.protocol_compile.selection import degradation_findings, select_agents
from packages.application.protocol_compile.workspace_policy import resolve_agent_workspace_policy
from packages.domain.activation import activate_roles
from packages.domain.enums import (
    CapabilityStatus,
    ModelBindingMode,
    ModelCapability,
)
from packages.domain.protocols import (
    CompileFindingCode,
    FindingSeverity,
    ModelEligibilityRecord,
    PreflightFinding,
    ProtocolDefinition,
)
from packages.domain.roles import AgentSpec, RolePool
from packages.domain.team_plan import PhaseAssignment, RoleActivationRecord


@dataclass(slots=True)
class RoleResolution:
    role_pools: dict[str, int] = field(default_factory=dict)
    agent_candidates: dict[str, list[str]] = field(default_factory=dict)
    resolved_models: dict[str, str] = field(default_factory=dict)
    model_eligibility: list[ModelEligibilityRecord] = field(default_factory=list)
    role_activations: list[RoleActivationRecord] = field(default_factory=list)
    phase_assignments: list[PhaseAssignment] = field(default_factory=list)
    agent_workspace_policies: dict[str, str] = field(default_factory=dict)
    findings: list[PreflightFinding] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RoleResolutionContext:
    team_roles: dict[str, RolePool]
    catalog: CatalogSnapshot
    project: ProjectSettings
    phase_capabilities: set[str] = field(default_factory=set)


def _finding(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.ERROR, message, subject)


def _model_profile_id(
    agent: AgentSpec,
    role_id: str,
    team_roles: dict[str, RolePool],
    catalog: CatalogSnapshot,
    project: ProjectSettings,
) -> str | None:
    if agent.model_binding.mode is ModelBindingMode.MODEL_PROFILE:
        return agent.model_binding.value
    if agent.model_binding.mode is ModelBindingMode.EXPLICIT_MODEL:
        return None
    pool = team_roles.get(role_id)
    role = catalog.roles.get(role_id)
    return (
        (pool.model_profile if pool else None)
        or (role.default_model_profile if role else None)
        or project.default_model_profile_id
    )


def _model_id_for_agent(
    agent: AgentSpec,
    role_id: str,
    team_roles: dict[str, RolePool],
    catalog: CatalogSnapshot,
    project: ProjectSettings,
) -> tuple[str | None, str | None, PreflightFinding | None]:
    profile_id: str | None = None
    if agent.model_binding.mode is ModelBindingMode.EXPLICIT_MODEL:
        model_id = agent.model_binding.value
    else:
        profile_id = _model_profile_id(agent, role_id, team_roles, catalog, project)
        if profile_id is None or profile_id not in catalog.model_profiles:
            return (
                None,
                profile_id,
                _finding(
                    CompileFindingCode.MODEL_PROFILE_MISSING.value,
                    f"agent {agent.id} has no resolvable model profile",
                    f"agent:{agent.id}",
                ),
            )
        model_id = catalog.model_profiles[profile_id].primary
    if model_id is None or model_id not in catalog.models:
        return (
            None,
            profile_id,
            _finding(
                CompileFindingCode.MODEL_MISSING.value,
                f"agent {agent.id} references missing model {model_id}",
                f"agent:{agent.id}",
            ),
        )
    return model_id, profile_id, None


def _required_capabilities(
    role_id: str,
    profile_id: str | None,
    catalog: CatalogSnapshot,
) -> tuple[ModelCapability, ...]:
    role = catalog.roles.get(role_id)
    values = list(role.hard_model_capabilities.all_of) if role else []
    if profile_id is not None and profile_id in catalog.model_profiles:
        values.extend(item.value for item in catalog.model_profiles[profile_id].hard_capabilities)
    return tuple(dict.fromkeys(ModelCapability(value) for value in values))


def _eligibility(
    agent_id: str,
    role_id: str,
    model_id: str,
    profile_id: str | None,
    catalog: CatalogSnapshot,
) -> ModelEligibilityRecord:
    model = catalog.models[model_id]
    role = catalog.roles[role_id]
    all_of = set(_required_capabilities(role_id, profile_id, catalog))
    any_of = {ModelCapability(item) for item in role.hard_model_capabilities.any_of}
    decision = decide_eligibility(model, all_of)
    any_satisfied = not any_of or any(
        model.capabilities.get(capability)
        and model.capabilities[capability].status is CapabilityStatus.SUPPORTED
        for capability in any_of
    )
    missing = list(decision.missing_capabilities)
    if any_of and not any_satisfied:
        missing.extend(sorted(any_of, key=lambda item: item.value))
    return ModelEligibilityRecord(
        agent_id=agent_id,
        role_id=role_id,
        model_id=model_id,
        eligible=decision.allowed and any_satisfied,
        hard_capabilities=tuple(sorted(all_of, key=lambda item: item.value)),
        missing_capabilities=tuple(dict.fromkeys(missing)),
    )


def _role_findings(
    role_id: str,
    minimum: int,
    pool: RolePool | None,
    catalog: CatalogSnapshot,
) -> list[PreflightFinding]:
    findings: list[PreflightFinding] = []
    if pool is None or pool.max_instances < minimum:
        findings.append(
            _finding(
                CompileFindingCode.ROLE_CAPACITY.value,
                f"team template cannot satisfy role {role_id} minimum {minimum}",
                f"role:{role_id}",
            )
        )
    if role_id not in catalog.roles:
        findings.append(
            _finding(
                CompileFindingCode.ROLE_CAPACITY.value,
                f"role {role_id} is not registered",
                f"role:{role_id}",
            )
        )
    return findings


def _resolve_agents(
    role_id: str,
    candidates: list[str],
    context: RoleResolutionContext,
) -> RoleResolution:
    result = RoleResolution()
    for agent_id in candidates:
        agent = context.catalog.agents[agent_id]
        model_id, profile_id, model_finding = _model_id_for_agent(
            agent, role_id, context.team_roles, context.catalog, context.project
        )
        if model_finding:
            result.findings.append(model_finding)
            continue
        assert model_id is not None
        result.resolved_models[agent_id] = model_id
        role = context.catalog.roles.get(role_id)
        workspace_policy, workspace_finding = resolve_agent_workspace_policy(
            agent, role.workspace_policy if role else None
        )
        result.agent_workspace_policies[agent_id] = workspace_policy
        if workspace_finding is not None:
            result.findings.append(workspace_finding)
        eligibility = _eligibility(agent_id, role_id, model_id, profile_id, context.catalog)
        result.model_eligibility.append(eligibility)
        if not eligibility.eligible:
            missing = ", ".join(item.value for item in eligibility.missing_capabilities)
            result.findings.append(
                _finding(
                    CompileFindingCode.MODEL_ELIGIBILITY.value,
                    f"model {model_id} is not eligible; missing: {missing or 'unknown'}",
                    f"agent:{agent_id}",
                )
            )
    return result


def _resolve_role(
    role_id: str,
    minimum: int,
    maximum: int,
    offset: int,
    context: RoleResolutionContext,
) -> RoleResolution:
    result = RoleResolution(
        findings=_role_findings(role_id, minimum, context.team_roles.get(role_id), context.catalog)
    )
    if role_id not in context.catalog.roles:
        return result
    pool = context.team_roles.get(role_id)
    candidate_limit = min(maximum, pool.max_instances) if pool else maximum
    candidates = sorted(
        (agent for agent in context.catalog.agents.values() if agent.role == role_id),
        key=lambda agent: agent.id,
    )
    if pool is None:
        selected = [agent.id for agent in candidates[:candidate_limit]]
    else:
        selected = select_agents(
            candidates,
            pool,
            candidate_limit,
            offset=offset,
            required_capabilities=context.phase_capabilities,
        )
    result.role_pools[role_id] = len(selected)
    result.agent_candidates[role_id] = selected
    if pool is not None:
        result.findings.extend(degradation_findings(pool, role_id))
    if len(selected) < minimum:
        result.findings.append(
            _finding(
                CompileFindingCode.AGENT_MISSING.value,
                f"role {role_id} requires {minimum} agents but only {len(selected)} are available",
                f"role:{role_id}",
            )
        )
    resolved = _resolve_agents(role_id, selected, context)
    result.resolved_models.update(resolved.resolved_models)
    result.model_eligibility.extend(resolved.model_eligibility)
    result.agent_workspace_policies.update(resolved.agent_workspace_policies)
    result.findings.extend(resolved.findings)
    return result


def resolve_roles(
    protocol: ProtocolDefinition,
    catalog: CatalogSnapshot,
    project: ProjectSettings,
) -> RoleResolution:
    team_roles = merged_team_roles(project.team_template_id, catalog)
    requirements, phase_capabilities = aggregate_required_roles(protocol)
    context = RoleResolutionContext(team_roles, catalog, project, phase_capabilities)
    result = RoleResolution()
    activation = activate_roles(set(requirements), team_roles, catalog.roles)
    result.role_activations = [
        RoleActivationRecord(
            role_id=decision.role_id,
            activated=decision.activated,
            policy=decision.policy.value,
            reason=decision.reason,
            folded_skill=decision.folded_skill,
        )
        for decision in activation.decisions
    ]
    result.findings.extend(activation.findings)
    ordered_roles = sorted(requirements)
    for offset, role_id in enumerate(ordered_roles):
        minimum, maximum = requirements[role_id]
        resolved = _resolve_role(role_id, minimum, maximum, offset, context)
        result.role_pools.update(resolved.role_pools)
        result.agent_candidates.update(resolved.agent_candidates)
        result.resolved_models.update(resolved.resolved_models)
        result.model_eligibility.extend(resolved.model_eligibility)
        result.agent_workspace_policies.update(resolved.agent_workspace_policies)
        result.findings.extend(resolved.findings)
    result.phase_assignments = phase_assignments(protocol, result.agent_candidates, activation)
    return result
