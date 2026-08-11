"""Protocol / Preflight 域实体定义。

来源：docs/architecture/RESEARCH_PROTOCOL.md、docs/architecture/DOMAIN_MODEL.md、
schemas/protocol.schema.json、schemas/preflight-report.schema.json。
本层仅定义实体与不变量；编译与执行属 M2。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from packages.domain.core import Money, Version


class PreflightStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


class FindingSeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class PhaseStrategy(StrEnum):
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    PARALLEL_LIMITED = "PARALLEL_LIMITED"
    BRANCH = "BRANCH"
    GATED = "GATED"
    MANUAL = "MANUAL"


@dataclass(frozen=True, slots=True)
class ProtocolPhase:
    id: str
    name: str
    strategy: PhaseStrategy
    required_roles: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    task_contracts: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("phase id must not be empty")


@dataclass(frozen=True, slots=True)
class ProtocolDefinition:
    id: str
    version: Version
    phases: list[ProtocolPhase]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("protocol id must not be empty")
        if not self.phases:
            raise ValueError("protocol must declare at least one phase")
        phase_ids = [phase.id for phase in self.phases]
        if len(phase_ids) != len(set(phase_ids)):
            raise ValueError("phase ids must be unique")


@dataclass(frozen=True, slots=True)
class PreflightFinding:
    code: str
    severity: FindingSeverity
    message: str
    subject_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("finding code must not be empty")
        if not self.message:
            raise ValueError("finding message must not be empty")


@dataclass(frozen=True, slots=True)
class PreflightReport:
    status: PreflightStatus
    findings: list[PreflightFinding] = field(default_factory=list)
    estimated_cost: Money | None = None
    reserved_budget_ref: str | None = None
    unresolved_risks: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        errors = [finding for finding in self.findings if finding.severity is FindingSeverity.ERROR]
        if self.status is PreflightStatus.FAIL and not errors:
            raise ValueError("FAIL preflight must contain at least one ERROR finding")


@dataclass(frozen=True, slots=True)
class CompiledRunPlan:
    """协议编译结果（M2 生成；本层仅定义契约）。"""

    protocol_id: str
    protocol_version: Version
    phase_dag: dict[str, list[str]]
    task_contract_refs: list[str]
    role_pool_refs: dict[str, int]
    gates: list[str]
    stop_conditions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.phase_dag:
            raise ValueError("compiled plan must contain a phase DAG")
        if not self.task_contract_refs:
            raise ValueError("compiled plan must reference task contracts")
