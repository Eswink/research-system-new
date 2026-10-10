"""SqliteMemoryStore：MemoryStore Port 的 SQLite 持久化实现（M12-R1 WP9）。

契约与 FakeMemoryStore 完全一致（contract suite 注册表驱动双实现验证）：
- 空 allowed_sources = deny-by-default（未配置来源时拒绝一切 commit）；
- 未授权 provenance 的 commit 拒绝；同 id 重复 commit 拒绝；
- deactivate = canonical tombstone（active=False 保留审计历史）；
  delete = 物理移除；未知 id 抛 InvalidInputError。

SQLite 是本轮生产持久化边界（M14 前不引入 PostgreSQL）。
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from datetime import datetime
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.enums import MemoryTier, MemoryType
from packages.domain.memory import MemoryRecord, MemoryWriteProposal

_SCHEMA = """
CREATE TABLE IF NOT EXISTS m12_memory (
    id TEXT PRIMARY KEY,
    tier TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    provenance TEXT NOT NULL,
    confidence REAL NOT NULL,
    -- GOAL-20261008-039 EC-02：适用范围（缺省 'project'；既有行按缺省读出）。
    scope TEXT NOT NULL DEFAULT 'project',
    valid_from TEXT,
    review_after TEXT,
    expires_at TEXT,
    supersedes TEXT NOT NULL,
    contradictions TEXT NOT NULL,
    active INTEGER NOT NULL
);
"""

_MEMORY_COLS = (
    "id, tier, kind, content, provenance, confidence, scope, valid_from, review_after, "
    "expires_at, supersedes, contradictions, active"
)


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class SqliteMemoryStore(SqliteAdapterBase):
    """SQLite 持久化 MemoryStore；commit 前执行 provenance 白名单门禁。"""

    def __init__(
        self,
        connection: sqlite3.Connection | str = ":memory:",
        allowed_sources: tuple[str, ...] = (),
    ) -> None:
        super().__init__("memory_store")
        if isinstance(connection, str):
            self._connection = sqlite3.connect(connection)
        else:
            self._connection = connection
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript(_SCHEMA)
        self._connection.commit()
        self._allowed_sources = set(allowed_sources)

    def allow_source(self, source: str) -> None:
        self._allowed_sources.add(source)

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
        if self._row(proposal.id) is not None:
            raise InvalidInputError(f"memory id already committed: {proposal.id}")
        record = MemoryRecord(
            id=proposal.id,
            tier=proposal.tier,
            kind=proposal.kind,
            content=proposal.content,
            provenance=proposal.provenance,
            confidence=proposal.confidence,
            # GOAL-20261008-039 EC-02/EC-03：适用范围 + 声明式时效必须**随提案落库**
            # （此前不落 ⇒ 提交回执与写面分叉，读面永远读到缺省）。
            scope=proposal.scope,
            review_after=proposal.review_after,
            expires_at=proposal.expires_at,
            supersedes=list(proposal.supersedes),
            # GOAL-20261010-045 EC-02：**声明式冲突与生效起点**必须随提案落库
            # （此前这两个字段在 `MemoryRecord` 上有、在提案上无 ⇒ 永远落回缺省）。
            contradictions=list(proposal.contradictions),
            valid_from=proposal.valid_from,
        )
        placeholders = ",".join("?" * len(_MEMORY_COLS.split(",")))
        with self._connection:
            self._connection.execute(
                f"INSERT INTO m12_memory ({_MEMORY_COLS}) VALUES ({placeholders})",
                self._values(record),
            )
        return record

    def get(self, memory_id: str) -> MemoryRecord:
        self._ensure_open()
        self._record("get", memory_id)
        row = self._row(memory_id)
        if row is None:
            raise InvalidInputError(f"unknown memory id: {memory_id}")
        return self._record_from_row(row)

    def query(
        self, tier: MemoryTier | None = None, scope: str | None = None
    ) -> tuple[MemoryRecord, ...]:
        """按 `tier` / `scope` 筛（**两维可并存**；都缺省 ⇒ 全部 —— 既有行为逐字不变）。

        GOAL-20261010-049 EC-02：`scope` 早在域里声明、读面也逐条披露，但**查询面此前只认
        `tier`** ⇒ 「看得见、选不着」。两个条件都是**可选**：`None` = 该维不筛（**不是**「筛出
        空集」）—— 语义差别写在签名与判据里。
        """
        self._ensure_open()
        self._record("query", f"{tier.value if tier else '*'}/{scope if scope else '*'}")
        clauses: list[str] = []
        params: list[str] = []
        if tier is not None:
            clauses.append("tier=?")
            params.append(tier.value)
        if scope is not None:
            clauses.append("scope=?")
            params.append(scope)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._connection.execute(
            f"SELECT * FROM m12_memory{where} ORDER BY id", tuple(params)
        ).fetchall()
        return tuple(self._record_from_row(row) for row in rows)

    def deactivate(self, memory_id: str) -> MemoryRecord:
        """canonical tombstone：active=False 保留记录（审计历史）。"""
        self._ensure_open()
        self._record("deactivate", memory_id)
        current = self._row(memory_id)
        if current is None:
            raise InvalidInputError(f"unknown memory id: {memory_id}")
        tombstone = replace(self._record_from_row(current), active=False)
        with self._connection:
            self._connection.execute("UPDATE m12_memory SET active=0 WHERE id=?", (memory_id,))
        return tombstone

    def delete(self, memory_id: str) -> None:
        self._ensure_open()
        self._record("delete", memory_id)
        if self._row(memory_id) is None:
            raise InvalidInputError(f"unknown memory id: {memory_id}")
        with self._connection:
            self._connection.execute("DELETE FROM m12_memory WHERE id=?", (memory_id,))

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
        super().close()

    # --- 内部 ---

    def _row(self, memory_id: str) -> sqlite3.Row | None:
        row = self._connection.execute(
            "SELECT * FROM m12_memory WHERE id=?", (memory_id,)
        ).fetchone()
        if row is None:
            return None
        assert isinstance(row, sqlite3.Row)
        return row

    @staticmethod
    def _values(record: MemoryRecord) -> tuple[Any, ...]:
        return (
            record.id,
            record.tier.value,
            record.kind.value,
            record.content,
            record.provenance,
            record.confidence,
            record.scope,
            record.valid_from.value.isoformat() if record.valid_from else None,
            record.review_after.value.isoformat() if record.review_after else None,
            record.expires_at.value.isoformat() if record.expires_at else None,
            _to_json(record.supersedes),
            _to_json(record.contradictions),
            1 if record.active else 0,
        )

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            tier=MemoryTier(row["tier"]),
            kind=MemoryType(row["kind"]),
            content=row["content"],
            provenance=row["provenance"],
            confidence=row["confidence"],
            # GOAL-20261008-039 EC-02：适用范围（旧行无该列值时按缺省读出）。
            scope=row["scope"] if "scope" in row.keys() and row["scope"] else "project",
            valid_from=(
                Timestamp(datetime.fromisoformat(row["valid_from"])) if row["valid_from"] else None
            ),
            review_after=(
                Timestamp(datetime.fromisoformat(row["review_after"]))
                if row["review_after"]
                else None
            ),
            expires_at=(
                Timestamp(datetime.fromisoformat(row["expires_at"])) if row["expires_at"] else None
            ),
            supersedes=json.loads(row["supersedes"]),
            contradictions=json.loads(row["contradictions"]),
            active=bool(row["active"]),
        )


__all__ = ["SqliteMemoryStore"]
