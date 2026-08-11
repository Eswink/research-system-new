#!/usr/bin/env python3
from __future__ import annotations

import shutil

from common import RUNTIME, emit, read_event, safe_id


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
    emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
