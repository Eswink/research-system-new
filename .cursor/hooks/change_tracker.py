#!/usr/bin/env python3
from __future__ import annotations

import json

from common import RUNTIME, emit, read_event, safe_id


def main() -> int:
    event = read_event()
    cid = safe_id(event.get("conversation_id"))
    path = str(event.get("file_path") or "")
    target = RUNTIME / "changes" / f"{cid}.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"file_path": path, "edit_count": len(event.get("edits") or [])}, ensure_ascii=False) + "\n")
    emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
