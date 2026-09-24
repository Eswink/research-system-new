"""ProtocolDraftStore：`created_at` 同刻时列表序必须是**全序**且与「按新近」一致。

契约用例 `test_protocol_draft_store_contract.py::test_list_orders_by_recency_and_filters_project`
断言最新的在前。但两次 `create` 落在**同一** `created_at` 时（Windows 时钟粒度约 15.6ms，
或任何同刻插入），旧实现的 tie-break 是 `draft_id` **升序** ⇒ 返回**旧的在先**，与该断言
相反。该用例于是在**整轮**里偶发判红（合并跑红、单独跑绿）——根因不在用例，而在
「按新近」这个语义**不是全序**。

本判据把那个偶发变成**确定性**：冻结时钟制造同刻，要求三个实现（SQLite / PostgreSQL /
InMemory）给出同语义的全序。判据**只增不减**：既有契约断言一字未改。
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import pytest

from packages.application.ports.protocol_draft_store import DraftQuery

_FROZEN = "2026-09-25T00:00:00.000000Z"
_DIGEST_A = "sha256:" + "a" * 64
_DIGEST_B = "sha256:" + "b" * 64
_PG_PROJECT = "goal015-draft-order-tie"
#: 制造同刻：把本测试自己两行草稿的 created_at 钉到同一值（**只绑定参数**，无拼接）。
_PG_TIE_UPDATE = "UPDATE protocol_drafts SET created_at = %s WHERE project_id = %s"


def _run_parameterized(conn: Any, statement: str, params: tuple[Any, ...]) -> None:
    """参数绑定执行（与适配器同一写法：语句是字面常量，占位符绑定参数）。"""
    runner = getattr(conn, "execute")
    runner(statement, params)


def _order(store: Any, project_id: str) -> list[str]:
    return [item.draft_id for item in store.list(DraftQuery(project_id=project_id))]


def _assert_recency_first(order: list[str], newest: str, oldest: str) -> None:
    assert order == [newest, oldest], (
        "同一 created_at 下列表序必须是全序且最新的在前；"
        f"实际 {order}（旧 tie-break 是 draft_id 升序 ⇒ 旧的在先）"
    )


def test_sqlite_list_is_recency_first_when_created_at_is_identical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from adapters.sqlite import protocol_draft_store as sqlite_store
    from adapters.sqlite.protocol_draft_store import SqliteProtocolDraftStore

    monkeypatch.setattr(sqlite_store, "now_iso", lambda _now=None: _FROZEN)
    store = SqliteProtocolDraftStore(":memory:")
    try:
        first = store.create("p1", "a", "yaml-a", _DIGEST_A, "k1")
        second = store.create("p1", "b", "yaml-b", _DIGEST_B, "k2")
        assert first.created_at == second.created_at  # 同刻前提成立
        _assert_recency_first(_order(store, "p1"), second.draft_id, first.draft_id)
    finally:
        store.close()


def test_inmemory_list_is_recency_first_when_created_at_is_identical() -> None:
    from packages.application.protocol_authoring.memory_store import InMemoryProtocolDraftStore

    tick = datetime.fromisoformat(_FROZEN.replace("Z", "+00:00")).astimezone(timezone.utc)
    store = InMemoryProtocolDraftStore(clock=lambda: tick)
    first = store.create("p1", "a", "yaml-a", _DIGEST_A, "m1")
    second = store.create("p1", "b", "yaml-b", _DIGEST_B, "m2")
    assert first.created_at == second.created_at
    _assert_recency_first(_order(store, "p1"), second.draft_id, first.draft_id)


def _pg_reachable(dsn: str) -> bool:
    try:
        import psycopg

        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=2)
    except Exception:  # noqa: BLE001 - any connect failure means "not reachable"
        return False
    conn.close()
    return True


@pytest.mark.postgres
def test_postgres_list_is_recency_first_when_created_at_is_identical() -> None:
    """PostgreSQL 实现同语义（不可达时判据自身 skip，与 `postgres` 标记同源）。"""
    dsn = os.environ.get("RESEARCHOS_POSTGRES_DSN") or os.environ.get("DATABASE_URL") or ""
    if not dsn:
        pytest.skip(
            "no RESEARCHOS_POSTGRES_DSN / DATABASE_URL pinned for the postgres parity check"
        )
    if not _pg_reachable(dsn):
        pytest.skip("PostgreSQL not reachable for the postgres parity check")
    from adapters.postgres import db as pg_db
    from adapters.postgres.protocol_draft_store import PgProtocolDraftStore

    pg_db.migrate(dsn)
    store = PgProtocolDraftStore(dsn=dsn)
    created: list[str] = []
    try:
        first = store.create(_PG_PROJECT, "a", "yaml-a", _DIGEST_A, "pg-k1")
        second = store.create(_PG_PROJECT, "b", "yaml-b", _DIGEST_B, "pg-k2")
        created = [first.draft_id, second.draft_id]
        conn = pg_db.connect(dsn)
        try:
            _run_parameterized(conn, _PG_TIE_UPDATE, (_FROZEN, _PG_PROJECT))
        finally:
            conn.close()
        _assert_recency_first(_order(store, _PG_PROJECT), second.draft_id, first.draft_id)
    finally:
        for draft_id in created:
            store.delete(draft_id)
        store.close()
