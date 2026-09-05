"""Cross-platform PostgreSQL and Artifact restore for personal deployment.

The command avoids shell redirection so PostgreSQL custom-format dump bytes are
preserved on Windows PowerShell as well as POSIX shells. Artifact extraction is
restricted to the content-addressed ``aa/<sha256>`` layout and verifies every
restored blob before returning success.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess as _proc
import sys
import tarfile
from pathlib import Path, PurePosixPath

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_run = _proc.run


def restore_postgres(container: str, dump: Path) -> None:
    """Stream a custom-format dump to pg_restore without a shell."""
    if not dump.is_file():
        raise FileNotFoundError(f"PostgreSQL dump not found: {dump}")
    command = [
        "docker",
        "exec",
        "-i",
        container,
        "pg_restore",
        "-U",
        "research_os",
        "-d",
        "research_os",
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-privileges",
    ]
    with dump.open("rb") as handle:
        _run(command, stdin=handle, check=True, shell=False)


def _member_target(root: Path, name: str) -> tuple[Path, str]:
    member = PurePosixPath(name)
    if member.is_absolute() or ".." in member.parts:
        raise ValueError(f"unsafe archive member: {name}")
    parts = [part for part in member.parts if part not in ("", ".")]
    if len(parts) != 2:
        raise ValueError(f"unsafe archive member: {name}")
    prefix, digest = parts
    if not _HEX64.fullmatch(digest) or prefix != digest[:2]:
        raise ValueError(f"invalid content-addressed blob path: {name}")
    target = root.joinpath(prefix, digest).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        raise ValueError(f"unsafe archive member: {name}") from None
    return target, digest


def _extract_blob(archive: tarfile.TarFile, member: tarfile.TarInfo, root: Path) -> None:
    if not member.isfile() or member.issym() or member.islnk():
        raise ValueError(f"unsafe archive member: {member.name}")
    target, expected = _member_target(root, member.name)
    source = archive.extractfile(member)
    if source is None:
        raise ValueError(f"archive member has no content: {member.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with source, target.open("wb") as output:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
            output.write(chunk)
    if digest.hexdigest() != expected:
        target.unlink(missing_ok=True)
        raise ValueError(f"artifact digest mismatch: {member.name}")


def restore_artifacts(archive_path: Path, blob_target: Path) -> int:
    """Extract and verify a content-addressed Artifact backup into an empty root."""
    if not archive_path.is_file():
        raise FileNotFoundError(f"Artifact archive not found: {archive_path}")
    if blob_target.exists() and any(blob_target.iterdir()):
        raise ValueError(f"Artifact restore target must be empty: {blob_target}")
    blob_target.mkdir(parents=True, exist_ok=True)
    checked = 0
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive.getmembers():
                _extract_blob(archive, member, blob_target)
                checked += 1
    except Exception:
        shutil.rmtree(blob_target, ignore_errors=True)
        raise
    return checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", required=True)
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--artifact-archive", type=Path)
    parser.add_argument("--blob-target", type=Path)
    args = parser.parse_args(argv)
    if (args.artifact_archive is None) != (args.blob_target is None):
        parser.error("--artifact-archive and --blob-target must be provided together")
    restore_postgres(args.container, args.dump)
    print(f"postgres: restored {args.dump} into {args.container}")
    if args.artifact_archive is not None and args.blob_target is not None:
        checked = restore_artifacts(args.artifact_archive, args.blob_target)
        print(f"artifacts: restored and verified {checked} blobs into {args.blob_target}")
    return 0


if __name__ == "__main__":
    if shutil.which("docker") is None:
        print("docker CLI not available — restore requires Docker", flush=True)
        sys.exit(2)
    sys.exit(main())
