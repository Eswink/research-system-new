#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from _release_files import NON_RELEASE_DIRS, RUNTIME_KEEP, archive_files


def _discover_root() -> Path:
    explicit = os.environ.get("CURSOR_FRAMEWORK_ROOT")
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "VERSION").is_file() and (candidate / ".cursor" / "framework.json").is_file():
            return candidate
    raise RuntimeError("Cannot locate repository root (VERSION + .cursor/framework.json)")


ROOT = _discover_root()
PYTHON = sys.executable


def run_checked(script: Path, root: Path, env: dict[str, str], extra: list[str] | None = None) -> None:
    cmd = [PYTHON, "-B", str(script), *(extra or [])]
    run_env = {**env, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    cp = subprocess.run(
        cmd,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=run_env,
        timeout=120,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"clean-extraction regression failed: {script.name}\n{(cp.stdout + cp.stderr)[-3000:]}")


def assert_archive_hygiene(zf: zipfile.ZipFile, archive_root: str) -> None:
    prefix = archive_root.rstrip("/") + "/"
    bad = []
    for name in zf.namelist():
        rel = name[len(prefix):] if name.startswith(prefix) else name
        if "__pycache__/" in rel or rel.endswith(".pyc") or NON_RELEASE_DIRS.intersection(rel.split("/")):
            bad.append(rel)
        if rel.startswith(".cursor/runtime/") and rel not in RUNTIME_KEEP:
            bad.append(rel)
        if rel.startswith("scripts/"):
            bad.append(rel)
    if bad:
        raise RuntimeError(f"archive hygiene failure: {sorted(set(bad))[:30]}")
    bad_crc = zf.testzip()
    if bad_crc:
        raise RuntimeError(f"ZIP CRC failure: {bad_crc}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--version")
    args = parser.parse_args()

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if args.version and args.version != version:
        print(f"ERROR: requested {args.version}, repository is {version}")
        return 2

    manifest = ROOT / "FRAMEWORK_MANIFEST.json"
    evidence = ROOT / ".cursor/releases/RELEASE_EVIDENCE.json"
    if not manifest.is_file() or not evidence.is_file():
        print("ERROR: run framework release before packaging")
        return 2

    env = os.environ.copy()
    env["CURSOR_FRAMEWORK_ROOT"] = str(ROOT)
    verify_script = ROOT / ".cursor/skills/framework-release/scripts/verify_cursor_framework_release.py"
    try:
        run_checked(verify_script, ROOT, env, ["--version", version])
    except RuntimeError as exc:
        print(f"ERROR: source release verification failed\n{exc}")
        return 3

    requested_output = Path(args.output).expanduser() if args.output else ROOT.parent / f"system-specification-cursor-framework-v{version}.zip"
    output = requested_output.resolve() if requested_output.is_absolute() else (ROOT / requested_output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    archive_root = f"system-specification-cursor-framework-v{version}"

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(archive_files(ROOT, output)):
            zf.write(path, Path(archive_root) / path.relative_to(ROOT))

    try:
        with zipfile.ZipFile(output) as zf:
            assert_archive_hygiene(zf, archive_root)
            with tempfile.TemporaryDirectory(prefix="cursor-framework-package-") as td:
                unpack_dir = Path(td)
                zf.extractall(unpack_dir)
                unpacked_root = unpack_dir / archive_root
                unpack_env = os.environ.copy()
                unpack_env["CURSOR_FRAMEWORK_ROOT"] = str(unpacked_root)
                unpack_env["CURSOR_EXPECTED_FRAMEWORK_VERSION"] = version
                suite = [
                    ".cursor/skills/system-spec-check/scripts/validate_bundle.py",
                    ".cursor/skills/governance-check/scripts/validate.py",
                    ".cursor/skills/cursor-framework-check/scripts/validate_cursor_framework.py",
                    ".cursor/skills/learning-check/scripts/validate_cursor_learning.py",
                    ".cursor/skills/cursor-framework-check/scripts/run_cursor_hook_evals.py",
                    ".cursor/skills/cursor-framework-check/scripts/run_cursor_framework_evals.py",
                    ".cursor/skills/learning-check/scripts/run_cursor_learning_evals.py",
                ]
                for rel in suite:
                    run_checked(unpacked_root / rel, unpacked_root, unpack_env)
                run_checked(unpacked_root / ".cursor/skills/framework-release/scripts/verify_cursor_framework_release.py", unpacked_root, unpack_env, ["--version", version])
    except (RuntimeError, zipfile.BadZipFile) as exc:
        output.unlink(missing_ok=True)
        print(f"ERROR: packaged artifact verification failed\n{exc}")
        return 4

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    sha_path = output.with_suffix(output.suffix + ".sha256")
    sha_path.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    print(f"PASS: packaged, hygiene-checked, clean-extraction-regressed {output}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
