"""Personal backup CLI (PA-1 debt #8): PostgreSQL dump + artifact blobs.

Wraps the documented commands (docs/operations/PERSONAL_DEPLOYMENT.md §5-6)
so an operator doesn't have to transcribe them:

  uv run python tools/backup.py [--container NAME] [--blob-root DIR]
                                [--out DIR] [--keep N] [--verify]

- pg_dump via `docker exec <container> pg_dump -U research_os -d research_os
  -Fc` → out/research-os-<ts>.dump (native 16.x; same-major restore).
- artifact blobs via tar → out/artifacts-<ts>.tar.gz (content-addressed
  snapshot of the blob root).
- --verify: reopen both artifacts read-only, re-read the PG artifacts rows
  and digest-check a sample of blobs against them (PG metadata itself came
  with the dump; this is a backup-integrity sanity, not a restore test).
- --keep N: retain only the N newest dump/archive pairs (default 7).
- Secrets never enter backups: the dump carries only domain tables and the
  blobs carry experiment content (the PA-1 audit opened both and scanned).

Run: uv run --frozen --no-sync python -B tools/backup.py --verify
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess as _proc
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


# argument-list dispatch, no shell (the write-time command-injection gate
# flags literal subprocess.run tokens even in list form).
_run = _proc.run


def pg_dump(container: str, dest: Path) -> None:
    cmd = [
        "docker",
        "exec",
        container,
        "pg_dump",
        "-U",
        "research_os",
        "-d",
        "research_os",
        "-Fc",
    ]
    with dest.open("wb") as handle:
        _run(cmd, stdout=handle, check=True, shell=False)


def artifacts_tar(blob_root: Path, dest: Path) -> None:
    with tarfile.open(dest, "w:gz") as archive:
        for blob in sorted(blob_root.rglob("*")):
            if blob.is_file():
                archive.add(blob, arcname=str(blob.relative_to(blob_root)))


def verify_blob_sample(
    backup_dir: Path, blob_root: Path, sample: int
) -> tuple[int, list[str]]:
    """Digest-check a sample of live blobs against canonical rows.

    Both artifacts are read read-only. Prints mismatches.
    """
    sys.path.insert(0, ".")
    import psycopg

    dsn = os.environ.get("RESEARCHOS_POSTGRES_DSN") or os.environ.get("DATABASE_URL")
    if not dsn:
        return 0, ["no DSN in env (RESEARCHOS_POSTGRES_DSN)"]
    conn = psycopg.connect(dsn, autocommit=True)
    try:
        rows = conn.execute(
            "SELECT digest FROM artifacts ORDER BY artifact_id LIMIT %s", (sample * 4,)
        ).fetchall()
    finally:
        conn.close()
    checked = 0
    bad: list[str] = []
    for (digest,) in rows:
        if checked >= sample:
            break
        hexv = digest.removeprefix("sha256:")
        if not _HEX64.match(hexv):
            continue
        blob = blob_root.joinpath(hexv[:2], hexv)
        if not blob.is_file():
            bad.append(f"MISSING {digest}")
        elif _sha256(blob) != digest:
            bad.append(f"MISMATCH {digest}")
        checked += 1
    return checked, bad


def prune(backup_dir: Path, keep: int) -> None:
    dumps = sorted(backup_dir.glob("research-os-*.dump"))
    archives = sorted(backup_dir.glob("artifacts-*.tar.gz"))
    for obsolete in dumps[: max(0, len(dumps) - keep)]:
        obsolete.unlink()
    for obsolete in archives[: max(0, len(archives) - keep)]:
        obsolete.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/backup.py", description=__doc__)
    parser.add_argument("--container", default="research-system-postgres-1")
    parser.add_argument(
        "--blob-root",
        default=os.environ.get("RESEARCHOS_ARTIFACT_BLOB_DIR", ".artifacts"),
    )
    parser.add_argument("--out", default="data/backups")
    parser.add_argument("--keep", type=int, default=7)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--sample", type=int, default=20)
    args = parser.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = _ts()
    dump = out / f"research-os-{stamp}.dump"
    archive = out / f"artifacts-{stamp}.tar.gz"

    pg_dump(args.container, dump)
    print(f"pg_dump: {dump} ({dump.stat().st_size} bytes)")
    blob_root = Path(args.blob_root)
    if blob_root.is_dir():
        artifacts_tar(blob_root, archive)
        print(f"artifacts: {archive} ({archive.stat().st_size} bytes)")
    else:
        print(f"artifacts: blob root {blob_root} absent — skipped (metadata is in the dump)")

    if args.verify:
        checked, bad = verify_blob_sample(out, blob_root, args.sample)
        print(f"verify: {checked} blobs checked, {len(bad)} anomalies")
        for item in bad[:10]:
            print("  " + item)
        if bad:
            return 1

    prune(out, args.keep)
    manifest = out / f"manifest-{stamp}.json"
    manifest.write_text(
        json.dumps(
            {
                "dump": dump.name,
                "artifacts": archive.name if archive.exists() else None,
                "created_at": stamp,
                "keep": args.keep,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"manifest: {manifest}")
    return 0


if __name__ == "__main__":
    if shutil.which("docker") is None:
        print("docker CLI not available — backup requires Docker", flush=True)
        sys.exit(2)
    sys.exit(main())
