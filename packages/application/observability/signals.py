"""Research OS 内部观测词汇:操作信号(范围、结果、关联、span 引用)。

M15 观测是自营稳定词汇(ADR-0026);`capture_content` 结构性不存在。
本模块只定义 begin/end 信号与标识符,不含任何内容字段。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


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


@dataclass(frozen=True, slots=True)
class OperationEnd:
    """一次观测操作结束信号。"""

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
