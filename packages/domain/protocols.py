"""Research Protocol 编译与 Preflight 的 Domain 契约。

来源：docs/architecture/RESEARCH_PROTOCOL.md、docs/architecture/DOMAIN_MODEL.md、
schemas/protocol.schema.json、schemas/compiled-run-plan.schema.json、
schemas/preflight-report.schema.json。
本层只定义不可变值对象与不变量；编译、资源查询和执行属于外层。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from packages.domain.budget import BudgetReservation
from packages.domain.core import Digest, Money, Version
from packages.domain.enums import GateType, ModelCapability
from packages.domain.serialization import digest_of
from packages.domain.team_plan import PhaseAssignment, RoleActivationRecord


class PreflightStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


class FindingSeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class PhaseStrategy(StrEnum):
    DETERMINISTIC = "deterministic"
    PARALLEL_AGENTS = "parallel_agents"
    MAP_REDUCE = "map_reduce"
    POPULATION_SEARCH = "population_search"
    ITERATIVE_OPTIMIZER = "iterative_optimizer"
    SINGLE_AGENT = "single_agent"


class CompileFindingCode(StrEnum):
    DAG_MISSING_DEPENDENCY = "DAG_MISSING_DEPENDENCY"
    DAG_FORWARD_REFERENCE = "DAG_FORWARD_REFERENCE"
    DAG_CYCLE = "DAG_CYCLE"
    DAG_ORPHAN_PHASE = "DAG_ORPHAN_PHASE"
    ROLE_CAPACITY = "ROLE_CAPACITY"
    AGENT_MISSING = "AGENT_MISSING"
    MODEL_MISSING = "MODEL_MISSING"
    MODEL_PROFILE_MISSING = "MODEL_PROFILE_MISSING"
    MODEL_ELIGIBILITY = "MODEL_ELIGIBILITY"
    TASK_CONTRACT_MISSING = "TASK_CONTRACT_MISSING"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    SUPPLY_CHAIN_UNPINNED = "SUPPLY_CHAIN_UNPINNED"
    WORKSPACE_UNAVAILABLE = "WORKSPACE_UNAVAILABLE"
    WORKSPACE_POLICY_VIOLATION = "WORKSPACE_POLICY_VIOLATION"
    SELECTION_STRATEGY_DEGRADED = "SELECTION_STRATEGY_DEGRADED"
    PROTOCOL_INVALID = "PROTOCOL_INVALID"


class PreflightFindingCode(StrEnum):
    """Preflight 的稳定、可测试错误分类。

    - POLICY_DENIED / POLICY_APPROVAL_REQUIRED / POLICY_MISSING：策略面
    - CREDENTIAL_MISSING / ENDPOINT_UNHEALTHY：凭据与端点面
    - MODEL_MISSING / MODEL_ELIGIBILITY / TOOL_UNAVAILABLE / SUPPLY_CHAIN_UNPINNED：
      模型/工具面（与 CompileFindingCode 同名的运行时复检）
    - WORKSPACE_UNAVAILABLE：工作区面
    - BUDGET_MISSING / BUDGET_EXHAUSTED / BUDGET_LIMIT_UNKNOWN /
      BUDGET_RESOURCE_UNMAPPED：预算面（未映射 ResourceType 表示预算检查不完整）
    - HUMAN_GATE_REQUIRED：人工门
    - ROLE_DISABLED / AGENT_PERMISSION_DENIED / HETEROGENEITY_VIOLATION /
      ROLE_NOT_FOUND / AGENT_NOT_FOUND：Role/Agent/Team 面（M4）
    """

    POLICY_DENIED = "POLICY_DENIED"
    POLICY_APPROVAL_REQUIRED = "POLICY_APPROVAL_REQUIRED"
    POLICY_MISSING = "POLICY_MISSING"
    CREDENTIAL_MISSING = "CREDENTIAL_MISSING"
    ENDPOINT_UNHEALTHY = "ENDPOINT_UNHEALTHY"
    MODEL_MISSING = "MODEL_MISSING"
    MODEL_ELIGIBILITY = "MODEL_ELIGIBILITY"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    SUPPLY_CHAIN_UNPINNED = "SUPPLY_CHAIN_UNPINNED"
    WORKSPACE_UNAVAILABLE = "WORKSPACE_UNAVAILABLE"
    BUDGET_MISSING = "BUDGET_MISSING"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    BUDGET_LIMIT_UNKNOWN = "BUDGET_LIMIT_UNKNOWN"
    BUDGET_RESOURCE_UNMAPPED = "BUDGET_RESOURCE_UNMAPPED"
    HUMAN_GATE_REQUIRED = "HUMAN_GATE_REQUIRED"
    ROLE_DISABLED = "ROLE_DISABLED"
    AGENT_PERMISSION_DENIED = "AGENT_PERMISSION_DENIED"
    HETEROGENEITY_VIOLATION = "HETEROGENEITY_VIOLATION"
    ROLE_NOT_FOUND = "ROLE_NOT_FOUND"
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"


@dataclass(frozen=True, slots=True)
class RoleRequirement:
    role: str
    min_instances: int
    max_instances: int

    def __post_init__(self) -> None:
        if not self.role:
            raise ValueError("required role must not be empty")
        if self.min_instances < 0:
            raise ValueError("role min_instances must be non-negative")
        if self.max_instances < self.min_instances:
            raise ValueError("role max_instances must be >= min_instances")


@dataclass(frozen=True, slots=True)
class StopConditions:
    max_iterations: int | None = None
    budget_exhausted: bool = False

    def __post_init__(self) -> None:
        if self.max_iterations is not None and self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")


@dataclass(frozen=True, slots=True)
class ProtocolPhase:
    id: str
    strategy: PhaseStrategy
    name: str | None = None
    depends_on: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    required_roles: list[RoleRequirement] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    task_contract: str | None = None
    task_contracts: list[str] = field(default_factory=list)
    timeout_seconds: int | None = None
    gate: GateType | None = None
    stop_conditions: StopConditions | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("phase id must not be empty")
        if self.timeout_seconds is not None and self.timeout_seconds < 1:
            raise ValueError("phase timeout_seconds must be >= 1")
        if len(self.depends_on) != len(set(self.depends_on)):
            raise ValueError("phase dependencies must be unique")
        if len(self.required_capabilities) != len(set(self.required_capabilities)):
            raise ValueError("phase capabilities must be unique")
        refs = list(self.task_contracts)
        if self.task_contract and self.task_contract not in refs:
            refs.insert(0, self.task_contract)
        if len(refs) != len(set(refs)):
            raise ValueError("phase task contracts must be unique")
        object.__setattr__(self, "task_contracts", refs)


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
class ModelEligibilityRecord:
    agent_id: str
    role_id: str
    model_id: str
    eligible: bool
    hard_capabilities: tuple[ModelCapability, ...] = ()
    missing_capabilities: tuple[ModelCapability, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolRequirement:
    phase_id: str
    capability: str
    provider_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WorkspaceRequirement:
    phase_id: str
    workspace_backend: str
    trust_profile: str
    compute_profile: str | None = None


@dataclass(frozen=True, slots=True)
class CompiledPhase:
    id: str
    strategy: PhaseStrategy
    depends_on: tuple[str, ...] = ()
    task_contract_refs: tuple[str, ...] = ()
    timeout_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class GateRequirement:
    phase_id: str
    gate: GateType


@dataclass(frozen=True, slots=True)
class CompiledStopCondition:
    phase_id: str
    max_iterations: int | None = None
    budget_exhausted: bool = False


@dataclass(frozen=True, slots=True)
class CompiledRunPlan:
    """解析完成的执行计划；它描述执行，不执行 Agent。"""

    protocol_id: str
    protocol_version: Version
    protocol_digest: Digest
    phase_dag: dict[str, list[str]]
    phases: list[CompiledPhase]
    task_contract_refs: list[str]
    role_pools: dict[str, int]
    agent_candidates: dict[str, list[str]]
    resolved_models: dict[str, str]
    model_eligibility: list[ModelEligibilityRecord]
    tool_requirements: list[ToolRequirement]
    workspace_requirements: list[WorkspaceRequirement]
    budget_reservations: list[BudgetReservation]
    tool_pack_digests: dict[str, str]
    gates: list[GateRequirement]
    stop_conditions: list[CompiledStopCondition]
    role_activations: list[RoleActivationRecord] = field(default_factory=list)
    phase_assignments: list[PhaseAssignment] = field(default_factory=list)
    agent_workspace_policies: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.protocol_id:
            raise ValueError("compiled plan protocol_id must not be empty")
        if not self.phase_dag or not self.phases:
            raise ValueError("compiled plan must contain phases and a phase DAG")
        if len({phase.id for phase in self.phases}) != len(self.phases):
            raise ValueError("compiled plan phase ids must be unique")

    def digest(self) -> Digest:
        return digest_of(self)


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
        if self.status is PreflightStatus.WARN and errors:
            raise ValueError("WARN preflight must not contain ERROR findings")
        if self.status is PreflightStatus.PASS and errors:
            raise ValueError("PASS preflight must not contain ERROR findings")

    @property
    def passed(self) -> bool:
        return self.status is PreflightStatus.PASS
