"""GOAL-20261012-062（序 30）：**冲突声明不再是一扇单向门** —— EC-02 / EC-03 的判据。

**为什么单列**：本轮的靶子（**被声明方**那一侧）自成一组；与 `test_conflict_timeliness.py`
（序 29 的声明时效）/ `test_conflict_resolution_*`（序 26 的消解）**分工不同** ——
那些判**声明方**那一侧，本组判**被声明方**。

**判的是什么**：`contradictions` 是**单方向**的声明 —— A 声明与 B 冲突 ⇒ **B 那侧读不出来**
（实测：B 侧 `contradictions=[]`、无反向键、`disposition=USE` 照用）。本轮补**反向索引**
（与序 18 的 `superseded_by_index` **同一手法**）与**处置面分派**（同类不同因）。

**两件事各自点名**：`conflicted`（自己声明）与 `conflicted_by`（被别人声明）**同类不同因**
（都落 `CONFLICTED`），判词必须点得出是哪一种。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.application.memory.disposition import (
    DISPOSITION_CONFLICTED,
    DISPOSITION_USE,
    conflicted_by_index,
    disposition_of,
    disposition_reason,
)


@dataclass
class _Row:
    """极小的记录替身（判据只读三个字段 —— 不构造整条 canonical 记录）。"""

    id: str
    contradictions: list[str] = field(default_factory=list)
    expires_at: Any = None
    review_after: Any = None


def test_the_reverse_index_reports_who_declared_a_conflict() -> None:
    """EC-02 ①：反向索引**报出声明方**（`被声明的 id → [声明方, …]`）。"""
    records = (_Row(id="m-a", contradictions=["m-b"]), _Row(id="m-b"))
    assert conflicted_by_index(records) == {"m-b": ["m-a"]}


def test_the_reverse_index_is_empty_when_nobody_declared() -> None:
    """EC-02 ②：**没人声明** ⇒ 空表（缺省形态逐字不变的前提）。"""
    records = (_Row(id="m-a"), _Row(id="m-b"))
    assert conflicted_by_index(records) == {}


def test_the_reverse_index_collects_several_declarers() -> None:
    """EC-02 ③：**多个声明方**逐个收集（不静默只留一个 —— 那会让读者漏看分歧）。"""
    records = (
        _Row(id="m-a", contradictions=["m-c"]),
        _Row(id="m-b", contradictions=["m-c"]),
        _Row(id="m-c"),
    )
    assert conflicted_by_index(records) == {"m-c": ["m-a", "m-b"]}


def test_being_declared_against_produces_conflicted_not_use() -> None:
    """EC-02 ④：**被别人声明冲突** ⇒ `CONFLICTED`（改动前是 `USE` —— 本轮的核心缺口）。"""
    assert disposition_of(None, conflicted_by=True) == DISPOSITION_CONFLICTED


def test_the_default_disposition_is_verbatim_when_nobody_declared() -> None:
    """EC-02 ⑤：**没人声明** ⇒ 逐字仍是 `USE`（缺省形态逐字不变）。"""
    assert disposition_of(None) == DISPOSITION_USE
    assert disposition_of(None, conflicted=False, conflicted_by=False) == DISPOSITION_USE


def test_the_two_causes_are_distinguishable_in_the_reason() -> None:
    """EC-02 ⑥：两种成因**同类不同因** —— 判词点得出是**哪一种**。

    受判面 = **两个形态**（自己声明 / 被别人声明）—— 少一个即「可区分」不成立。
    """
    own = disposition_reason(None, _Row(id="m-a", contradictions=["m-b"]))
    other = disposition_reason(None, _Row(id="m-b"), conflicted_by=["m-a"])
    assert "声明与 m-b 冲突" in own, own
    assert "被 m-a 声明与它冲突" in other, other
    assert own != other, ("两种成因的判词必须不同（否则读者分不出是哪一种）", own, other)


def test_the_reason_does_not_double_report_the_same_cause() -> None:
    """EC-02 ⑦：**自己声明**时**不**再叠加反向句（同一件事说两遍会让判词失真）。"""
    note = disposition_reason(None, _Row(id="m-a", contradictions=["m-b"]), conflicted_by=["m-c"])
    assert "被 m-c 声明" not in note, ("自己已声明 ⇒ 不追加反向句", note)


def test_an_empty_reverse_list_adds_nothing() -> None:
    """EC-02 ⑧：反向列表**为空** ⇒ 判词**不凭空**追加任何句子。"""
    assert disposition_reason(None, _Row(id="m-b"), conflicted_by=[]) == disposition_reason(
        None, _Row(id="m-b")
    )


def test_the_priority_order_is_unchanged() -> None:
    """EC-02 反证臂：**优先级未变** —— 已取代 / 已过期仍**先于**冲突（承序 18/19）。"""
    from packages.application.memory.validity import ValidityState

    assert disposition_of(ValidityState.EXPIRED, conflicted_by=True) != DISPOSITION_CONFLICTED
    assert disposition_of(None, superseded=True, conflicted_by=True) != DISPOSITION_CONFLICTED
