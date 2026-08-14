"""Preflight 的 Role/Agent 维度检查纯函数。

覆盖 M4 目标：启动前发现缺失角色、Agent 权限问题与异构评审约束违反。
- ROLE_DISABLED：role 被 DISABLED 但 plan 仍为其分配了 agent。
- AGENT_PERMISSION_DENIED：agent 引用的 skill/capability 越出 role 能力面，
  或 agent 使用 role 禁止的 capability（Reviewer 只读 / Writer 不得改 Claim truth）。
- HETEROGENEITY_VIOLATION：同一模型同时承担 Writer 与 Reviewer/MetaReviewer。
"""

from __future__ import annotations

from packages.application.ports import PreflightContext
from packages.application.protocol_compile.workspace_policy import check_workspace_capability
from packages.domain.enums import ReviewPanelRole, WorkspacePolicy
from packages.domain.protocols import (
    CompiledRunPlan,
    FindingSeverity,
    PreflightFinding,
    PreflightFindingCode,
)


def _finding(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.ERROR, message, subject)


def _activation_map(plan: CompiledRunPlan) -> dict[str, bool]:
    return {item.role_id: item.activated for item in plan.role_activations}


def _agent_role_map(plan: CompiledRunPlan, context: PreflightContext) -> dict[str, str]:
    return {
        agent_id: agent.role
        for agent_id, agent in context.catalog.agents.items()
        if agent_id in plan.resolved_models
    }


def check_role_activations(
    plan: CompiledRunPlan, context: PreflightContext
) -> list[PreflightFinding]:
    """DISABLED / 未注册 role 不得出现在 phase 分配中。"""
    activated = _activation_map(plan)
    assigned_roles = {
        role_id for assignment in plan.phase_assignments for role_id in assignment.role_assignments
    }
    findings = [
        _finding(
            PreflightFindingCode.ROLE_DISABLED.value,
            f"role {role_id} is not activated but assigned to a phase",
            f"role:{role_id}",
        )
        for role_id in sorted(assigned_roles)
        if role_id in activated and not activated[role_id]
    ]
    findings.extend(
        _finding(
            PreflightFindingCode.ROLE_NOT_FOUND.value,
            f"role {role_id} is not registered in the resource catalog",
            f"role:{role_id}",
        )
        for role_id in sorted(assigned_roles)
        if role_id not in context.catalog.roles
    )
    return findings


def check_agent_permissions(
    plan: CompiledRunPlan, context: PreflightContext
) -> list[PreflightFinding]:
    """Agent 的 skill/capability 引用必须落在 role 能力面内。"""
    findings: list[PreflightFinding] = []
    for agent_id in sorted(_agent_role_map(plan, context)):
        findings.extend(_check_agent(agent_id, plan, context))
    return findings


def _registration_findings(agent_id: str, context: PreflightContext) -> list[PreflightFinding]:
    """agent 或其引用 role 未注册必须阻断（不得静默放行）。"""
    agent = context.catalog.agents.get(agent_id)
    if agent is None:
        # 防御性检查：正常解析流程中 agent 必然注册；缺失说明 catalog 被替换。
        return [
            _finding(
                PreflightFindingCode.AGENT_NOT_FOUND.value,
                f"agent {agent_id} is not registered in the resource catalog",
                f"agent:{agent_id}",
            )
        ]
    if agent.role not in context.catalog.roles:
        # compile 层 ROLE_CAPACITY 已覆盖主路径，此处兜底 compile 与
        # preflight 之间 catalog 漂移。
        return [
            _finding(
                PreflightFindingCode.ROLE_NOT_FOUND.value,
                f"agent {agent_id} references unregistered role {agent.role}",
                f"agent:{agent_id}",
            )
        ]
    return []


def _check_agent(
    agent_id: str, plan: CompiledRunPlan, context: PreflightContext
) -> list[PreflightFinding]:
    missing = _registration_findings(agent_id, context)
    if missing:
        return missing
    agent = context.catalog.agents[agent_id]
    role = context.catalog.roles[agent.role]
    requested = set(agent.capability_refs)
    findings: list[PreflightFinding] = []
    for skill_id in agent.skill_refs:
        skill = context.catalog.skills.get(skill_id)
        if skill is None:
            findings.append(
                _finding(
                    PreflightFindingCode.AGENT_PERMISSION_DENIED.value,
                    f"agent {agent_id} references missing skill {skill_id}",
                    f"agent:{agent_id}",
                )
            )
            continue
        requested.update(skill.capabilities)
    allowed = set(role.requested_capabilities)
    forbidden = set(role.forbidden_capabilities)
    findings.extend(
        _finding(
            PreflightFindingCode.AGENT_PERMISSION_DENIED.value,
            (
                f"agent {agent_id} requests capability {capability} "
                f"outside role {role.id} capability surface"
            ),
            f"agent:{agent_id}",
        )
        for capability in sorted(requested - allowed)
    )
    findings.extend(
        _finding(
            PreflightFindingCode.AGENT_PERMISSION_DENIED.value,
            (f"agent {agent_id} requests capability {capability} forbidden by role {role.id}"),
            f"agent:{agent_id}",
        )
        for capability in sorted(requested & forbidden)
    )
    # 写面 capability 与 agent 有效 workspace policy 的静态一致性检查。
    findings.extend(_workspace_capability_findings(plan, agent_id, requested))
    return findings


def _workspace_capability_findings(
    plan: CompiledRunPlan, agent_id: str, requested: set[str]
) -> list[PreflightFinding]:
    effective_policy = plan.agent_workspace_policies.get(agent_id)
    if effective_policy is None:
        return []
    try:
        policy = WorkspacePolicy(effective_policy)
    except ValueError:
        return []
    return [
        finding
        for capability in sorted(requested)
        if (finding := check_workspace_capability(agent_id, capability, policy)) is not None
    ]


def _panel_role_map(
    plan: CompiledRunPlan, context: PreflightContext
) -> tuple[dict[str, set[str]], dict[str, ReviewPanelRole]]:
    """role → 模型集合 与 role → review_panel_role 的聚合视图。"""
    model_by_role: dict[str, set[str]] = {}
    panel_role_by_role: dict[str, ReviewPanelRole] = {}
    for agent_id, role_id in _agent_role_map(plan, context).items():
        model_id = plan.resolved_models.get(agent_id)
        if model_id is None:
            continue
        model_by_role.setdefault(role_id, set()).add(model_id)
        role = context.catalog.roles.get(role_id)
        panel_role_by_role[role_id] = (
            role.review_panel_role if role is not None else ReviewPanelRole.NONE
        )
    return model_by_role, panel_role_by_role


def _shared_model_findings(
    model_by_role: dict[str, set[str]],
    writer_roles: set[str],
    reviewer_roles: set[str],
) -> list[PreflightFinding]:
    shared = sorted(
        set().union(*(model_by_role.get(role_id, set()) for role_id in writer_roles))
        & set().union(*(model_by_role[role_id] for role_id in reviewer_roles))
    )
    findings: list[PreflightFinding] = []
    for model_id in shared:
        writer_roles_used = ", ".join(
            sorted(role for role in writer_roles if model_id in model_by_role.get(role, set()))
        )
        reviewer_roles_used = ", ".join(
            sorted(role for role in reviewer_roles if model_id in model_by_role[role])
        )
        findings.append(
            _finding(
                PreflightFindingCode.HETEROGENEITY_VIOLATION.value,
                (
                    f"model {model_id} is shared between writer roles ({writer_roles_used}) "
                    f"and reviewer roles ({reviewer_roles_used}); "
                    "use distinct models for an independent review panel"
                ),
                f"model:{model_id}",
            )
        )
    return findings


def check_heterogeneity(plan: CompiledRunPlan, context: PreflightContext) -> list[PreflightFinding]:
    """同一模型不得同时承担 Writer 与 Reviewer/MetaReviewer。

    按 RoleDefinition.review_panel_role 聚合模型（支持自定义角色，不依赖 role id）；
    writer 角色集合与任一 reviewer 角色集合只要有交集即判违规，逐对输出 finding。
    """
    model_by_role, panel_role_by_role = _panel_role_map(plan, context)
    writer_roles = {
        role_id for role_id, panel in panel_role_by_role.items() if panel is ReviewPanelRole.WRITER
    }
    reviewer_roles = {
        role_id
        for role_id, panel in panel_role_by_role.items()
        if panel is ReviewPanelRole.REVIEWER
    }
    if not writer_roles or not reviewer_roles:
        return []
    return _shared_model_findings(model_by_role, writer_roles, reviewer_roles)


def check_team(plan: CompiledRunPlan, context: PreflightContext) -> list[PreflightFinding]:
    findings: list[PreflightFinding] = []
    findings.extend(check_role_activations(plan, context))
    findings.extend(check_agent_permissions(plan, context))
    findings.extend(check_heterogeneity(plan, context))
    return findings
