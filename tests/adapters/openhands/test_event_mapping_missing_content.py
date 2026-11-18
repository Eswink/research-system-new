"""EC-03 ①：`MessageEvent` **没有 `content` 属性**时不得抛 `AttributeError`。

**它补哪一格**（GOAL-20261119-115 建档实测）：24 次 `dual_model_review` FAILED 里有
**7 次**是 `'MessageEvent' object has no attribute 'content'` —— author 会话在映射事件时
崩溃，run 根本没走到评审。修法是 `event_mapping` 用 `getattr(llm_message, "content", None)`，
但**没有任何判据钉住它**：改回直接属性访问，全仓不会红。

**关键实测**（2026-11-20 在本机确认）：真实 `MessageEvent` 的字段是
`id / timestamp / source / parent_id / llm_message / llm_response_id / …` ——
**没有 `content`**。所以「以为事件自己有 content」不是假想形态，就是这个 SDK 版本的事实。

**判什么**（三种缺失形态，每一种都必须「不抛」且不编造正文）：

1. `event.llm_message` 为 `None`；
2. `llm_message` 存在但**没有 `content` 属性**（用一个只有 `role` 的替身）；
3. `content` 属性存在但值为 `None`。

**反证臂**：直接 `event.content` / `llm_message.content` 必须抛 `AttributeError`
（证明 `getattr` 不是装饰）。
"""

from __future__ import annotations

from typing import Any

import pytest
from openhands.sdk.event.llm_convertible import MessageEvent
from openhands.sdk.llm import Message, TextContent

from adapters.openhands.event_mapping import map_event_stream


class _NoContentLLMMessage:
    """**没有 `content` 属性**的 llm_message（SDK 形态漂移的最小复现）。"""

    role = "assistant"


def _event(llm_message: Any) -> Any:
    """真实 `MessageEvent`，只把 `llm_message` 换成受判形态。

    用 `model_construct` 绕过校验：本判据要测的是**映射函数的容错**，
    不是 SDK 的构造校验（后者会在更早的地方挡住，测不到缺陷）。
    """
    return MessageEvent.model_construct(
        source="agent",
        llm_message=llm_message,
        llm_response_id=None,
        activated_skills=None,
        extended_content=None,
        sender=None,
        critic_result=None,
    )


def _mapped_texts(event: Any) -> list[str]:
    """跑**真实映射入口**，取它投影出的 MESSAGE 正文（不绕过产品代码）。"""
    events = map_event_stream([event], session_id="s-1")
    return [item.message for item in events if item.message is not None]


class TestTheSdkShapeThatCausedTheCrash:
    """先把「缺陷的前提」判掉：真实事件确实没有顶层 `content`。"""

    def test_a_real_message_event_has_no_top_level_content(self) -> None:
        event = MessageEvent.model_construct(
            source="agent",
            llm_message=Message(role="assistant", content=[TextContent(text="x")]),
            llm_response_id=None,
            activated_skills=None,
            extended_content=None,
            sender=None,
            critic_result=None,
        )
        assert not hasattr(event, "content"), (
            "本 SDK 版本给 MessageEvent 加了 content —— 缺陷前提变了，需重新取证"
        )


class TestAMissingContentNeverRaises:
    @pytest.mark.parametrize(
        ("label", "llm_message"),
        [
            ("llm_message-is-none", None),
            ("llm_message-has-no-content", _NoContentLLMMessage()),
        ],
        ids=["none-message", "no-content-attribute"],
    )
    def test_mapping_does_not_raise(self, label: str, llm_message: Any) -> None:
        texts = _mapped_texts(_event(llm_message))
        assert isinstance(texts, list), (label, texts)

    @pytest.mark.parametrize(
        ("label", "llm_message"),
        [
            ("llm_message-is-none", None),
            ("llm_message-has-no-content", _NoContentLLMMessage()),
        ],
        ids=["none-message", "no-content-attribute"],
    )
    def test_the_result_does_not_invent_content(self, label: str, llm_message: Any) -> None:
        """不得把 `None` / repr 当正文（那会让下游以为"模型说了话"）。"""
        for text in _mapped_texts(_event(llm_message)):
            assert "NoContentLLMMessage" not in text, (label, text)

    def test_a_content_none_message_is_also_tolerated(self) -> None:
        llm_message = Message.model_construct(role="assistant", content=None)
        _mapped_texts(_event(llm_message))  # 不抛即通过


class TestTheCriterionBites:
    """**反证臂**：直接属性访问必须抛 —— `getattr` 不是装饰。"""

    def test_direct_attribute_access_raises_on_the_no_content_stub(self) -> None:
        with pytest.raises(AttributeError):
            _ = _NoContentLLMMessage().content  # type: ignore[attr-defined]  # noqa: B018

    def test_direct_attribute_access_raises_on_the_real_event(self) -> None:
        with pytest.raises(AttributeError):
            _ = _event(None).content  # noqa: B018

    def test_the_stub_really_lacks_the_attribute(self) -> None:
        assert not hasattr(_NoContentLLMMessage(), "content"), (
            "替身必须有 content 才能证明 getattr 的必要性 —— 现在它有，反证臂空转"
        )
