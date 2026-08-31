"""Research OS 内部观测词汇:操作信号(范围、结果、关联、span 引用)。

M15 观测是自营稳定词汇(ADR-0026);`capture_content` 结构性不存在。
本模块只定义 begin/end 信号与标识符,不含任何内容字段。

定界原则(M15 复审修复):自由文本字段在**结构上**不可承载凭据或原文——
`failure_category` 收敛到闭集、`name` 与 correlation id 经脱敏并有长度上限。
越界值折叠为哨兵而非抛错:这些对象在 `_Operation.__exit__` 里构造,位于
fail-open 外壳之外,抛错会直接打断业务路径。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from packages.domain.enums import FailureCategory
from packages.domain.redaction import redact_text

_MAX_NAME_LENGTH = 96
_MAX_CORRELATION_LENGTH = 128


class OperationFailureReason(StrEnum):
    """编排层失败原因;与 Port `FailureCategory` 并列构成 failure 闭集。

    `OTHER` 是越界折叠哨兵:任何不在闭集内的值(例如误传的异常消息)落到这里,
    使 span attribute / metric label 结构上无法承载自由文本。
    """

    RUN_FAILED = "run_failed"
    TASK_FAILED = "task_failed"
    PHASE_FAILED = "phase_failed"
    TOOL_EXECUTION = "tool_execution"
    LEASE_RECOVERY_FAILED = "lease_recovery_failed"
    OUTBOX_RELAY_FAILED = "outbox_relay_failed"
    EVAL_RUN_FAILED = "eval_run_failed"
    EXPERIMENT_FAILED = "experiment_failed"
    TELEMETRY_LIFECYCLE_TIMEOUT = "telemetry_lifecycle_timeout"
    OTHER = "other"


_ALLOWED_FAILURE_CATEGORIES = frozenset(
    {member.value for member in FailureCategory}
    | {member.value for member in OperationFailureReason}
)


def is_allowed_failure_category(value: str) -> bool:
    """failure_category 闭集判定(Port 分类 + 编排层原因)。"""
    return value in _ALLOWED_FAILURE_CATEGORIES


def coerce_failure_category(value: str | None) -> str | None:
    """越界 failure_category 折叠为 `other`;None 透传。"""
    if value is None:
        return None
    return value if is_allowed_failure_category(value) else OperationFailureReason.OTHER.value


def _bounded_identifier(value: str, limit: int) -> str:
    """脱敏后截断(顺序固定:先脱敏,截断不得切断凭据使正则失配)。"""
    return redact_text(value)[:limit]


class OperationScope(StrEnum):
    PROJECT = "project"
    RUN = "run"
    PHASE = "phase"
    TASK = "task"
    AGENT_SESSION = "agent_session"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    EXPERIMENT_RUN = "experiment_run"
    EVAL_RUN = "eval_run"
    WORKFLOW_QUEUE = "workflow_queue"
    OUTBOX_RELAY = "outbox_relay"
    LEASE_RECOVERY = "lease_recovery"
    # M16 distributed execution plane
    WORKER_SESSION = "worker_session"
    WORKER_DISPATCH = "worker_dispatch"
    REMOTE_EXECUTION = "remote_execution"


class OperationOutcome(StrEnum):
    OK = "OK"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    DENIED = "DENIED"
    SKIPPED = "SKIPPED"


def outcome_is_error(outcome: OperationOutcome) -> bool:
    return outcome in (
        OperationOutcome.FAILED,
        OperationOutcome.TIMEOUT,
        OperationOutcome.CANCELLED,
    )


@dataclass(frozen=True, slots=True)
class CorrelationRef:
    """观测操作关联的现有业务标识;全部可选,永不替代 Domain identity。"""

    project_id: str | None = None
    run_id: str | None = None
    phase_run_id: str | None = None
    task_id: str | None = None
    agent_session_id: str | None = None
    tool_call_id: str | None = None
    experiment_run_id: str | None = None
    eval_run_id: str | None = None
    trace_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "project_id",
            "run_id",
            "phase_run_id",
            "task_id",
            "agent_session_id",
            "tool_call_id",
            "experiment_run_id",
            "eval_run_id",
            "trace_id",
        ):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{name} must be a string")
            if value is not None and not value:
                raise ValueError(f"{name} must be non-empty when present")
            if value is not None:
                # correlation id 是业务标识(UUID/digest),不是内容通道:脱敏 + 定长
                # 上限,避免调用方把凭据或原文塞进 id 位（M15 复审实测可行）。
                object.__setattr__(self, name, _bounded_identifier(value, _MAX_CORRELATION_LENGTH))


@dataclass(frozen=True, slots=True)
class SpanRef:
    """span 引用:telemetry correlation id,永不替代 Domain identity。"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("span_ref must not be empty")


@dataclass(frozen=True, slots=True)
class ParentSpanRef:
    """父 span 引用(可空);None 表示该操作无父(root)。"""

    value: str | None = None

    def __post_init__(self) -> None:
        if self.value is not None and not self.value:
            raise ValueError("parent_span_ref must be non-empty when present")


@dataclass(frozen=True, slots=True)
class OperationBegin:
    """一次观测操作开始信号。"""

    span_ref: SpanRef
    parent_span_ref: ParentSpanRef
    scope: OperationScope
    name: str
    correlation: CorrelationRef = field(default_factory=CorrelationRef)
    attributes: dict[str, str | int | bool] = field(default_factory=dict)
    started_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("operation name must not be empty")
        if self.started_at is not None and self.started_at.tzinfo is None:
            raise ValueError("started_at must be timezone-aware")
        # span name 由站点以字面量提供(llm.call / tool.execute / phase / …);
        # 脱敏 + 上限使它在结构上无法承载 prompt/凭据（M15 复审实测可行）。
        object.__setattr__(self, "name", _bounded_identifier(self.name, _MAX_NAME_LENGTH))


@dataclass(frozen=True, slots=True)
class OperationEnd:
    """一次观测操作结束信号。

    `failure_category` 是闭集(Port `FailureCategory` + `OperationFailureReason`);
    越界值折叠为 `other`。M15 复审前它是自由文本,且被同时写成 span attribute
    与 OTel `Status.description`——实测可导出 8105 字符含 DSN 密码的载荷两次。
    """

    span_ref: SpanRef
    outcome: OperationOutcome
    failure_category: str | None = None
    attributes: dict[str, str | int | bool] = field(default_factory=dict)
    duration_ms: int | None = None
    ended_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if self.ended_at is not None and self.ended_at.tzinfo is None:
            raise ValueError("ended_at must be timezone-aware")
        object.__setattr__(self, "failure_category", coerce_failure_category(self.failure_category))
