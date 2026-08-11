#!/usr/bin/env python3
"""Cursor stop hook: record a sanitized, local-only git status audit.

The hook never stages, commits, pushes, or prints non-JSON text to stdout.
Its runtime audit is ignored by Git and excluded from release artifacts.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys

from common import ROOT, RUNTIME, atomic_json, emit, read_event, safe_id

ALLOWED_DIRS = (".cursor", "docs", "schemas", "examples", "apps", "services", "packages", "adapters", "tests")
SENSITIVE_NAME_RE = re.compile(r"(^|/)(\\.env([.-].*)?|.*\\.(pem|key|p12))$", re.IGNORECASE)
SENSITIVE_CONTENT_RE = re.compile(
    r"(?:api[_-]?key|access[_-]?token|password|secret)\\s*[:=]\\s*[^\\s]{8,}|"
    r"\\bsk-[A-Za-z0-9_-]{20,}\\b|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
)


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=5,
    )


def is_sensitive_path(relative: str) -> bool:
    if SENSITIVE_NAME_RE.search(relative):
        return True
    path = ROOT / relative
    try:
        if path.is_file() and SENSITIVE_CONTENT_RE.search(path.read_text(encoding="utf-8", errors="ignore")):
            return True
    except OSError:
        pass
    return False


def classify_status() -> dict[str, list[str]]:
    categories = {"modified": [], "allowed_untracked": [], "sensitive": [], "outside_whitelist": []}
    try:
        result = run_git("status", "--porcelain")
    except (OSError, subprocess.TimeoutExpired):
        return categories
    if result.returncode != 0:
        return categories
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        xy, raw_path = line[:2], line[3:]
        path = raw_path.split(" -> ", 1)[-1] if (xy[0] in ("R", "C") or xy[1] in ("R", "C")) else raw_path
        if xy.startswith("??"):
            parts = path.split("/", 1)
            if is_sensitive_path(path): categories["sensitive"].append(path)
            elif len(parts) == 2 and parts[0] in ALLOWED_DIRS: categories["allowed_untracked"].append(path)
            else: categories["outside_whitelist"].append(path)
        elif is_sensitive_path(path): categories["sensitive"].append(path)
        else: categories["modified"].append(path)
    return categories


def digest_path(path: str) -> str:
    return hashlib.sha256(path.encode("utf-8", errors="replace")).hexdigest()[:16]


def main() -> int:
    event = {} if "--debug" in sys.argv else read_event()
    if event.get("hook_event_name") not in (None, "stop"):
        emit({})
        return 0

    categories = classify_status()
    payload = {
        "schema_version": 1,
        "conversation": safe_id(event.get("conversation_id")),
        "status": str(event.get("status") or "unknown"),
        "counts": {key: len(items) for key, items in categories.items()},
        # Keep the audit useful for change correlation without persisting local paths.
        "path_digests": {key: [digest_path(item) for item in items] for key, items in categories.items()},
    }
    atomic_json(RUNTIME / "git-audit" / f"{payload['conversation']}.json", payload)

    # stop hook output only needs optional followup_message; no continuation is desired.
    emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
