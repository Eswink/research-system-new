"""GOAL-20261009-042 EC-02 判据：**`memory.read` 的时效判定与处置**（三态互不混用）。

靶子：读面按**调用方给的时点**（`now`）给每条记忆的 `validity` 与 `disposition`：

- `EXPIRED`（`expires_at <= now`）⇒ `SKIP`（**不**参与后续行为）；
- `REVIEW_DUE`（`review_after <= now`，且未过期）⇒ `ANNOTATE`；
- `None`（未声明时效 **或** 都未到）⇒ `USE`（**不猜** —— §8 口径：未声明不得当成已到期）。

**三条硬约束的判据**（逐条）：

1. **不读挂钟**：同一条记录 + **同一个** `now` ⇒ 判定必相同；且换 `now` 会让判定**翻转**
   （两向都可判：两侧时点分别落 `USE` 与 `SKIP`）；
2. **未声明不猜**：没声明时效的记录在任何时点都是 `USE`（构造性反证）；
3. **点名**：缺 `MemoryStore` / 缺 `now` / `now` 非法（含 naive）⇒ **点名拒绝**
   （**不**返回空列表冒充「没有记忆」）。

**边界**（如实登记）：本文件只判**读面**的判定与处置；「研究循环按处置改变行为」是
EC-03 的事（另有判据）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from adapters.canonical.memory_read import (
    DISPOSITION_ANNOTATE,
    DISPOSITION_SKIP,
    DISPOSITION_USE,
    memory_read,
)
from adapters.fakes import FakeMemoryStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

_EPOCH = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)


def _moment(offset_days: int) -> str:
    """时点（相对 `_EPOCH` 偏移若干天；**RFC3339**，UTC）。"""
    return (_EPOCH + timedelta(days=offset_days)).isoformat()


def _record(
    memory_id: str,
    *,
    expires_at: datetime | None = None,
    review_after: datetime | None = None,
) -> MemoryWriteProposal:
    """一条**待提交**的记忆（经既有 §8 写入门链落到 store ⇒ 与产品路径同一形态）。"""
    return MemoryWriteProposal(
        id=memory_id,
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content=f"内容 {memory_id}",
        provenance="test:goal042",
        confidence=0.9,
        scope="project",
        expires_at=Timestamp(expires_at) if expires_at is not None else None,
        review_after=Timestamp(review_after) if review_after is not None else None,
    )


def _first(payload: dict[str, object]) -> dict[str, object]:
    """读面载荷里的第一条记忆（类型化取值：读面契约里 `memories` 是对象数组）。"""
    rows = payload["memories"]
    assert isinstance(rows, list) and rows, rows
    first = rows[0]
    assert isinstance(first, dict), first
    return first


def _store(*records: MemoryWriteProposal) -> FakeMemoryStore:
    """把记录**真的提交**进 store（deny-by-default 的来源先登记 —— 与产品路径同一形态）。"""
    store = FakeMemoryStore(allowed_sources=("test:goal042",))
    for record in records:
        store.commit(record)
    return store


class TestTheThreeDispositionsDoNotMix:
    """三态 → 处置：**互不混用**（读面按 `disposition` 即可分派，不靠措辞）。"""

    def test_an_expired_record_is_skipped(self) -> None:
        record = _record("m-expired", expires_at=_EPOCH - timedelta(days=1))
        payload = memory_read(_store(record), {"now": _moment(0)})
        row = _first(payload)
        assert row["validity"] == "EXPIRED", row
        assert row["disposition"] == DISPOSITION_SKIP, row
        assert "已过" in str(row["reason"]), row
        assert str(row["reason"]).startswith("expires_at="), ("理由点名被引的声明值", row)

    def test_a_review_due_record_is_annotated_not_skipped(self) -> None:
        record = _record("m-due", review_after=_EPOCH - timedelta(days=1))
        payload = memory_read(_store(record), {"now": _moment(0)})
        row = _first(payload)
        assert row["validity"] == "REVIEW_DUE", row
        assert row["disposition"] == DISPOSITION_ANNOTATE, row
        assert row["disposition"] != DISPOSITION_SKIP, ("待复核不是过期：处置必须可分", row)
        assert str(row["reason"]).startswith("review_after="), row

    def test_an_expiry_dominates_a_due_review(self) -> None:
        """过期是更强的状态：两条声明都到了 ⇒ `EXPIRED`（不是 `REVIEW_DUE`）。"""
        record = _record(
            "m-both",
            expires_at=_EPOCH - timedelta(days=1),
            review_after=_EPOCH - timedelta(days=2),
        )
        payload = memory_read(_store(record), {"now": _moment(0)})
        assert _first(payload)["validity"] == "EXPIRED", payload["memories"]

    def test_a_record_without_declared_validity_is_used(self) -> None:
        """**未声明不猜**（§8 口径）：没声明时效 ⇒ `USE`，理由明写「不得被当成已到期」。"""
        record = _record("m-plain")
        payload = memory_read(_store(record), {"now": _moment(0)})
        row = _first(payload)
        assert row["validity"] is None, row
        assert row["disposition"] == DISPOSITION_USE, row
        assert "不得被当成已到期" in str(row["reason"]), row

    def test_dispositions_are_counted_for_consumers_that_do_not_parse_the_array(self) -> None:
        store = _store(
            _record("m-a", expires_at=_EPOCH - timedelta(days=1)),
            _record("m-b", review_after=_EPOCH - timedelta(days=1)),
            _record("m-c"),
        )
        payload = memory_read(store, {"now": _moment(0)})
        assert payload["dispositions"] == {
            DISPOSITION_USE: 1,
            DISPOSITION_ANNOTATE: 1,
            DISPOSITION_SKIP: 1,
        }, payload["dispositions"]
        assert payload["memory_count"] == 3


class TestTheDecisionIsReproducible:
    """**不读挂钟**：同一记录 + 同一时点 ⇒ 判定相同；换时点 ⇒ 判定翻转（两向）。"""

    def test_the_same_moment_yields_the_same_decision(self) -> None:
        record = _record("m-1", expires_at=_EPOCH)
        store = _store(record)
        first = memory_read(store, {"now": _moment(0)})
        second = memory_read(store, {"now": _moment(0)})
        assert first["memories"] == second["memories"], "同一时点必须给出同一判定"

    def test_the_decision_flips_across_the_declared_boundary(self) -> None:
        """两向反证：`expires_at` **之前** ⇒ `USE`；**之后** ⇒ `SKIP`（同一份记录）。"""
        record = _record("m-2", expires_at=_EPOCH)
        store = _store(record)
        before = memory_read(store, {"now": _moment(-1)})
        after = memory_read(store, {"now": _moment(0)})
        assert _first(before)["disposition"] == DISPOSITION_USE, before["memories"]
        assert _first(after)["disposition"] == DISPOSITION_SKIP, after["memories"]

    def test_the_moment_is_echoed_so_a_reader_can_recheck(self) -> None:
        payload = memory_read(_store(_record("m-3")), {"now": _moment(0)})
        assert payload["now"] == _moment(0), payload


class TestMissingDependenciesAreNamed:
    """**点名而非静默降级**：缺依赖 / 缺时点 / 时点非法 ⇒ 点名拒绝。"""

    def test_a_missing_store_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="MemoryStore"):
            memory_read(None, {"now": _moment(0)})

    def test_a_missing_moment_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="explicit 'now'"):
            memory_read(_store(), {})

    def test_a_blank_moment_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="explicit 'now'"):
            memory_read(_store(), {"now": "   "})

    def test_a_naive_moment_is_named(self) -> None:
        """naive 时间戳 ⇒ 点名（挂钟语义会随机器时区漂 ⇒ 不接受）。"""
        with pytest.raises(InvalidInputError, match="timezone-aware"):
            memory_read(_store(), {"now": "2026-10-01T12:00:00"})

    def test_an_unparsable_moment_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="not a valid timestamp"):
            memory_read(_store(), {"now": "not-a-timestamp"})

    def test_an_unknown_tier_is_named(self) -> None:
        with pytest.raises(InvalidInputError, match="not a known tier"):
            memory_read(_store(), {"now": _moment(0), "tier": "GALAXY"})


class TestTheReadFaceIsScopeAware:
    """tier 过滤走既有口径（`MemoryStore.query(tier=...)`），未知 tier **点名**。"""

    def test_a_tier_filter_is_passed_through(self) -> None:
        store = FakeMemoryStore()
        payload = memory_read(store, {"now": _moment(0), "tier": "PROJECT"})
        assert payload["tier"] == "PROJECT", payload
        assert payload["memory_count"] == 0, payload
