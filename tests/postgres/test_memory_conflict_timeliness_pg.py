"""PG 记忆的**冲突声明时效**往返（GOAL-20261012-061 EC-02/EC-03）。

跑在 live PG 上（`postgres` 标记）。它证的是 SQLite 面证不到的那一半：
`PostgresMemoryStore` 若不带上这两列 ⇒ 两个适配器会**分叉**
（与 GOAL-039 / 045 / 061 同款的「三实现同契约」判据）。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.memory_store import PostgresMemoryStore
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

pytestmark = pytest.mark.postgres

_BASE = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


def _dsn() -> str:
    import os

    return os.environ.get(
        "RESEARCHOS_POSTGRES_DSN",
        "postgresql://research_os:research_os_m14_test@localhost:15432/research_os",
    )


def _clean() -> None:
    import psycopg

    migrate(_dsn())
    conn = psycopg.connect(_dsn(), autocommit=True)
    conn.execute("TRUNCATE m12_memory CASCADE")
    conn.commit()
    conn.close()


def test_the_conflict_timeliness_round_trips_on_pg() -> None:
    """EC-02/EC-03：两列**原样往返**；未声明 ⇒ `None`（不是被回填出来的某个时刻）。"""
    _clean()
    source = f"test:memory-conflict-ts-{uuid.uuid4().hex[:8]}"
    declared = f"mem-{uuid.uuid4().hex[:8]}"
    plain = f"mem-{uuid.uuid4().hex[:8]}"
    review = Timestamp(_BASE + timedelta(days=1))
    expires = Timestamp(_BASE + timedelta(days=2))
    store = PostgresMemoryStore(dsn=_dsn(), allowed_sources=(source,))
    store.commit(
        MemoryWriteProposal(
            id=declared,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="c",
            provenance=source,
            confidence=0.9,
            contradictions=[f"mem-{uuid.uuid4().hex[:8]}"],
            conflict_review_after=review,
            conflict_expires_at=expires,
        )
    )
    store.commit(
        MemoryWriteProposal(
            id=plain,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="c",
            provenance=source,
            confidence=0.9,
        )
    )
    back = store.get(declared)
    assert back.conflict_review_after is not None
    assert back.conflict_review_after.value == review.value
    assert back.conflict_expires_at is not None
    assert back.conflict_expires_at.value == expires.value
    assert store.get(plain).conflict_review_after is None
    assert store.get(plain).conflict_expires_at is None


def test_the_proposed_by_round_trips_on_pg() -> None:
    """GOAL-20261012-065 EC-02：**提议者**在 PG 侧往返 —— 与 SQLite / Fake 同一份契约。

    两臂逐条：声明的 `proposed_by="agent:x"` 读回同值；未声明的读回 `None`
    （`NULL` = **未声明**，不是被回填出来的某个值）。
    """
    _clean()
    source = f"test:memory-author-{uuid.uuid4().hex[:8]}"
    authored = f"mem-{uuid.uuid4().hex[:8]}"
    plain = f"mem-{uuid.uuid4().hex[:8]}"
    store = PostgresMemoryStore(dsn=_dsn(), allowed_sources=(source,))
    store.commit(
        MemoryWriteProposal(
            id=authored,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="c",
            provenance=source,
            confidence=0.9,
            proposed_by="agent:x",
        )
    )
    store.commit(
        MemoryWriteProposal(
            id=plain,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="c",
            provenance=source,
            confidence=0.9,
        )
    )
    assert store.get(authored).proposed_by == "agent:x"
    assert store.get(plain).proposed_by is None
