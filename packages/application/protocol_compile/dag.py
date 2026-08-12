"""Protocol phase DAG 的确定性校验。"""

from __future__ import annotations

from dataclasses import dataclass
from graphlib import CycleError, TopologicalSorter

from packages.domain.protocols import CompileFindingCode, ProtocolDefinition


@dataclass(frozen=True, slots=True)
class DagFinding:
    code: str
    message: str
    subject_ref: str | None = None


@dataclass(frozen=True, slots=True)
class DagResult:
    phase_dag: dict[str, list[str]]
    ordered_phase_ids: tuple[str, ...]
    findings: tuple[DagFinding, ...] = ()

    @property
    def valid(self) -> bool:
        return not any(
            finding.code != CompileFindingCode.DAG_ORPHAN_PHASE.value for finding in self.findings
        )


def is_phase_id(protocol: ProtocolDefinition, reference: str) -> bool:
    return reference in {phase.id for phase in protocol.phases}


def _reference_findings(protocol: ProtocolDefinition) -> list[DagFinding]:
    phase_ids = [phase.id for phase in protocol.phases]
    known = set(phase_ids)
    findings: list[DagFinding] = []
    for index, phase in enumerate(protocol.phases):
        previous = set(phase_ids[:index])
        for dependency in phase.depends_on:
            if dependency not in known:
                findings.append(
                    DagFinding(
                        CompileFindingCode.DAG_MISSING_DEPENDENCY.value,
                        f"phase {phase.id} depends on missing phase {dependency}",
                        f"phase:{phase.id}",
                    )
                )
            elif dependency not in previous:
                findings.append(
                    DagFinding(
                        CompileFindingCode.DAG_FORWARD_REFERENCE.value,
                        f"phase {phase.id} depends on later phase {dependency}",
                        f"phase:{phase.id}",
                    )
                )
    return findings


def _orphan_findings(protocol: ProtocolDefinition) -> list[DagFinding]:
    """孤立 phase：既无前驱也无后继。信息级诊断，不阻断编译。"""
    phase_ids = {phase.id for phase in protocol.phases}
    referenced: set[str] = {
        dependency for phase in protocol.phases for dependency in phase.depends_on
    } & phase_ids
    dependents: set[str] = {phase.id for phase in protocol.phases if phase.depends_on}
    return [
        DagFinding(
            CompileFindingCode.DAG_ORPHAN_PHASE.value,
            f"phase {phase.id} is not connected to any other phase",
            f"phase:{phase.id}",
        )
        for phase in protocol.phases
        if phase.id not in referenced and phase.id not in dependents
    ]


def _topological_order(
    phase_dag: dict[str, list[str]],
) -> tuple[tuple[str, ...], DagFinding | None]:
    try:
        sorter = TopologicalSorter({key: set(value) for key, value in phase_dag.items()})
        return tuple(sorter.static_order()), None
    except CycleError as exc:
        return (), DagFinding(
            CompileFindingCode.DAG_CYCLE.value,
            f"protocol phase graph contains a cycle: {exc}",
        )


def compile_dag(protocol: ProtocolDefinition) -> DagResult:
    phase_dag = {
        phase.id: sorted(phase.depends_on)
        for phase in sorted(protocol.phases, key=lambda item: item.id)
    }
    findings = _reference_findings(protocol)
    missing_dependency = any(
        finding.code == CompileFindingCode.DAG_MISSING_DEPENDENCY.value for finding in findings
    )
    if missing_dependency:
        findings.extend(_orphan_findings(protocol))
        return DagResult(phase_dag, (), tuple(findings))
    ordered, cycle = _topological_order(phase_dag)
    if cycle is not None:
        findings.append(cycle)
        ordered = ()
    findings.extend(_orphan_findings(protocol))
    return DagResult(phase_dag, ordered, tuple(findings))
