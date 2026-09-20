"""线协议选路面（gateway 私有拆分）。

`endpoint.protocol` 决定线上形态：

- ``OPENAI_COMPATIBLE`` ⇒ 按 ``api_style`` 分 ``chat_completions`` / ``responses``；
- ``ANTHROPIC`` ⇒ Messages 形态（``/messages``）。

鉴权头同样按协议构造：OpenAI-compatible 用 ``Authorization: Bearer``；
Messages 形态用 ``x-api-key`` + ``anthropic-version``（**不**发送 ``Authorization``）。

未知协议 **fail-closed**：不静默回退到 OpenAI 形态——静默回退会让「配了某种协议」与
「实际跑的是另一种形态」不可区分（与 runtime 选择面的裁定同构，GOAL-007 EC-01）。
"""

from __future__ import annotations

from enum import StrEnum

from adapters.relay.transport import RelayHTTPError
from packages.application.ports import SecretValue
from packages.domain.enums import FailureCategory, LLMProtocol

#: Messages 形态要求的版本头（Anthropic Messages API 公开版本标识）。
ANTHROPIC_VERSION = "2023-06-01"
_DEFAULT_ACCEPT = "application/json"


class WireShape(StrEnum):
    """线上请求形态（由 protocol 与 api_style 共同决定）。"""

    CHAT_COMPLETIONS = "chat_completions"
    RESPONSES = "responses"
    ANTHROPIC_MESSAGES = "anthropic_messages"


def _known_protocol(protocol: str) -> LLMProtocol:
    try:
        return LLMProtocol(protocol)
    except ValueError as exc:
        legal = ", ".join(sorted(member.value for member in LLMProtocol))
        raise RelayHTTPError(
            FailureCategory.MODEL_INCOMPATIBLE,
            f"unsupported endpoint protocol: {protocol!r} (expected one of: {legal})",
        ) from exc


def select_wire_shape(protocol: str, api_style: str) -> WireShape:
    """按协议（与 api_style）选线形态；未知协议抛 RelayHTTPError（不发起请求）。"""
    known = _known_protocol(protocol)
    if known is LLMProtocol.ANTHROPIC:
        return WireShape.ANTHROPIC_MESSAGES
    if api_style == "responses":
        return WireShape.RESPONSES
    return WireShape.CHAT_COMPLETIONS


def request_headers(protocol: str, credential: SecretValue) -> dict[str, str]:
    """按协议构造鉴权头（未知协议同样 fail-closed）。"""
    known = _known_protocol(protocol)
    if known is LLMProtocol.ANTHROPIC:
        return {
            "x-api-key": credential.value,
            "anthropic-version": ANTHROPIC_VERSION,
            "Accept": _DEFAULT_ACCEPT,
        }
    return {"Authorization": f"Bearer {credential.value}", "Accept": _DEFAULT_ACCEPT}


__all__ = ["ANTHROPIC_VERSION", "WireShape", "request_headers", "select_wire_shape"]
