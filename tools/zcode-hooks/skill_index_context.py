"""ZCode `SessionStart` 注入：把本仓可调用技能的索引压成一段上下文。

**为什么需要**：ZCode 只扫描 `~/.zcode/skills`、`~/.agents/skills`、
`<repo>/.zcode/skills`、`<repo>/.agents/skills` 与插件根 —— `.cursor/skills/` 不在其中。
所以「本仓有哪些技能可调」不是模型能自己发现的，必须由机器事实注入。

注入内容只有 `name` 与 `description`，**不含正文**：正文仍要经 Skill 工具加载
（`tools/zcode-hooks/skill_invocation_guard.py` 负责拦直接读文件）。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Final

#: 仓库根：hook 的 cwd 是项目根（ZCode 约定），但仍用 `__file__` 兜底定位。
ROOT: Final[Path] = Path(__file__).resolve().parents[2]

#: 技能根（相对仓库根）。与 `skill_invocation_guard.GUARDED_SKILL_ROOT` 同一个面。
SKILLS_ROOT: Final[Path] = ROOT / ".agents" / "skills"

SKILL_FILE_NAME: Final[str] = "SKILL.md"

_HOOK_EVENT: Final[str] = "SessionStart"


def _frontmatter(text: str) -> dict[str, str]:
    """解析 `---` 围栏里的一行一件事（`key: value`）；不做 YAML 全语法。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if separator and key.strip() and not key.startswith((" ", "-")):
            fields[key.strip()] = value.strip()
    return fields


def _first_sentence(description: str, limit: int = 120) -> str:
    """取描述的首句（索引只用来路由，不承担完整触发条件）。

    分句点包含中文分号与全角冒号 —— 本仓技能的 `description` 普遍写成
    「触发条件；动作；边界」三段，只认句号会把整段带进索引。
    **取最早出现的那个分句点**，不按分隔符优先级返回：否则「句号」这一项
    一旦命中就会把后面所有分号段一并带出。
    """
    text = description.strip()
    positions = [index for delimiter in ("。", "；", "：") if (index := text.find(delimiter)) > 0]
    if positions:
        cut = min(positions)
        return text[: cut + 1]
    head = text.split(". ", 1)[0].strip()
    return head if head != text else text[:limit]


def skill_index() -> list[tuple[str, str]]:
    """按目录名排序的 `(name, 首句)`；没有技能时返回空表。"""
    if not SKILLS_ROOT.is_dir():
        return []
    entries: list[tuple[str, str]] = []
    for directory in sorted(SKILLS_ROOT.iterdir()):
        skill_file = directory / SKILL_FILE_NAME
        if not directory.is_dir() or not skill_file.is_file():
            continue
        fields = _frontmatter(skill_file.read_text(encoding="utf-8"))
        name = fields.get("name", "").strip() or directory.name
        entries.append((name, _first_sentence(fields.get("description", "").strip())))
    return entries


def build_context() -> str:
    entries = skill_index()
    if not entries:
        return ""
    lines = [
        f"本仓可调用技能 {len(entries)} 个（.agents/skills/）。任务命中下面任一条的**适用条件**时，"
        "先调 Skill 工具再动手，不要先读 SKILL.md：",
        *[f"- {name}：{summary}" for name, summary in entries],
        "调用形态：Skill(skill=<name>)。"
        "直接 Read/Bash 读 SKILL.md 会被 PreToolUse 拦下，并提示改走 Skill 工具。",
    ]
    return "\n".join(lines)


def main() -> int:
    context = build_context()
    if not context:
        return 0
    payload = {"hookSpecificOutput": {"hookEventName": _HOOK_EVENT, "additionalContext": context}}
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
