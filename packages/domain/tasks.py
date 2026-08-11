"""Task / Handoff 域实体定义。

来源：docs/architecture/TASK_HANDOFF.md、docs/architecture/DOMAIN_MODEL.md、
schemas/task-contract.schema.json、schemas/handoff-bundle.schema.json。
LLM 不能自行宣布验收通过；副作用绑定 task_id + attempt + operation_key。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.domain.core import ID, Digest
from packages.domain.enums import AcceptanceCriterionType, FailureCategory
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
    type: AcceptanceCriterionType
    description: str = ""
    target: str | None = None


@dataclass(frozen=True, slots=True)
class TaskContract:
    id: str
    version: str
    purpose: str
    required_capabilities: list[str] = field(default_factory=list)
    output_schema: str | None = None
    required_artifacts: list[str] = field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    timeout_seconds: int | None = None
    retry_policy: RetryPolicy | None = None
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

    def __post_init__(self) -> None:
        if self.priority < 0:
            raise ValueError("priority must be non-negative")
        if self.attempt < 1:
            raise ValueError("attempt must be >= 1")
        if self.attempt > 1 and self.lease_id is None:
            raise ValueError("retried task must carry a lease_id")


@dataclass(frozen=True, slots=True)
class HandoffBundle:
    task_id: ID
    producer: str
    summary: str
    digest: Digest
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
