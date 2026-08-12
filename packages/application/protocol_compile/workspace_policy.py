"""Agent 有效 workspace policy 解析（Role 边界 + Agent 显式覆盖）与写面 capability 一致性。"""

from __future__ import annotations

from packages.domain.enums import WorkspacePolicy
from packages.domain.protocols import CompileFindingCode, FindingSeverity, PreflightFinding
from packages.domain.roles import AgentSpec

# workspace policy 偏序：agent 显式策略的写面不得超出 role 边界。
_WITHIN: dict[WorkspacePolicy, frozenset[WorkspacePolicy]] = {
    WorkspacePolicy.READ_ONLY: frozenset({WorkspacePolicy.READ_ONLY}),
    WorkspacePolicy.NOTES_ONLY: frozenset({WorkspacePolicy.READ_ONLY, WorkspacePolicy.NOTES_ONLY}),
    WorkspacePolicy.DELIVERABLE_ONLY: frozenset({
        WorkspacePolicy.READ_ONLY,
        WorkspacePolicy.DELIVERABLE_ONLY,
    }),
    WorkspacePolicy.ISOLATED_WRITABLE: frozenset(set(WorkspacePolicy)),
}

# 写面 capability → 允许的有效 workspace policy（isolated_writable 覆盖全部写面）。
_WRITE_CAPABILITY_POLICIES: dict[str, frozenset[WorkspacePolicy]] = {
    "workspace.write.notes": frozenset({
        WorkspacePolicy.NOTES_ONLY,
        WorkspacePolicy.ISOLATED_WRITABLE,
    }),
    "workspace.write.code": frozenset({WorkspacePolicy.ISOLATED_WRITABLE}),
    "workspace.delete": frozenset({WorkspacePolicy.ISOLATED_WRITABLE}),
    "deliverable.write": frozenset({
        WorkspacePolicy.DELIVERABLE_ONLY,
        WorkspacePolicy.ISOLATED_WRITABLE,
    }),
    "deliverable.edit": frozenset({
        WorkspacePolicy.DELIVERABLE_ONLY,
        WorkspacePolicy.ISOLATED_WRITABLE,
    }),
}


def resolve_agent_workspace_policy(
    agent: AgentSpec,
    role_workspace_policy: WorkspacePolicy | None,
) -> tuple[str, PreflightFinding | None]:
    """解析 agent 的有效 workspace policy。

    未显式配置时继承 role 默认；显式配置不得宽于 role 边界，
    否则返回编译期 finding（WORKSPACE_POLICY_VIOLATION）。
    """
    agent_policy = agent.workspace_policy
    effective = agent_policy or role_workspace_policy
    if effective is None:
        return WorkspacePolicy.READ_ONLY.value, None
    if (
        agent_policy is not None
        and role_workspace_policy is not None
        and agent_policy not in _WITHIN[role_workspace_policy]
    ):
        return effective.value, PreflightFinding(
            CompileFindingCode.WORKSPACE_POLICY_VIOLATION.value,
            FindingSeverity.ERROR,
            (
                f"agent {agent.id} workspace policy {agent_policy.value} "
                f"exceeds role boundary {role_workspace_policy.value}"
            ),
            f"agent:{agent.id}",
        )
    return effective.value, None


def check_workspace_capability(
    agent_id: str,
    capability: str,
    effective_workspace_policy: WorkspacePolicy,
) -> PreflightFinding | None:
    """校验写面 capability 是否被 agent 的有效 workspace policy 允许。

    静态一致性前移：M6/M7 执行期 Policy Wrapper 仍负责运行时 enforce，
    但编译期/preflight 必须拒绝明显不一致的配置。
    """
    allowed = _WRITE_CAPABILITY_POLICIES.get(capability)
    if allowed is None:
        return None
    if effective_workspace_policy in allowed:
        return None
    return PreflightFinding(
        CompileFindingCode.WORKSPACE_POLICY_VIOLATION.value,
        FindingSeverity.ERROR,
        (
            f"agent {agent_id} capability {capability} requires workspace policy "
            f"{' or '.join(sorted(policy.value for policy in allowed))}, "
            f"but effective policy is {effective_workspace_policy.value}"
        ),
        f"agent:{agent_id}",
    )
