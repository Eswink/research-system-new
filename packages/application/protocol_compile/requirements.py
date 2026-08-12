"""Compile 阶段的资源需求派生：TaskContract / Tool / Workspace / Budget。

与 compiler.py 分离，保持编译器主体只做编排与组装；本模块是纯派生函数。
"""

from __future__ import annotations

from packages.application.ports import CatalogSnapshot, ProjectSettings
from packages.domain.budget import BudgetReservation, ResourceType
from packages.domain.protocols import (
    CompileFindingCode,
    FindingSeverity,
    PreflightFinding,
    ProtocolDefinition,
    ProtocolPhase,
    ToolRequirement,
    WorkspaceRequirement,
)
from packages.domain.roles import RolePool


def finding(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.ERROR, message, subject)


def merged_team_roles(template_id: str, catalog: CatalogSnapshot) -> dict[str, RolePool]:
    """TeamTemplate extends 链确定性 deep merge（parent 先、child 覆盖）。"""
    lineage: list[dict[str, RolePool]] = []
    current = template_id
    visited: set[str] = set()
    while current and current not in visited:
        visited.add(current)
        template = catalog.team_templates.get(current)
        if template is None:
            break
        lineage.append(template.roles)
        current = template.extends or ""
    merged: dict[str, RolePool] = {}
    for roles in reversed(lineage):
        merged.update(roles)
    return merged


def task_contract_refs(
    protocol: ProtocolDefinition,
    catalog: CatalogSnapshot,
) -> tuple[list[str], list[PreflightFinding]]:
    refs = sorted({ref for phase in protocol.phases for ref in phase.task_contracts})
    findings = [
        finding(
            CompileFindingCode.TASK_CONTRACT_MISSING.value,
            f"phase references missing task contract {ref}",
            f"task-contract:{ref}",
        )
        for ref in refs
        if ref not in catalog.task_contracts
    ]
    return refs, findings


def phase_capabilities(phase: ProtocolPhase, catalog: CatalogSnapshot) -> set[str]:
    capabilities = set(phase.required_capabilities)
    for contract_id in phase.task_contracts:
        contract = catalog.task_contracts.get(contract_id)
        if contract is not None:
            capabilities.update(contract.required_capabilities)
    return capabilities


def aggregate_required_roles(
    protocol: ProtocolDefinition,
) -> tuple[dict[str, tuple[int, int]], set[str]]:
    """聚合全部 phase 的 required_roles（min/max 取各 phase 最大值）与 phase capabilities。"""
    requirements: dict[str, tuple[int, int]] = {}
    phase_capability_set: set[str] = set()
    for phase in protocol.phases:
        phase_capability_set.update(phase.required_capabilities)
        for requirement in phase.required_roles:
            current = requirements.get(requirement.role, (0, 0))
            requirements[requirement.role] = (
                max(current[0], requirement.min_instances),
                max(current[1], requirement.max_instances),
            )
    return requirements, phase_capability_set


def tool_requirements(
    protocol: ProtocolDefinition,
    catalog: CatalogSnapshot,
) -> tuple[list[ToolRequirement], list[PreflightFinding]]:
    requirements: list[ToolRequirement] = []
    findings: list[PreflightFinding] = []
    for phase in protocol.phases:
        for capability in sorted(phase_capabilities(phase, catalog)):
            providers = tuple(
                sorted(
                    provider.id
                    for provider in catalog.tool_providers.values()
                    if capability in provider.capabilities
                )
            )
            requirements.append(ToolRequirement(phase.id, capability, providers))
            if not providers:
                findings.append(
                    finding(
                        CompileFindingCode.TOOL_UNAVAILABLE.value,
                        f"no tool provider exposes capability {capability}",
                        f"phase:{phase.id}",
                    )
                )
    return requirements, findings


def workspace_requirements(
    protocol: ProtocolDefinition,
    catalog: CatalogSnapshot,
    project: ProjectSettings,
) -> tuple[list[WorkspaceRequirement], list[PreflightFinding]]:
    requirements: list[WorkspaceRequirement] = []
    findings: list[PreflightFinding] = []
    workspace = catalog.workspaces.get(project.workspace_backend)
    for phase in protocol.phases:
        if workspace is None:
            findings.append(
                finding(
                    CompileFindingCode.WORKSPACE_UNAVAILABLE.value,
                    f"workspace backend {project.workspace_backend} is not registered",
                    f"phase:{phase.id}",
                )
            )
            continue
        requirements.append(
            WorkspaceRequirement(
                phase_id=phase.id,
                workspace_backend=workspace.id,
                trust_profile=workspace.trust_profile.value,
                compute_profile=project.compute_profile,
            )
        )
    return requirements, findings


def budget_reservations(
    protocol: ProtocolDefinition,
    catalog: CatalogSnapshot,
) -> list[BudgetReservation]:
    reservations: list[BudgetReservation] = []
    for phase in protocol.phases:
        phase_roles = sum(requirement.min_instances for requirement in phase.required_roles)
        reservations.extend([
            BudgetReservation(
                id=f"budget:{phase.id}:agent_sessions",
                scope=f"phase:{phase.id}",
                resource_type=ResourceType.PARALLELISM,
                quantity=phase_roles,
                unit="agent-sessions",
            ),
            BudgetReservation(
                id=f"budget:{phase.id}:tool_requests",
                scope=f"phase:{phase.id}",
                resource_type=ResourceType.TOOL_REQUESTS,
                quantity=len(phase_capabilities(phase, catalog)),
                unit="requests",
            ),
        ])
        if phase.timeout_seconds is not None:
            reservations.append(
                BudgetReservation(
                    id=f"budget:{phase.id}:wall_clock",
                    scope=f"phase:{phase.id}",
                    resource_type=ResourceType.WALL_CLOCK,
                    quantity=phase.timeout_seconds,
                    unit="seconds",
                )
            )
    return reservations
