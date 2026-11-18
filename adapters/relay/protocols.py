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


def request_headers(
    protocol: str,
    credential: SecretValue,
    extra_headers: tuple[tuple[str, str], ...] = (),
) -> dict[str, str]:
    """按协议构造鉴权头（未知协议同样 fail-closed）。

    `extra_headers` 是**非凭据**的静态头（如中转站要求的路由/会话头），在鉴权头之后
    **追加**；与鉴权头同名时**点名拒绝**（静默覆盖会让「凭据只从 credential_ref 来」
    变成假象）。域对象已在构造期拒过一遍，这里是第二道 —— 两条腿都经过本函数，
    而域校验只保证「存进去的值合法」，不保证「调用方没在运行期另塞一份」。
    """
    known = _known_protocol(protocol)
    if known is LLMProtocol.ANTHROPIC:
        headers = {
            "x-api-key": credential.value,
            "anthropic-version": ANTHROPIC_VERSION,
            "Accept": _DEFAULT_ACCEPT,
        }
    else:
        headers = {"Authorization": f"Bearer {credential.value}", "Accept": _DEFAULT_ACCEPT}
    return {**headers, **_checked_extra_headers(extra_headers, headers)}


def _checked_extra_headers(
    extra_headers: tuple[tuple[str, str], ...],
    base: dict[str, str],
) -> dict[str, str]:
    """静态头的第二道校验：不得与鉴权头重名（大小写不敏感）。"""
    taken = {name.lower() for name in base}
    for name, _value in extra_headers:
        if name.lower() in taken:
            raise RelayHTTPError(
                FailureCategory.MODEL_INCOMPATIBLE,
                f"extra_headers must not override a credential header: {name!r}",
            )
    return dict(extra_headers)


__all__ = [
    "ANTHROPIC_VERSION",
    "WireShape",
    "request_headers",
    "select_wire_shape",
]
