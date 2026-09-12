"""SqliteProtocolDraftStore：草稿与不可变修订的 SQLite 持久化。

事务保证：save 在单事务内做 revision 校验 + 修订追加（乐观并发）；
幂等键唯一约束保证重复重试不产生多次修订。
语句均为模块级字面常量，占位符 ? 绑定参数，无任何 SQL 拼接。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso
from packages.application.ports.protocol_draft_store import (
    DraftQuery,
    DraftSaveResult,
    DraftStoreConflictError,
    ProtocolDraftRecord,
    ProtocolDraftRevision,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS protocol_drafts (
    draft_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_idempotency_key TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS protocol_draft_revisions (
    draft_id TEXT NOT NULL REFERENCES protocol_drafts(draft_id),
    revision INTEGER NOT NULL,
    yaml_text TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (draft_id, revision)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_protocol_draft_idem
    ON protocol_draft_revisions(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_protocol_drafts_project
    ON protocol_drafts(project_id, created_at DESC);
"""

_SELECT_LATEST = """
SELECT d.draft_id, d.project_id, d.name, d.created_at,
       r.revision, r.yaml_text, r.source_digest, r.created_at AS revision_at
FROM protocol_drafts d JOIN protocol_draft_revisions r
  ON r.draft_id = d.draft_id AND r.revision = (
    SELECT MAX(revision) FROM protocol_draft_revisions WHERE draft_id = d.draft_id)
"""

_SELECT_LATEST_BY_ID = """
SELECT d.draft_id, d.project_id, d.name, d.created_at,
       r.revision, r.yaml_text, r.source_digest, r.created_at AS revision_at
FROM protocol_drafts d JOIN protocol_draft_revisions r
  ON r.draft_id = d.draft_id AND r.revision = (
    SELECT MAX(revision) FROM protocol_draft_revisions WHERE draft_id = d.draft_id)
WHERE d.draft_id = ?
"""

_SELECT_LATEST_PAGE = """
SELECT d.draft_id, d.project_id, d.name, d.created_at,
       r.revision, r.yaml_text, r.source_digest, r.created_at AS revision_at
FROM protocol_drafts d JOIN protocol_draft_revisions r
  ON r.draft_id = d.draft_id AND r.revision = (
    SELECT MAX(revision) FROM protocol_draft_revisions WHERE draft_id = d.draft_id)
WHERE d.project_id = ?
ORDER BY d.created_at DESC, d.draft_id LIMIT ? OFFSET ?
"""

_SELECT_CURRENT_REVISION = """
SELECT MAX(revision) AS current_revision FROM protocol_draft_revisions
WHERE draft_id = ?
"""

_SELECT_IDEMPOTENT = """
SELECT draft_id, revision FROM protocol_draft_revisions WHERE idempotency_key = ?
"""

_INSERT_DRAFT = """
INSERT INTO protocol_drafts
 (draft_id, project_id, name, created_at, last_idempotency_key)
VALUES (?, ?, ?, ?, ?)
"""

_INSERT_REVISION_1 = """
INSERT INTO protocol_draft_revisions
 (draft_id, revision, yaml_text, source_digest, idempotency_key, created_at)
VALUES (?, 1, ?, ?, ?, ?)
"""

_INSERT_REVISION_NEXT = """
INSERT INTO protocol_draft_revisions
 (draft_id, revision, yaml_text, source_digest, idempotency_key, created_at)
VALUES (?, ?, ?, ?, ?, ?)
"""

_SELECT_REVISIONS = """
SELECT draft_id, revision, yaml_text, source_digest, created_at
FROM protocol_draft_revisions WHERE draft_id = ? ORDER BY revision
"""

_SELECT_ONE_REVISION = """
SELECT draft_id, revision, yaml_text, source_digest, created_at
FROM protocol_draft_revisions WHERE draft_id = ? AND revision = ?
"""

_DELETE_REVISIONS = "DELETE FROM protocol_draft_revisions WHERE draft_id = ?"
_DELETE_DRAFT = "DELETE FROM protocol_drafts WHERE draft_id = ?"


class SqliteProtocolDraftStore(SqliteAdapterBase):
    """SQLite 持久化 ProtocolDraftStore（事务化乐观并发）。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__("protocol_draft_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        runner = getattr(self._conn, "executescript")
        runner(_SCHEMA)
        self._counter = 0

    def _sql(self, statement: str, params: tuple[Any, ...]) -> Any:
        """参数化执行（语句为字面常量；占位符 ? 绑定参数，无拼接）。"""
        runner = getattr(self._conn, "execute")
        return runner(statement, params)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    # ── Port 面 ──
    def create(
        self,
        project_id: str,
        name: str,
        yaml_text: str,
        source_digest: str,
        idempotency_key: str,
    ) -> ProtocolDraftRecord:
        self._ensure_open()
        replay = self._find_by_idempotency(idempotency_key)
        if replay is not None:
            record = self.get(replay[0])
            assert record is not None
            return record
        self._counter += 1
        draft_id = f"pdraft_{self._counter:08d}"
        created = now_iso(None)
        with self._conn:
            self._sql(_INSERT_DRAFT, (draft_id, project_id, name, created, idempotency_key))
            self._sql(
                _INSERT_REVISION_1,
                (draft_id, yaml_text, source_digest, idempotency_key, created),
            )
        self._record("create", draft_id, result=project_id)
        record = self.get(draft_id)
        assert record is not None
        return record

    def get(self, draft_id: str) -> ProtocolDraftRecord | None:
        self._ensure_open()
        row = self._sql(_SELECT_LATEST_BY_ID, (draft_id,)).fetchone()
        if row is None:
            return None
        return _record_from_row(row)

    def list(self, query: DraftQuery) -> tuple[ProtocolDraftRecord, ...]:
        self._ensure_open()
        rows = self._sql(
            _SELECT_LATEST_PAGE, (query.project_id, query.limit, query.offset)
        ).fetchall()
        return tuple(_record_from_row(row) for row in rows)

    def save(
        self,
        draft_id: str,
        *,
        yaml_text: str,
        source_digest: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> DraftSaveResult:
        self._ensure_open()
        replay_row = self._sql(_SELECT_IDEMPOTENT, (idempotency_key,)).fetchone()
        row = self._sql(_SELECT_CURRENT_REVISION, (draft_id,)).fetchone()
        if row is None or row["current_revision"] is None:
            raise KeyError(draft_id)
        current = int(row["current_revision"])
        if replay_row is not None:
            record = self.get(draft_id)
            assert record is not None
            replayed = int(replay_row["revision"]) == current
            return DraftSaveResult(record=record, replayed=replayed)
        if expected_revision != current:
            raise DraftStoreConflictError(expected_revision, current)
        created = now_iso(None)
        try:
            with self._conn:
                self._sql(
                    _INSERT_REVISION_NEXT,
                    (
                        draft_id,
                        current + 1,
                        yaml_text,
                        source_digest,
                        idempotency_key,
                        created,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise DraftStoreConflictError(
                expected_revision, self._current_revision(draft_id)
            ) from exc
        self._record("save", draft_id, result=str(current + 1))
        record = self.get(draft_id)
        assert record is not None
        return DraftSaveResult(record=record, replayed=False)

    def list_revisions(self, draft_id: str) -> tuple[ProtocolDraftRevision, ...]:
        self._ensure_open()
        rows = self._sql(_SELECT_REVISIONS, (draft_id,)).fetchall()
        if not rows:
            raise KeyError(draft_id)
        return tuple(_revision_from_row(row) for row in rows)

    def get_revision(self, draft_id: str, revision: int) -> ProtocolDraftRevision | None:
        self._ensure_open()
        row = self._sql(_SELECT_ONE_REVISION, (draft_id, revision)).fetchone()
        return None if row is None else _revision_from_row(row)

    def delete(self, draft_id: str) -> bool:
        self._ensure_open()
        with self._conn:
            self._sql(_DELETE_REVISIONS, (draft_id,))
            cursor = self._sql(_DELETE_DRAFT, (draft_id,))
        removed = int(cursor.rowcount) > 0
        self._record("delete", draft_id, result=str(removed))
        return removed

    # ── 内部 ──
    def _current_revision(self, draft_id: str) -> int:
        row: Any = self._sql(_SELECT_CURRENT_REVISION, (draft_id,)).fetchone()
        return int(row["current_revision"]) if row and row["current_revision"] else 0

    def _find_by_idempotency(self, key: str) -> tuple[str, int] | None:
        row = self._sql(_SELECT_IDEMPOTENT, (key,)).fetchone()
        return None if row is None else (row["draft_id"], int(row["revision"]))


def _record_from_row(row: Any) -> ProtocolDraftRecord:
    return ProtocolDraftRecord(
        draft_id=row["draft_id"],
        project_id=row["project_id"],
        name=row["name"],
        revision=int(row["revision"]),
        yaml_text=row["yaml_text"],
        source_digest=row["source_digest"],
        created_at=row["created_at"],
        updated_at=row["revision_at"],
    )


def _revision_from_row(row: Any) -> ProtocolDraftRevision:
    return ProtocolDraftRevision(
        draft_id=row["draft_id"],
        revision=int(row["revision"]),
        yaml_text=row["yaml_text"],
        source_digest=row["source_digest"],
        created_at=row["created_at"],
    )
