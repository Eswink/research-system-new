"""引用充分性的结构读数（GOAL-20261103-105 EC-01）。

**它补哪一格**：`MANUSCRIPT_QUALITY.md` §7 把 `NOT_JUDGED` 第 4 项判成「可机械判（弱口径）
但本轮不实现」，理由是「阈值需要先有真实语料标定」。本模块把**读数**做出来、阈值留 `None`
—— 所以这一格的判据必须同时钉住**读数真的成立**与**没有偷偷拍阈值**。

**四条判据**（对应 EC-01 的 (i)–(iv)）：

1. **三个读数各有正例**：3 句 / 4 条引用 / 其中 1 条单支撑的夹具，逐项等于期望值。
2. **反证**：同一份正文加一条引用 ⇒ 「每句引用数」与「条目被引次数」**都随之变**
   （证明读数真从字节来，不是硬编码）。
3. **反证**：`enforce=False` 时一份「每句 0 引用」的正文**不抛错**（读数不是判负）。
4. **三个常量默认全部 `None`**，且非 `None` 时必须在 `CALIBRATION_SOURCES` 里有来源、
   且该来源出现在模块 docstring 里（「不得拍阈值」的机械形态）。

另有一条**语法同源**判据：本模块的引用正则与 `manuscript.CITATION_PATTERN` /
`manuscript_quality._CITATION` 同形 —— 三份实现（两份产品 + 本模块复用）不许漂。
"""

from __future__ import annotations

import re

import pytest

from packages.application.deliverable import citation_sufficiency as cs
from packages.application.deliverable.manuscript import CITATION_PATTERN
from packages.application.deliverable.manuscript_quality import _CITATION, NOT_JUDGED

#: 夹具：3 句（introduction，第 2 句带两个引用）/ 4 条被引条目（1、2、3、4）/
#: 其中 `methods` 是**单支撑节**（唯一引用 [4]、在该节出现一次、全稿也只出现一次）。
#: 逐项期望值：introduction = (1, 2, 0)；results = (1,)；discussion = (1,)。
_SECTIONS = {
    "title": "A study",
    "abstract": "We report a result.",
    "introduction": "Alpha [1]. Beta [2] and [3]. Gamma.",
    "related_work": "Prior work exists.",
    "methods": "We used the pipeline [4].",
    "results": "The measurement held [1].",
    "discussion": "It follows [2].",
    "conclusion": "It holds.",
}


def test_the_three_readings_match_their_expected_values() -> None:
    """**(i) 正例**：三个读数逐项等于期望值（不是「非空」那种弱断言）。"""
    readings = cs.measure_citation_sufficiency(_SECTIONS)

    assert [(item.section, item.index, item.marks) for item in readings.per_sentence] == [
        ("introduction", 1, 1),
        ("introduction", 2, 2),
        ("introduction", 3, 0),
        ("results", 1, 1),
        ("discussion", 1, 1),
    ]
    assert dict(readings.per_reference) == {1: 2, 2: 2, 3: 1, 4: 1}
    assert readings.single_support_sections == ("methods",), (
        "methods 只引 [4] 一次，且 [4] 全稿只被引一次 ⇒ 它是单支撑节"
    )


def test_adding_one_citation_moves_both_readings() -> None:
    """**(ii) 反证**：加一条引用 ⇒ 逐句读数**与**条目计数**都**变（读数从字节来）。

    这条判据的形状是关键：它**不**断言某个具体数值，而是断言「同一份正文改一个字符 ⇒
    两个读数都动」。硬编码的读数（返回常量 / 缓存）在这里必然红。
    """
    before = cs.measure_citation_sufficiency(_SECTIONS)
    mutated = dict(_SECTIONS)
    # 在第 3 句（此前 0 个标记）末尾加一条引用，编号用一个**新的** [5]。
    mutated["introduction"] = "Alpha [1]. Beta [2] and [3]. Gamma [5]."
    after = cs.measure_citation_sufficiency(mutated)

    assert before.per_sentence != after.per_sentence, "逐句读数必须随字节变"
    assert before.per_reference != after.per_reference, "条目计数必须随字节变"
    # 具体变化也对得上：第 3 句 0 → 1；[5] 从「不存在」变成「被引 1 次」。
    third_before = before.per_sentence[2]
    third_after = after.per_sentence[2]
    assert (third_before.marks, third_after.marks) == (0, 1)
    assert 5 not in before.per_reference and after.per_reference[5] == 1


def test_a_body_with_no_marks_is_not_an_error_when_not_enforcing() -> None:
    """**(iii) 反证**：`enforce=False` 时「每句 0 引用」的正文**不抛错**。

    读数不是判负：一份没有引用的正文在这里是**一份有读数的**正文。若这条判据红，
    说明有人把「读数」升级成了「判据」—— 那正是 §7 明令禁止的冒充。
    """
    empty = {
        "introduction": "No citation at all.",
        "results": "Still none.",
        "discussion": "Nor here.",
    }
    readings = cs.measure_citation_sufficiency(empty)  # 缺省 enforce=False
    assert all(item.marks == 0 for item in readings.per_sentence)
    assert dict(readings.per_reference) == {}
    assert readings.single_support_sections == ()
    # 零引用的句子是**读数的一部分**（可读），不是异常。
    assert len(readings.sentences_without_marks) == 3


def test_enforcing_with_no_threshold_still_does_not_judge() -> None:
    """`enforce=True` 但阈值全 `None` ⇒ 仍然什么都不判（阈值才是判负的唯一来源）。"""
    empty = {"introduction": "No citation at all."}
    readings = cs.measure_citation_sufficiency(empty, enforce=True)
    assert readings.per_sentence[0].marks == 0


def test_all_three_thresholds_are_none_by_default() -> None:
    """**(iv)** 三个常量缺省**全部 `None`** —— 仓内零真实语料，不得拍阈值。"""
    assert cs.MIN_MARKS_PER_SENTENCE is None
    assert cs.MIN_CITATIONS_PER_REFERENCE is None
    assert cs.MIN_SUPPORT_PER_SECTION is None
    assert cs.uncalibrated_thresholds() == ()


def test_a_threshold_without_a_calibration_source_is_named(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**(iv) 反向**：把某个阈值填上但**不给标定来源** ⇒ `uncalibrated_thresholds()` 点名它。

    这是「填值本身可以，但必须有来源」的机械形态。两个方向都按：给了来源且写进 docstring
    ⇒ 空；没给来源 ⇒ 点名那个常量名。
    """
    monkeypatch.setitem(cs._THRESHOLDS, "MIN_MARKS_PER_SENTENCE", 2)
    assert cs.uncalibrated_thresholds() == ("MIN_MARKS_PER_SENTENCE",), (
        "填了值却没有标定来源 ⇒ 必须点名它"
    )
    monkeypatch.setitem(cs.CALIBRATION_SOURCES, "MIN_MARKS_PER_SENTENCE", "three real manuscripts")
    # 来源在映射里但**不在 docstring 里** ⇒ 仍然点名（来源必须是可读的、不是一句私货）。
    assert cs.uncalibrated_thresholds() == ("MIN_MARKS_PER_SENTENCE",)


def test_the_three_names_are_the_ones_the_spec_declares() -> None:
    """名字是**合约**（GOAL 正文与文档逐字引用它们）⇒ 改名要同轮改文档与判据。"""
    assert {
        "MIN_MARKS_PER_SENTENCE",
        "MIN_CITATIONS_PER_REFERENCE",
        "MIN_SUPPORT_PER_SECTION",
    } <= set(cs.CALIBRATION_SOURCES)


def test_the_citation_grammar_is_the_same_one() -> None:
    """本模块的引用正则与手稿模块**同形**（不写第四份语法）。"""
    probe = "Alpha [1]. Beta [23]. Gamma [not-a-mark]."
    assert [m.group(1) for m in cs._CITATION.finditer(probe)] == [
        m.group(1) for m in CITATION_PATTERN.finditer(probe)
    ]
    assert [m.group(1) for m in cs._CITATION.finditer(probe)] == [
        m.group(1) for m in _CITATION.finditer(probe)
    ]
    # 三者的 pattern 逐字相同（不只是"等价"）：改一处就必须同轮改三处。
    assert cs._CITATION.pattern == CITATION_PATTERN.pattern == _CITATION.pattern
    assert isinstance(cs._CITATION, re.Pattern)


def test_the_fifth_item_stays_in_not_judged() -> None:
    """**第 4 项仍留在 `NOT_JUDGED` 里** —— 有读数 ≠ 判了「充分」。

    移出它会让 `test_nothing_was_implemented_under_the_cover_of_the_argument` 的
    `len(NOT_JUDGED) == 5` 判红，而那是**冒充**。这条判据把「不许冒充」钉在**本模块**
    的判据面上：将来有人为了让第 4 项「看起来已实现」而删它，这里先红。
    """
    assert len(NOT_JUDGED) == 5
    assert any("sufficient" in item for item in NOT_JUDGED), (
        "「引用是否充分」必须仍在 NOT_JUDGED 里：本模块只产读数"
    )


def test_a_single_support_section_needs_all_three_conditions() -> None:
    """读数 3 的三条条件缺一不算（反向按压：每个条件单独破坏一次）。"""
    # ① 该节引了两个编号 ⇒ 不是单支撑（即使两个都只出现一次）。
    two_refs = dict(_SECTIONS)
    two_refs["methods"] = "We used the pipeline [4] and [7]."
    assert "methods" not in cs.single_support_sections(two_refs)
    # ③ 该编号在全稿被引多次 ⇒ 不是单支撑（先让 discussion 也引 [4]）。
    reused = dict(_SECTIONS)
    reused["discussion"] = "It follows [4]."
    assert "methods" not in cs.single_support_sections(reused)
    # 原夹具正面成立（与上面两条构成两向）。
    assert cs.single_support_sections(_SECTIONS) == ("methods",)
