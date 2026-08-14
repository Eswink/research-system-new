"""SqliteArtifactStore 单元测试：digest 校验、状态流转、tombstone、幂等。"""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.sqlite.artifact_store import SqliteArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest
from packages.domain.enums import ArtifactState


def _store(tmp_path: Path) -> SqliteArtifactStore:
    return SqliteArtifactStore(":memory:", blob_dir=tmp_path / "blobs")


def _artifact(content: bytes, artifact_id: str = "a-1") -> Artifact:
    return Artifact(
        id=artifact_id,
        digest=Digest.of_bytes(content),
        size_bytes=len(content),
        media_type="text/plain",
        created_by="agent-1",
        source_refs=[f"task:{artifact_id}"],
        state=ArtifactState.STAGED,
    )


class TestPutAndVerify:
    def test_put_verifies_digest(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        content = b"analysis report"
        store.put(_artifact(content), content)
        assert store.verify("a-1") is True

    def test_put_rejects_corrupted_content(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        with pytest.raises(InvalidInputError, match="digest mismatch"):
            store.put(_artifact(b"expected"), b"tampered")

    def test_get_returns_content(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        content = b"report-body"
        store.put(_artifact(content), content)
        assert store.get("a-1") == content

    def test_put_same_id_twice_is_stable(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        content = b"data"
        artifact = _artifact(content)
        store.put(artifact, content)
        store.put(artifact, content)
        assert store.verify("a-1") is True
        assert len(store.list_refs()) == 1


class TestStateTransitions:
    def test_legal_transitions(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        content = b"data"
        store.put(_artifact(content), content)
        store.mark("a-1", ArtifactState.VERIFIED)
        store.mark("a-1", ArtifactState.ACTIVE)
        store.archive("a-1")
        assert store.list_refs()[0].state is ArtifactState.ARCHIVED

    def test_illegal_transition_rejected(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        content = b"data"
        store.put(_artifact(content), content)
        with pytest.raises(InvalidInputError, match="illegal"):
            store.mark("a-1", ArtifactState.ARCHIVED)

    def test_unknown_artifact_raises(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        with pytest.raises(InvalidInputError):
            store.get("missing")
        with pytest.raises(InvalidInputError):
            store.verify("missing")


class TestDeleteTombstone:
    def _active_artifact(self, store: SqliteArtifactStore) -> None:
        content = b"data"
        store.put(_artifact(content), content)
        store.mark("a-1", ArtifactState.VERIFIED)
        store.mark("a-1", ArtifactState.ACTIVE)

    def test_delete_makes_content_unreadable(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        self._active_artifact(store)
        store.delete("a-1")
        assert store.list_refs()[0].state is ArtifactState.DELETED_TOMBSTONE
        with pytest.raises(InvalidInputError, match="deleted"):
            store.get("a-1")
        with pytest.raises(InvalidInputError, match="deleted"):
            store.verify("a-1")

    def test_double_delete_rejected(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        self._active_artifact(store)
        store.delete("a-1")
        with pytest.raises(InvalidInputError):
            store.delete("a-1")

    def test_blob_file_removed_on_delete(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        self._active_artifact(store)
        store.delete("a-1")
        blobs = list((tmp_path / "blobs").rglob("*"))
        assert all(item.is_dir() for item in blobs)
