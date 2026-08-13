"""adapter-core 单测：error_mapping / event_mapping 纯函数 + 状态映射。"""

from __future__ import annotations

from openhands.sdk.conversation.state import ConversationExecutionStatus
from openhands.sdk.event.conversation_error import ConversationErrorEvent
from openhands.sdk.event.conversation_state import ConversationStateUpdateEvent
from openhands.sdk.event.llm_convertible import (
    ActionEvent,
    MessageEvent,
    ObservationEvent,
)
from openhands.sdk.event.llm_convertible.observation import AgentErrorEvent
from openhands.sdk.event.user_action import InterruptEvent, PauseEvent
from openhands.sdk.llm import Message, MessageToolCall, TextContent
from openhands.sdk.tool.schema import Observation

from adapters.openhands.error_mapping import (
    map_agent_error_event,
    map_conversation_error_event,
    map_unexpected_exception,
    port_cancelled,
)
from adapters.openhands.event_mapping import map_event, map_event_stream
from adapters.openhands.session_types import map_status_to_domain
from packages.application.ports.agent_runtime import RuntimeEventKind
from packages.application.ports.errors import (
    PermanentPortError,
    PortCancelledError,
    TransientPortError,
)
from packages.domain.enums import FailureCategory


class _PlainObservation(Observation):
    """判别联合的具体 Observation 子类（测试用，无副作用）；kind 自动生成。"""


class TestErrorMapping:
    def test_conversation_error_auth_maps_permanent_auth(self) -> None:
        event = ConversationErrorEvent(
            source="environment", code="LLMAuthenticationError", detail="bad key"
        )
        error = map_conversation_error_event(event)
        assert isinstance(error, PermanentPortError)
        assert error.failure_category is FailureCategory.MODEL_AUTH
        assert error.retryable is False

    def test_conversation_error_transient_retryable(self) -> None:
        event = ConversationErrorEvent(
            source="environment", code="LLMTimeoutError", detail="timed out"
        )
        error = map_conversation_error_event(event)
        assert isinstance(error, TransientPortError)
        assert error.failure_category is FailureCategory.MODEL_RELAY_UNAVAILABLE

    def test_conversation_error_quota_maps_budget(self) -> None:
        event = ConversationErrorEvent(
            source="environment", code="MaxBudgetReached", detail="budget gone"
        )
        error = map_conversation_error_event(event)
        assert isinstance(error, PermanentPortError)
        assert error.failure_category is FailureCategory.BUDGET_EXHAUSTED

    def test_agent_error_maps_tool_unavailable(self) -> None:
        event = AgentErrorEvent(
            tool_name="some_tool",
            tool_call_id="call-1",
            error="boom",
        )
        error = map_agent_error_event(event)
        assert isinstance(error, PermanentPortError)
        assert error.failure_category is FailureCategory.TOOL_UNAVAILABLE
        assert "some_tool" in str(error)

    def test_unexpected_exception_converges_to_system_bug(self) -> None:
        error = map_unexpected_exception(RuntimeError("weird sdk failure"))
        assert isinstance(error, PermanentPortError)
        assert error.failure_category is FailureCategory.SYSTEM_BUG
        assert error.retryable is False

    def test_port_cancelled_is_distinct_signal(self) -> None:
        error = port_cancelled("interrupted")
        assert isinstance(error, PortCancelledError)
        assert error.failure_category is None
        assert error.retryable is False


class TestEventMapping:
    def test_message_event_maps_to_message_kind(self) -> None:
        event = MessageEvent(
            source="user",
            llm_message=Message(role="user", content=[TextContent(text="hello")]),
        )
        mapped = map_event(event, "s1")
        assert len(mapped) == 1
        assert mapped[0].kind is RuntimeEventKind.MESSAGE
        assert "hello" in mapped[0].message

    def test_action_event_maps_to_tool_call_requested(self) -> None:
        event = ActionEvent(
            source="agent",
            thought=[],
            tool_name="echo",
            tool_call_id="call-9",
            tool_call=MessageToolCall(
                id="call-9",
                name="echo",
                arguments="{}",
                origin="completion",
            ),
            action=None,
            llm_response_id="resp-1",
        )
        mapped = map_event(event, "s1")
        assert len(mapped) == 1
        assert mapped[0].kind is RuntimeEventKind.TOOL_CALL_REQUESTED
        assert mapped[0].payload["tool_name"] == "echo"

    def test_observation_event_maps_to_step_completed(self) -> None:
        event = ObservationEvent(
            source="environment",
            tool_name="echo",
            tool_call_id="call-9",
            observation=_PlainObservation(content=[TextContent(text="result")]),
            action_id="act-1",
        )
        mapped = map_event(event, "s1")
        assert len(mapped) == 1
        assert mapped[0].kind is RuntimeEventKind.STEP_COMPLETED
        assert mapped[0].payload["tool_name"] == "echo"

    def test_agent_error_event_marks_step_error(self) -> None:
        event = AgentErrorEvent(
            tool_name="echo",
            tool_call_id="call-9",
            error="failed",
        )
        mapped = map_event(event, "s1")
        assert len(mapped) == 1
        assert mapped[0].kind is RuntimeEventKind.STEP_COMPLETED
        assert mapped[0].payload["error"] is True

    def test_pause_and_interrupt_events(self) -> None:
        assert map_event(PauseEvent(source="user"), "s1")[0].kind is RuntimeEventKind.SESSION_PAUSED
        assert (
            map_event(InterruptEvent(source="user"), "s1")[0].kind
            is RuntimeEventKind.SESSION_CANCELLED
        )

    def test_state_update_maps_paused_and_stuck(self) -> None:
        paused = ConversationStateUpdateEvent(
            key="full_state",
            value={"execution_status": ConversationExecutionStatus.PAUSED.value},
        )
        stuck = ConversationStateUpdateEvent(
            key="full_state",
            value={"execution_status": ConversationExecutionStatus.STUCK.value},
        )
        assert map_event(paused, "s1")[0].kind is RuntimeEventKind.SESSION_PAUSED
        assert map_event(stuck, "s1")[0].kind is RuntimeEventKind.SESSION_STUCK

    def test_unrelated_events_are_ignored(self) -> None:
        event = MessageEvent(
            source="user",
            llm_message=Message(role="user", content=[TextContent(text="x")]),
        )
        mapped = map_event_stream([event], "s1")
        assert len(mapped) == 1

    def test_conversation_error_event_maps_failed(self) -> None:
        event = ConversationErrorEvent(source="environment", code="LLMTimeoutError", detail="late")
        mapped = map_event(event, "s1")
        assert mapped[0].kind is RuntimeEventKind.SESSION_FAILED


class TestStatusMapping:
    def test_all_sdk_statuses_map_explicitly(self) -> None:
        assert map_status_to_domain(ConversationExecutionStatus.IDLE) == "CREATED"
        assert map_status_to_domain(ConversationExecutionStatus.RUNNING) == "RUNNING"
        assert map_status_to_domain(ConversationExecutionStatus.PAUSED) == "PAUSED"
        assert (
            map_status_to_domain(ConversationExecutionStatus.WAITING_FOR_CONFIRMATION)
            == "WAITING_FOR_APPROVAL"
        )
        assert map_status_to_domain(ConversationExecutionStatus.FINISHED) == "SUCCEEDED"
        assert map_status_to_domain(ConversationExecutionStatus.ERROR) == "FAILED"
        assert map_status_to_domain(ConversationExecutionStatus.STUCK) == "STUCK"
        assert map_status_to_domain(ConversationExecutionStatus.DELETING) == "FAILED"
