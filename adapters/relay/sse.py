"""SSE 行解析（自实现，无第三方依赖）。

OpenAI Chat Completions 流式响应为简化 SSE：
- 每个事件 `data: <json>\\n\\n`
- 结束 `data: [DONE]\\n\\n`
- 忽略 `event:` / `id:` / 注释行

实现为生成器：逐行消费，产出完整 JSON 事件；`[DONE]` 终止。
"""

from __future__ import annotations

import json
from collections.abc import Iterator

_DONE = "[DONE]"


def parse_sse_events(lines: Iterator[str]) -> Iterator[dict[str, object]]:
    """从文本行迭代器解析 SSE 事件（跳过注释与元数据行）。

    每产出一次代表一个 `data:` 载荷；多行 `data:` 会拼接为一行 JSON。
    """
    data_lines: list[str] = []
    for line in lines:
        stripped = line.rstrip("\r\n")
        if stripped.startswith(":"):
            continue
        if stripped.startswith("data:"):
            data_lines.append(stripped[5:].lstrip())
            continue
        if stripped == "" and data_lines:
            payload = "\n".join(data_lines)
            data_lines = []
            if payload == _DONE:
                return
            if payload:
                yield json.loads(payload)
    if data_lines:
        payload = "\n".join(data_lines)
        if payload and payload != _DONE:
            yield json.loads(payload)
