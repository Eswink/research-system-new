"""Role activation / collapsing 领域决策（纯函数，无副作用）。

来源：docs/architecture/ROLE_MODEL.md §3-§4、docs/configuration/TEAM_TEMPLATES.md、
docs/architecture/RESEARCH_PROTOCOL.md §6。

- ActivationPolicy 决定 RolePool 是否进入实际 Team Plan。
- Role folding 仅在 Role 显式声明等价 Skill（default_skills）时允许；
  折叠结果为 `folded_skill`，不实例化 Agent。
- DISABLED 且协议要求 → ERROR finding，Preflight 不得放行。
- BUDGET_PERMITTING 在编译期视为激活候选，最终由 Preflight 的预算 gate 裁决。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from packages.domain.enums import ActivationPolicy
from packages.domain.protocols import CompileFindingCode, FindingSeverity, PreflightFinding
from packages.domain.roles import RoleDefinition, RolePool


@dataclass(frozen=True, slots=True)
class RoleActivationDecision:
    role_id: str
    activated: bool
    policy: ActivationPolicy
    reason: str
    folded_skill: str | None = None


@dataclass(frozen=True, slots=True)
class RoleActivationResult:
    decisions: tuple[RoleActivationDecision, ...] = ()
    findings: tuple[PreflightFinding, ...] = ()

    def decision_for(self, role_id: str) -> RoleActivationDecision | None:
        for decision in self.decisions:
            if decision.role_id == role_id:
                return decision
        return None


def _finding(code: str, message: str, subject: str) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.ERROR, message, subject)


def _foldable_skill(role: RoleDefinition | None) -> str | None:
    if role is None:
        return None
    return role.default_skills[0] if role.default_skills else None


def _policy_for(
    role_id: str,
    pool: RolePool | None,
    role: RoleDefinition | None,
) -> ActivationPolicy:
    if pool is not None and pool.activation_policy is not None:
        return pool.activation_policy
    if role is not None:
        return role.activation_default
    return ActivationPolicy.ON_DEMAND


def _decide_required(
    role_id: str, policy: ActivationPolicy, role: RoleDefinition | None
) -> RoleActivationDecision:
    skill = _foldable_skill(role)
    if skill is not None:
        return RoleActivationDecision(
            role_id, False, policy, "role not required; folded to equivalent skill", skill
        )
    return RoleActivationDecision(role_id, False, policy, "role not required by protocol")


def _decide_on_demand(
    role_id: str, policy: ActivationPolicy, role: RoleDefinition | None
) -> RoleActivationDecision:
    skill = _foldable_skill(role)
    if skill is not None:
        return RoleActivationDecision(
            role_id, False, policy, "role folded; equivalent skill declared", skill
        )
    return RoleActivationDecision(role_id, False, policy, "role folded; no agent instantiated")


def _decide_disabled(
    role_id: str, policy: ActivationPolicy, required: bool, findings: list[PreflightFinding]
) -> RoleActivationDecision:
    if required:
        findings.append(
            _finding(
                CompileFindingCode.ROLE_CAPACITY.value,
                f"role {role_id} is DISABLED but required by protocol",
                f"role:{role_id}",
            )
        )
    return RoleActivationDecision(role_id, False, policy, "role disabled by policy")


def _decide_budget_permitting(
    role_id: str, policy: ActivationPolicy, required: bool
) -> RoleActivationDecision:
    if required:
        return RoleActivationDecision(role_id, True, policy, "activated pending budget gate")
    return RoleActivationDecision(
        role_id, False, policy, "not required; budget permitting only when demanded"
    )


def activate_roles(
    required_roles: set[str],
    team_roles: Mapping[str, RolePool],
    catalog_roles: Mapping[str, RoleDefinition],
) -> RoleActivationResult:
    """根据协议要求与 RolePool/默认策略计算每个 role 的激活状态。

    `required_roles` 是 Protocol 中所有 phase 要求的 role 集合；
    `team_roles` 是模板解析后的 RolePool 映射；
    `catalog_roles` 提供 activation_default 与折叠 Skill。
    """
    decisions: list[RoleActivationDecision] = []
    findings: list[PreflightFinding] = []
    role_ids = sorted(set(team_roles) | set(catalog_roles) | required_roles)
    for role_id in role_ids:
        pool = team_roles.get(role_id)
        role = catalog_roles.get(role_id)
        policy = _policy_for(role_id, pool, role)
        required = role_id in required_roles
        if policy is ActivationPolicy.ALWAYS:
            decisions.append(
                RoleActivationDecision(role_id, True, policy, "policy ALWAYS activates the role")
            )
        elif policy is ActivationPolicy.REQUIRED_BY_PROTOCOL:
            if required:
                decisions.append(
                    RoleActivationDecision(role_id, True, policy, "role is required by protocol")
                )
            else:
                decisions.append(_decide_required(role_id, policy, role))
        elif policy is ActivationPolicy.ON_DEMAND:
            if required:
                decisions.append(
                    RoleActivationDecision(role_id, True, policy, "role activated on demand")
                )
            else:
                decisions.append(_decide_on_demand(role_id, policy, role))
        elif policy is ActivationPolicy.BUDGET_PERMITTING:
            decisions.append(_decide_budget_permitting(role_id, policy, required))
        elif policy is ActivationPolicy.DISABLED:
            decisions.append(_decide_disabled(role_id, policy, required, findings))
    return RoleActivationResult(tuple(decisions), tuple(findings))
