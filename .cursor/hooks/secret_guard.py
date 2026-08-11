#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from common import allow, deny, is_sensitive_path, read_event_result


def read_target(event: dict[str, Any]) -> str | None:
    tool_input = event.get("tool_input")
    candidates = [event.get("path"), event.get("file_path")]
    if isinstance(tool_input, dict):
        candidates.extend((tool_input.get("path"), tool_input.get("file_path")))
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return None


def main() -> int:
    event, error = read_event_result()
    if error is not None:
        deny(
            f"安全门禁无法解析 Cursor Hook 输入，已按 fail-closed 拒绝读取：{error}",
            "修复 Hook JSON 协议后重试。",
        )
        return 0
    assert event is not None

    target = read_target(event)
    if target is None:
        deny(
            "安全门禁缺少待读取文件路径，已按 fail-closed 拒绝读取。",
            "Read 事件必须提供 tool_input.path 或兼容的 file_path 字段。",
        )
        return 0
    if is_sensitive_path(target):
        deny("安全策略阻止读取真实凭据/私钥文件。请使用脱敏示例或受控 credential mechanism。")
        return 0

    allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
