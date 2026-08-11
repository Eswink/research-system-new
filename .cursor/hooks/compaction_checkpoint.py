#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone

from common import RUNTIME, atomic_json, emit, read_event, safe_id


def main() -> int:
    event = read_event()
    cid = safe_id(event.get("conversation_id"))
    atomic_json(RUNTIME / "compaction" / f"{cid}.json", {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "trigger": event.get("trigger"),
        "context_usage_percent": event.get("context_usage_percent"),
        "message_count": event.get("message_count"),
    })
    emit({"user_message": "上下文即将压缩；继续工作前以活动 Plan、验证证据和仓库文件为准，不依赖聊天记忆。"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
