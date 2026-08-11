#!/usr/bin/env python3
from __future__ import annotations

from common import RUNTIME, allow, deny, read_event_result, safe_id

MAX_PARALLEL_SUBAGENTS = 3


def main() -> int:
    # hooks.json scopes this script to matcher=Task.
    event, error = read_event_result()
    if error is not None:
        deny(
            f"子代理门禁无法解析 Cursor Hook 输入，已按 fail-closed 拒绝委派：{error}",
            "修复 Hook JSON 协议后重试。",
        )
        return 0
    assert event is not None

    conversation_raw = event.get("conversation_id") or event.get("parent_conversation_id")
    if not isinstance(conversation_raw, str) or not conversation_raw.strip():
        deny("子代理门禁缺少 conversation_id，已按 fail-closed 拒绝委派。")
        return 0

    conversation = safe_id(conversation_raw)
    bucket = RUNTIME / "subagents" / conversation
    active = len(list(bucket.glob("*.active"))) if bucket.exists() else 0
    if active >= MAX_PARALLEL_SUBAGENTS:
        deny(
            f"当前并行 wave 已有 {active} 个 active 子代理；上限为 {MAX_PARALLEL_SUBAGENTS}。"
            "请等待已有子代理结束并整合结果后再创建下一 wave。"
        )
        return 0
    allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
