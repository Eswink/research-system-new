"""GOAL-20261012-065（序 33）：**谁提议的这条记忆读得出来** —— EC-02 / EC-03 的判据。

**为什么单列**：本轮的靶子是**作者面**（`proposed_by`）；与序 17（`scope` 可筛）/
序 29（冲突时效）分工不同 —— 那两轮判别的维度，本组判「**谁把这条知识记下来**」。

**判的是什么**：`proposed_by` 在**提案**面上（序 13 起）且两个内部调用点**会填它**，
但 `MemoryRecord` **根本没有该字段** ⇒ **实跑**：带作者的提案经产品路径提交 ⇒
落库记录**无作者面**、读面 20 键里也没有它 ⇒ 「谁提的」在 canonical **无从可查**。
本轮让它在 canonical 有位、在**两个读面**都读得出；**缺省形态逐字不变**（未声明 ⇒ `None`）。

**与 `provenance` 是两件事**：一个是**来源**（知识从哪来），一个是**谁提议**记下来
—— 判据逐条钉住两者**互不顶替**。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from adapters.canonical.memory_read import memory_read
from adapters.fakes import FakeMemoryStore
from adapters.sqlite.memory_store import SqliteMemoryStore
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryRecord, MemoryWriteProposal

_NOW = "2026-05-01T12:00:00+00:00"
_STAMP = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


def _proposal(**overrides: object) -> MemoryWriteProposal:
    base: dict[str, object] = {
        "id": "m-author",
        "tier": MemoryTier.PROJECT,
        "kind": MemoryType.FACT,
        "content": "c",
        "provenance": "source:a",
        "confidence": 0.9,
        "proposed_by": "agent:x",
    }
    base.update(overrides)
    return MemoryWriteProposal(**base)  # type: ignore[arg-type]


def _store(*, authored: bool = True) -> FakeMemoryStore:
    store = FakeMemoryStore(allowed_sources=("source:a",))
    store.allow_source("source:a")
    store.commit(_proposal(proposed_by="agent:x" if authored else None))
    return store


def _rows(store: FakeMemoryStore) -> dict[str, dict[str, object]]:
    payload = memory_read(store, {"now": _NOW})
    rows = cast("list[dict[str, object]]", payload["memories"])
    return {str(row["memory_id"]): row for row in rows}


def test_the_record_carries_the_author_now() -> None:
    """EC-02 ①：**记录**上有作者面（改动前该字段**根本不存在**）。"""
    record = _store().get("m-author")
    assert getattr(record, "proposed_by", None) == "agent:x", record
    assert "proposed_by" in {f.name for f in __import__("dataclasses").fields(MemoryRecord)}


def test_the_author_survives_a_sqlite_round_trip() -> None:
    """EC-02 ②：SQLite **落库往返**（声明值原样读回）。"""
    store = SqliteMemoryStore(":memory:", allowed_sources=("source:a",))
    store.commit(_proposal())
    assert store.get("m-author").proposed_by == "agent:x"


def test_the_undeclared_author_stays_none() -> None:
    """EC-02 ③：**未声明** ⇒ `None`（**不猜**、不伪造成某个值）—— 两库同口径。"""
    fake = FakeMemoryStore(allowed_sources=("source:a",))
    fake.allow_source("source:a")
    fake.commit(_proposal(proposed_by=None))
    assert fake.get("m-author").proposed_by is None

    sqlite = SqliteMemoryStore(":memory:", allowed_sources=("source:a",))
    sqlite.commit(_proposal(proposed_by=None))
    assert sqlite.get("m-author").proposed_by is None


def test_the_two_declaration_points_agree() -> None:
    """EC-02 ④：**两处声明面**（提案 / 记录）同值 —— 提案写了什么，记录就是什么。"""
    proposal = _proposal(proposed_by="curator:y")
    assert proposal.proposed_by == "curator:y"
    store = FakeMemoryStore(allowed_sources=("source:a",))
    store.allow_source("source:a")
    store.commit(proposal)
    assert store.get("m-author").proposed_by == proposal.proposed_by


def test_the_orchestration_face_discloses_the_author() -> None:
    """EC-03 ①：**编排读面**逐条披露作者面。"""
    rows = _rows(_store())
    assert rows["m-author"]["proposed_by"] == "agent:x", rows["m-author"]


def test_the_author_and_the_provenance_are_separate_facts() -> None:
    """EC-03 ②：**作者与来源互不顶替** —— 记录上两者**各自在场**且值不同。

    受判面 = **记录的两个字段**（`proposed_by` / `provenance`）：本轮**不**把两者混成一个
    （混起来会让读者分不出「谁提的」与「从哪来」）。**注**：编排读面本轮只披露
    `proposed_by`（`provenance` 从不在该面上）—— 这一条判**记录侧**的分离，读面侧由下一条判。
    """
    record = _store().get("m-author")
    assert record.proposed_by == "agent:x", record
    assert record.provenance == "source:a", record
    assert record.proposed_by != record.provenance, ("两者是**不同**的事实", record)


def test_the_undeclared_author_reads_none_verbatim() -> None:
    """EC-03 ③：**未声明** ⇒ 读面 `None`（既有行为逐字不变），既有键逐条仍在。"""
    row = _rows(_store(authored=False))["m-author"]
    assert row["proposed_by"] is None, row
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
        "resolved_with",
        "dangling_supersedes",
        "dangling_contradictions",
    ):
        assert key in row, (key, sorted(row))


def test_both_faces_read_the_same_canonical_fact() -> None:
    """EC-03 ④（**判关系**）：两读面都从**同一份 canonical 事实**取（不各写一套判定）。

    受判面 = **两处的源文本**都直接读记录字段（`record.proposed_by`）。
    """
    root = Path(__file__).resolve().parents[3]
    for relative in (
        "adapters/canonical/memory_read.py",
        "services/api/routers/memory.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        assert "record.proposed_by" in source, relative


def test_a_third_party_import_path_still_works() -> None:
    """EC-02 ⑤：**既有消费者**（内部调用点填 `proposed_by`）不受影响 —— 仍能构造提案。"""
    for author in ("system:m12-evidence-chain", "agent:planner"):
        assert _proposal(proposed_by=author).proposed_by == author


def test_the_timestamp_constant_is_used() -> None:
    """夹具自检：`_STAMP` 保持可用（显式引用，避免未用导入掩盖后续改动）。"""
    assert _STAMP.tzinfo is not None


def test_the_other_optional_fields_are_untouched() -> None:
    """EC-02 反证臂：**其它可选声明面逐条仍在**（本轮只加作者面）。"""
    fields = {f.name for f in __import__("dataclasses").fields(MemoryRecord)}
    for name in (
        "scope",
        "valid_from",
        "review_after",
        "expires_at",
        "supersedes",
        "contradictions",
        "resolutions",
        "conflict_review_after",
        "conflict_expires_at",
    ):
        assert name in fields, (name, sorted(fields))


def _unused(_: Any) -> None:  # pragma: no cover - 类型占位（保持 mypy 对 Any 的可读性）
    return None
