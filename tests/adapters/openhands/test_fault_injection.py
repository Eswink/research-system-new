"""OpenHands Adapter fault injection：错误分类与 secret redaction 边界。

覆盖：ConversationErrorEvent 分类（auth/timeout/quota/transient）、
未知异常收敛、SDK 类型零越过边界、redaction 语义、provider 类型泄漏
（ports 不 import openhands）。
"""

from __future__ import annotations

import pathlib

import pytest
from openhands.sdk.event.conversation_error import ConversationErrorEvent
from openhands.sdk.event.llm_convertible.observation import AgentErrorEvent

from adapters.openhands.error_mapping import (
    map_agent_error_event,
    map_conversation_error_event,
    map_unexpected_exception,
)
from packages.application.ports.errors import (
    PermanentPortError,
    PortError,
    TransientPortError,
)
from packages.domain.enums import FailureCategory


class TestErrorClassification:
    @pytest.mark.parametrize(
        ("code", "expected_type", "expected_category"),
        [
            ("LLMAuthenticationError", PermanentPortError, FailureCategory.MODEL_AUTH),
            ("LLMRateLimitError", TransientPortError, FailureCategory.MODEL_RATE_LIMIT),
            ("LLMTimeoutError", TransientPortError, FailureCategory.MODEL_RELAY_UNAVAILABLE),
            ("MaxBudgetReached", PermanentPortError, FailureCategory.BUDGET_EXHAUSTED),
            (
                "LLMServiceUnavailableError",
                TransientPortError,
                FailureCategory.MODEL_RELAY_UNAVAILABLE,
            ),
        ],
    )
    def test_conversation_error_classification(
        self, code: str, expected_type: type[PortError], expected_category: FailureCategory
    ) -> None:
        event = ConversationErrorEvent(source="environment", code=code, detail="boom")
        error = map_conversation_error_event(event)
        assert isinstance(error, expected_type)
        assert error.failure_category is expected_category
        assert error.retryable is (expected_type is TransientPortError)

    def test_unexpected_exception_is_permanent_system_bug(self) -> None:
        error = map_unexpected_exception(RuntimeError("weird sdk crash"))
        assert isinstance(error, PermanentPortError)
        assert error.failure_category is FailureCategory.SYSTEM_BUG
        assert error.retryable is False

    def test_agent_error_event_is_tool_failure(self) -> None:
        event = AgentErrorEvent(tool_name="x", tool_call_id="c-1", error="nope")
        error = map_agent_error_event(event)
        assert error.failure_category is FailureCategory.TOOL_UNAVAILABLE

    def test_sdk_exception_type_never_crosses_boundary(self) -> None:
        """SDK 异常类型不得出现在 Port 错误输出中。"""
        sdk_event = ConversationErrorEvent(source="environment", code="x", detail="y")
        error = map_unexpected_exception(Exception(str(sdk_event)))
        assert isinstance(error, PortError)
        assert not isinstance(error, ConversationErrorEvent)


class TestSecretRedaction:
    def test_api_key_redacted_in_error_message(self) -> None:
        event = ConversationErrorEvent(
            source="environment",
            code="LLMAuthenticationError",
            detail="invalid api key sk-live-secret-abc123",
        )
        error = map_conversation_error_event(event)
        assert "sk-live-secret-abc123" not in str(error)
        assert "sk-live-secret-abc123" not in repr(error)

    def test_ports_do_not_import_openhands(self) -> None:
        """provider 类型泄漏负测：ports 模块不得 import openhands/litellm。"""
        root = pathlib.Path(__file__).resolve().parents[2]
        ports_dir = root / "packages" / "application" / "ports"
        forbidden = ("openhands", "litellm", "lite_llm")
        for source in ports_dir.glob("*.py"):
            text = source.read_text(encoding="utf-8")
            assert not any(token in text for token in forbidden), f"leak in {source.name}"

    def test_domain_does_not_import_openhands(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[2]
        domain_dir = root / "packages" / "domain"
        forbidden = ("openhands", "litellm")
        for source in domain_dir.glob("*.py"):
            text = source.read_text(encoding="utf-8")
            assert not any(token in text for token in forbidden), f"leak in {source.name}"
