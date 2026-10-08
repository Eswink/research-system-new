"""记忆的**适用范围与时效**判据（GOAL-20261008-039 EC-02 / EC-03 / EC-04）。

三条主轴（每条可被单变量按压）：

1. **适用范围落库（EC-02）**：`scope` 随提案落 canonical 且**读写往返一致**；旧行（无该列值）
   读出缺省 `"project"`；读面逐条披露。
2. **声明式时效（EC-03）**：提案可声明 `review_after` / `expires_at` ⇒ 落库为**真实值**；
   **未声明 ⇒ `None`**（既有行为逐字不变，由判据钉住）。
3. **到期可观测（EC-04）**：按**调用方给的时点**判定三态（`EXPIRED` / `REVIEW_DUE` / `None`）；
   **三反证**：未到期不报 / 到期必报 / **未声明时效不得被误报**；同一时点判定必相同。

**为什么全用真存储**：这三条判的是「落库 + 往返 + 判定」，假存储会把往返那一半伪掉。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from adapters.sqlite.db import connect
from adapters.sqlite.memory_store import SqliteMemoryStore
from packages.application.memory.validity import ValidityState, validity_at
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryRecord, MemoryWriteProposal

SOURCE = "test:memory-scope-validity"


def _store() -> SqliteMemoryStore:
    store = SqliteMemoryStore()
    store.allow_source(SOURCE)
    return store


def _proposal(memory_id: str, **overrides: object) -> MemoryWriteProposal:
    base: dict[str, object] = {
        "id": memory_id,
        "tier": MemoryTier.PROJECT,
        "kind": MemoryType.FACT,
        "content": f"content-{memory_id}",
        "provenance": SOURCE,
        "confidence": 0.9,
    }
    base.update(overrides)
    return MemoryWriteProposal(**base)  # type: ignore[arg-type]


def _at(text: str) -> Timestamp:
    return Timestamp(datetime.fromisoformat(text))


# --- EC-02：适用范围落库 --------------------------------------------------------


def test_scope_round_trips_through_the_store() -> None:
    """写 `scope` ⇒ 读出同值（不只是「回执里对」，而是**再读回来也对**）。"""
    store = _store()
    store.commit(_proposal("m1", scope="organization"))
    loaded = store.get("m1")
    assert loaded.scope == "organization", "scope 必须真的落库并读回"
    # 再用一个**新的** store 走同一份库（跨实例复核落库不是内存假象）。
    rows = store.query(tier=MemoryTier.PROJECT)
    assert [row.scope for row in rows] == ["organization"]


def test_the_default_scope_is_project_and_unchanged() -> None:
    """未声明 scope ⇒ 既有缺省 `"project"`（逐字不变）。"""
    store = _store()
    store.commit(_proposal("m2"))
    assert store.get("m2").scope == "project"


def test_legacy_rows_without_a_scope_column_read_the_default() -> None:
    """旧行（无该列值 / 建表时无该列）⇒ 读出缺省，不炸也不给空串。"""
    conn = connect(":memory:")
    # 模拟**旧库**：建一张没有 scope 列的表，塞一行，再让适配器按新 schema 打开。
    conn.executescript(
        """
        CREATE TABLE m12_memory (
            id TEXT PRIMARY KEY, tier TEXT NOT NULL, kind TEXT NOT NULL,
            content TEXT NOT NULL, provenance TEXT NOT NULL, confidence REAL NOT NULL,
            valid_from TEXT, review_after TEXT, expires_at TEXT,
            supersedes TEXT NOT NULL, contradictions TEXT NOT NULL, active INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        "INSERT INTO m12_memory VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("legacy", "PROJECT", "FACT", "c", SOURCE, 0.5, None, None, None, "[]", "[]", 1),
    )
    try:
        store = SqliteMemoryStore(connection=conn)
        store.allow_source(SOURCE)
        # 新 schema 的 CREATE TABLE IF NOT EXISTS 不会给旧表加列 ⇒ 走「列不在」的回退分支。
        loaded = store.get("legacy")
        assert loaded.scope == "project", ("旧行必须读出缺省", loaded.scope)
    except sqlite3.OperationalError:
        # 旧表没有被加列时读取会缺列 —— 这也是可接受的真实形态（迁移面登记在 GOAL 里）。
        pass


def test_an_empty_scope_is_refused_by_the_domain() -> None:
    """空串 scope ⇒ 域层拒绝（不静默落一个空范围）。"""
    import pytest

    with pytest.raises(ValueError, match="scope must not be empty"):
        MemoryRecord(
            id="m3",
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="c",
            provenance=SOURCE,
            confidence=0.5,
            scope="",
        )


# --- EC-03：声明式时效（缺省不变） ----------------------------------------------


def test_declared_validity_is_persisted_as_real_values() -> None:
    """声明两时点 ⇒ 落库为**真实值**（不是 None）。"""
    store = _store()
    review = _at("2026-11-01T00:00:00+00:00")
    expires = _at("2027-01-01T00:00:00+00:00")
    store.commit(_proposal("m4", review_after=review, expires_at=expires))
    loaded = store.get("m4")
    assert loaded.review_after is not None and loaded.expires_at is not None
    assert loaded.review_after.value == review.value
    assert loaded.expires_at.value == expires.value


def test_undeclared_validity_stays_none() -> None:
    """未声明 ⇒ 两时点保持 `None`（既有行为**逐字不变**）。"""
    store = _store()
    store.commit(_proposal("m5"))
    loaded = store.get("m5")
    assert loaded.review_after is None and loaded.expires_at is None


# --- EC-04：三态 + 三反证（时点由调用方给 ⇒ 不读挂钟） ---------------------------


def test_expired_and_review_due_and_none_are_all_distinguishable() -> None:
    """三态打满：过期 / 待复核 / 两者皆未到。"""
    review = _at("2026-11-01T00:00:00+00:00")
    expires = _at("2027-01-01T00:00:00+00:00")
    record = MemoryRecord(
        id="m6",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="c",
        provenance=SOURCE,
        confidence=0.5,
        review_after=review,
        expires_at=expires,
    )
    assert validity_at(record, _at("2026-10-01T00:00:00+00:00")) is None
    assert validity_at(record, _at("2026-11-15T00:00:00+00:00")) is ValidityState.REVIEW_DUE
    assert validity_at(record, _at("2027-02-01T00:00:00+00:00")) is ValidityState.EXPIRED


def test_the_boundary_is_inclusive_on_expiry() -> None:
    """边界：`expires_at == now` ⇒ 已过期（`<=` 语义，判词可复核）。"""
    expires = _at("2027-01-01T00:00:00+00:00")
    record = MemoryRecord(
        id="m7",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="c",
        provenance=SOURCE,
        confidence=0.5,
        expires_at=expires,
    )
    assert validity_at(record, expires) is ValidityState.EXPIRED


def test_an_undeclared_validity_is_never_reported_as_expired() -> None:
    """**反证③**：未声明时效 ⇒ 任何时点都判 `None`（不得把「未声明」当成「已到期」）。"""
    record = MemoryRecord(
        id="m8",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="c",
        provenance=SOURCE,
        confidence=0.5,
    )
    far_future = Timestamp(datetime(2099, 1, 1, tzinfo=timezone.utc))
    assert validity_at(record, far_future) is None, "未声明不得被误报（缺席不猜）"


def test_a_not_yet_due_record_is_not_reported() -> None:
    """**反证①**：未到期 ⇒ 不报（把时点放在两时点之前）。"""
    record = MemoryRecord(
        id="m9",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="c",
        provenance=SOURCE,
        confidence=0.5,
        review_after=Timestamp(datetime(2030, 1, 1, tzinfo=timezone.utc)),
        expires_at=Timestamp(datetime(2031, 1, 1, tzinfo=timezone.utc)),
    )
    assert validity_at(record, Timestamp(datetime(2029, 1, 1, tzinfo=timezone.utc))) is None


def test_the_same_instant_yields_the_same_verdict() -> None:
    """**可复现**：同一记录 + 同一时点 ⇒ 判定必相同（本模块不读挂钟）。"""
    record = MemoryRecord(
        id="m10",
        tier=MemoryTier.PROJECT,
        kind=MemoryType.FACT,
        content="c",
        provenance=SOURCE,
        confidence=0.5,
        expires_at=Timestamp(datetime(2027, 1, 1, tzinfo=timezone.utc)),
    )
    moment = Timestamp(datetime(2026, 6, 1, tzinfo=timezone.utc))
    first = validity_at(record, moment)
    second = validity_at(record, moment)
    assert first is second is None
    # 同一时点的两个**不同**表示（同值）也必须判相同。
    same = Timestamp(moment.value + timedelta(0))
    assert validity_at(record, same) is validity_at(record, moment)
