"""GOAL-20261012-064（序 32）：**引用被删的记录不再是静默的** —— EC-02 / EC-03 的判据。

**为什么单列**：本轮的靶子是**悬空引用的可见性**；与序 30（声明反向）/ 序 31（消解对端）
分工不同 —— 那两轮判「谁声明了 / 谁消解了」，本组判「**被引的那条还在不在**」。

**判的是什么**：写面对被引 id 有**存在性校验**（序 22：未知 id ⇒ 拒提交），但**删除之后
没人再查** —— **实跑**：A 引用 `m-b` 后 `m-b` 被删 ⇒ 读面照旧披露那两个 id、
**没有任何悬空标记**，`terminal` 甚至报 `CURRENT` ⇒ 一条记录的「来源可查」在**生命周期
后半段**失效。本轮让它在**两个方向各自点名**（`supersedes` / `contradictions` 语义不同）。

**边界**：**不**级联删除 / **不**自愈 / **不**改 `terminal` 的既有取值（悬空信号**另键**）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from adapters.canonical.memory_read import memory_read
from adapters.fakes import FakeMemoryStore
from packages.application.memory.disposition import dangling_reference_index
from packages.application.memory.lifecycle import (
    MemoryLifecycleDeps,
    delete_memory,
)
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

_NOW = "2026-05-01T12:00:00+00:00"


@dataclass
class _Row:
    """极小的记录替身（判据只读 `id` / `supersedes` / `contradictions`）。"""

    id: str
    supersedes: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)


def _store(*, delete_target: bool = True) -> FakeMemoryStore:
    """A 引用 B（两个方向）；（可选）把 B **删掉** —— 全走**产品路径**。"""
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
            contradictions=["m-b"],
            supersedes=["m-b"],
        )
    )
    if delete_target:
        delete_memory(MemoryLifecycleDeps(store=store), "m-b")
    return store


def _rows(store: FakeMemoryStore) -> dict[str, dict[str, object]]:
    payload = memory_read(store, {"now": _NOW})
    rows = cast("list[dict[str, object]]", payload["memories"])
    return {str(row["memory_id"]): row for row in rows}


def test_the_dangling_index_names_both_directions() -> None:
    """EC-02 ①：悬空表**两个方向各自报**（`supersedes` 与 `contradictions` 语义不同）。"""
    dangling = dangling_reference_index((
        _Row(id="m-a", supersedes=["m-gone"], contradictions=["m-also-gone"]),
    ))
    assert dangling == {"m-a": (["m-gone"], ["m-also-gone"])}, dangling


def test_the_dangling_index_is_empty_when_everything_resolves() -> None:
    """EC-02 ②：**全都在批内** ⇒ 空表（缺省形态逐字不变的前提）。"""
    assert dangling_reference_index((_Row(id="m-a", supersedes=["m-b"]), _Row(id="m-b"))) == {}


def test_a_deleted_record_leaves_a_named_dangling_reference() -> None:
    """EC-02 ③：**被引记录被删** ⇒ 读面**逐条点名**（改动前完全静默）。"""
    rows = _rows(_store())
    assert rows["m-a"]["dangling_supersedes"] == ["m-b"], rows["m-a"]
    assert rows["m-a"]["dangling_contradictions"] == ["m-b"], rows["m-a"]


def test_the_existing_keys_are_unchanged_when_a_record_is_deleted() -> None:
    """EC-02 ④（**既有键一字不动**）：`supersedes` / `contradictions` / `terminal` 逐字不变。

    **为什么重要**：本轮的加法是**另键点名**，**不**改既有语义 —— 一条被删的引用不会
    让「这条指向谁」消失（那是历史事实），只是**另外**告诉读者「那条不在了」。
    """
    rows = _rows(_store())
    assert rows["m-a"]["supersedes"] == ["m-b"], rows["m-a"]
    assert rows["m-a"]["contradictions"] == ["m-b"], rows["m-a"]
    assert rows["m-a"]["terminal"] == {"state": "CURRENT", "ids": ["m-a"]}, (
        "`terminal` 的取值**不**因悬空而改变（那是序 21 判据钉住的）",
        rows["m-a"],
    )


def test_nothing_is_dangling_before_the_delete() -> None:
    """EC-02 ⑤（反证臂）：**未删** ⇒ 两键都空（受判面与上条只差一个动作）。"""
    rows = _rows(_store(delete_target=False))
    assert rows["m-a"]["dangling_supersedes"] == [], rows["m-a"]
    assert rows["m-a"]["dangling_contradictions"] == [], rows["m-a"]


def test_the_default_form_is_verbatim_for_clean_records() -> None:
    """EC-02 ⑥：**引用都成立**的记录 ⇒ 两键都空（缺省形态逐字不变）。"""
    rows = _rows(_store(delete_target=False))
    assert rows["m-b"]["dangling_supersedes"] == [], rows["m-b"]
    assert rows["m-b"]["dangling_contradictions"] == [], rows["m-b"]


def test_the_range_scope_is_not_guessed() -> None:
    """EC-02 ⑦：**跨范围**（看不见 ≠ 不存在）**不猜** —— 只报**本批**看不到的那些。

    受判面：声明方在 `project` 范围、被引的那条在 `organization` 范围 ⇒ 按 `project` 筛选时
    被引的那条**不在本批** ⇒ 悬空表**如实**报它（「本批看不到」是对的读数，
    **不**假装它一定被删 —— 由调用方按「看不见 ≠ 不存在」解读）。
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
            supersedes=["m-b"],
        )
    )
    scoped = memory_read(store, {"now": _NOW, "scope": "project"})
    rows = {str(r["memory_id"]): r for r in cast("list[dict[str, object]]", scoped["memories"])}
    assert rows["m-a"]["dangling_supersedes"] == ["m-b"], (
        "本批看不到 ⇒ 如实报（不猜「它一定被删」）",
        rows["m-a"],
    )


def test_both_faces_use_the_same_shared_helper() -> None:
    """EC-03 ①（**判关系**）：两读面**都引用**同一个纯函数（少一处 ⇒ 可能各写一套）。"""
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    for relative in (
        "adapters/canonical/memory_read.py",
        "services/api/routers/memory.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        assert "dangling_reference_index" in source, relative


def test_the_deletion_semantics_are_untouched() -> None:
    """EC-02 反证臂：**删除语义一字不动** —— 被删的记录确实消失，别的记录**不被改写**。

    本 GOAL **不**做级联删除 / 自愈（那会改写历史事实）。
    """
    store = _store()
    rows = _rows(store)
    assert "m-b" not in rows, ("被删的记录必须真的不在", sorted(rows))
    assert rows["m-a"]["supersedes"] == ["m-b"], (
        "引用字段**不**被自愈（历史事实保留，另键点名）",
        rows["m-a"],
    )


def test_the_dangling_key_is_absent_from_the_clean_case_payload() -> None:
    """EC-03 ②：**干净记录**的悬空键是**空列表**（不是 `None` —— 与既有读面同形）。"""
    row: Any = _rows(_store(delete_target=False))["m-a"]
    assert row["dangling_supersedes"] == []
    assert isinstance(row["dangling_supersedes"], list)
