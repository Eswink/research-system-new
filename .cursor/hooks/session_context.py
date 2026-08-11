#!/usr/bin/env python3
from __future__ import annotations

import json

from common import ROOT, RUNTIME, atomic_json, emit, read_event


def main() -> int:
    event = read_event()
    framework_path = ROOT / ".cursor" / "framework.json"
    try:
        framework = json.loads(framework_path.read_text(encoding="utf-8"))
    except Exception:
        framework = {}
    version = str(framework.get("framework_version") or "unknown")
    cursor_version = str(event.get("cursor_version") or "unknown")
    atomic_json(RUNTIME / "cursor_version.json", {"observed": cursor_version, "project_version": version})
    context = (
        f"Research OS Cursor Engineering Framework / system specification version {version}. "
        "复杂或高影响任务先确认适用的仓库契约；需要细节时按需查阅 AGENTS.md、.cursor/knowledge/INDEX.md 和活动计划（如存在），不重复注入整篇文档。"
        "Rule=稳定约束，Skill=按需流程，Subagent=独立上下文/并行复核，Hook=防御性观测或门禁（非 Sandbox）。"
        "Subagent 按需使用；每个并行 wave 最多3个，任务总累计不设固定上限；本项目采用比 Cursor 平台更严格的 no-nesting 策略；不得把 Cursor 工程记忆写入 Research OS 产品 Memory。"
    )
    emit({
        "env": {
            "RESEARCH_OS_PROJECT_VERSION": version,
            "RESEARCH_OS_CURSOR_FRAMEWORK_VERSION": version,
        },
        "additional_context": context + f" 当前 Cursor version={cursor_version}；未在 compatibility matrix 验证时先运行 probe。",
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
