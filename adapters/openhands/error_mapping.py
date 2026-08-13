"""OpenHands SDK 错误/事件 → Research OS PortError 映射。

SDK v1.42.0 错误模型为事件驱动：ConversationErrorEvent（含 ErrorClassification
闭集：AUTH/QUOTA/RATE_LIMIT/CONFIG/TRANSIENT/AGENT_ACTION/INTERNAL/UNKNOWN +
retryable 标志）。run() 不抛业务异常，错误经由事件流暴露，状态迁移为 ERROR。

本模块把 SDK 错误事件与兜底异常收敛为 PortError 层级；SDK 类型绝不越过边界。
"""

from __future__ import annotations

from openhands.sdk.event.conversation_error import ConversationErrorEvent
from openhands.sdk.event.error_classification import FailureKind
from openhands.sdk.event.llm_convertible.observation import AgentErrorEvent
from openhands.sdk.llm.exceptions import (
    LLMAuthenticationError,
    LLMBadRequestError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMTimeoutError,
)

from packages.application.ports.errors import (
    PermanentPortError,
    PortCancelledError,
    PortError,
    TransientPortError,
)
from packages.domain.enums import FailureCategory


def _category_for_kind(kind: FailureKind) -> FailureCategory | None:
    """SDK FailureKind → Research OS FailureCategory；取消类返回 None。"""
    mapping: dict[FailureKind, FailureCategory] = {
        FailureKind.AUTH: FailureCategory.MODEL_AUTH,
        FailureKind.QUOTA: FailureCategory.BUDGET_EXHAUSTED,
        FailureKind.RATE_LIMIT: FailureCategory.MODEL_RATE_LIMIT,
        FailureKind.CONFIG: FailureCategory.CONFIGURATION,
        FailureKind.TRANSIENT: FailureCategory.MODEL_RELAY_UNAVAILABLE,
        FailureKind.AGENT_ACTION: FailureCategory.TOOL_UNAVAILABLE,
        FailureKind.INTERNAL: FailureCategory.SYSTEM_BUG,
        FailureKind.UNKNOWN: FailureCategory.SYSTEM_BUG,
    }
    return mapping.get(kind)


def map_conversation_error_event(event: ConversationErrorEvent) -> PortError:
    """ConversationErrorEvent → PortError（run loop 顶层失败）。"""
    classification = event.classification
    category: FailureCategory = FailureCategory.SYSTEM_BUG
    retryable = False
    if classification is not None:
        category = _category_for_kind(classification.kind) or FailureCategory.SYSTEM_BUG
        retryable = classification.retryable
    message = f"{event.code}: {event.detail}"
    if retryable:
        return TransientPortError(message, failure_category=category)
    return PermanentPortError(message, failure_category=category)


# SDK ConversationRunError.original_exception 类型 → PortError 映射
# （SDK run() 双通道：事件 + 异常，见 M5_CORRECTIONS_LOG M6-2 修正）
def _category_for_llm_exception(exc: Exception) -> FailureCategory | None:
    if isinstance(exc, LLMAuthenticationError):
        return FailureCategory.MODEL_AUTH
    if isinstance(exc, LLMRateLimitError):
        return FailureCategory.MODEL_RATE_LIMIT
    if isinstance(exc, (LLMTimeoutError, LLMServiceUnavailableError)):
        return FailureCategory.MODEL_RELAY_UNAVAILABLE
    if isinstance(exc, LLMBadRequestError):
        return FailureCategory.CONFIGURATION
    return None


def map_conversation_run_error(
    exc: Exception,
    error_event: ConversationErrorEvent | None = None,
) -> PortError:
    """ConversationRunError → PortError（事件分类优先，其次原始异常类型）。

    SDK v1.42.0 run() 失败时同时发 ConversationErrorEvent 并抛
    ConversationRunError（original_exception 保留原始异常）。
    """
    if error_event is not None:
        return map_conversation_error_event(error_event)
    original = getattr(exc, "original_exception", None)
    if isinstance(original, Exception):
        category = _category_for_llm_exception(original)
        if category is not None:
            message = str(original) or original.__class__.__name__
            if category in {
                FailureCategory.MODEL_RATE_LIMIT,
                FailureCategory.MODEL_RELAY_UNAVAILABLE,
            }:
                return TransientPortError(message, failure_category=category)
            return PermanentPortError(message, failure_category=category)
    return PermanentPortError(
        str(exc) or exc.__class__.__name__,
        failure_category=FailureCategory.SYSTEM_BUG,
    )


def map_agent_error_event(event: AgentErrorEvent) -> PortError:
    """AgentErrorEvent → PortError（工具/agent 动作失败，可恢复）。"""
    tool_name = getattr(event, "tool_name", None)
    message = getattr(event, "message", None) or "agent tool error"
    detail = f"[{tool_name}] {message}" if tool_name else str(message)
    return PermanentPortError(detail, failure_category=FailureCategory.TOOL_UNAVAILABLE)


def map_unexpected_exception(exc: Exception) -> PortError:
    """兜底：未知异常收敛为永久失败（SDK 异常类型不传播）。"""
    return PermanentPortError(
        str(exc) or exc.__class__.__name__,
        failure_category=FailureCategory.SYSTEM_BUG,
    )


def port_cancelled(reason: str) -> PortCancelledError:
    """取消信号 → PortCancelledError（独立信号，不按 transient 重试）。"""
    return PortCancelledError(reason)


__all__ = [
    "map_conversation_error_event",
    "map_agent_error_event",
    "map_unexpected_exception",
    "port_cancelled",
]
