#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

from common import RUNTIME, emit, read_event, safe_id

ERROR_CLASS_PATTERNS = [
    (re.compile(r"(?i)timeout|timed out|deadline"), "TIMEOUT"),
    (re.compile(r"(?i)permission|denied|forbidden|unauthori[sz]ed|401|403"), "PERMISSION"),
    (re.compile(r"(?i)rate.?limit|429|too many requests"), "RATE_LIMIT"),
    (re.compile(r"(?i)not found|404|no such file"), "NOT_FOUND"),
    (re.compile(r"(?i)connection|dns|network|socket|tls|ssl"), "NETWORK"),
    (re.compile(r"(?i)syntax|parse|invalid json|validation"), "VALIDATION"),
]


OFFICIAL_FAILURE_TYPES = {
    "timeout": "CURSOR_TIMEOUT",
    "error": "CURSOR_ERROR",
    "permission_denied": "CURSOR_PERMISSION_DENIED",
}


def normalize_error_class(text: str, failure_type: str | None = None) -> str:
    normalized_failure_type = (failure_type or "").strip().lower().replace("-", "_")
    if normalized_failure_type in OFFICIAL_FAILURE_TYPES:
        return OFFICIAL_FAILURE_TYPES[normalized_failure_type]
    # Unknown/legacy categories are not promoted into unbounded event labels.
    for pattern, label in ERROR_CLASS_PATTERNS:
        if pattern.search(text):
            return label
    return "TOOL_FAILURE"


def safe_signature(text: str) -> str:
    # Never persist raw error text. A digest is sufficient for clustering repeated failures.
    compact = re.sub(r"\s+", " ", text.strip()).encode("utf-8", errors="replace")
    return hashlib.sha256(compact).hexdigest()[:20]


def main() -> int:
    event = read_event()
    cid = safe_id(event.get("conversation_id"))
    # Cursor's documented postToolUseFailure schema uses error_message + failure_type.
    # Legacy/fallback fields are accepted only for compatibility with older fixtures.
    raw = str(
        event.get("error_message")
        or event.get("error")
        or event.get("tool_output")
        or event.get("message")
        or ""
    )
    failure_type = str(event.get("failure_type") or "") or None
    record = {
        "at": datetime.now(timezone.utc).isoformat(),
        "tool_name": event.get("tool_name"),
        "duration_ms": event.get("duration"),
        "is_interrupt": bool(event.get("is_interrupt", False)),
        "error_class": normalize_error_class(raw, failure_type),
        "error_signature": safe_signature(raw),
    }
    target = RUNTIME / "observations" / f"{cid}.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
