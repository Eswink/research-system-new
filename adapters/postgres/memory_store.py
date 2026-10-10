"""PostgreSQL adapter for MemoryStore (M14 DS-3 domain state).

Mirrors adapters/sqlite/memory_store.py semantics with PG-native types
(TIMESTAMPTZ, BOOLEAN, JSONB). Atomic commit via ON CONFLICT DO NOTHING
+ row-count verification; deactivate/delete conditional writes with
rowcount validation (0 rows → InvalidInputError).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryRecord, MemoryWriteProposal


class PostgresMemoryStore(PostgresAdapterBase):
    """PostgreSQL MemoryStore; commit gated by provenance whitelist."""

    def __init__(
        self,
        *,
        dsn: str | None = None,
        connection: Any | None = None,
        allowed_sources: tuple[str, ...] = (),
    ) -> None:
        super().__init__("memory_store")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PostgresMemoryStore requires dsn or connection")
            self._conn = pg_connect(resolved)
        self._allowed_sources = set(allowed_sources)

    def allow_source(self, source: str) -> None:
        self._allowed_sources.add(source)

    def close(self) -> None:
        if self._owns_connection:
            try:
                self._conn.close()
            except Exception:
                pass
        super().close()

    def commit(self, proposal: MemoryWriteProposal) -> MemoryRecord:
        self._ensure_open()
        self._record("commit", proposal.id)
        if not self._allowed_sources:
            raise InvalidInputError(
                "memory store has no registered provenance sources (deny by default)",
            )
        if proposal.provenance not in self._allowed_sources:
            raise InvalidInputError(
                f"memory provenance gate rejected source {proposal.provenance!r}",
            )
        # Atomic check-and-insert: ON CONFLICT DO NOTHING + rowcount verify.
        with self._conn.transaction():
            cur = self._conn.execute(
                "INSERT INTO m12_memory"
                " (id, tier, kind, content, provenance, confidence, scope,"
                " valid_from, review_after, expires_at,"
                " supersedes, contradictions, active)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)"
                " ON CONFLICT (id) DO NOTHING",
                _proposal_values(proposal),
            )
            rowcount = cur.rowcount
        if rowcount == 0:
            # Conflict → either idempotent replay or genuine conflict.
            existing = self._row(proposal.id)
            if existing is not None and existing["provenance"] == proposal.provenance:
                # Idempotent: same provenance, return existing record.
                return _record_from_row(existing)
            raise InvalidInputError(f"memory id already committed: {proposal.id}")
        record = MemoryRecord(
            id=proposal.id,
            tier=proposal.tier,
            kind=proposal.kind,
            content=proposal.content,
            provenance=proposal.provenance,
            confidence=proposal.confidence,
            # EC-02/EC-03：提交回执必须与**写进去的**一致（否则读面与写面分叉）。
            scope=proposal.scope,
            review_after=proposal.review_after,
            expires_at=proposal.expires_at,
            supersedes=list(proposal.supersedes),
        )
        return record

    def get(self, memory_id: str) -> MemoryRecord:
        self._ensure_open()
        self._record("get", memory_id)
        row = self._row(memory_id)
        if row is None:
            raise InvalidInputError(f"unknown memory id: {memory_id}")
        return _record_from_row(row)

    def query(self, tier: MemoryTier | None = None) -> tuple[MemoryRecord, ...]:
        self._ensure_open()
        self._record("query", tier.value if tier else "*")
        if tier is None:
            rows: Any = self._conn.execute("SELECT * FROM m12_memory ORDER BY id").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM m12_memory WHERE tier=%s ORDER BY id", (tier.value,)
            ).fetchall()
        return tuple(_record_from_row(row) for row in rows)

    def deactivate(self, memory_id: str) -> MemoryRecord:
        """Canonical tombstone: active=False, preserves audit history."""
        self._ensure_open()
        self._record("deactivate", memory_id)
        current = self._row(memory_id)
        if current is None:
            raise InvalidInputError(f"unknown memory id: {memory_id}")
        with self._conn.transaction():
            cur = self._conn.execute(
                "UPDATE m12_memory SET active = FALSE WHERE id = %s AND active = TRUE",
                (memory_id,),
            )
            if cur.rowcount == 0:
                # Already deactivated or missing — re-read for idempotency.
                row = self._row(memory_id)
                if row is None:
                    raise InvalidInputError(f"unknown memory id: {memory_id}")
                return _record_from_row(row)
        return _record_from_row(self._row(memory_id))

    def delete(self, memory_id: str) -> None:
        self._ensure_open()
        self._record("delete", memory_id)
        with self._conn.transaction():
            cur = self._conn.execute("DELETE FROM m12_memory WHERE id = %s", (memory_id,))
            if cur.rowcount == 0:
                raise InvalidInputError(f"unknown memory id: {memory_id}")

    def _row(self, memory_id: str) -> Any:
        return self._conn.execute("SELECT * FROM m12_memory WHERE id = %s", (memory_id,)).fetchone()


# --- Internal helpers ---


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _proposal_values(proposal: MemoryWriteProposal) -> tuple[Any, ...]:
    return (
        proposal.id,
        proposal.tier.value,
        proposal.kind.value,
        proposal.content,
        proposal.provenance,
        proposal.confidence,
        # GOAL-20261008-039 EC-02：适用范围（提案面既有字段，此前从不落库）。
        proposal.scope,
        # GOAL-20261010-045 EC-02：生效起点（提案声明则写，缺省 None ⇒ 既有行为逐字不变）。
        proposal.valid_from.value if proposal.valid_from else None,
        # EC-03：声明式时效 —— 提案声明什么就写什么（缺省 None ⇒ 既有行为逐字不变）。
        proposal.review_after.value if proposal.review_after else None,
        proposal.expires_at.value if proposal.expires_at else None,
        _json(proposal.supersedes),
        # GOAL-20261010-045 EC-02：冲突声明（此前**硬编码 `[]`** ⇒ 声明被静默丢弃）。
        _json(proposal.contradictions),
        True,  # active
    )


def _opt_ts(value: Any) -> Timestamp | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return Timestamp(value)
    if isinstance(value, str):
        return Timestamp(datetime.fromisoformat(value.replace("Z", "+00:00")))
    return None


def _record_from_row(row: Any) -> MemoryRecord:
    raw_sup = row["supersedes"]
    supersedes: list[str] = json.loads(raw_sup) if isinstance(raw_sup, str) else list(raw_sup)
    raw_con = row["contradictions"]
    contradictions: list[str] = json.loads(raw_con) if isinstance(raw_con, str) else list(raw_con)
    return MemoryRecord(
        id=row["id"],
        tier=MemoryTier(row["tier"]),
        kind=MemoryType(row["kind"]),
        content=row["content"],
        provenance=row["provenance"],
        confidence=float(row["confidence"]),
        # GOAL-20261008-039 EC-02：适用范围（旧行按缺省读出）。
        scope=str(row["scope"]) if row.get("scope") else "project",
        valid_from=_opt_ts(row["valid_from"]),
        review_after=_opt_ts(row["review_after"]),
        expires_at=_opt_ts(row["expires_at"]),
        supersedes=supersedes,
        contradictions=contradictions,
        active=bool(row["active"]),
    )
