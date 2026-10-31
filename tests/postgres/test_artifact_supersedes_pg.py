"""GOAL-20261031-102 EC-01：`supersedes` 在 **Postgres 序列化两侧**逐字节往返。

与 SQLite 侧（`tests/adapters/sqlite/test_artifact_store.py`）同一组判法；这一侧在
`030_artifact_supersedes.sql` 加列之后由 `pg_migrate` 幂等补齐 schema。无 DSN ⇒ 按
`postgres` 标记跳过（m0 的既定形态），不是没判——本仓两侧序列化各自受判。
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from adapters.postgres.artifact_store import PostgresArtifactStore
from packages.domain.artifacts import Artifact, validate_supersedes
from packages.domain.core import Digest
from tests.postgres_guard import postgres_dsn

pytestmark = pytest.mark.postgres


def _store(tmp_path: Path) -> PostgresArtifactStore:
    return PostgresArtifactStore(dsn=postgres_dsn(), blob_dir=tmp_path / "blobs")


def _artifact(content: bytes, artifact_id: str, *, supersedes: str | None = None) -> Artifact:
    return Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="text/markdown",
        supersedes=supersedes,
    )


def test_supersedes_survives_put_and_meta(tmp_path: Path) -> None:
    """run 前缀带 uuid ⇒ 与库里的历史行互不相撞（同库多次跑本判据也成立）。"""
    run = f"pgsup-{uuid.uuid4().hex[:8]}"
    store = _store(tmp_path)
    content = b"manuscript v1"
    store.put(_artifact(content, f"{run}:manuscript.md"), content)
    child = b"manuscript v2"
    store.put(_artifact(child, f"{run}:manuscript_v2.md", supersedes=f"{run}:manuscript.md"), child)
    loaded = store.meta(f"{run}:manuscript_v2.md")
    assert loaded is not None
    assert loaded.supersedes == f"{run}:manuscript.md", loaded
    parent = store.meta(f"{run}:manuscript.md")
    assert parent is not None and parent.supersedes is None
    validate_supersedes(loaded, run_id=run, resolve=store.meta)
