#!/usr/bin/env python3
from __future__ import annotations

from common import RUNTIME, allow, deny, read_event_result, resolve_bucket_id

MAX_PARALLEL_SUBAGENTS = 3


def main() -> int:
    # hooks.json scopes this script to matcher=Task.
    event, error = read_event_result()
    if error is not None:
        deny(
            f"子代理门禁无法解析 Cursor Hook 输入，已按 fail-closed 拒绝委派：{error}",
            "这是项目 Hook 环境内部错误，模型侧无法修复。请停止重试该操作，"
            "并告知用户检查 Cursor Hook 环境与 .cursor/hooks/ 配置。",
        )
        return 0
    assert event is not None

    if not (
        event.get("conversation_id")
        or event.get("parent_conversation_id")
        or event.get("session_id")
    ):
        deny(
            "子代理门禁缺少 conversation_id，已按 fail-closed 拒绝委派。",
            "这是项目 Hook 环境内部错误，模型侧无法修复。请停止重试该操作，"
            "并告知用户检查 Cursor Hook 环境。",
        )
        return 0

    conversation = resolve_bucket_id(event)
    bucket = RUNTIME / "subagents" / conversation
    active = len(list(bucket.glob("*.active"))) if bucket.exists() else 0
    if active >= MAX_PARALLEL_SUBAGENTS:
        deny(
            f"当前并行 wave 已有 {active} 个 active 子代理；上限为 {MAX_PARALLEL_SUBAGENTS}。"
            "请等待已有子代理结束并整合结果后再创建下一 wave。",
            "当前并行 wave 已满：先等待已有子代理结束并整合结果，"
            "再创建下一 wave；不要立即原样重试 Task。",
        )
        return 0
    allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
