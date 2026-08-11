#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

from common import RUNTIME, allow, deny, read_event_result, safe_id

MAX_PARALLEL_SUBAGENTS = 3


def task_signature(value: object) -> str:
    return hashlib.sha256(str(value or "").strip().encode("utf-8")).hexdigest()[:20]


def main() -> int:
    event, error = read_event_result()
    if error is not None:
        deny(
            f"子代理门禁无法解析 Cursor Hook 输入，已按 fail-closed 拒绝启动：{error}",
            "修复 Hook JSON 协议后重试。",
        )
        return 0
    assert event is not None

    parent_raw = event.get("parent_conversation_id") or event.get("conversation_id")
    subagent_raw = event.get("subagent_id") or event.get("tool_call_id")
    subagent_type = event.get("subagent_type")
    task = event.get("task")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (parent_raw, subagent_raw, subagent_type, task)
    ):
        deny("子代理门禁缺少 parent/subagent/type/task 字段，已按 fail-closed 拒绝启动。")
        return 0

    parent = safe_id(parent_raw)
    subagent = safe_id(subagent_raw)
    bucket = RUNTIME / "subagents" / parent
    bucket.mkdir(parents=True, exist_ok=True)
    token = bucket / f"{subagent}.active"
    if token.exists():
        allow()
        return 0

    active = len(list(bucket.glob("*.active")))
    if active >= MAX_PARALLEL_SUBAGENTS:
        deny(
            f"单个并行委派波次最多 {MAX_PARALLEL_SUBAGENTS} 个子代理。"
            "请等待现有子代理结束并整合结果，再决定是否启动下一波。"
        )
        return 0

    metadata = {
        "parent_signature": parent,
        "subagent_signature": subagent,
        "subagent_type": str(event.get("subagent_type") or ""),
        "task_signature": task_signature(event.get("task")),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        fd = os.open(token, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, ensure_ascii=False)
            fh.write("\n")
    except FileExistsError:
        pass
    allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
