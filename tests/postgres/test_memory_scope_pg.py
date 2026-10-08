"""PG 记忆的**适用范围与时效**往返（GOAL-20261008-039 EC-02 / EC-03）。

跑在 live PG 上（`postgres` 标记）。它证的是 SQLite 面证不到的那一半：
`PostgresMemoryStore` 此前把 `valid_from` / `review_after` / `expires_at` **硬编码为 `None`**、
连 `scope` 参数都不带 ⇒ 两个适配器会**分叉**。本判据把「三实现同契约」钉在真库上。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from adapters.postgres.db import migrate
from adapters.postgres.memory_store import PostgresMemoryStore
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryWriteProposal

pytestmark = pytest.mark.postgres


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


def test_scope_and_validity_round_trip_on_pg() -> None:
    """写 `scope` 与两时点 ⇒ 读回同值（PG 此前写死 `None`、不带 `scope`）。"""
    _clean()
    source = f"test:memory-scope-{uuid.uuid4().hex[:8]}"
    memory_id = f"mem-{uuid.uuid4().hex[:8]}"
    review = Timestamp(datetime(2026, 11, 1, tzinfo=timezone.utc))
    expires = Timestamp(datetime(2027, 1, 1, tzinfo=timezone.utc))
    store = PostgresMemoryStore(dsn=_dsn(), allowed_sources=(source,))
    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=MemoryTier.PROJECT,
            kind=MemoryType.FACT,
            content="c",
            provenance=source,
            confidence=0.9,
            scope="organization",
            review_after=review,
            expires_at=expires,
        )
    )
    loaded = store.get(memory_id)
    assert loaded.scope == "organization"
    assert loaded.review_after is not None and loaded.review_after.value == review.value
    assert loaded.expires_at is not None and loaded.expires_at.value == expires.value
    store.close()


def test_undeclared_validity_stays_none_on_pg() -> None:
    """未声明 ⇒ `None`（缺省路径逐字不变）。"""
    _clean()
    source = f"test:memory-scope-{uuid.uuid4().hex[:8]}"
    memory_id = f"mem-{uuid.uuid4().hex[:8]}"
    store = PostgresMemoryStore(dsn=_dsn(), allowed_sources=(source,))
    store.commit(
        MemoryWriteProposal(
            id=memory_id,
            tier=MemoryTier.SESSION,
            kind=MemoryType.FACT,
            content="c",
            provenance=source,
            confidence=0.5,
        )
    )
    loaded = store.get(memory_id)
    assert loaded.scope == "project" and loaded.review_after is None and loaded.expires_at is None
    store.close()
