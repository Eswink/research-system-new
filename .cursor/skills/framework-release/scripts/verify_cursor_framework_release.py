#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from _release_files import releasable_files as iter_releasable_files


def _discover_root() -> Path:
    explicit = os.environ.get("CURSOR_FRAMEWORK_ROOT")
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "VERSION").is_file() and (
            candidate / ".cursor" / "framework.json"
        ).is_file():
            return candidate
    raise RuntimeError("Cannot locate repository root (VERSION + .cursor/framework.json)")


ROOT = _discover_root()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def releasable_files() -> set[str]:
    return {path.relative_to(ROOT).as_posix() for path in iter_releasable_files(ROOT)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version")
    args = ap.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    requested = args.version or version
    if requested != version:
        print("ERROR: requested version mismatch")
        return 2
    mp = ROOT / "FRAMEWORK_MANIFEST.json"
    ep = ROOT / ".cursor/releases/RELEASE_EVIDENCE.json"
    if not mp.exists() or not ep.exists():
        print("ERROR: release manifest/evidence missing")
        return 2
    m = json.loads(mp.read_text(encoding="utf-8"))
    errors = []
    if m.get("status") != "VALIDATED":
        errors.append("release status is not VALIDATED")
    if m.get("framework_version") != version:
        errors.append("framework version mismatch")
    if m.get("version_source") != "VERSION":
        errors.append("manifest version_source mismatch")
    if m.get("release_evidence_sha256") != sha(ep):
        errors.append("release evidence digest mismatch")
    try:
        evidence = json.loads(ep.read_text(encoding="utf-8"))
        if evidence.get("framework_version") != version:
            errors.append("release evidence framework version mismatch")
        if evidence.get("gate") != "DETERMINISTIC_VALIDATION":
            errors.append("release evidence gate mismatch")
        expected_scripts = [
            ".cursor/skills/system-spec-check/scripts/validate_bundle.py",
            ".cursor/skills/governance-check/scripts/validate.py",
            ".cursor/skills/cursor-framework-check/scripts/validate_cursor_framework.py",
            ".cursor/skills/learning-check/scripts/validate_cursor_learning.py",
            ".cursor/skills/cursor-framework-check/scripts/run_cursor_hook_evals.py",
            ".cursor/skills/cursor-framework-check/scripts/run_cursor_framework_evals.py",
            ".cursor/skills/learning-check/scripts/run_cursor_learning_evals.py",
        ]
        commands = evidence.get("commands") or []
        observed = []
        for item in commands:
            cmd = item.get("command") or []
            if cmd and (
                str(cmd[0]).startswith("/")
                or (len(str(cmd[0])) > 2 and str(cmd[0])[1:3] in {":\\", ":/"})
            ):
                errors.append("absolute interpreter path in release evidence")
            if item.get("returncode") != 0:
                errors.append(f"release evidence contains non-zero command: {cmd}")
            output_sha = str(item.get("output_sha256") or "")
            if len(output_sha) != 64 or any(
                ch not in "0123456789abcdef" for ch in output_sha.lower()
            ):
                errors.append(f"invalid output digest in release evidence: {cmd}")
            if len(cmd) >= 3 and cmd[0] == "python" and cmd[1] == "-B":
                observed.append(str(cmd[2]))
            else:
                errors.append(f"unexpected release command shape: {cmd}")
        if observed != expected_scripts:
            errors.append("release evidence command set/order mismatch")
    except Exception as exc:
        errors.append(f"release evidence invalid: {exc}")

    listed = {item.get("path") for item in (m.get("files") or []) if isinstance(item, dict)}
    actual = releasable_files()
    missing_from_manifest = sorted(actual - listed)
    extra_in_manifest = sorted(listed - actual)
    if missing_from_manifest:
        errors.append(f"manifest missing file entries: {missing_from_manifest[:20]}")
    if extra_in_manifest:
        errors.append(f"manifest references non-release files: {extra_in_manifest[:20]}")

    for item in m.get("files") or []:
        p = ROOT / item["path"]
        if not p.exists():
            errors.append(f"missing {item['path']}")
        elif sha(p) != item["sha256"]:
            errors.append(f"digest mismatch {item['path']}")
        elif p.stat().st_size != item.get("bytes"):
            errors.append(f"size mismatch {item['path']}")
    if errors:
        for e in errors:
            print("ERROR:", e)
        return 3
    print(f"PASS: Cursor Framework {version} manifest verified; {len(listed)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
