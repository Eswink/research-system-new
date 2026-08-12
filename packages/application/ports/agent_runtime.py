"""AgentRuntime Port：AgentSession 生命周期（docs/architecture/AGENT_RUNTIME.md）。

职责：create/run/pause/cancel/stream_events/fork 会话生命周期；输出归一化
runtime event 与终端结果；状态必须来自 domain AgentSessionState。
非职责：不编排 run/phase/task（WorkflowEngine）；不选择模型（ModelGateway）；
不记账（BudgetLedger）；runtime event 不替代 Domain Event（EventPublisher）。

本 Port 不预设任何上游 Runtime（OpenHands 等）的 Conversation/Event 类型；
上游状态由 adapter 显式映射到 domain 状态（AGENT_RUNTIME.md §5）。
M5 决策 D2：Port 为同步语义；cancellation 为协作式。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, runtime_checkable

from packages.domain.budget import BudgetReservation
from packages.domain.core import ID
from packages.domain.memory import ContextSnapshot
from packages.domain.roles import AgentSpec, RoleDefinition
from packages.domain.session_state import AgentSessionState
from packages.domain.tasks import TaskContract
from packages.domain.workspace import WorkspaceLease


@dataclass(frozen=True, slots=True)
class AgentSessionSpec:
    """会话创建规格（AGENT_RUNTIME.md §2）。"""

    task_id: ID
    task_contract: TaskContract
    role: RoleDefinition
    agent: AgentSpec
    frozen_tool_set: tuple[str, ...] = ()
    workspace_lease: WorkspaceLease | None = None
    context_snapshot: ContextSnapshot | None = None
    budget_reservation: BudgetReservation | None = None
    manifest_ref: str | None = None


@dataclass(frozen=True, slots=True)
class AgentSessionHandle:
    session_id: str
    status: str = AgentSessionState.State.CREATED

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id must not be empty")


@dataclass(frozen=True, slots=True)
class AgentSessionResult:
    session_id: str
    status: str
    message: str = ""
    structured_output: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id must not be empty")
        if self.status not in AgentSessionState.terminal():
            raise ValueError(f"session result status must be terminal, got {self.status!r}")


class RuntimeEventKind(StrEnum):
    """归一化 runtime event（AGENT_RUNTIME.md §5 状态映射的流式投影）。

    属于 AgentRuntime 输出契约，不替代 Domain Event（EVENT_MODEL.md）。
    """

    SESSION_CREATED = "session.created"
    SESSION_STARTED = "session.started"
    STEP_COMPLETED = "step.completed"
    TOOL_CALL_REQUESTED = "tool_call.requested"
    APPROVAL_REQUESTED = "approval.requested"
    SESSION_PAUSED = "session.paused"
    SESSION_STUCK = "session.stuck"
    SESSION_SUCCEEDED = "session.succeeded"
    SESSION_FAILED = "session.failed"
    SESSION_CANCELLED = "session.cancelled"


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    session_id: str
    kind: RuntimeEventKind
    message: str = ""
    payload: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id must not be empty")


@dataclass(frozen=True, slots=True)
class ForkSpec:
    session_id: str
    reason: str
    model_override: str | None = None
    tool_set_override: tuple[str, ...] | None = None
    manifest_revision_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id must not be empty")
        if not self.reason:
            raise ValueError("fork reason must not be empty")


@runtime_checkable
class AgentRuntime(Protocol):
    """AgentSession 生命周期（同步语义，D2）。"""

    def create_session(self, spec: AgentSessionSpec) -> AgentSessionHandle: ...

    def run(self, session_id: str) -> AgentSessionResult: ...

    def pause(self, session_id: str) -> None: ...

    def cancel(self, session_id: str) -> None: ...

    def stream_events(self, session_id: str) -> tuple[RuntimeEvent, ...]: ...

    def fork(self, session_id: str, spec: ForkSpec) -> AgentSessionHandle: ...
