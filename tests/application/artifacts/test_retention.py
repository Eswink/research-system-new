"""Artifact retention use case 测试（M9）。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from adapters.sqlite.artifact_store import SqliteArtifactStore
from packages.application.artifacts import apply_retention
from packages.domain.artifacts import Artifact, ArtifactRetentionPolicy
from packages.domain.core import Digest, Timestamp
from packages.domain.enums import ArtifactState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _Clock:
    def __init__(self) -> None:
        self.current = _EPOCH

    def __call__(self) -> datetime:
        return self.current

    def advance(self, days: int) -> None:
        self.current += timedelta(days=days)


def _artifact(
    artifact_id: str,
    content: bytes,
    *,
    policy: ArtifactRetentionPolicy | None,
    state: ArtifactState = ArtifactState.ACTIVE,
    created_at: Timestamp,
) -> tuple[Artifact, bytes]:
    return (
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="text/plain",
            retention_policy=policy,
            state=state,
            created_at=created_at,
        ),
        content,
    )


def _store(tmp_path: Path, clock: _Clock) -> SqliteArtifactStore:
    return SqliteArtifactStore(blob_dir=tmp_path / "blobs", now=clock)


class TestRetentionPolicyActions:
    def test_expired_retain_days_is_archived(self, tmp_path: Path) -> None:
        clock = _Clock()
        store = _store(tmp_path, clock)
        artifact, content = _artifact(
            "a-expired",
            b"data-1",
            policy=ArtifactRetentionPolicy.retain_days(30),
            created_at=Timestamp(_EPOCH - timedelta(days=31)),
        )
        store.put(artifact, content)
        report = apply_retention(store, now=clock())
        assert report.archived == ("a-expired",)
        assert store.list_refs()[0].state is ArtifactState.ARCHIVED

    def test_unexpired_retain_days_is_kept(self, tmp_path: Path) -> None:
        clock = _Clock()
        store = _store(tmp_path, clock)
        artifact, content = _artifact(
            "a-fresh",
            b"data-2",
            policy=ArtifactRetentionPolicy.retain_days(30),
            created_at=Timestamp(_EPOCH - timedelta(days=10)),
        )
        store.put(artifact, content)
        report = apply_retention(store, now=clock())
        assert report.archived == ()
        assert store.list_refs()[0].state is ArtifactState.ACTIVE

    def test_keep_forever_never_archived(self, tmp_path: Path) -> None:
        clock = _Clock()
        store = _store(tmp_path, clock)
        artifact, content = _artifact(
            "a-forever",
            b"data-3",
            policy=ArtifactRetentionPolicy.keep_forever(),
            created_at=Timestamp(_EPOCH - timedelta(days=3650)),
        )
        store.put(artifact, content)
        report = apply_retention(store, now=clock())
        assert report.archived == ()
        assert store.list_refs()[0].state is ArtifactState.ACTIVE

    def test_legal_hold_never_deleted(self, tmp_path: Path) -> None:
        clock = _Clock()
        store = _store(tmp_path, clock)
        artifact, content = _artifact(
            "a-hold",
            b"data-4",
            policy=ArtifactRetentionPolicy.legal_hold(),
            created_at=Timestamp(_EPOCH - timedelta(days=3650)),
        )
        store.put(artifact, content)
        report = apply_retention(store, now=clock())
        assert report.archived == () and report.deleted == ()

    def test_old_quarantined_is_deleted(self, tmp_path: Path) -> None:
        clock = _Clock()
        store = _store(tmp_path, clock)
        artifact, content = _artifact(
            "a-quarantined",
            b"data-5",
            policy=ArtifactRetentionPolicy.keep_forever(),
            state=ArtifactState.QUARANTINED,
            created_at=Timestamp(_EPOCH - timedelta(days=20)),
        )
        store.put(artifact, content)
        report = apply_retention(store, now=clock(), quarantine_days=14)
        assert report.deleted == ("a-quarantined",)
        assert store.list_refs()[0].state is ArtifactState.DELETED_TOMBSTONE

    def test_fresh_quarantined_is_kept(self, tmp_path: Path) -> None:
        clock = _Clock()
        store = _store(tmp_path, clock)
        artifact, content = _artifact(
            "a-quarantined-fresh",
            b"data-6",
            policy=ArtifactRetentionPolicy.keep_forever(),
            state=ArtifactState.QUARANTINED,
            created_at=Timestamp(_EPOCH - timedelta(days=3)),
        )
        store.put(artifact, content)
        report = apply_retention(store, now=clock(), quarantine_days=14)
        assert report.deleted == ()
        assert store.list_refs()[0].state is ArtifactState.QUARANTINED

    def test_naive_now_rejected(self, tmp_path: Path) -> None:
        store = _store(tmp_path, _Clock())
        with pytest.raises(ValueError):
            apply_retention(store, now=datetime(2026, 1, 1))


class TestSharedBlobDeletion:
    def test_delete_keeps_shared_blob_alive(self, tmp_path: Path) -> None:
        """内容寻址去重：一个引用删除后，共享 blob 不得物理删除。"""
        clock = _Clock()
        store = _store(tmp_path, clock)
        content = b"shared-payload"
        first, _ = _artifact(
            "a-1",
            content,
            policy=ArtifactRetentionPolicy.keep_forever(),
            created_at=Timestamp(_EPOCH),
        )
        second, _ = _artifact(
            "a-2",
            content,
            policy=ArtifactRetentionPolicy.keep_forever(),
            created_at=Timestamp(_EPOCH),
        )
        store.put(first, content)
        store.put(second, content)
        store.delete("a-1")
        assert store.get("a-2") == content
        assert store.verify("a-2")

    def test_delete_last_reference_removes_blob(self, tmp_path: Path) -> None:
        clock = _Clock()
        store = _store(tmp_path, clock)
        content = b"sole-payload"
        artifact, _ = _artifact(
            "a-1",
            content,
            policy=ArtifactRetentionPolicy.keep_forever(),
            created_at=Timestamp(_EPOCH),
        )
        store.put(artifact, content)
        store.delete("a-1")
        with pytest.raises(Exception):
            store.get("a-1")
