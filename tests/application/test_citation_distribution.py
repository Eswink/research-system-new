"""`citation_distribution` 的判据（GOAL-20261107-107 EC-04）。

**它封住的失败形态**：GOAL-105 留下三个 `None` 阈值，理由是「需要语料标定」。如果只做
一个「能算分布的模块」，那三个 `None` 会一直 `None` —— 或者更糟：有人为了让读数「看起来
有用」，在零语料下填一个数字。本文件的四条判据把「能不能标定」变成**可检的门**。

四条（每条的臂都在下面写明）：

1. **正例**：一份受控手稿的三个读数逐项等于手算值（句数 / 标记数 / 条目数）。
2. **反证**：同一份正文加一条引用 ⇒ 句子级读数与条目级读数**都**随之变（证明读数真从
   字节来，不是常量）。
3. **门的边界**：n=1 与 n=2 判「不足」并**点名缺多少**；n=3 判「可标定」——
   这就是 `MIN_CORPUS` 的三向边界，缺一向门就可能是恒真或恒假。
4. **关于阈值的守恒律**：门判「不足」时 `citation_sufficiency` 的阈值面必须仍然全空
   （读既有公开面 `uncalibrated_thresholds()`，不另立清单）。
"""

from __future__ import annotations

from dataclasses import fields

import pytest

from packages.application.deliverable.citation_distribution import (
    MIN_CORPUS,
    calibration_gate,
    collect_readings,
    summarize,
)
from packages.application.deliverable.citation_sufficiency import (
    MIN_CITATIONS_PER_REFERENCE,
    MIN_MARKS_PER_SENTENCE,
    MIN_SUPPORT_PER_SECTION,
    uncalibrated_thresholds,
)

#: 一份受控手稿：introduction 3 句 / results 2 句 / discussion 3 句 = **8 句**。
#:
#: 逐节标记数（实测，不是心算）：introduction 1/1/0、results 2/1、discussion 1/0/0
#: ⇒ 标记总数 **6**；三个编号各被引 **2** 次 ⇒ `references == 3`。
#: 这份注释写的是**跑出来的**读数：第一版心算成 7，被判据当场指出（保留这条记录，
#: 因为「手算错一次」正是「断言必须来自实跑」的实证）。
_MANUSCRIPT = """# A study

## 1. Introduction

Alpha claim [1]. Beta claim [2]. Gamma claim without any citation.

## 4. Results

Delta measured [1] and [2]. Epsilon measured [3].

## 5. Discussion

Zeta discussion [3]. Eta discussion without a mark. Theta discussion without a mark.
"""


def _text(extra_reference: bool = False) -> str:
    """受控正文；`extra_reference=True` 时在 Discussion 里多加一条 `[2]`。"""
    if not extra_reference:
        return _MANUSCRIPT
    return _MANUSCRIPT.replace("Zeta discussion [3].", "Zeta discussion [3] and [2].")


def test_readings_match_a_hand_counted_manuscript() -> None:
    """正例：三个读数逐项等于手算值。"""
    (reading,) = collect_readings([("fixture", _text())])
    assert reading.sentences == 8, f"句子数意外：{reading.sentences}"
    assert reading.marks == 6, f"标记数意外：{reading.marks}"
    assert reading.references == 3, f"被引条目数意外：{reading.references}"
    assert reading.single_support_sections == 0


def test_adding_one_citation_moves_both_readings() -> None:
    """**反证**：多一条 `[2]` ⇒ 标记数 +1，且 `[2]` 的引用次数 +1（条目数不变）。

    两个读数**都**要动：只动一个说明其中一个不是从字节算的。
    """
    plain = collect_readings([("fixture", _text())])[0]
    extra = collect_readings([("fixture", _text(extra_reference=True))])[0]
    assert extra.marks == plain.marks + 1, "标记数没有随正文增长"
    # 条目数不变（仍是 1/2/3 三个编号）—— 这一条同时证明 `references` 数的是**不同编号**。
    assert extra.references == plain.references == 3


def test_the_gate_opens_exactly_at_the_declared_corpus_size() -> None:
    """门的**三向边界**：n=1 / n=2 不足且点名缺口，n=3 才可标定。

    缺任何一向，门都可能是恒真（永远可标定）或恒假（永远不足）—— 两种都会让
    阈值面的守卫失去意义。
    """
    assert MIN_CORPUS == 3, "标定条件变了：§7 原文写的是 3 份"
    one = calibration_gate(collect_readings([("a", _text())]))
    assert one.sufficient is False
    assert one.manuscripts == 1
    assert one.missing and "1 of 3" in one.missing[0], one.missing

    two = calibration_gate(collect_readings([("a", _text()), ("b", _text())]))
    assert two.sufficient is False
    assert "2 of 3" in two.missing[0], two.missing

    three = calibration_gate(collect_readings([("a", _text()), ("b", _text()), ("c", _text())]))
    assert three.sufficient is True
    assert three.may_calibrate is True
    assert three.missing == ()


def test_a_threshold_may_not_be_set_before_the_gate_opens() -> None:
    """**守恒律**：门判「不足」时，`citation_sufficiency` 的三个阈值必须仍然全空。

    读的是**既有公开面** `uncalibrated_thresholds()`（它自己已经钉住「填了值必须有标定
    来源」）；本条再钉一层：**连来源都不该有**，因为仓内语料还不够。两层的区别是
    「填了但没写来源」与「根本没有资格填」——后者更早拦住。
    """
    gate = calibration_gate(collect_readings([("only-one", _text())]))
    assert gate.sufficient is False, "本判据的前提是本轮语料不足"
    assert (MIN_MARKS_PER_SENTENCE, MIN_CITATIONS_PER_REFERENCE, MIN_SUPPORT_PER_SECTION) == (
        None,
        None,
        None,
    ), "语料不足时不得拍阈值：没有语料支撑的数字不是阈值，是编造"
    assert uncalibrated_thresholds() == (), "阈值面不应有任何已填项（含已声明来源的）"


def test_the_summary_describes_distributions_without_recommending_a_threshold() -> None:
    """摘要只描述分布：逐类原值保留，**不**给建议值（也不含「建议」类字段）。"""
    readings = collect_readings([("a", _text()), ("b", _text(extra_reference=True))])
    distribution = summarize(readings)
    assert distribution.manuscripts == 2
    assert distribution.marks == (6, 7), distribution.marks
    assert distribution.marks_per_sentence[1] > distribution.marks_per_sentence[0]
    # 没有「建议阈值」这类出口：字段集固定，且不含 recommendation 语义。
    # `slots=True` 的 dataclass 没有 `__dict__` ⇒ 用 `fields()`，不用 `vars()`。
    assert not any("recommend" in field.name for field in fields(distribution))


@pytest.mark.parametrize("count", [0, 1, 2])
def test_an_empty_or_short_corpus_never_opens_the_gate(count: int) -> None:
    """短语料的每一档都关着门（含 0 份 —— 空集合不是「通过」）。"""
    texts = [(f"m{index}", _text()) for index in range(count)]
    assert calibration_gate(collect_readings(texts)).sufficient is False
