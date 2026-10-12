"""GOAL-20261012-063（序 31）：**已消解的一对在两端都看得见** —— EC-02 / EC-03 的判据。

**为什么单列**：本轮的靶子是**消解记载的对端可见性**；与 `test_reverse_conflict_link.py`
（序 30 的**声明**反向）/ `test_conflict_resolution_*`（序 26 的**记载方**）分工不同 ——
本组判「**记载了消解，对端扣不扣得掉**」。

**判的是什么**：序 30 让**冲突声明**反向可读（`conflicted_by`），但**消解记载**仍是**单向**的
—— **实跑**：A 与 B 的一对被消解 ⇒ **A 读 `USE`**，而 **B 仍读 `CONFLICTED`**
（`conflicted_by=['m-a']` 未被抵消）⇒ **同一条已消解的分歧两端处置不一致**。
本轮让对端**扣得掉**（**逐对**）且**看得见**（`resolved_with`）。

**不静默消失**：扣掉的那些在 `resolved_with` 里逐条点名（读者要能回答
「那一对是被消解了，还是从来没声明过」）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, cast

from adapters.canonical.memory_read import memory_read
from adapters.fakes import FakeMemoryStore
from packages.application.memory.disposition import resolved_pair_index
from packages.application.memory.lifecycle import (
    MemoryLifecycleDeps,
    resolve_memory_conflict,
)
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

_NOW = "2026-05-01T12:00:00+00:00"
_STAMP = Timestamp(datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc))


@dataclass
class _Resolution:
    """极小的消解记载替身（判据只读 `other_id`）。"""

    other_id: str


@dataclass
class _Row:
    """极小的记录替身（判据只读 `id` 与 `resolutions`）。"""

    id: str
    resolutions: list[Any] = field(default_factory=list)


def _store(*, declared: bool = True, resolved: bool = True) -> FakeMemoryStore:
    """A（可选）声明与 B 冲突；可选把这一对**消解**掉 —— 全走**产品路径**。"""
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
    if declared and resolved:
        resolve_memory_conflict(
            MemoryLifecycleDeps(store=store),
            "m-a",
            "m-b",
            resolved_by="curator:x",
            resolved_at=_STAMP,
        )
    return store


def _rows(store: FakeMemoryStore) -> dict[str, dict[str, object]]:
    payload = memory_read(store, {"now": _NOW})
    rows = cast("list[dict[str, object]]", payload["memories"])
    return {str(row["memory_id"]): row for row in rows}


def test_the_reverse_resolution_index_reports_the_recorded_pair() -> None:
    """EC-02 ①：反向消解表**按被消解方索引、值为记载方**。"""
    records = (_Row(id="m-a", resolutions=[_Resolution(other_id="m-b")]), _Row(id="m-b"))
    assert resolved_pair_index(records) == {"m-b": {"m-a"}}


def test_the_reverse_resolution_index_is_empty_without_resolutions() -> None:
    """EC-02 ②：**没有任何消解记载** ⇒ 空表（缺省形态逐字不变的前提）。"""
    assert resolved_pair_index((_Row(id="m-a"), _Row(id="m-b"))) == {}


def test_both_sides_of_a_resolved_pair_agree_now() -> None:
    """EC-02 ③：**一对被消解 ⇒ 两端处置一致**（本轮的核心缺口）。"""
    rows = _rows(_store())
    assert rows["m-a"]["disposition"] == "USE", rows["m-a"]
    assert rows["m-b"]["disposition"] == "USE", (
        "对端必须扣掉已消解的那一对（否则同一条已消解的分歧两端不一致）",
        rows["m-b"],
    )


def test_the_resolved_side_sees_what_was_resolved() -> None:
    """EC-02 ④：**对端看得见**那一对已消解（不静默消失 —— 读者要能分辨两种情形）。"""
    rows = _rows(_store())
    assert rows["m-b"]["resolved_with"] == ["m-a"], rows["m-b"]
    assert rows["m-b"]["conflicted_by"] == [], ("已消解 ⇒ 不再算作反向冲突", rows["m-b"])


def test_an_unresolved_pair_still_reads_conflicted() -> None:
    """EC-02 ⑤（反证臂）：**未消解** ⇒ 对端仍是 `CONFLICTED`（受判面与上条只差一个动作）。"""
    rows = _rows(_store(resolved=False))
    assert rows["m-b"]["disposition"] == "CONFLICTED", rows["m-b"]
    assert rows["m-b"]["resolved_with"] == [], rows["m-b"]


def test_the_default_form_is_verbatim_when_nothing_was_resolved() -> None:
    """EC-02 ⑥：**没有消解记载** ⇒ 两键都空且处置逐字与改动前相同。"""
    rows = _rows(_store(declared=False))
    for key in ("m-a", "m-b"):
        assert rows[key]["resolved_with"] == [], rows[key]
        assert rows[key]["disposition"] == "USE", rows[key]


def test_only_the_resolved_pair_is_deducted() -> None:
    """EC-02 ⑦：**逐对** —— 只消解一对 ⇒ 其余声明方仍算数（不整条抹掉）。"""
    store = FakeMemoryStore(allowed_sources=("source:a",))
    store.allow_source("source:a")
    store.commit(
        MemoryWriteProposal(
            id="m-c",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="C",
            provenance="source:a",
            confidence=0.9,
        )
    )
    store.commit(
        MemoryWriteProposal(
            id="m-b",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="B",
            provenance="source:a",
            confidence=0.9,
            contradictions=["m-c"],
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
            contradictions=["m-c"],
        )
    )
    resolve_memory_conflict(
        MemoryLifecycleDeps(store=store),
        "m-a",
        "m-c",
        resolved_by="curator:x",
        resolved_at=_STAMP,
    )
    rows = _rows(store)
    assert rows["m-c"]["resolved_with"] == ["m-a"], rows["m-c"]
    assert rows["m-c"]["conflicted_by"] == ["m-b"], (
        "只消解一对 ⇒ 其余声明方仍算数（逐对）",
        rows["m-c"],
    )
    assert rows["m-c"]["disposition"] == "CONFLICTED", rows["m-c"]


def test_the_recorded_side_keeps_its_own_reading() -> None:
    """EC-02 ⑧：**记载方**的既有读法一字不动（`conflict_resolutions` 仍是它的记载）。"""
    rows = _rows(_store())
    resolutions = cast("list[object]", rows["m-a"]["conflict_resolutions"])
    assert len(resolutions) == 1, rows["m-a"]
    assert rows["m-a"]["resolved_with"] == [], ("记载方没有被别人消解", rows["m-a"])


def test_the_existing_keys_are_all_still_present() -> None:
    """EC-03 ①：**既有键逐条仍在**（本轮是加法：不挪走任何既有披露）。"""
    rows = _rows(_store())
    for key in (
        "memory_id",
        "content",
        "validity",
        "disposition",
        "reason",
        "contradictions",
        "conflict_resolutions",
        "conflict_timeliness",
        "conflicted_by",
    ):
        assert key in rows["m-b"], (key, sorted(rows["m-b"]))


def test_both_faces_use_the_same_shared_helper() -> None:
    """EC-03 ②（**判关系**）：两读面**都引用**同一个纯函数（少一处 ⇒ 可能各写一套）。"""
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    for relative in (
        "adapters/canonical/memory_read.py",
        "services/api/routers/memory.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        assert "resolved_pair_index" in source, relative
