#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from _release_files import releasable_files


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
CURSOR = ROOT / ".cursor"
PYTHON = sys.executable


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_command(script: str) -> list[str]:
    # Evidence is portable; do not persist build-machine absolute interpreter paths.
    return ["python", "-B", script]


def execute_command(script: str, env: dict[str, str]) -> tuple[int | str, str]:
    cmd = [PYTHON, "-B", script]
    print("RUN:", " ".join(normalized_command(script)), flush=True)
    with tempfile.TemporaryFile(mode="w+b") as log:
        try:
            cp = subprocess.run(
                cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=env, timeout=120
            )
        except subprocess.TimeoutExpired:
            log.seek(0)
            blob = log.read()
            return "TIMEOUT", hashlib.sha256(blob).hexdigest()
        log.seek(0)
        blob = log.read()
    if cp.returncode != 0 and blob:
        print(blob.decode("utf-8", errors="replace")[-3000:], flush=True)
    return cp.returncode, hashlib.sha256(blob).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version")
    args = parser.parse_args()

    fw = json.loads((CURSOR / "framework.json").read_text(encoding="utf-8"))
    version = str(fw.get("framework_version"))
    if args.version and args.version != version:
        print(f"ERROR: requested {args.version}, framework is {version}")
        return 2
    if (ROOT / "VERSION").read_text(encoding="utf-8").strip() != version:
        print("ERROR: VERSION mismatch")
        return 2

    scripts = [
        ".cursor/skills/system-spec-check/scripts/validate_bundle.py",
        ".cursor/skills/governance-check/scripts/validate.py",
        ".cursor/skills/cursor-framework-check/scripts/validate_cursor_framework.py",
        ".cursor/skills/learning-check/scripts/validate_cursor_learning.py",
        ".cursor/skills/cursor-framework-check/scripts/run_cursor_hook_evals.py",
        ".cursor/skills/cursor-framework-check/scripts/run_cursor_framework_evals.py",
        ".cursor/skills/learning-check/scripts/run_cursor_learning_evals.py",
    ]
    evidence = []
    env = os.environ.copy()
    env["CURSOR_EXPECTED_FRAMEWORK_VERSION"] = version
    env["CURSOR_FRAMEWORK_ROOT"] = str(ROOT)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    for script in scripts:
        returncode, output_sha = execute_command(script, env)
        evidence.append({
            "command": normalized_command(script),
            "returncode": returncode,
            "output_sha256": output_sha,
        })
        if returncode == "TIMEOUT":
            print(f"ERROR: release command timed out after 120s: {script}")
            return 124
        if returncode != 0:
            print(f"ERROR: release command failed: {script}")
            return int(returncode) or 4
        print("PASS:", " ".join(normalized_command(script)), flush=True)

    release_dir = CURSOR / "releases"
    release_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = release_dir / "RELEASE_EVIDENCE.json"
    evidence_doc = {
        "framework_version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate": "DETERMINISTIC_VALIDATION",
        "environment": {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": sys.platform,
        },
        "commands": evidence,
    }
    evidence_path.write_text(
        json.dumps(evidence_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    files = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": digest(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(releasable_files(ROOT))
    ]

    manifest = {
        "framework_version": version,
        "status": "VALIDATED",
        "version_source": "VERSION",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release_evidence_sha256": digest(evidence_path),
        "files": files,
    }
    (ROOT / "FRAMEWORK_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    verify = subprocess.run(
        [
            PYTHON,
            "-B",
            ".cursor/skills/framework-release/scripts/verify_cursor_framework_release.py",
            "--version",
            version,
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=env,
        timeout=120,
    )
    if verify.returncode != 0:
        print("ERROR: generated release failed manifest verification")
        print((verify.stdout + verify.stderr)[-3000:])
        return verify.returncode or 5
    print(
        f"PASS: Cursor Framework {version} deterministic release generated and verified; {len(files)} file(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
