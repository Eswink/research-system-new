"""Export bundle use case 测试（M9）：打包 → 解包 → digest 复核往返。"""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.sqlite.artifact_store import SqliteArtifactStore
from packages.application.artifacts import build_export_bundle, decode_export_bundle
from packages.application.ports.errors import InvalidInputError
from packages.domain.artifacts import Artifact
from packages.domain.core import Digest, ID
from packages.domain.reproducibility import ReproducibilityAudit

_RUN_ID = ID("7a2b3c4d-5e6f-4a5b-9c0d-1e2f3a4b5c6d")


def _put(store: SqliteArtifactStore, artifact_id: str, content: bytes) -> None:
    store.put(
        Artifact(
            id=artifact_id,
            digest=Digest.of_bytes(content),
            size_bytes=len(content),
            media_type="application/octet-stream",
        ),
        content,
    )


def _audit() -> ReproducibilityAudit:
    return ReproducibilityAudit(
        audit_id=ID("8b3c4d5e-6f7a-4b5c-9d0e-1f2a3b4c5d6e"),
        experiment_run_id=_RUN_ID,
        input_digest=Digest.of_bytes(b"input"),
        seed=42,
    ).with_audit_digest()


class TestExportBundle:
    def test_build_and_decode_roundtrip(self, tmp_path: Path) -> None:
        store = SqliteArtifactStore(blob_dir=tmp_path / "blobs")
        _put(store, "a-1", b"alpha-content")
        _put(store, "a-2", b"beta-content")
        bundle_id = build_export_bundle(
            _RUN_ID, _audit(), export_id="exp-1", artifacts=store
        )
        manifest, contents = decode_export_bundle(store, bundle_id)
        assert manifest.export_id == "exp-1"
        assert manifest.experiment_run_id == str(_RUN_ID.value)
        assert manifest.audit_digest is not None
        assert {entry.artifact_id for entry in manifest.entries} == {"a-1", "a-2"}
        assert contents["a-1"] == b"alpha-content"
        assert contents["a-2"] == b"beta-content"

    def test_bundle_is_content_addressed(self, tmp_path: Path) -> None:
        store = SqliteArtifactStore(blob_dir=tmp_path / "blobs")
        _put(store, "a-1", b"alpha-content")
        first = build_export_bundle(_RUN_ID, _audit(), export_id="exp-1", artifacts=store)
        second = build_export_bundle(_RUN_ID, _audit(), export_id="exp-1", artifacts=store)
        assert first == second

    def test_tampered_content_fails_decode(self, tmp_path: Path) -> None:
        store = SqliteArtifactStore(blob_dir=tmp_path / "blobs")
        _put(store, "a-1", b"alpha-content")
        bundle_id = build_export_bundle(_RUN_ID, _audit(), export_id="exp-1", artifacts=store)
        tampered = bytearray(store.get(bundle_id))
        tampered[-1] ^= 0xFF
        store.put(
            Artifact(
                id="tampered-bundle",
                digest=Digest.of_bytes(bytes(tampered)),
                size_bytes=len(tampered),
                media_type="application/vnd.research-os.export-bundle",
            ),
            bytes(tampered),
        )
        with pytest.raises(InvalidInputError):
            decode_export_bundle(store, "tampered-bundle")

    def test_bad_magic_rejected(self, tmp_path: Path) -> None:
        store = SqliteArtifactStore(blob_dir=tmp_path / "blobs")
        _put(store, "a-1", b"alpha-content")
        bundle_id = build_export_bundle(_RUN_ID, None, export_id="exp-1", artifacts=store)
        corrupted = b"GARBAGE!" + store.get(bundle_id)[8:]
        store.put(
            Artifact(
                id="corrupt-bundle",
                digest=Digest.of_bytes(corrupted),
                size_bytes=len(corrupted),
                media_type="application/vnd.research-os.export-bundle",
            ),
            corrupted,
        )
        with pytest.raises(InvalidInputError):
            decode_export_bundle(store, "corrupt-bundle")

    def test_empty_export_rejected(self, tmp_path: Path) -> None:
        store = SqliteArtifactStore(blob_dir=tmp_path / "blobs")
        with pytest.raises(InvalidInputError):
            build_export_bundle(_RUN_ID, None, export_id="exp-1", artifacts=store)