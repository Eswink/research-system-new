"""Task / Handoff 域实体定义。

来源：docs/architecture/TASK_HANDOFF.md、docs/architecture/DOMAIN_MODEL.md、
schemas/task-contract.schema.json、schemas/handoff-bundle.schema.json。
LLM 不能自行宣布验收通过；副作用绑定 task_id + attempt + operation_key。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from packages.domain.core import ID, Digest, Timestamp
from packages.domain.enums import (
    AcceptanceCriterionType,
    ComparisonOperator,
    FailureCategory,
    TaskKind,
)
from packages.domain.state_machines import ResearchTaskState


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int
    retryable_categories: list[FailureCategory] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")


@dataclass(frozen=True, slots=True)
class AcceptanceCriterion:
    """验收标准；结构化参数与 schemas/task-contract.schema.json 的 acceptanceCriterion 对齐。

    `description`/`target` 为向后兼容的展示字段；求值语义以 type 与结构化参数为准
    （见 packages/domain/acceptance.py）。
    """

    type: AcceptanceCriterionType
    description: str = ""
    target: str | None = None
    artifact: str | None = None
    minimum_sources: int | None = None
    metric: str | None = None
    operator: ComparisonOperator | None = None
    threshold: Decimal | None = None
    evaluator: str | None = None

    def __post_init__(self) -> None:
        if self.minimum_sources is not None and self.minimum_sources < 0:
            raise ValueError("minimum_sources must be >= 0")


@dataclass(frozen=True, slots=True)
class TaskContract:
    id: str
    version: str
    purpose: str
    required_capabilities: list[str] = field(default_factory=list)
    input_schema: str | None = None
    output_schema: str | None = None
    required_artifacts: list[str] = field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    budget: dict[str, Decimal | None] = field(default_factory=dict)
    timeout_seconds: int | None = None
    retry_policy: RetryPolicy | None = None
    failure_policy: dict[str, str | bool | int | list[str]] = field(default_factory=dict)
    idempotency_scope: str = "task"

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("task contract id must not be empty")
        if not self.version:
            raise ValueError("task contract version must not be empty")
        if not self.purpose:
            raise ValueError("task contract purpose must not be empty")
        if not self.acceptance_criteria:
            raise ValueError("task contract must declare at least one acceptance criterion")
        if self.timeout_seconds is not None and self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be >= 1")


@dataclass(frozen=True, slots=True)
class ResearchTask:
    id: ID
    run_id: ID
    phase_run_id: ID | None = None
    contract_id: str | None = None
    assigned_agent_id: str | None = None
    status: str = ResearchTaskState.State.CREATED
    priority: int = 0
    attempt: int = 1
    idempotency_key: str | None = None
    lease_id: str | None = None
    # M16（ADR-0027）：默认 AGENT_SESSION 向后兼容；EXECUTION 为远程 worker
    # 可 claim 的一次性执行作业。partition/required_capability 是 claim 过滤
    # 投影（所有权权威仍是 leases 行），非分区权威。
    kind: TaskKind = TaskKind.AGENT_SESSION
    partition: int | None = None
    required_capability: str | None = None

    def __post_init__(self) -> None:
        if self.priority < 0:
            raise ValueError("priority must be non-negative")
        if self.attempt < 1:
            raise ValueError("attempt must be >= 1")
        if self.attempt > 1 and self.lease_id is None:
            raise ValueError("retried task must carry a lease_id")
        if not isinstance(self.kind, TaskKind):
            object.__setattr__(self, "kind", TaskKind(self.kind))
        if self.partition is not None and self.partition < 0:
            raise ValueError("partition must be non-negative")
        if self.required_capability is not None and not self.required_capability.strip():
            raise ValueError("required_capability must be non-empty when present")


@dataclass(frozen=True, slots=True)
class HandoffBundle:
    task_id: ID
    producer: str
    summary: str
    digest: Digest
    created_at: Timestamp = field(default_factory=Timestamp.now)
    producer_agent_id: str | None = None
    producer_role_id: str | None = None
    structured_output: dict[str, object] = field(default_factory=dict)
    artifact_refs: list[str] = field(default_factory=list)
    claim_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    decision_refs: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    known_failures: list[str] = field(default_factory=list)
    recommended_next_actions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.producer:
            raise ValueError("handoff producer must not be empty")
        if not self.summary:
            raise ValueError("handoff summary must not be empty")
