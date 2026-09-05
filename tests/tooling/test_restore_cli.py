"""Cross-platform personal PostgreSQL and Artifact restore CLI tests."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import subprocess
import sys
import tarfile
from pathlib import Path
from types import ModuleType
from typing import Any, BinaryIO, cast

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _ROOT / "tools" / "restore.py"


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("researchos_restore", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _archive(path: Path, name: str, content: bytes) -> None:
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo(name)
        info.size = len(content)
        archive.addfile(info, io.BytesIO(content))


def test_restore_cli_help_is_available() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(_SCRIPT), "--help"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "--dump" in completed.stdout
    assert "--artifact-archive" in completed.stdout
    assert "--blob-target" in completed.stdout


def test_artifact_restore_verifies_content_addressed_digest(tmp_path: Path) -> None:
    module = _module()
    content = b"restored artifact content"
    digest = hashlib.sha256(content).hexdigest()
    archive = tmp_path / "artifacts.tar.gz"
    _archive(archive, f"{digest[:2]}/{digest}", content)
    target = tmp_path / "restored"

    checked = module.restore_artifacts(archive, target)

    assert checked == 1
    assert target.joinpath(digest[:2], digest).read_bytes() == content


def test_artifact_restore_rejects_path_traversal(tmp_path: Path) -> None:
    module = _module()
    archive = tmp_path / "bad.tar.gz"
    _archive(archive, "../escape", b"bad")

    with pytest.raises(ValueError, match="unsafe archive member"):
        module.restore_artifacts(archive, tmp_path / "target")


def test_postgres_restore_streams_dump_bytes_without_shell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()
    dump = tmp_path / "state.dump"
    dump.write_bytes(b"PGDMP-binary\x00payload")
    observed: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: object) -> object:
        observed["command"] = command
        handle = cast(BinaryIO, kwargs["stdin"])
        observed["bytes"] = handle.read()
        observed["shell"] = kwargs.get("shell")
        return object()

    monkeypatch.setattr(module, "_run", fake_run)

    module.restore_postgres("restore-postgres", dump)

    assert observed["bytes"] == dump.read_bytes()
    assert observed["shell"] is False
    assert observed["command"][:4] == ["docker", "exec", "-i", "restore-postgres"]
