"""Smoke tests for tools/backup.py (PA-1 debt #8): CLI parsing, tar/prune.

The real pg_dump/docker path is exercised by the documented deployment
procedure (PERSONAL_DEPLOYMENT.md §5-6), not by unit tests.
"""

from __future__ import annotations

import hashlib
import tarfile
from pathlib import Path

import tools.backup as backup


def test_artifacts_tar_roundtrip(tmp_path: Path) -> None:
    root = tmp_path / "blobs"
    payload = b"predictable-content"
    hexv = hashlib.sha256(payload).hexdigest()
    blob = root / hexv[:2] / hexv
    blob.parent.mkdir(parents=True)
    blob.write_bytes(payload)
    dest = tmp_path / "artifacts-test.tar.gz"
    backup.artifacts_tar(root, dest)
    with tarfile.open(dest, "r:gz") as archive:
        names = archive.getnames()
        assert f"{hexv[:2]}/{hexv}" in names


def test_prune_keeps_newest(tmp_path: Path) -> None:
    for stamp in ("20260101-000000", "20260102-000000", "20260103-000000"):
        (tmp_path / f"research-os-{stamp}.dump").write_bytes(b"x")
        (tmp_path / f"artifacts-{stamp}.tar.gz").write_bytes(b"y")
    backup.prune(tmp_path, keep=2)
    remaining = sorted(p.name for p in tmp_path.iterdir())
    assert remaining == [
        "artifacts-20260102-000000.tar.gz",
        "artifacts-20260103-000000.tar.gz",
        "research-os-20260102-000000.dump",
        "research-os-20260103-000000.dump",
    ]


def test_cli_parsing_defaults(monkeypatch: object, tmp_path: Path) -> None:

    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> object:
        calls.append(cmd)
        raise AssertionError("docker must not be invoked in this test")

    monkeypatch.setattr(backup, "_run", fake_run)  # type: ignore[attr-defined]
    monkeypatch.setattr(
        backup, "artifacts_tar", lambda root, dest: dest.write_bytes(b"")  # noqa: ARG005
    )
    monkeypatch.chdir(tmp_path)
    with __import__("pytest").raises(AssertionError, match="docker must not"):
        backup.main(["--out", str(tmp_path)])
    # pg_dump path was attempted first with the default container name
    assert calls[0][:3] == ["docker", "exec", "research-system-postgres-1"]
