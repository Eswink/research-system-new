"""GOAL-20261012-061（序 29）：**冲突声明的时效** —— EC-02 / EC-03 的判据。

**为什么单列**：本轮的靶子（冲突声明的时效成为可判定）横跨域 / 三适配器 / 两读面，
自成一组；与 `test_conflict_resolution_lifecycle.py`（序 26 的消解）/ `validity.py`
的**记录**时效判据**分工不同** —— 那些判别的维度，本组判**冲突声明本身**还算不算数。

**判的是什么**：`contradictions` 可声明、可落库、可处置（序 19）、可消解（序 26），
但**时效面零命中** ⇒ **一条很久以前声明的冲突永久算数**，与记忆自身的
`review_after` / `expires_at`（序 7 起）**不对称**。本轮补三态：`STALE`（失效）/
`REVIEW_DUE`（该复核）/ `None`（未到期或未声明 —— **不猜**）。

**两件互不顶替**：`validity`（**记录**的时效）与本轮的**冲突**时效是两件事 ——
记录过期**不代表**冲突声明失效（判据逐条钉住这一点）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from packages.application.memory.validity import (
    ConflictTimelinessState,
    conflict_timeliness_at,
)
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryRecord

_BASE = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


def _record(**overrides: object) -> MemoryRecord:
    base: dict[str, object] = {
        "id": "mem-1",
        "tier": MemoryTier.PROJECT,
        "kind": MemoryType.FACT,
        "content": "c",
        "provenance": "user",
        "confidence": 0.9,
        "contradictions": ["mem-elsewhere"],
    }
    base.update(overrides)
    return MemoryRecord(**base)  # type: ignore[arg-type]


def _at(offset_days: float) -> Timestamp:
    return Timestamp(_BASE + timedelta(days=offset_days))


def test_an_expired_conflict_declaration_reads_stale() -> None:
    """EC-02 ①：`conflict_expires_at` 已到 ⇒ `STALE`（这条冲突声明**失效**）。"""
    record = _record(conflict_expires_at=_at(-1))
    assert conflict_timeliness_at(record, _at(0)) is ConflictTimelinessState.STALE


def test_a_conflict_due_for_review_reads_review_due() -> None:
    """EC-02 ②：`conflict_review_after` 已到（未失效）⇒ `REVIEW_DUE`（该复核了）。"""
    record = _record(conflict_review_after=_at(-1))
    assert conflict_timeliness_at(record, _at(0)) is ConflictTimelinessState.REVIEW_DUE


def test_an_undeclared_timeliness_stays_none_not_stale() -> None:
    """EC-02 ③：**未声明** ⇒ `None`（**不猜**）—— 「未声明」**不得**被当成「已失效」。"""
    record = _record()
    assert conflict_timeliness_at(record, _at(3650)) is None


def test_a_future_bound_has_not_arrived_yet() -> None:
    """EC-02 ④：两个界都**未到** ⇒ `None`（照旧算数）。"""
    record = _record(conflict_review_after=_at(1), conflict_expires_at=_at(2))
    assert conflict_timeliness_at(record, _at(0)) is None


def test_expiry_wins_over_review_when_both_have_arrived() -> None:
    """EC-02 ⑤：两界**都到** ⇒ `STALE`（更强的状态优先 —— 与 `validity_at` 同一口径）。"""
    record = _record(conflict_review_after=_at(-2), conflict_expires_at=_at(-1))
    assert conflict_timeliness_at(record, _at(0)) is ConflictTimelinessState.STALE


def test_a_record_without_contradictions_has_no_conflict_timeliness() -> None:
    """EC-02 ⑥：**没有冲突声明** ⇒ 也 `None`（没有冲突就没有「冲突时效」可言）。"""
    record = _record(contradictions=[])
    assert conflict_timeliness_at(record, _at(0)) is None


def test_the_boundary_is_inclusive_exactly_at_the_bound() -> None:
    """EC-02：界的**闭区间**（`<= now` ⇒ 到点即判 —— 与 `validity_at` 逐字同一口径）。"""
    record = _record(conflict_expires_at=_at(0))
    assert conflict_timeliness_at(record, _at(0)) is ConflictTimelinessState.STALE


def test_declaring_timeliness_without_contradictions_is_refused() -> None:
    """EC-02：**声明了时效却没有任何冲突** ⇒ 点名拒绝（否则它永远不生效 = 看不见的故障）。"""
    with pytest.raises(ValueError, match="declares no contradictions"):
        _record(contradictions=[], conflict_expires_at=_at(1))


def test_expiry_before_review_is_refused_by_name() -> None:
    """EC-02：`conflict_expires_at` **早于** `conflict_review_after` ⇒ 点名拒绝。

    那种组合下「该复核」**永远不会到来**（过期已把它们都盖住）⇒ 声明期就该拒。
    """
    with pytest.raises(ValueError, match="must not precede"):
        _record(conflict_review_after=_at(2), conflict_expires_at=_at(1))


def test_the_record_level_timeliness_is_a_separate_dimension() -> None:
    """EC-02 反证臂：**记录**的时效与**冲突**的时效**互不顶替**（两件不同的事）。

    记录已过期（`expires_at` 到了）而冲突声明**未声明时效** ⇒ 冲突时效仍是 `None`
    （**不**跟着记录一起失效）—— 反过来也一样。
    """
    expired_record = _record(expires_at=_at(-1))
    assert conflict_timeliness_at(expired_record, _at(0)) is None
    fresh_record = _record(conflict_expires_at=_at(-1))
    assert conflict_timeliness_at(fresh_record, _at(0)) is ConflictTimelinessState.STALE


def test_the_declaration_fields_are_off_by_default() -> None:
    """EC-02：两个声明位**缺省 `None`**（既有行为逐字不变）。"""
    record = _record()
    assert record.conflict_review_after is None
    assert record.conflict_expires_at is None
