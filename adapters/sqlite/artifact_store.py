"""SqliteArtifactStore：ArtifactStore Port 的 SQLite + 文件系统实现。

内容寻址（storage/ARTIFACT_STORE.md）：sha256 digest 校验后，
内容存 blob 目录（digest[:2]/digest），元数据存 SQLite。
状态流转与 Fake 语义一致（STAGED→VERIFIED/QUARANTINED→ACTIVE→
ARCHIVED→DELETED_TOMBSTONE）；DELETE 后内容立即不可读（tombstone）。
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from adapters.sqlite.base import SqliteAdapterBase
from adapters.sqlite.db import connect, now_iso, parse_iso
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import (
    Artifact,
    ArtifactRetentionPolicy,
    verify_artifact_content,
)
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ArtifactState

_VALID_TRANSITIONS: dict[ArtifactState, frozenset[ArtifactState]] = {
    ArtifactState.STAGED: frozenset({ArtifactState.VERIFIED, ArtifactState.QUARANTINED}),
    ArtifactState.VERIFIED: frozenset({ArtifactState.ACTIVE, ArtifactState.QUARANTINED}),
    ArtifactState.QUARANTINED: frozenset({
        ArtifactState.ACTIVE,
        ArtifactState.VERIFIED,
        ArtifactState.DELETED_TOMBSTONE,
    }),
    ArtifactState.ACTIVE: frozenset({ArtifactState.ARCHIVED, ArtifactState.DELETED_TOMBSTONE}),
    ArtifactState.ARCHIVED: frozenset({ArtifactState.DELETED_TOMBSTONE}),
    ArtifactState.DELETED_TOMBSTONE: frozenset(),
}

_STATE_BY_VALUE = {state.value: state for state in ArtifactState}


class SqliteArtifactStore(SqliteAdapterBase):
    """内容寻址存储：blob 目录 + SQLite 元数据。"""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        blob_dir: str | Path | None = None,
        *,
        connection: sqlite3.Connection | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__("artifact_store")
        self._owns_connection = connection is None
        self._conn = connection if connection is not None else connect(str(db_path))
        self._blob_root = Path(blob_dir) if blob_dir else Path.cwd() / ".artifacts"
        self._now = now

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()
        super().close()

    def put(self, artifact: Artifact, content: bytes) -> None:
        self._ensure_open()
        if not verify_artifact_content(artifact, content):
            self._record("put", artifact.id, error="InvalidInputError")
            raise InvalidInputError(f"artifact content digest mismatch for {artifact.id}")
        blob_path = self._blob_path(artifact.digest)
        if not blob_path.exists():
            blob_path.parent.mkdir(parents=True, exist_ok=True)
            blob_path.write_bytes(content)
        with self._conn:
            existing = self._conn.execute(
                "SELECT 1 FROM artifacts WHERE artifact_id = ?", (artifact.id,)
            ).fetchone()
            if existing is None:
                self._insert_metadata(artifact)
            else:
                self._update_metadata(artifact)
        self._record("put", f"{artifact.id}/{len(content)}", result="stored")

    def get(self, artifact_id: str) -> bytes:
        self._ensure_open()
        row = self._require_metadata("get", artifact_id)
        if row["state"] == ArtifactState.DELETED_TOMBSTONE.value:
            self._record("get", artifact_id, error="InvalidInputError")
            raise InvalidInputError(f"artifact deleted: {artifact_id}")
        content = self._blob_path(Digest.parse(row["digest"])).read_bytes()
        self._record("get", artifact_id, result=str(len(content)))
        return content

    def verify(self, artifact_id: str) -> bool:
        self._ensure_open()
        row = self._require_metadata("verify", artifact_id)
        if row["state"] == ArtifactState.DELETED_TOMBSTONE.value:
            self._record("verify", artifact_id, error="InvalidInputError")
            raise InvalidInputError(f"artifact deleted: {artifact_id}")
        content = self._blob_path(Digest.parse(row["digest"])).read_bytes()
        declared = _artifact_from_row(row)
        ok = verify_artifact_content(declared, content)
        self._record("verify", artifact_id, result=str(ok))
        return ok

    def meta(self, artifact_id: str) -> Artifact | None:
        self._ensure_open()
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()
        artifact = _artifact_from_row(row) if row is not None else None
        self._record("meta", artifact_id, result="found" if artifact is not None else "none")
        return artifact

    def mark(self, artifact_id: str, state: ArtifactState) -> None:
        self._ensure_open()
        row = self._require_metadata("mark", artifact_id)
        current = _STATE_BY_VALUE[row["state"]]
        if state not in _VALID_TRANSITIONS[current]:
            self._record("mark", artifact_id, error="InvalidInputError")
            raise InvalidInputError(
                f"illegal artifact state transition {current.value} -> {state.value}",
            )
        with self._conn:
            self._conn.execute(
                "UPDATE artifacts SET state = ? WHERE artifact_id = ?",
                (state.value, artifact_id),
            )
        self._record("mark", f"{artifact_id}/{state.value}")

    def list_refs(self) -> tuple[Artifact, ...]:
        self._ensure_open()
        rows = self._conn.execute("SELECT * FROM artifacts ORDER BY created_at").fetchall()
        self._record("list_refs", "")
        return tuple(_artifact_from_row(row) for row in rows)

    def archive(self, artifact_id: str) -> None:
        self.mark(artifact_id, ArtifactState.ARCHIVED)

    def delete(self, artifact_id: str) -> None:
        self._ensure_open()
        row = self._require_metadata("delete", artifact_id)
        current = _STATE_BY_VALUE[row["state"]]
        if ArtifactState.DELETED_TOMBSTONE not in _VALID_TRANSITIONS[current]:
            self._record("delete", artifact_id, error="InvalidInputError")
            raise InvalidInputError(
                f"illegal artifact state transition {current.value} -> "
                f"{ArtifactState.DELETED_TOMBSTONE.value}",
            )
        with self._conn:
            self._conn.execute(
                "UPDATE artifacts SET state = ? WHERE artifact_id = ?",
                (ArtifactState.DELETED_TOMBSTONE.value, artifact_id),
            )
        if not self._digest_still_referenced(row["digest"], artifact_id):
            blob = self._blob_path(Digest.parse(row["digest"]))
            blob.unlink(missing_ok=True)
        self._record("delete", artifact_id)

    def _digest_still_referenced(self, digest: str, excluding_id: str) -> bool:
        """内容寻址去重：blob 只有在无其他非 tombstone 引用时才物理删除。"""
        rows = self._conn.execute(
            "SELECT 1 FROM artifacts WHERE digest = ? AND artifact_id != ? AND state != ?",
            (digest, excluding_id, ArtifactState.DELETED_TOMBSTONE.value),
        ).fetchall()
        return len(rows) > 0

    def _insert_metadata(self, artifact: Artifact) -> None:
        self._conn.execute(
            "INSERT INTO artifacts (artifact_id, digest, size_bytes, media_type, storage_uri,"
            " created_by, source_refs_json, classification, retention_policy, state, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                artifact.id,
                str(artifact.digest),
                artifact.size_bytes,
                artifact.media_type,
                artifact.storage_uri,
                artifact.created_by,
                json.dumps(artifact.source_refs),
                artifact.classification,
                _policy_to_text(artifact.retention_policy),
                artifact.state.value,
                _created_at_text(artifact, self._now),
            ),
        )

    def _update_metadata(self, artifact: Artifact) -> None:
        self._conn.execute(
            "UPDATE artifacts SET digest = ?, size_bytes = ?, media_type = ?, storage_uri = ?,"
            " created_by = ?, source_refs_json = ?, classification = ?, retention_policy = ?,"
            " state = ? WHERE artifact_id = ?",
            (
                str(artifact.digest),
                artifact.size_bytes,
                artifact.media_type,
                artifact.storage_uri,
                artifact.created_by,
                json.dumps(artifact.source_refs),
                artifact.classification,
                _policy_to_text(artifact.retention_policy),
                artifact.state.value,
                artifact.id,
            ),
        )

    def _require_metadata(self, method: str, artifact_id: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()
        if row is None:
            self._record(method, artifact_id, error="InvalidInputError")
            raise InvalidInputError(f"unknown artifact id: {artifact_id}")
        assert isinstance(row, sqlite3.Row)
        return row

    def _blob_path(self, digest: Digest) -> Path:
        return self._blob_root / digest.hex_value[:2] / digest.hex_value


def _artifact_from_row(row: sqlite3.Row) -> Artifact:
    return Artifact(
        id=row["artifact_id"],
        digest=Digest.parse(row["digest"]),
        size_bytes=row["size_bytes"],
        media_type=row["media_type"],
        storage_uri=row["storage_uri"],
        created_by=row["created_by"],
        source_refs=list(json.loads(row["source_refs_json"])),
        classification=row["classification"],
        retention_policy=_policy_from_text(row["retention_policy"]),
        state=_STATE_BY_VALUE[row["state"]],
        created_at=Timestamp(parse_iso(row["created_at"])),
    )


def _policy_to_text(policy: ArtifactRetentionPolicy | None) -> str | None:
    return policy.to_str() if policy is not None else None


def _policy_from_text(text: str | None) -> ArtifactRetentionPolicy | None:
    return ArtifactRetentionPolicy.parse(text) if text is not None else None


def _created_at_text(artifact: Artifact, now: Callable[[], datetime] | None) -> str:
    """created_at：优先采纳 artifact 声明的创建时间（导入/迁移场景），
    否则用注入时钟（默认真实当前时间）。"""
    if artifact.created_at is not None:
        return artifact.created_at.value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return now_iso(now)
