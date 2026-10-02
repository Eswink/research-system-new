"""OpenHandsRuntimeAdapter 的类型与状态映射（独立模块避免 runtime_adapter 超限）。

- map_status_to_domain：ConversationExecutionStatus → AgentSessionState 显式映射；
- _SessionEntry：adapter 内部会话登记；
- AdapterDependencies：composition root 依赖集合。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openhands.sdk.conversation.impl.local_conversation import LocalConversation
from openhands.sdk.conversation.state import ConversationExecutionStatus

from packages.application.ports.agent_runtime import (
    AgentSessionResult,
    AgentSessionSpec,
    RuntimeEvent,
    RuntimeEventKind,
)
from packages.application.ports.credential_resolver import CredentialResolver
from packages.application.ports.policy_evaluator import PolicyEvaluator
from packages.domain.session_state import AgentSessionState

# SDK 执行状态 → domain 会话状态（显式映射；未知收敛 FAILED）
_STATUS_TO_DOMAIN: dict[str, str] = {
    ConversationExecutionStatus.IDLE.value: AgentSessionState.State.CREATED,
    ConversationExecutionStatus.RUNNING.value: AgentSessionState.State.RUNNING,
    ConversationExecutionStatus.PAUSED.value: AgentSessionState.State.PAUSED,
    ConversationExecutionStatus.WAITING_FOR_CONFIRMATION.value: (
        AgentSessionState.State.WAITING_FOR_APPROVAL
    ),
    ConversationExecutionStatus.FINISHED.value: AgentSessionState.State.SUCCEEDED,
    ConversationExecutionStatus.ERROR.value: AgentSessionState.State.FAILED,
    ConversationExecutionStatus.STUCK.value: AgentSessionState.State.STUCK,
    ConversationExecutionStatus.DELETING.value: AgentSessionState.State.FAILED,
}

# SDK 终态 → domain 终态收敛（SDK STUCK 是终态，domain STUCK 非终态）
_SDK_TERMINAL_TO_DOMAIN: dict[str, str] = {
    ConversationExecutionStatus.FINISHED.value: AgentSessionState.State.SUCCEEDED,
    ConversationExecutionStatus.ERROR.value: AgentSessionState.State.FAILED,
    ConversationExecutionStatus.STUCK.value: AgentSessionState.State.FAILED,
}

_TERMINAL_EVENT_KIND: dict[str, RuntimeEventKind] = {
    AgentSessionState.State.SUCCEEDED: RuntimeEventKind.SESSION_SUCCEEDED,
    AgentSessionState.State.FAILED: RuntimeEventKind.SESSION_FAILED,
    AgentSessionState.State.CANCELLED: RuntimeEventKind.SESSION_CANCELLED,
}


def map_status_to_domain(status: ConversationExecutionStatus) -> str:
    """SDK 执行状态 → domain 会话状态（仅中间态；未知收敛 FAILED）。"""
    return _STATUS_TO_DOMAIN.get(status.value, AgentSessionState.State.FAILED)


@dataclass
class _SessionEntry:
    """adapter 内部会话登记（SDK Conversation + Research OS 状态投影）。"""

    session_id: str
    spec: AgentSessionSpec
    conversation: LocalConversation
    conversation_id: str
    status: str = AgentSessionState.State.CREATED
    cancel_requested: bool = False
    terminal_result: AgentSessionResult | None = None
    events: list[RuntimeEvent] = field(default_factory=list)
    seen_event_ids: set[str] = field(default_factory=set)
    # 事件映射已投影过的终端 kind（_finish 不再重复追加，M6 复审 F-5）
    terminal_kinds_seen: set[RuntimeEventKind] = field(default_factory=set)


@dataclass(frozen=True, slots=True)
class AdapterDependencies:
    """adapter 外部依赖集合（composition root 注入，避免构造参数爆炸）。"""

    credential_resolver: CredentialResolver
    policy_evaluator: PolicyEvaluator
    build_llm: Any
    build_workspace: Any
    register_tools: Any = None
    build_agent: Any = None
    build_llm_for_fork: Any = None  # fork model_override 时构建新 LLM（缺省回退 build_llm）
    budget_ledger: Any = None
    usage_reporter: Any = None
    persistence_dir: str | None = None
    callbacks: list[Any] | None = None


__all__ = [
    "_SessionEntry",
    "AdapterDependencies",
    "map_status_to_domain",
    "_SDK_TERMINAL_TO_DOMAIN",
    "_TERMINAL_EVENT_KIND",
]
