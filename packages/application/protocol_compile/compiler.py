"""ProtocolDefinition → CompiledRunPlan 的确定性编译器。"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.ports import CatalogSnapshot, ProjectSettings
from packages.application.protocol_compile.dag import DagResult, compile_dag, is_phase_id
from packages.application.protocol_compile.requirements import (
    budget_reservations,
    task_contract_refs,
    tool_requirements,
    workspace_requirements,
)
from packages.application.protocol_compile.resolution import RoleResolution, resolve_roles
from packages.domain.protocols import (
    CompiledPhase,
    CompiledRunPlan,
    CompiledStopCondition,
    CompileFindingCode,
    FindingSeverity,
    GateRequirement,
    PreflightFinding,
    ProtocolDefinition,
    ToolRequirement,
    WorkspaceRequirement,
)
from packages.domain.serialization import digest_of


@dataclass(frozen=True, slots=True)
class CompileResult:
    plan: CompiledRunPlan | None
    findings: tuple[PreflightFinding, ...] = ()

    @property
    def successful(self) -> bool:
        return self.plan is not None and not self.findings


@dataclass(frozen=True, slots=True)
class PlanParts:
    """Compile 各派生步骤的中间产物，打包传给 plan 组装。"""

    dag: DagResult
    roles: RoleResolution
    task_contract_refs: list[str]
    tools: list[ToolRequirement]
    workspaces: list[WorkspaceRequirement]
    gates: list[GateRequirement]


def _finding(code: str, message: str, subject: str | None = None) -> PreflightFinding:
    return PreflightFinding(code, FindingSeverity.ERROR, message, subject)


def _compiled_phases(protocol: ProtocolDefinition, ordered: tuple[str, ...]) -> list[CompiledPhase]:
    phases = {phase.id: phase for phase in protocol.phases}
    return [
        CompiledPhase(
            id=phase_id,
            strategy=phases[phase_id].strategy,
            depends_on=tuple(sorted(phases[phase_id].depends_on)),
            task_contract_refs=tuple(phases[phase_id].task_contracts),
            timeout_seconds=phases[phase_id].timeout_seconds,
        )
        for phase_id in ordered
    ]


def _gates(protocol: ProtocolDefinition) -> tuple[list[GateRequirement], list[PreflightFinding]]:
    findings: list[PreflightFinding] = []
    gates = [GateRequirement(phase.id, phase.gate) for phase in protocol.phases if phase.gate]
    for requirement in gates:
        if not is_phase_id(protocol, requirement.phase_id):
            findings.append(
                _finding(
                    CompileFindingCode.PROTOCOL_INVALID.value,
                    f"gate references unknown phase {requirement.phase_id}",
                    f"phase:{requirement.phase_id}",
                )
            )
    return gates, findings


def _stop_conditions(protocol: ProtocolDefinition) -> list[CompiledStopCondition]:
    return [
        CompiledStopCondition(
            phase_id=phase.id,
            max_iterations=phase.stop_conditions.max_iterations,
            budget_exhausted=phase.stop_conditions.budget_exhausted,
        )
        for phase in protocol.phases
        if phase.stop_conditions is not None
    ]


def _validate_stop_conditions(protocol: ProtocolDefinition) -> list[PreflightFinding]:
    """stop_conditions 引用的 phase 必须存在；否则协议非法。"""
    return [
        _finding(
            CompileFindingCode.PROTOCOL_INVALID.value,
            f"stop_conditions reference unknown phase {condition.phase_id}",
            f"phase:{condition.phase_id}",
        )
        for condition in _stop_conditions(protocol)
        if not is_phase_id(protocol, condition.phase_id)
    ]


def _assemble_plan(
    protocol: ProtocolDefinition,
    parts: PlanParts,
    catalog: CatalogSnapshot,
) -> CompiledRunPlan:
    return CompiledRunPlan(
        protocol_id=protocol.id,
        protocol_version=protocol.version,
        protocol_digest=digest_of(protocol),
        phase_dag=parts.dag.phase_dag,
        phases=_compiled_phases(protocol, parts.dag.ordered_phase_ids),
        task_contract_refs=parts.task_contract_refs,
        role_pools=parts.roles.role_pools,
        agent_candidates=parts.roles.agent_candidates,
        resolved_models=parts.roles.resolved_models,
        model_eligibility=parts.roles.model_eligibility,
        tool_requirements=parts.tools,
        workspace_requirements=parts.workspaces,
        budget_reservations=budget_reservations(protocol, catalog),
        tool_pack_digests=dict(sorted(catalog.tool_pack_digests.items())),
        gates=parts.gates,
        stop_conditions=_stop_conditions(protocol),
        role_activations=list(parts.roles.role_activations),
        phase_assignments=list(parts.roles.phase_assignments),
        agent_workspace_policies=dict(parts.roles.agent_workspace_policies),
    )


def compile_protocol(
    protocol: ProtocolDefinition,
    catalog: CatalogSnapshot,
    project: ProjectSettings,
) -> CompileResult:
    dag = compile_dag(protocol)
    findings = [
        PreflightFinding(
            item.code,
            FindingSeverity.INFO
            if item.code == CompileFindingCode.DAG_ORPHAN_PHASE.value
            else FindingSeverity.ERROR,
            item.message,
            item.subject_ref,
        )
        for item in dag.findings
    ]
    blocking = [finding for finding in findings if finding.severity is FindingSeverity.ERROR]
    if blocking:
        return CompileResult(None, tuple(findings))
    gates, gate_findings = _gates(protocol)
    findings.extend(gate_findings)
    findings.extend(_validate_stop_conditions(protocol))
    roles = resolve_roles(protocol, catalog, project)
    findings.extend(roles.findings)
    refs, ref_findings = task_contract_refs(protocol, catalog)
    findings.extend(ref_findings)
    tools, tool_findings = tool_requirements(protocol, catalog)
    findings.extend(tool_findings)
    workspaces, workspace_findings = workspace_requirements(protocol, catalog, project)
    findings.extend(workspace_findings)
    parts = PlanParts(
        dag=dag,
        roles=roles,
        task_contract_refs=refs,
        tools=tools,
        workspaces=workspaces,
        gates=gates,
    )
    plan = _assemble_plan(protocol, parts, catalog)
    # ERROR 使计划不可用；INFO/WARNING（如策略退化、孤立 phase）随计划携带，
    # 由 Preflight 聚合展示（不得静默丢弃）。
    if findings:
        return CompileResult(plan, tuple(findings))
    return CompileResult(plan, ())
