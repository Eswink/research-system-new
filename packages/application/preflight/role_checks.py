"""Preflight 的 Role/Agent 维度检查纯函数。

覆盖 M4 目标：启动前发现缺失角色、Agent 权限问题与异构评审约束违反。
- ROLE_DISABLED：role 被 DISABLED 但 plan 仍为其分配了 agent。
- AGENT_PERMISSION_DENIED：agent 引用的 skill/capability 越出 role 能力面，
  或 agent 使用 role 禁止的 capability（Reviewer 只读 / Writer 不得改 Claim truth）。
- HETEROGENEITY_VIOLATION：同一模型同时承担 Writer 与 Reviewer/MetaReviewer。
"""

from __future__ import annotations

from packages.application.ports import PreflightContext
from packages.application.preflight.review_independence import (
    describe_target,
    resolve_targets_by_role,
)
from packages.application.preflight.skill_checks import check_role_skills, skill_issue_findings
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


def _warning(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.WARNING, message, subject)


def _activation_map(plan: CompiledRunPlan) -> dict[str, bool]:
    return {item.role_id: item.activated for item in plan.role_activations}


def _agent_role_map(
    plan: CompiledRunPlan,
    context: PreflightContext,
    *,
    include_unresolved: bool = False,
) -> dict[str, str]:
    """plan 里参与本次运行的 agent → role。

    `include_unresolved` 给评审独立性判定面用：编译期**解析失败**（如绑定指向未注册模型）
    的 agent 不在 `plan.resolved_models` 里，但把它整个跳过会让「评审独立性」在配置残缺时
    **静默消失** —— 那正是「空集被读成无交集」的假绿形态。判定面因此要在场并**点名**。
    范围仍受本次运行的**phase 分配**收窄（不是全目录 agent 两两互查）。
    """
    assigned_roles = {
        role_id for assignment in plan.phase_assignments for role_id in assignment.role_assignments
    }
    return {
        agent_id: agent.role
        for agent_id, agent in context.catalog.agents.items()
        if agent_id in plan.resolved_models or (include_unresolved and agent.role in assigned_roles)
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


def _skill_capability_findings(
    agent_id: str, context: PreflightContext
) -> tuple[set[str], list[PreflightFinding]]:
    """agent skill 引用展开：capability 声明并入能力面 + Registry 校验。

    MISSING skill 沿用 AGENT_PERMISSION_DENIED（历史兼容）；
    digest/status 问题由 skill_issue_findings 产出 SKILL_* findings。
    """
    agent = context.catalog.agents[agent_id]
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
    findings.extend(
        skill_issue_findings(
            context.catalog.skills,
            tuple(agent.skill_refs),
            f"agent:{agent_id}",
            PreflightFindingCode.AGENT_PERMISSION_DENIED.value,
            skip_missing=True,
        )
    )
    return requested, findings


def _check_agent(
    agent_id: str, plan: CompiledRunPlan, context: PreflightContext
) -> list[PreflightFinding]:
    missing = _registration_findings(agent_id, context)
    if missing:
        return missing
    role = context.catalog.roles[context.catalog.agents[agent_id].role]
    requested, findings = _skill_capability_findings(agent_id, context)
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
) -> tuple[dict[str, set[str]], dict[str, ReviewPanelRole], list[PreflightFinding]]:
    """role → **执行目标**集合、role → review_panel_role、以及解析失败的 finding。

    **GOAL-20261018-084 EC-02**：判定面装的是**解析后的执行目标**
    （`endpoint/model_name`，见 `review_independence`）—— 出厂目录里多个
    ModelDefinition 可以共用同一个 `model_name`（同一个底层模型），比 model id 会让
    「评审与生产者同模型」判绿。

    **解析失败要点名（`EC-01` 第三条边界）**：解析不出目标的 role **不进**比较集合，
    并**逐条输出 finding** —— 空集若被当成「无交集」就会**假绿**，而静默跳过会让
    「评审独立性」在配置残缺时无声失效。点名用 `MODEL_MISSING`（既有 code，
    语义就是「引用了解析不出的模型」）。
    """
    model_by_role: dict[str, set[str]] = {}
    panel_role_by_role: dict[str, ReviewPanelRole] = {}
    problems: list[PreflightFinding] = []
    role_of_agent = _agent_role_map(plan, context, include_unresolved=True)
    agents_of_role: dict[str, tuple[str, ...]] = {}
    for agent_id, role_id in role_of_agent.items():
        agents_of_role[role_id] = (*agents_of_role.get(role_id, ()), agent_id)
    targets_by_role, unresolved = resolve_targets_by_role(
        set(agents_of_role),
        agents_of_role,
        context.catalog,
        plan.resolved_models,
    )
    for role_id in sorted(agents_of_role):
        labels = {describe_target(target) for target in targets_by_role.get(role_id, set())}
        if labels:
            model_by_role[role_id] = labels
        for reason in unresolved.get(role_id, ()):
            problems.append(
                _finding(
                    PreflightFindingCode.MODEL_MISSING.value,
                    f"role {role_id} has an agent whose review-independence target cannot be "
                    f"resolved ({reason}); review independence cannot be judged for this role",
                    f"role:{role_id}",
                )
            )
        role = context.catalog.roles.get(role_id)
        panel_role_by_role[role_id] = (
            role.review_panel_role if role is not None else ReviewPanelRole.NONE
        )
    return model_by_role, panel_role_by_role, problems


def _shared_model_findings(
    model_by_role: dict[str, set[str]],
    writer_roles: set[str],
    reviewer_roles: set[str],
) -> list[PreflightFinding]:
    shared = sorted(
        set().union(*(model_by_role.get(role_id, set()) for role_id in writer_roles))
        & set().union(*(model_by_role.get(role_id, set()) for role_id in reviewer_roles))
    )
    findings: list[PreflightFinding] = []
    for target in shared:
        writer_roles_used = ", ".join(
            sorted(role for role in writer_roles if target in model_by_role.get(role, set()))
        )
        reviewer_roles_used = ", ".join(
            sorted(role for role in reviewer_roles if target in model_by_role.get(role, set()))
        )
        findings.append(
            _finding(
                PreflightFindingCode.HETEROGENEITY_VIOLATION.value,
                (
                    f"model target {target} (endpoint/model_name) is reachable by both writer "
                    f"roles ({writer_roles_used}) and reviewer roles ({reviewer_roles_used}); "
                    "use distinct underlying models for an independent review panel"
                ),
                f"model:{target}",
            )
        )
    return findings


def check_heterogeneity(plan: CompiledRunPlan, context: PreflightContext) -> list[PreflightFinding]:
    """同一**底层模型**不得同时承担 Writer 与 Reviewer/MetaReviewer。

    按 RoleDefinition.review_panel_role 聚合（支持自定义角色，不依赖 role id）；
    比较的是**解析后的执行目标** `(endpoint, model_name)` —— 含 profile 的 primary 与
    **每一个 fallback**（那是一个 agent 可能落到的完整面）。writer 集合与 reviewer 集合
    只要有交集即判违规，逐对输出 finding 并**点名相交的目标**。
    """
    model_by_role, panel_role_by_role, problems = _panel_role_map(plan, context)
    writer_roles = {
        role_id for role_id, panel in panel_role_by_role.items() if panel is ReviewPanelRole.WRITER
    }
    reviewer_roles = {
        role_id
        for role_id, panel in panel_role_by_role.items()
        if panel is ReviewPanelRole.REVIEWER
    }
    if not writer_roles or not reviewer_roles:
        return problems
    return [*problems, *_shared_model_findings(model_by_role, writer_roles, reviewer_roles)]


def check_team(plan: CompiledRunPlan, context: PreflightContext) -> list[PreflightFinding]:
    findings: list[PreflightFinding] = []
    findings.extend(check_role_activations(plan, context))
    findings.extend(check_agent_permissions(plan, context))
    findings.extend(check_heterogeneity(plan, context))
    findings.extend(check_role_skills(plan, context))
    return findings
