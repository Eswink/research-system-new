"""Role activation / collapsing 领域决策测试。"""

from __future__ import annotations

from packages.domain.activation import activate_roles
from packages.domain.enums import ActivationPolicy, RoleCategory, WorkspacePolicy
from packages.domain.roles import RoleDefinition, RolePool


def _role(
    role_id: str, policy: ActivationPolicy, skills: list[str] | None = None
) -> RoleDefinition:
    return RoleDefinition(
        id=role_id,
        role_type=role_id.title(),
        category=RoleCategory.DISCOVERY,
        activation_default=policy,
        requested_capabilities=["literature.read"],
        default_skills=list(skills or []),
        workspace_policy=WorkspacePolicy.READ_ONLY,
    )


def _pool(
    policy: ActivationPolicy | None = None,
    *,
    min_instances: int = 1,
    max_instances: int = 2,
) -> RolePool:
    return RolePool(
        min_instances=min_instances,
        max_instances=max_instances,
        activation_policy=policy,
    )


def test_required_by_protocol_activates_when_required() -> None:
    roles = {
        "scout": _role("scout", ActivationPolicy.REQUIRED_BY_PROTOCOL, ["literature_scouting"])
    }
    result = activate_roles({"scout"}, {"scout": _pool()}, roles)
    decision = result.decision_for("scout")
    assert decision is not None
    assert decision.activated is True
    assert decision.policy is ActivationPolicy.REQUIRED_BY_PROTOCOL
    assert not result.findings


def test_required_by_protocol_folds_when_not_required() -> None:
    roles = {
        "scout": _role("scout", ActivationPolicy.REQUIRED_BY_PROTOCOL, ["literature_scouting"])
    }
    result = activate_roles(set(), {"scout": _pool()}, roles)
    decision = result.decision_for("scout")
    assert decision is not None
    assert decision.activated is False
    assert decision.folded_skill == "literature_scouting"
    assert "folded" in decision.reason


def test_always_activates_regardless_of_protocol() -> None:
    roles = {"director": _role("director", ActivationPolicy.ALWAYS)}
    result = activate_roles(set(), {"director": _pool()}, roles)
    decision = result.decision_for("director")
    assert decision is not None
    assert decision.activated is True


def test_on_demand_activates_when_required() -> None:
    roles = {"analyst": _role("analyst", ActivationPolicy.ON_DEMAND)}
    result = activate_roles({"analyst"}, {"analyst": _pool()}, roles)
    decision = result.decision_for("analyst")
    assert decision is not None
    assert decision.activated is True


def test_on_demand_folds_with_equivalent_skill() -> None:
    roles = {"editor": _role("editor", ActivationPolicy.ON_DEMAND, ["scholarly_writing"])}
    result = activate_roles(set(), {"editor": _pool()}, roles)
    decision = result.decision_for("editor")
    assert decision is not None
    assert decision.activated is False
    assert decision.folded_skill == "scholarly_writing"


def test_on_demand_without_skill_has_no_fold() -> None:
    roles = {"analyst": _role("analyst", ActivationPolicy.ON_DEMAND)}
    result = activate_roles(set(), {"analyst": _pool()}, roles)
    decision = result.decision_for("analyst")
    assert decision is not None
    assert decision.folded_skill is None


def test_budget_permitting_required_is_pending_budget_gate() -> None:
    roles = {"engineer": _role("engineer", ActivationPolicy.BUDGET_PERMITTING)}
    result = activate_roles({"engineer"}, {"engineer": _pool()}, roles)
    decision = result.decision_for("engineer")
    assert decision is not None
    assert decision.activated is True
    assert "budget" in decision.reason


def test_budget_permitting_not_required_stays_inactive() -> None:
    roles = {"engineer": _role("engineer", ActivationPolicy.BUDGET_PERMITTING)}
    result = activate_roles(set(), {"engineer": _pool()}, roles)
    decision = result.decision_for("engineer")
    assert decision is not None
    assert decision.activated is False


def test_disabled_required_produces_error_finding() -> None:
    roles = {"legacy": _role("legacy", ActivationPolicy.DISABLED)}
    result = activate_roles({"legacy"}, {"legacy": _pool()}, roles)
    decision = result.decision_for("legacy")
    assert decision is not None
    assert decision.activated is False
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.subject_ref == "role:legacy"


def test_pool_policy_overrides_role_default() -> None:
    roles = {"scout": _role("scout", ActivationPolicy.REQUIRED_BY_PROTOCOL)}
    # pool 显式 DISABLED，role 默认 REQUIRED_BY_PROTOCOL
    result = activate_roles({"scout"}, {"scout": _pool(ActivationPolicy.DISABLED)}, roles)
    decision = result.decision_for("scout")
    assert decision is not None
    assert decision.policy is ActivationPolicy.DISABLED
    assert decision.activated is False
    assert result.findings


def test_unregistered_role_falls_back_to_on_demand() -> None:
    result = activate_roles({"ghost"}, {}, {})
    decision = result.decision_for("ghost")
    assert decision is not None
    assert decision.policy is ActivationPolicy.ON_DEMAND


def test_role_not_in_template_still_evaluated() -> None:
    roles = {"editor": _role("editor", ActivationPolicy.ON_DEMAND, ["scholarly_writing"])}
    # role 在 catalog 但不在 team_roles
    result = activate_roles(set(), {}, roles)
    decision = result.decision_for("editor")
    assert decision is not None
    assert decision.activated is False
    assert decision.folded_skill == "scholarly_writing"
