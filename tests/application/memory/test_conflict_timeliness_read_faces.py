"""GOAL-20261012-061（序 29）：**冲突时效在两个读面同源、在三个适配器同契约**。

**判的是什么**（本文件专判**披露面**，域判据在 `tests/domain/test_conflict_timeliness.py`）：

1. **编排面**（`memory_read`）逐条披露 `conflict_timeliness`，**按调用方给的时点**判；
2. **同源**：读面**不重写第二套判定**（直接调应用层纯函数）—— 判**关系**（两处同值）；
3. **三个适配器同契约**：SQLite / Fake 落库往返 ⇒ 声明值原样读回（PG 侧在
   `tests/postgres/test_memory_conflict_timeliness_pg.py` 同形）；
4. **未声明逐字不变**：未声明时效 ⇒ `None`（**不猜**）且**既有键逐字不变**。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import cast

from adapters.canonical.memory_read import memory_read
from adapters.fakes import FakeMemoryStore
from adapters.sqlite.memory_store import SqliteMemoryStore
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

_BASE = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


def _proposal(**overrides: object) -> MemoryWriteProposal:
    base: dict[str, object] = {
        "id": "m-main",
        "tier": MemoryTier.PROJECT,
        "kind": MemoryType.FACT,
        "content": "内容 m-main",
        "provenance": "source:article-1",
        "confidence": 0.9,
        "contradictions": ["m-peer"],
    }
    base.update(overrides)
    return MemoryWriteProposal(**base)  # type: ignore[arg-type]


def _store(*, expired: bool = False, undisclosed: bool = False) -> FakeMemoryStore:
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    store.allow_source("source:article-1")
    store.commit(_proposal(id="m-peer", contradictions=[]))
    overrides: dict[str, object] = {}
    if expired:
        overrides["conflict_expires_at"] = Timestamp(_BASE - timedelta(days=1))
    if undisclosed:
        overrides["contradictions"] = []
        overrides.pop("conflict_expires_at", None)
    store.commit(_proposal(**overrides))
    return store


def _at(offset_days: float) -> str:
    return (_BASE + timedelta(days=offset_days)).isoformat()


def _rows(store: FakeMemoryStore, at: str) -> dict[str, dict[str, object]]:
    """读面载荷按 `memory_id` 索引（与编排面既有键**逐字同形**）。"""
    payload = memory_read(store, {"now": at})
    rows = cast("list[dict[str, object]]", payload["memories"])
    return {str(row["memory_id"]): row for row in rows}


def test_the_orchestration_face_discloses_the_conflict_timeliness() -> None:
    """EC-03 ①：编排面**逐条披露** `conflict_timeliness`（失效的报 `STALE`）。"""
    rows = _rows(_store(expired=True), _at(0))
    assert rows["m-main"]["conflict_timeliness"] == "STALE", rows["m-main"]


def test_an_unexpired_conflict_declaration_is_not_stale() -> None:
    """EC-03 反证臂：**未到期** ⇒ `None`（受判面与上条**只差一个声明值**）。"""
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    store.allow_source("source:article-1")
    store.commit(_proposal(id="m-peer", contradictions=[]))
    store.commit(_proposal(conflict_expires_at=Timestamp(_BASE + timedelta(days=30))))
    rows = _rows(store, _at(0))
    assert rows["m-main"]["conflict_timeliness"] is None, rows["m-main"]


def test_an_undeclared_timeliness_discloses_none_verbatim() -> None:
    """EC-03 ②：**未声明** ⇒ `None`（**不猜**），且**既有键逐字不变**。"""
    rows = _rows(_store(undisclosed=True), _at(0))
    row = rows["m-main"]
    assert row["conflict_timeliness"] is None, row
    # 既有键**逐字**仍在（本轮的加法不挪走任何既有披露）。
    for key in (
        "memory_id",
        "content",
        "validity",
        "disposition",
        "reason",
        "contradictions",
        "conflict_resolutions",
    ):
        assert key in row, (key, sorted(row))


def test_the_records_own_validity_and_the_conflict_timeliness_are_separate_keys() -> None:
    """EC-03 ③：**记录**时效（`validity`）与**冲突**时效（本键）**互不顶替**。

    记录已过期（`expires_at` 到了 ⇒ `validity == EXPIRED`）而冲突声明**未声明时效**
    ⇒ 本键仍是 `None` —— 「这条记忆过期了」**不等于**「当年声明的那个分歧失效了」。
    """
    store = FakeMemoryStore(allowed_sources=("source:article-1",))
    store.allow_source("source:article-1")
    store.commit(_proposal(id="m-peer", contradictions=[]))
    store.commit(_proposal(expires_at=Timestamp(_BASE - timedelta(days=1))))
    rows = _rows(store, _at(0))
    row = rows["m-main"]
    assert row["validity"] == "EXPIRED", row
    assert row["conflict_timeliness"] is None, (
        "记录的时效与冲突的时效是**两件事**（互不顶替）",
        row,
    )


def test_the_judgement_is_the_same_function_on_both_faces() -> None:
    """EC-03 ④（**判关系**）：读面**不重写第二套判定** —— 直接调应用层纯函数。

    受判面 = **两处的源文本**：编排面与 HTTP 面都必须**引用**同一个名字
    （`conflict_timeliness_at`）。少一处 ⇒ 两处可能各写一套（漂移无从发现）。
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    for relative in (
        "adapters/canonical/memory_read.py",
        "services/api/routers/memory.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        assert "conflict_timeliness_at" in source, relative


def test_the_sqlite_store_round_trips_the_conflict_timeliness() -> None:
    """EC-03 ⑤：SQLite **落库往返**（声明值原样读回；未声明 ⇒ `None`）。"""
    store = SqliteMemoryStore(":memory:", allowed_sources=("source:article-1",))
    store.commit(
        _proposal(
            conflict_review_after=Timestamp(_BASE),
            conflict_expires_at=Timestamp(_BASE + timedelta(days=2)),
        )
    )
    back = store.get("m-main")
    assert back.conflict_review_after is not None
    assert back.conflict_review_after.value == _BASE
    assert back.conflict_expires_at is not None
    store.commit(_proposal(id="m-plain", contradictions=[]))
    assert store.get("m-plain").conflict_expires_at is None


def test_the_fake_store_carries_the_same_contract() -> None:
    """EC-03 ⑤：**Fake 同契约**（少带 ⇒ 该路径上的判据假绿 —— 承序 13 的实测教训）。"""
    store = _store(expired=True)
    record = store.get("m-main")
    assert record.conflict_expires_at is not None
    assert record.conflict_expires_at.value == _BASE - timedelta(days=1)
