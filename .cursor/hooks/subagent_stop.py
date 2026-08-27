#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from common import RUNTIME, emit, read_event, resolve_bucket_id, resolve_task_text


def task_signature(value: object) -> str:
    return hashlib.sha256(str(value or "").strip().encode("utf-8")).hexdigest()[:20]


def read_token(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def candidate_tokens(event: dict) -> list[Path]:
    root = RUNTIME / "subagents"
    if not root.exists():
        return []

    # subagentStop has no hook-specific subagent_id/parent_conversation_id in the
    # current Cursor schema. The common conversation_id is only a best-effort hint.
    conversation = resolve_bucket_id(event)
    preferred = root / conversation
    candidates = list(preferred.glob("*.active")) if preferred.exists() else []
    if candidates:
        return candidates
    return list(root.glob("*/*.active"))


def main() -> int:
    event = read_event()
    wanted_type = str(event.get("subagent_type") or "")
    wanted_task = task_signature(resolve_task_text(event))

    scored: list[tuple[int, float, Path]] = []
    has_task = bool(resolve_task_text(event))
    for token in candidate_tokens(event):
        meta = read_token(token)
        score = 0
        if wanted_type and meta.get("subagent_type") == wanted_type:
            score += 2
        if has_task and meta.get("task_signature") == wanted_task:
            score += 4
        try:
            mtime = token.stat().st_mtime
        except OSError:
            continue
        scored.append((score, mtime, token))

    if scored:
        scored.sort(key=lambda item: (-item[0], item[1], item[2].as_posix()))
        scored[0][2].unlink(missing_ok=True)

    # Cursor's current subagentStop output schema only defines followup_message.
    # Cleanup needs no follow-up, so emit an empty JSON object rather than a
    # permission field that belongs to subagentStart/before* hooks.
    emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
