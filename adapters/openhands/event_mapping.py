"""OpenHands Event 树 → Research OS RuntimeEvent 归一化（纯函数）。

SDK 事件树与 RuntimeEvent 无 1:1（M5_PORT_COMPATIBILITY_MATRIX §1）；映射表
在 adapter 内显式定义。输出只包含 Port 类型；SDK 事件类型不越过本模块。

映射基准（M6_ADAPTER_DESIGN_NOTES §2 + SDK v1.42.0 event 树实测）：
- MessageEvent          → MESSAGE
- ActionEvent           → TOOL_CALL_REQUESTED（携带 tool_name/tool_call_id）
- ObservationEvent      → STEP_COMPLETED（携带 tool_name；工具结果）
- AgentErrorEvent       → STEP_COMPLETED（携带 tool_name + error 标记）
- ConversationErrorEvent→ SESSION_FAILED 前置（adapter 最终收敛状态）
- ConversationStateUpdateEvent → 按 execution_status 投影（PAUSED/STUCK/…）
- PauseEvent            → SESSION_PAUSED
- InterruptEvent        → SESSION_CANCELLED（中断即取消意图，显式收敛在 adapter）
- LLMCompletionLogEvent → 不产生 RuntimeEvent（走 usage_mapping → BudgetLedger）
- 其余（Token/StreamingDelta/Condensation/Hook…）→ 忽略（非业务投影）
"""

from __future__ import annotations

from collections.abc import Iterable

from openhands.sdk.event.base import Event
from openhands.sdk.event.conversation_error import ConversationErrorEvent
from openhands.sdk.event.conversation_state import ConversationStateUpdateEvent
from openhands.sdk.event.llm_convertible import (
    ActionEvent,
    MessageEvent,
    ObservationEvent,
)
from openhands.sdk.event.llm_convertible.observation import AgentErrorEvent
from openhands.sdk.event.user_action import InterruptEvent, PauseEvent

from packages.application.ports.agent_runtime import RuntimeEvent, RuntimeEventKind
from packages.domain.redaction import redact_exception_message


def _message_text(event: Event) -> str:
    llm_message = getattr(event, "llm_message", None)
    if llm_message is not None:
        content = getattr(llm_message, "content", None)
        if content is not None:
            return redact_exception_message(str(content)[:500])
        return redact_exception_message(str(llm_message)[:500])
    return redact_exception_message(str(getattr(event, "message", None) or "")[:500])


def _tool_call_requested(event: ActionEvent, session_id: str) -> RuntimeEvent:
    tool_name = getattr(event, "tool_name", "") or "unknown_tool"
    tool_call_id = str(getattr(event, "tool_call_id", "") or "")
    return RuntimeEvent(
        session_id=session_id,
        kind=RuntimeEventKind.TOOL_CALL_REQUESTED,
        message=tool_name,
        payload={"tool_name": tool_name, "tool_call_id": tool_call_id},
    )


def _step_completed(
    session_id: str,
    *,
    tool_name: str,
    tool_call_id: str = "",
    error: bool = False,
) -> RuntimeEvent:
    payload: dict[str, object] = {"tool_name": tool_name}
    if tool_call_id:
        payload["tool_call_id"] = tool_call_id
    if error:
        payload["error"] = True
    return RuntimeEvent(
        session_id=session_id,
        kind=RuntimeEventKind.STEP_COMPLETED,
        message=tool_name,
        payload=payload,
    )


def map_event(event: Event, session_id: str) -> tuple[RuntimeEvent, ...]:
    """单个 SDK 事件 → 0..n 个 RuntimeEvent（纯函数）。"""
    if isinstance(event, MessageEvent):
        text = _message_text(event)
        return (RuntimeEvent(session_id=session_id, kind=RuntimeEventKind.MESSAGE, message=text),)
    if isinstance(event, ActionEvent):
        return (_tool_call_requested(event, session_id),)
    if isinstance(event, AgentErrorEvent):
        tool_name = getattr(event, "tool_name", "") or "unknown_tool"
        return (
            _step_completed(
                session_id,
                tool_name=tool_name,
                tool_call_id=str(getattr(event, "tool_call_id", "") or ""),
                error=True,
            ),
        )
    if isinstance(event, ObservationEvent):
        tool_name = getattr(event, "tool_name", "") or "unknown_tool"
        return (
            _step_completed(
                session_id,
                tool_name=tool_name,
                tool_call_id=str(getattr(event, "tool_call_id", "") or ""),
            ),
        )
    if isinstance(event, ConversationErrorEvent):
        return (
            RuntimeEvent(
                session_id=session_id,
                kind=RuntimeEventKind.SESSION_FAILED,
                message=redact_exception_message(f"{event.code}: {event.detail}"[:500]),
            ),
        )
    if isinstance(event, ConversationStateUpdateEvent):
        return _map_state_update(event, session_id)
    if isinstance(event, PauseEvent):
        return (RuntimeEvent(session_id=session_id, kind=RuntimeEventKind.SESSION_PAUSED),)
    if isinstance(event, InterruptEvent):
        return (RuntimeEvent(session_id=session_id, kind=RuntimeEventKind.SESSION_CANCELLED),)
    return ()


def _map_state_update(
    event: ConversationStateUpdateEvent, session_id: str
) -> tuple[RuntimeEvent, ...]:
    value = event.value
    if not isinstance(value, dict):
        return ()
    status = str(value.get("execution_status") or value.get("executionStatus") or "")
    status_name = status.split(".")[-1].upper()
    if status_name in {"PAUSED", "PAUSE"}:
        return (RuntimeEvent(session_id=session_id, kind=RuntimeEventKind.SESSION_PAUSED),)
    if status_name == "STUCK":
        return (RuntimeEvent(session_id=session_id, kind=RuntimeEventKind.SESSION_STUCK),)
    if status_name in {"ERROR", "FAILED"}:
        return (RuntimeEvent(session_id=session_id, kind=RuntimeEventKind.SESSION_FAILED),)
    return ()


def map_event_stream(events: Iterable[Event], session_id: str) -> tuple[RuntimeEvent, ...]:
    """事件流 → RuntimeEvent 元组（保持顺序，单调追加）。"""
    mapped: list[RuntimeEvent] = []
    for event in events:
        mapped.extend(map_event(event, session_id))
    return tuple(mapped)


__all__ = ["map_event", "map_event_stream"]
