"""ZCode `PreToolUse` 门禁：读 `.agents/skills/**/SKILL.md` 必须走 Skill 工具。

**为什么需要这个 hook**：技能正文是**按需加载**的（Skill 工具负责载入并登记
调用事实），而 `Read` / `Bash cat` 能绕过它 —— 绕过之后 agent 拿到了正文，
但既没有技能名可引用，也没有「本次确实调用过哪个技能」的事实。判据见
`tests/tooling/test_zcode_skill_invocation_guard.py`。

**射程只有 `.agents/skills/`**：`ZCode` 不扫描 `.cursor/skills/`（那 17 个技能
在 ZCode 侧没有 Skill 工具入口），拦它们等于让正文彻底不可读。射程边界是
**显式**的，不是遗漏：遍历式读取（`grep -r`）不点名 `SKILL.md`，本 hook 不拦。

输入（stdin JSON，ZCode `_In()` 组装）：`tool_name` ∈ {`Read`, `Bash`}，
`tool_input` 为对应工具的参数对象。输出只用 `hookSpecificOutput` 一种形态。
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Final

#: 受门禁的技能根（相对仓库根，POSIX 形态；判定时两种分隔符都接受）。
GUARDED_SKILL_ROOT: Final[str] = ".agents/skills"

#: 技能正文的固定文件名（生态 canonical filename，不随项目改名）。
SKILL_FILE_NAME: Final[str] = "SKILL.md"

#: `Bash` 命令里**点名** `SKILL.md` 的形态：命令串中任一处出现该文件名。
#: 只要它同时指向受门禁的技能根就拦 —— 判据见
#: `test_bash_reading_a_skill_file_is_denied`。
_SHELL_SKILL_MENTION: Final[re.Pattern[str]] = re.compile(
    rf"{re.escape(SKILL_FILE_NAME)}",
    re.IGNORECASE,
)

#: 命令里出现受门禁的技能根（`\` 与 `/` 都算，Windows 与 POSIX 同判）。
_SHELL_GUARDED_ROOT: Final[re.Pattern[str]] = re.compile(
    r"\.agents[\\/]+skills[\\/]",
    re.IGNORECASE,
)

_HOOK_EVENT: Final[str] = "PreToolUse"


def skill_name_of(path: str) -> str | None:
    """从路径里取技能名；不是受门禁的 `SKILL.md` 就返回 `None`。

    判定用**归一化后的路径片段**，不用字符串前缀 —— 绝对路径、`./` 前缀、
    反斜杠三种形态都要能命中（Windows 上三者都会出现）。
    """
    normalized = path.replace("\\", "/")
    parts = [item for item in normalized.split("/") if item and item != "."]
    if not parts or parts[-1] != SKILL_FILE_NAME:
        return None
    root = GUARDED_SKILL_ROOT.split("/")
    for index in range(len(parts) - 1):
        if parts[index : index + len(root)] == root and len(parts) > index + len(root) + 1:
            return parts[index + len(root)]
    return None


def _deny(reason: str) -> dict[str, object]:
    """`PreToolUse` 的严格输出形态（多余键会让输出校验失败并丢弃裁决）。"""
    return {
        "hookSpecificOutput": {
            "hookEventName": _HOOK_EVENT,
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _refusal(skill: str) -> str:
    return (
        f"{GUARDED_SKILL_ROOT}/{skill}/{SKILL_FILE_NAME} 要通过 Skill 工具加载，不要直接读文件。"
        f"下一步：调用 Skill(skill={skill!r})。"
        "Skill 工具会把正文载入本回合、并在 system-reminder 里登记这次调用；"
        "直接 Read 会得到同样内容但没有任何调用记录，事后无从取证「这次是否真的用过该技能」。"
    )


def decide(payload: object) -> dict[str, object] | None:
    """返回裁决；`None` 表示放行（放行时不输出任何 JSON）。"""
    if not isinstance(payload, dict):
        return None
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    if tool_name == "Read":
        target = tool_input.get("file_path")
        if not isinstance(target, str):
            return None
        skill = skill_name_of(target)
        return None if skill is None else _deny(_refusal(skill))
    if tool_name == "Bash":
        command = tool_input.get("command")
        if not isinstance(command, str):
            return None
        if _SHELL_SKILL_MENTION.search(command) and _SHELL_GUARDED_ROOT.search(command):
            skill = _first_skill_in_command(command)
            return _deny(_refusal(skill))
    return None


def _first_skill_in_command(command: str) -> str:
    """从命令里取第一个技能名（判词要点名一个可执行的替代动作）。"""
    for token in command.replace("\\", "/").split():
        cleaned = token.strip("'\"").strip(",;")
        skill = skill_name_of(cleaned)
        if skill is not None:
            return skill
    return "<skill>"


def main() -> int:
    raw = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
    try:
        payload = json.loads(raw) if raw.strip() else None
    except json.JSONDecodeError:
        return 0
    verdict = decide(payload)
    if verdict is None:
        return 0
    sys.stdout.buffer.write((json.dumps(verdict, ensure_ascii=False) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
