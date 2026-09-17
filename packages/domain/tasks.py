"""Task / Handoff 域实体定义。

来源：docs/architecture/TASK_HANDOFF.md、docs/architecture/DOMAIN_MODEL.md、
schemas/task-contract.schema.json、schemas/handoff-bundle.schema.json。
LLM 不能自行宣布验收通过；副作用绑定 task_id + attempt + operation_key。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from packages.domain.core import ID, Digest, Timestamp
from packages.domain.enums import (
    AcceptanceCriterionType,
    ComparisonOperator,
    FailureAction,
    FailureCategory,
    TaskKind,
)
from packages.domain.state_machines import ResearchTaskState

# 失败处置 → 落库状态（RETRY 走 RETRY_SCHEDULED，不在这张表里）。
_FAILURE_STATUS = {
    FailureAction.FAIL: ResearchTaskState.State.FAILED,
    FailureAction.DEAD_LETTER: ResearchTaskState.State.DEAD_LETTER,
}


@dataclass(frozen=True, slots=True)
class FailureDisposition:
    """一次完成的落库处置：写成什么状态、做了什么动作、要不要重排。"""

    status: str
    action: FailureAction
    retrying: bool


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int
    retryable_categories: list[FailureCategory] = field(default_factory=list)
    # 退避（PLAN-20260915-079）：`backoff_seconds` 是指数退避的**基数**，第 n 次尝试失败后
    # 等 `min(base * 2^(n-1), max_backoff_seconds)`。两个字段都可空 —— 不写就是"立即重排"，
    # 与退避字段出现之前完全一致（既有契约不受影响）。
    backoff_seconds: int | None = None
    max_backoff_seconds: int | None = None

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.backoff_seconds is not None and self.backoff_seconds < 0:
            raise ValueError("backoff_seconds must be >= 0")
        if self.max_backoff_seconds is not None and self.max_backoff_seconds < 0:
            raise ValueError("max_backoff_seconds must be >= 0")
        if (
            self.backoff_seconds is not None
            and self.max_backoff_seconds is not None
            and self.max_backoff_seconds < self.backoff_seconds
        ):
            # 否则 cap 会静默压低基数（写的是 30s 上限、5s 基数却得到 5s 上限）。
            raise ValueError("max_backoff_seconds must be >= backoff_seconds")


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

    def disposition(
        self, *, outcome: str, attempt: int, category: FailureCategory | None
    ) -> FailureDisposition:
        """一次完成的**落库处置**：写成什么状态、做了什么动作、要不要重排。

        成功/失败只在这里分叉一次，两个 adapter 直接用结果写库，各自不再有第二套 if。
        """
        if outcome == "SUCCEEDED":
            return FailureDisposition(
                status=ResearchTaskState.State.SUCCEEDED, action=FailureAction.FAIL, retrying=False
            )
        action = self.decide_failure(attempt=attempt, category=category)
        if action is FailureAction.RETRY:
            return FailureDisposition(
                status=ResearchTaskState.State.RETRY_SCHEDULED, action=action, retrying=True
            )
        return FailureDisposition(status=_FAILURE_STATUS[action], action=action, retrying=False)

    def decide_failure(self, *, attempt: int, category: FailureCategory | None) -> FailureAction:
        """一次**失败**的完成该被怎么处置（纯函数，两个 adapter 共用同一判据）。

        规则（顺序即优先级）：

        1. 没有 `retry_policy`，或本次完成**没有给出失败类别** ⇒ `FAIL`。
           没有类别就无从判断"这类失败可不可重试"，默认不重试（保守）。
        2. 类别不在 `retryable_categories` 里 ⇒ `FAIL`。
        3. 类别可重试且 `attempt < max_attempts` ⇒ `RETRY`。
        4. 类别可重试但次数已用尽 ⇒ `DEAD_LETTER`（不再自动重试，等人工恢复）。

        `attempt` 是**本次**尝试的序号（从 1 开始）。退避时延不在这里：见
        `retry_delay`（同一份策略，纯函数）。
        """
        policy = self.retry_policy
        if policy is None or category is None:
            return FailureAction.FAIL
        if category not in policy.retryable_categories:
            return FailureAction.FAIL
        if attempt < policy.max_attempts:
            return FailureAction.RETRY
        return FailureAction.DEAD_LETTER

    def retry_delay(self, *, attempt: int) -> timedelta:
        """第 `attempt` 次尝试失败、决定重排后，**等多久**再交付下一次（纯函数）。

        规则：`min(backoff_seconds * 2^(attempt-1), max_backoff_seconds)`；
        没有 `retry_policy`、没写 `backoff_seconds`、或基数为 0 ⇒ 零时延
        （= 退避字段出现之前的行为）。上限只封顶、不压低基数。

        时延由 Domain 算、由 adapter 落库（`tasks.retry_at`）：两个 adapter 各自
        "什么时候能再 claim"的判断必须来自同一个数，否则 SQLite 与 PG 会漂移。
        """
        policy = self.retry_policy
        if policy is None or not policy.backoff_seconds:
            return timedelta(0)
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        seconds = policy.backoff_seconds * (2 ** (attempt - 1))
        if policy.max_backoff_seconds is not None:
            seconds = min(seconds, policy.max_backoff_seconds)
        return timedelta(seconds=seconds)

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
