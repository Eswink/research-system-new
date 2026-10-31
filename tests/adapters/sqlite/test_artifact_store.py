"""SqliteArtifactStore 单元测试：digest 校验、状态流转、tombstone、幂等。"""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.sqlite.artifact_store import SqliteArtifactStore
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact, validate_supersedes
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


class TestSupersedesRoundTrip:
    """GOAL-20261031-102 EC-01：`supersedes` 在 **SQLite 序列化两侧**逐字节往返。"""

    def test_supersedes_survives_put_and_meta(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        content = b"manuscript v1"
        store.put(_artifact(content, "run-1:manuscript.md"), content)
        child_content = b"manuscript v2"
        child = _artifact(child_content, "run-1:manuscript_v2.md")
        child = Artifact(
            id=child.id,
            digest=child.digest,
            size_bytes=child.size_bytes,
            media_type=child.media_type,
            supersedes="run-1:manuscript.md",
        )
        store.put(child, child_content)
        loaded = store.meta("run-1:manuscript_v2.md")
        assert loaded is not None
        assert loaded.supersedes == "run-1:manuscript.md", loaded
        parent = store.meta("run-1:manuscript.md")
        assert parent is not None and parent.supersedes is None

    def test_update_writes_supersedes(self, tmp_path: Path) -> None:
        """覆盖写（同 id 二次 put）也带上父指针（update 侧同受判）。"""
        store = _store(tmp_path)
        content = b"first assembly"
        artifact = _artifact(content, "run-1:manuscript_v2.md")
        store.put(artifact, content)
        revised = Artifact(
            id=artifact.id,
            digest=artifact.digest,
            size_bytes=artifact.size_bytes,
            media_type=artifact.media_type,
            supersedes="run-1:manuscript.md",
        )
        store.put(revised, content)
        loaded = store.meta("run-1:manuscript_v2.md")
        assert loaded is not None and loaded.supersedes == "run-1:manuscript.md"

    def test_chain_validates_across_stored_rows(self, tmp_path: Path) -> None:
        """存储行读回的制品足以做**同 run** 链校验（产品路径的判法）。"""
        store = _store(tmp_path)
        v1 = b"v1"
        v2 = b"v2"
        store.put(_artifact(v1, "run-1:manuscript.md"), v1)
        store.put(
            Artifact(
                id="run-1:manuscript_v2.md",
                digest=Digest.of_bytes(v2),
                size_bytes=len(v2),
                media_type="text/plain",
                supersedes="run-1:manuscript.md",
            ),
            v2,
        )
        loaded = store.meta("run-1:manuscript_v2.md")
        assert loaded is not None
        validate_supersedes(loaded, run_id="run-1", resolve=store.meta)
