#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta, timezone

from common import OBSERVATION_RETENTION_DAYS, RUNTIME, emit, read_event, safe_id


def cleanup_expired_observations() -> None:
    obs_dir = RUNTIME / "observations"
    if not obs_dir.is_dir():
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=OBSERVATION_RETENTION_DAYS)
    for path in obs_dir.glob("*.jsonl"):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        if not lines:
            path.unlink(missing_ok=True)
            continue
        try:
            first = json.loads(lines[0])
            recorded = datetime.fromisoformat(str(first.get("at") or ""))
        except (json.JSONDecodeError, ValueError):
            continue
        if recorded.replace(tzinfo=timezone.utc) < cutoff:
            path.unlink(missing_ok=True)


def main() -> int:
    event = read_event()
    sid = safe_id(event.get("session_id") or event.get("conversation_id"))
    for path in (
        RUNTIME / "subagents" / sid,
        RUNTIME / "changes" / f"{sid}.jsonl",
        RUNTIME / "compaction" / f"{sid}.json",
    ):
        try:
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        except OSError:
            pass
    cleanup_expired_observations()
    emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

