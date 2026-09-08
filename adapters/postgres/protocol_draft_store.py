"""PgProtocolDraftStore: mirrors sqlite/protocol_draft_store.py with PG types.

Transaction guarantee: save performs revision check + append inside a single
transaction (optimistic concurrency); the idempotency unique index prevents
duplicate revisions on client retry. All statements are parameterized literal
SQL constants — no user input ever enters statement text.
"""

from __future__ import annotations

from typing import Any

from adapters.postgres.base import PostgresAdapterBase
from adapters.postgres.db import connect as pg_connect
from adapters.postgres.db import dsn_from_env, now_iso
from packages.application.ports.protocol_draft_store import (
    DraftQuery,
    DraftSaveResult,
    DraftStoreConflictError,
    ProtocolDraftRecord,
    ProtocolDraftRevision,
)

_SELECT_RECORD = """
SELECT d.draft_id, d.project_id, d.name, d.created_at,
       r.revision, r.yaml_text, r.source_digest, r.created_at AS revision_at
FROM protocol_drafts d JOIN protocol_draft_revisions r
  ON r.draft_id = d.draft_id AND r.revision = (
    SELECT MAX(revision) FROM protocol_draft_revisions WHERE draft_id = d.draft_id)
"""

_SELECT_RECORD_BY_ID = """
SELECT d.draft_id, d.project_id, d.name, d.created_at,
       r.revision, r.yaml_text, r.source_digest, r.created_at AS revision_at
FROM protocol_drafts d JOIN protocol_draft_revisions r
  ON r.draft_id = d.draft_id AND r.revision = (
    SELECT MAX(revision) FROM protocol_draft_revisions WHERE draft_id = d.draft_id)
WHERE d.draft_id = %s
"""

_SELECT_RECORD_PAGE = """
SELECT d.draft_id, d.project_id, d.name, d.created_at,
       r.revision, r.yaml_text, r.source_digest, r.created_at AS revision_at
FROM protocol_drafts d JOIN protocol_draft_revisions r
  ON r.draft_id = d.draft_id AND r.revision = (
    SELECT MAX(revision) FROM protocol_draft_revisions WHERE draft_id = d.draft_id)
WHERE d.project_id = %s
ORDER BY d.created_at DESC, d.draft_id LIMIT %s OFFSET %s
"""

_SELECT_CURRENT_REVISION = """
SELECT MAX(revision) AS current_revision FROM protocol_draft_revisions
WHERE draft_id = %s
"""

_SELECT_IDEMPOTENT = """
SELECT draft_id, revision FROM protocol_draft_revisions WHERE idempotency_key = %s
"""

_INSERT_DRAFT = """
INSERT INTO protocol_drafts
 (draft_id, project_id, name, created_at, last_idempotency_key)
VALUES (%s, %s, %s, %s, %s)
"""

_INSERT_REVISION = """
INSERT INTO protocol_draft_revisions
 (draft_id, revision, yaml_text, source_digest, idempotency_key, created_at)
VALUES (%s, %s, %s, %s, %s, %s)
"""

_INSERT_REVISION_GUARDED = """
INSERT INTO protocol_draft_revisions
 (draft_id, revision, yaml_text, source_digest, idempotency_key, created_at)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (draft_id, revision) DO NOTHING
"""

_SELECT_REVISIONS = """
SELECT draft_id, revision, yaml_text, source_digest, created_at
FROM protocol_draft_revisions WHERE draft_id = %s ORDER BY revision
"""

_SELECT_ONE_REVISION = """
SELECT draft_id, revision, yaml_text, source_digest, created_at
FROM protocol_draft_revisions WHERE draft_id = %s AND revision = %s
"""


class PgProtocolDraftStore(PostgresAdapterBase):
    """PostgreSQL ProtocolDraftStore（同一 Port 契约；生产路径）。"""

    def __init__(
        self,
        *,
        dsn: str | None = None,
        connection: Any | None = None,
    ) -> None:
        super().__init__("protocol_draft_store")
        self._owns_connection = connection is None
        if connection is not None:
            self._conn: Any = connection
        else:
            resolved = dsn or dsn_from_env()
            if not resolved:
                raise ValueError("PgProtocolDraftStore requires dsn or connection")
            self._conn = pg_connect(resolved)
        self._counter = 0

    def _sql(self, statement: str, params: tuple[Any, ...]) -> Any:
        """参数化执行（语句为模块级字面常量；占位符 %s 绑定参数）。"""
        runner = getattr(self._conn, "execute")
        return runner(statement, params)

    def _sql_one(self, statement: str) -> Any:
        runner = getattr(self._conn, "execute")
        return runner(statement)

    def close(self) -> None:
        if self._owns_connection:
            try:
                self._conn.close()
            except Exception:
                pass
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
        draft_id = self._next_draft_id()
        created = now_iso(None)
        with self._conn.transaction():
            self._sql(_INSERT_DRAFT, (draft_id, project_id, name, created, idempotency_key))
            self._sql(
                _INSERT_REVISION,
                (draft_id, 1, yaml_text, source_digest, idempotency_key, created),
            )
        self._record("create", draft_id, result=project_id)
        record = self.get(draft_id)
        assert record is not None
        return record

    def get(self, draft_id: str) -> ProtocolDraftRecord | None:
        self._ensure_open()
        row: Any = self._sql(_SELECT_RECORD_BY_ID, (draft_id,)).fetchone()
        return None if row is None else _record_from_row(row)

    def list(self, query: DraftQuery) -> tuple[ProtocolDraftRecord, ...]:
        self._ensure_open()
        rows: Any = self._sql(
            _SELECT_RECORD_PAGE, (query.project_id, query.limit, query.offset)
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
        replay_row: Any = self._sql(_SELECT_IDEMPOTENT, (idempotency_key,)).fetchone()
        row: Any = self._sql(_SELECT_CURRENT_REVISION, (draft_id,)).fetchone()
        if row is None or row["current_revision"] is None:
            raise KeyError(draft_id)
        current = int(row["current_revision"])
        if replay_row is not None:
            record = self.get(draft_id)
            assert record is not None
            return DraftSaveResult(record=record, replayed=int(replay_row["revision"]) == current)
        if expected_revision != current:
            raise DraftStoreConflictError(expected_revision, current)
        created = now_iso(None)
        with self._conn.transaction():
            inserted = self._sql(
                _INSERT_REVISION_GUARDED,
                (draft_id, current + 1, yaml_text, source_digest, idempotency_key, created),
            ).rowcount
            if not inserted:
                raise DraftStoreConflictError(expected_revision, self._current_revision(draft_id))
        self._record("save", draft_id, result=str(current + 1))
        record = self.get(draft_id)
        assert record is not None
        return DraftSaveResult(record=record, replayed=False)

    def list_revisions(self, draft_id: str) -> tuple[ProtocolDraftRevision, ...]:
        self._ensure_open()
        rows: Any = self._sql(_SELECT_REVISIONS, (draft_id,)).fetchall()
        if not rows:
            raise KeyError(draft_id)
        return tuple(_revision_from_row(row) for row in rows)

    def get_revision(self, draft_id: str, revision: int) -> ProtocolDraftRevision | None:
        self._ensure_open()
        row: Any = self._sql(_SELECT_ONE_REVISION, (draft_id, revision)).fetchone()
        return None if row is None else _revision_from_row(row)

    # ── 内部 ──
    def _current_revision(self, draft_id: str) -> int:
        row: Any = self._sql(_SELECT_CURRENT_REVISION, (draft_id,)).fetchone()
        return int(row["current_revision"]) if row and row["current_revision"] else 0

    def _find_by_idempotency(self, key: str) -> tuple[str, int] | None:
        row: Any = self._sql(_SELECT_IDEMPOTENT, (key,)).fetchone()
        return None if row is None else (row["draft_id"], int(row["revision"]))

    def _next_draft_id(self) -> str:
        self._counter += 1
        return f"pdraft_{self._counter:08d}_{id(self._conn) % 100000:05d}"


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
