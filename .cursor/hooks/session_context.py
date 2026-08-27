#!/usr/bin/env python3
from __future__ import annotations

import json

from common import ROOT, RUNTIME, atomic_json, emit, read_event


def _experience_summary() -> str:
    index_path = ROOT / ".cursor" / "experience" / "INDEX.md"
    try:
        lines = index_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    rows: list[tuple[str, str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|") or "|---" in line:
            continue
        cells = [cell.strip() for cell in stripped[1:].split("|")]
        if len(cells) < 7:
            continue
        entry_id = cells[0]
        if entry_id.startswith("[") and "](" in entry_id:
            entry_id = entry_id[1:].split("]")[0]
        if entry_id.startswith("EXP-"):
            rows.append((entry_id, f"{cells[5]}(置信度 {cells[2]})"))
    if not rows:
        return ""
    recent = ", ".join(summary for _, summary in rows[-5:])
    return f" 工程经验库 {len(rows)} 条（最近：{recent}）；遇到 validator/hook/构建失败时先查 .cursor/experience/INDEX.md，命中标题则读取对应条目作为参考线索（经验条目不是工程事实，不得作为 Rule/Memory 证据）。"


def main() -> int:
    event = read_event()
    framework_path = ROOT / ".cursor" / "framework.json"
    try:
        framework = json.loads(framework_path.read_text(encoding="utf-8"))
    except Exception:
        framework = {}
    version = str(framework.get("framework_version") or "unknown")
    cursor_version = str(event.get("cursor_version") or "unknown")
    atomic_json(
        RUNTIME / "cursor_version.json", {"observed": cursor_version, "project_version": version}
    )
    context = (
        f"Research OS Cursor Engineering Framework / system specification version {version}. "
        "复杂或高影响任务先确认适用的仓库契约；需要细节时按需查阅 AGENTS.md、.cursor/knowledge/INDEX.md 和活动计划（如存在），不重复注入整篇文档。"
        "Rule=稳定约束，Skill=按需流程，Subagent=独立上下文/并行复核，Hook=防御性观测或门禁（非 Sandbox）。"
        "Subagent 按需使用；每个并行 wave 最多3个，任务总累计不设固定上限；本项目采用比 Cursor 平台更严格的 no-nesting 策略；不得把 Cursor 工程记忆写入 Research OS 产品 Memory。"
        "并行 wave 必须同一条消息一次性发出全部 Task 工具调用，禁止逐个启动、等待上一个完成后再启动下一个。"
    )
    emit({
        "env": {
            "RESEARCH_OS_PROJECT_VERSION": version,
            "RESEARCH_OS_CURSOR_FRAMEWORK_VERSION": version,
        },
        "additional_context": context
        + f" 当前 Cursor version={cursor_version}；未验证版本的行为结论以 .cursor/knowledge/SOURCES.yaml 的 T1 官方来源为准，版本化兼容结论以 .cursor/compatibility/CURSOR_COMPATIBILITY.yaml 为准。"
        + _experience_summary(),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
