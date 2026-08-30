"""Preflight dry-run projection（投影视图；与冻结分离以控制文件长度）。"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports import PreflightContext
from packages.application.preflight.policy_check import check_policy
from packages.domain.budget import BudgetReservation
from packages.domain.core import Money
from packages.domain.protocols import (
    CompiledRunPlan,
    PreflightFindingCode,
    PreflightReport,
)


@dataclass(frozen=True, slots=True)
class DryRunProjection:
    role_counts: dict[str, int]
    agent_models: dict[str, str]
    tools: dict[str, tuple[str, ...]]
    workspaces: dict[str, str]
    compute_profiles: dict[str, str | None]
    estimated_cost: Money | None = None
    approval_actions: tuple[str, ...] = ()
    budget_reservations: tuple[BudgetReservation, ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "role_counts": dict(sorted(self.role_counts.items())),
            "agent_models": dict(sorted(self.agent_models.items())),
            "tools": {key: list(value) for key, value in sorted(self.tools.items())},
            "workspaces": dict(sorted(self.workspaces.items())),
            "compute_profiles": dict(sorted(self.compute_profiles.items())),
            "budget_reservations": [
                {
                    "id": item.id,
                    "scope": item.scope,
                    "resource_type": item.resource_type.value,
                    "quantity": item.quantity,
                    "unit": item.unit,
                }
                for item in self.budget_reservations
            ],
            "estimated_cost_minor": (
                self.estimated_cost.minor_units if self.estimated_cost else None
            ),
            "estimated_cost_currency": (
                self.estimated_cost.currency if self.estimated_cost else None
            ),
            "approval_actions": list(self.approval_actions),
        }


def dry_run_projection(
    plan: CompiledRunPlan,
    context: PreflightContext,
    report: PreflightReport | None = None,
) -> DryRunProjection:
    """干运行投影：展示团队/资源/预留与审批动作（零 Research side effect）。"""
    source_findings = report.findings if report else check_policy(plan, context)[0]
    approval_codes = {
        PreflightFindingCode.POLICY_APPROVAL_REQUIRED.value,
        PreflightFindingCode.HUMAN_GATE_REQUIRED.value,
    }
    approval_actions = tuple(
        sorted(finding.message for finding in source_findings if finding.code in approval_codes)
    )
    return DryRunProjection(
        role_counts=dict(plan.role_pools),
        agent_models=dict(plan.resolved_models),
        tools={
            f"{item.phase_id}:{item.capability}": item.provider_ids
            for item in plan.tool_requirements
        },
        workspaces={item.phase_id: item.workspace_backend for item in plan.workspace_requirements},
        compute_profiles={
            item.phase_id: item.compute_profile for item in plan.workspace_requirements
        },
        budget_reservations=tuple(plan.budget_reservations),
        approval_actions=approval_actions,
    )


__all__ = ["DryRunProjection", "dry_run_projection"]
