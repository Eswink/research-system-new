"""GOAL-20261012-062（序 30）：**被声明方在两个读面都读得出** —— EC-03 的判据。

**判的是什么**（域/处置面的判据在 `test_reverse_conflict_link.py`）：

1. **编排面**逐条披露 `conflicted_by`（本记录**没有**正向声明也读得出）；
2. **同源**：两个读面**都引用**同一批纯函数（不各写一套）；
3. **缺省逐字不变**：没有任何反向声明 ⇒ `conflicted_by == []` 且 `disposition` 与改动前相同；
4. **正向读法一字不动**：`contradictions` 仍是**正向**声明（两件事**互不顶替**）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from adapters.canonical.memory_read import memory_read
from adapters.fakes import FakeMemoryStore
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

_NOW = "2026-05-01T12:00:00+00:00"
_STAMP = Timestamp(datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc))


def _store(*, declared: bool) -> FakeMemoryStore:
    """A（可选）声明与 B 冲突 —— 全走**产品路径**（`commit` 经门链）。"""
    store = FakeMemoryStore(allowed_sources=("source:a",))
    store.allow_source("source:a")
    store.commit(
        MemoryWriteProposal(
            id="m-b",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="B",
            provenance="source:a",
            confidence=0.9,
        )
    )
    store.commit(
        MemoryWriteProposal(
            id="m-a",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="A",
            provenance="source:a",
            confidence=0.9,
            contradictions=["m-b"] if declared else [],
        )
    )
    return store


def _rows(store: FakeMemoryStore) -> dict[str, dict[str, object]]:
    payload = memory_read(store, {"now": _NOW})
    rows = cast("list[dict[str, object]]", payload["memories"])
    return {str(row["memory_id"]): row for row in rows}


def test_the_declared_against_record_discloses_who_declared() -> None:
    """EC-03 ①：**被声明方**逐条披露声明方（改动前该键不存在）。"""
    rows = _rows(_store(declared=True))
    assert rows["m-b"]["conflicted_by"] == ["m-a"], rows["m-b"]


def test_the_declared_against_record_is_no_longer_used_verbatim() -> None:
    """EC-03 ②：**被声明方**不再是 `USE`（本轮的靶子：改动前它照用）。"""
    rows = _rows(_store(declared=True))
    assert rows["m-b"]["disposition"] == "CONFLICTED", rows["m-b"]
    assert rows["m-a"]["disposition"] == "CONFLICTED", rows["m-a"]


def test_the_declaring_record_keeps_its_own_positive_reading() -> None:
    """EC-03 ③：**声明方**的正向读法**一字不动**（`contradictions` 仍是声明）。"""
    rows = _rows(_store(declared=True))
    assert rows["m-a"]["contradictions"] == ["m-b"], rows["m-a"]
    assert rows["m-a"]["conflicted_by"] == [], ("声明方没有反向声明", rows["m-a"])


def test_the_default_form_is_verbatim_when_nobody_declared() -> None:
    """EC-03 ④：**没人声明** ⇒ `conflicted_by == []` 且处置逐字仍是 `USE`。"""
    rows = _rows(_store(declared=False))
    assert rows["m-a"]["conflicted_by"] == [], rows["m-a"]
    assert rows["m-b"]["conflicted_by"] == [], rows["m-b"]
    assert rows["m-a"]["disposition"] == "USE", rows["m-a"]
    assert rows["m-b"]["disposition"] == "USE", rows["m-b"]


def test_the_existing_keys_are_all_still_present() -> None:
    """EC-03 ⑤：**既有键逐条仍在**（本轮是加法：不挪走任何既有披露）。"""
    rows = _rows(_store(declared=True))
    row = rows["m-b"]
    for key in (
        "memory_id",
        "content",
        "validity",
        "disposition",
        "reason",
        "contradictions",
        "conflict_resolutions",
        "conflict_timeliness",
    ):
        assert key in row, (key, sorted(row))


def test_both_faces_use_the_same_shared_helper() -> None:
    """EC-03 ⑥（**判关系**）：两读面**都引用**同一个纯函数（少一处 ⇒ 可能各写一套）。"""
    root = Path(__file__).resolve().parents[3]
    for relative in (
        "adapters/canonical/memory_read.py",
        "services/api/routers/memory.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        assert "conflicted_by_index" in source, relative


def test_the_range_boundary_is_named_not_faked() -> None:
    """EC-03 ⑦：反向索引**只报本批看到的**（看不见 ≠ 不存在 ⇒ 由调用方点名）。

    受判面：把声明方**移出本批**（按 `scope` 筛）⇒ 被声明方**读不到**反向声明
    —— 本函数**不**假装它不存在（返回空表就是「本批看不到」的**如实**结果）。
    """
    store = FakeMemoryStore(allowed_sources=("source:a",))
    store.allow_source("source:a")
    store.commit(
        MemoryWriteProposal(
            id="m-b",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="B",
            provenance="source:a",
            confidence=0.9,
            scope="organization",
        )
    )
    store.commit(
        MemoryWriteProposal(
            id="m-a",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="A",
            provenance="source:a",
            confidence=0.9,
            scope="project",
            contradictions=["m-b"],
        )
    )
    scoped = memory_read(store, {"now": _NOW, "scope": "organization"})
    rows = {str(r["memory_id"]): r for r in cast("list[dict[str, object]]", scoped["memories"])}
    assert rows["m-b"]["conflicted_by"] == [], (
        "声明方在本批看不到 ⇒ 反向表为空（如实；不假装它不存在）",
        rows["m-b"],
    )
    assert _STAMP is not None  # 保持夹具类型可用性（显式引用，避免未用导入）
