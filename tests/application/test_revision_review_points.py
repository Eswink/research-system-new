"""判词内容驱动改稿：`action_taken` 必须与它回应的评审点**不是无关**（GOAL-20261103-105 EC-04）。

**它补哪一格**：`AuthorResponse.action_taken` 此前只要求引用制品名
（`validate_action_references` 的判据 ①②）——「作者说按评审意见改了」与「改的内容与
那条意见**毫无关系**」在结构上不可分。本轮给同一个函数加判据 ③：`action_taken` 必须
与 `ReviewPoint.text` 共享至少一个**实词**（复用 `manuscript_quality.content_words`）。

**四条判据**（对应 EC-04 的 (i)–(iv)）：

1. **正例**：`action_taken` 含该 point 的一个实词 ⇒ 通过。
2. **反证**：毫无词重叠 ⇒ 判红，判词**指出是哪个 `point_id`**。
3. **反证**：把 `content_words` 换成恒空集 ⇒ 判据**全红**（证明它真在比词，不是恒真）。
4. **F-5 边界**：point 文本不含任何实词（`content_words(text) == frozenset()`）⇒
   **点名**说明该点不可比较，**不静默通过**（「空真不算通过」）。

**射程（措辞纪律，与产品 docstring 同一口径）**：这条判的是「回应与评审点**不是无关**」，
**不是**「回应**解决了**那个问题」。人工核对时必须按这个口径读 —— 一份「已修改
reproducibility 相关段落」的回应与一个讲 reproducibility 的评审点重叠，但正文可能一个
字都没改对。**判「解决了」仍需人评**，阶梯「复检」行的 `下一级` 因此仍然未达成。
"""

from __future__ import annotations

import pytest

from packages.application.deliverable.author_response import AuthorResponse, ResponseError
from packages.application.deliverable.manuscript_quality import content_words
from packages.application.run_orchestration.revision_assembly import (
    MANUSCRIPT_V2_NAME,
    validate_action_references,
)

#: 一条**有实词**的评审点（产品点表的形态：`ReviewPoint` 的四个字段）。
_POINT_TEXT = "the related work does not name the planning choice that differs between the arms"


class _Point:
    """`ReviewPoint` 的最小替身（本文件只读 `point_id` / `text` 两个字段）。"""

    def __init__(self, point_id: str, text: str) -> None:
        self.point_id = point_id
        self.text = text


def _answer(action: str, *, point_id: str = "P1") -> AuthorResponse:
    return AuthorResponse(point_id=point_id, response="ok", action_taken=action)


def _validated(action: str, points: tuple[object, ...], *, point_id: str = "P1") -> None:
    validate_action_references(
        (_answer(action, point_id=point_id),),
        known_names=frozenset({MANUSCRIPT_V2_NAME}),
        points=points,
    )


def test_an_action_that_names_a_word_from_its_point_passes() -> None:
    """**(i) 正例**：`action_taken` 含该 point 的一个实词（`planning`）⇒ 通过。"""
    _validated(
        f"named the planning choice in the related work; see {MANUSCRIPT_V2_NAME}",
        (_Point("P1", _POINT_TEXT),),
    )


def test_an_action_with_no_shared_word_names_the_point_id() -> None:
    """**(ii) 反证**：毫无词重叠 ⇒ 判红，且判词**指出 `point_id`**（不笼统说「回应无关」）。"""
    with pytest.raises(ResponseError) as caught:
        _validated(
            f"revised the section named in P1; see {MANUSCRIPT_V2_NAME}",
            (_Point("P1", _POINT_TEXT),),
        )
    message = str(caught.value)
    assert "P1" in message, message
    assert "shares no content word" in message, message
    # 判词必须带上那句原文（读者能一眼看出「无关」指的是哪一条）。
    assert "related work" in message, message


def test_the_criterion_really_compares_words(monkeypatch: pytest.MonkeyPatch) -> None:
    """**(iii) 反证**：把 `content_words` 换成恒空集 ⇒ 判据**全红**（证明它真在比词）。

    这条是「判据不是恒真」的机械证据：如果实施层把 `content_words` 换成恒空集，
    正例立刻变红（空集与任何集合的交集都为空 ⇒ 判负）。**注意方向**：恒空集让判据
    **更严**（所有点都「不可比较」⇒ 全红），而不是更松 —— 这正好证明它没有走
    「空就跳过」的偷懒分支。
    """
    import packages.application.run_orchestration.revision_assembly as module

    monkeypatch.setattr(module, "content_words", lambda _text: frozenset())
    with pytest.raises(ResponseError) as caught:
        _validated(
            f"named the planning choice; see {MANUSCRIPT_V2_NAME}",
            (_Point("P1", _POINT_TEXT),),
        )
    assert "no comparable content word" in str(caught.value), caught.value


def test_a_point_without_content_words_is_named_not_passed() -> None:
    """**(iv) F-5 边界**：point 文本不含任何实词 ⇒ **点名不可比较**，不静默通过。

    实测边界（F-5）：`content_words("It is to be or not") == frozenset()`（全停用词/短词）。
    按「空真不算通过」的纪律，这种情况必须是可观测的拒绝，而不是一个空交集恰好没判负。
    """
    assert content_words("It is to be or not") == frozenset(), "前提：该文本确实没有实词"
    with pytest.raises(ResponseError) as caught:
        _validated(
            f"did something; see {MANUSCRIPT_V2_NAME}",
            (_Point("P9", "It is to be or not"),),
            point_id="P9",
        )
    message = str(caught.value)
    assert "P9" in message, message
    assert "no comparable content word" in message, message


def test_an_answer_to_a_point_the_run_does_not_carry_is_named() -> None:
    """回应一条**本 run 没有的**评审点 ⇒ 点名拒绝（不是跳过）。

    没有这一条，「P99」这种编号会绕过重叠判据：点表里找不到它 ⇒ 若静默跳过，
    作者只要写一个不存在的编号就能免检 —— 那正是判据最容易被架空的地方。
    """
    with pytest.raises(ResponseError) as caught:
        _validated(
            f"named the planning choice; see {MANUSCRIPT_V2_NAME}",
            (_Point("P1", _POINT_TEXT),),
            point_id="P99",
        )
    assert "P99" in str(caught.value), caught.value


def test_without_points_the_earlier_two_criteria_are_unchanged() -> None:
    """`points=None` ⇒ 判据 ③ 不跑（既有调用点与既有判据**逐字不变**）。

    这是零回归的机械形态：`revision_closure_step` 传点表，而 `test_revision_closure.py`
    里那条直臂（不传 `points`）必须继续只看名字。
    """
    # 一句与任何评审点都无关的 action_taken —— 不传 points 时它必须通过（不抛即通过）。
    validate_action_references(
        (_answer(f"revised the section named in P1; see {MANUSCRIPT_V2_NAME}"),),
        known_names=frozenset({MANUSCRIPT_V2_NAME}),
    )


def test_the_two_earlier_criteria_still_fire_with_points_present() -> None:
    """判据 ①② 在传了点表之后**仍然先判**（顺序固定：空谈 / 编造 先于 无关）。"""
    with pytest.raises(ResponseError) as caught:
        _validated("nothing named here", (_Point("P1", _POINT_TEXT),))
    assert MANUSCRIPT_V2_NAME in str(caught.value), caught.value
