"""ZCode `PreToolUse` 门禁：读 `.agents/skills/**/SKILL.md` 必须走 Skill 工具。

**为什么需要这个 hook**：技能正文是**按需加载**的（Skill 工具负责载入并登记
调用事实），而 `Read` / `Bash cat` 能绕过它 —— 绕过之后 agent 拿到了正文，
但既没有技能名可引用，也没有「本次确实调用过哪个技能」的事实。判据见
`tests/tooling/test_zcode_skill_invocation_guard.py`。

**判的是「读取动作」，不是「字符串出现」**。早期版本对整条命令串做子串匹配，
于是把三类**不含读取**的写法也拦了（实测两次自伤）：heredoc 正文里提到受门禁路径
的写文件命令、`grep` 的模式串本身就写着这两个字面量、以及重定向**写入**技能文件。
现在先剥 heredoc 与重定向目标，再按简单命令切分，只在**读类程序**的文件参数上判定。

**射程只有 `.agents/skills/`**：`ZCode` 不扫描 `.cursor/skills/`（那 17 个技能
在 ZCode 侧没有 Skill 工具入口），拦它们等于让正文彻底不可读。遍历式读取
（`grep -r` / `ls` / `find`）不点名正文文件，也不在射程内。

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

#: **读类**程序：只有它们的文件参数才构成「读正文」。写类（`tee`/`cp`/`mv`/
#: `echo >`/`python`/`git`）不在其中 —— 门禁管的是绕过 Skill 工具**取得**正文。
_READ_PROGRAMS: Final[frozenset[str]] = frozenset({
    "awk",
    "bat",
    "cat",
    "egrep",
    "fgrep",
    "gc",
    "get-content",
    "grep",
    "head",
    "less",
    "more",
    "nl",
    "od",
    "rg",
    "sed",
    "select-string",
    "strings",
    "tail",
    "type",
    "xxd",
})

#: 这些程序的首个非选项参数是**模式串**（不是文件），必须跳过，否则
#: `grep "SKILL.md\|.agents/skills" file` 会被误判成读正文。
_SCRIPT_FIRST: Final[frozenset[str]] = frozenset({
    "awk",
    "egrep",
    "fgrep",
    "grep",
    "perl",
    "rg",
    "sed",
})

#: heredoc 起始（`<<EOF` / `<<'EOF'` / `<<-EOF`）：正文不是命令，必须整段剥掉。
_HEREDOC: Final[re.Pattern[str]] = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")

#: 重定向目标（`> f` / `>> f` / `2> f` / `&> f`）：那是**写**，不是读。
_REDIRECT: Final[re.Pattern[str]] = re.compile(r"\d?&?>>?\s*[^\s;|&]+")

_HOOK_EVENT: Final[str] = "PreToolUse"


def skill_name_of(path: str) -> str | None:
    """从路径里取技能名；不是受门禁的 `SKILL.md` 就返回 `None`。

    判定用**归一化后的路径片段**，不用字符串前缀 —— 绝对路径、`./` 前缀、
    反斜杠三种形态都要能命中（Windows 上三者都会出现）。裸文件名（不含
    `.agents/skills/` 前缀）不算：那种写法依赖 cwd，判它会把普通同名文件一起拦。
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


def strip_heredocs(command: str) -> str:
    """剥掉 heredoc 正文（正文是数据，不是命令）。"""
    lines = command.splitlines()
    kept: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        match = _HEREDOC.search(line)
        if match is None:
            continue
        delimiter = match.group(2)
        while index < len(lines) and lines[index].strip() != delimiter:
            index += 1
        index += 1
    return "\n".join(kept)


def split_segments(command: str) -> list[str]:
    """按 `&&` / `||` / `;` / `|` / 换行切成简单命令（引号内的不算分隔符）。"""
    segments: list[str] = []
    current: list[str] = []
    quote: str | None = None
    index = 0
    length = len(command)
    while index < length:
        char = command[index]
        if quote is not None:
            current.append(char)
            if char == quote:
                quote = None
            index += 1
            continue
        if char in {'"', "'"}:
            quote = char
            current.append(char)
            index += 1
            continue
        pair = command[index : index + 2]
        if pair in {"&&", "||"}:
            segments.append("".join(current))
            current = []
            index += 2
            continue
        if char == "\n" or char in {";", "|", "&"}:
            segments.append("".join(current))
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    segments.append("".join(current))
    return [item for item in segments if item.strip()]


def _tokens(segment: str) -> list[str]:
    """按空白切 token，保留引号里的内容（引号本身去掉）。"""
    tokens: list[str] = []
    current: list[str] = []
    quote: str | None = None
    for char in segment:
        if quote is not None:
            if char == quote:
                quote = None
            else:
                current.append(char)
            continue
        if char in {'"', "'"}:
            quote = char
            continue
        if char.isspace():
            if current:
                tokens.append("".join(current))
                current = []
            continue
        current.append(char)
    if current:
        tokens.append("".join(current))
    return tokens


def _file_arguments(tokens: list[str]) -> list[str]:
    """取一个简单命令里**作为文件**的参数（跳过程序名、选项与模式串）。"""
    program = tokens[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    rest = [item for item in tokens[1:] if not item.startswith("-")]
    if program in _SCRIPT_FIRST and rest:
        rest = rest[1:]
    return rest


def bash_reads_skill_body(command: str) -> str | None:
    """返回被读取的技能名；没有读取受门禁正文就返回 `None`。"""
    stripped = _REDIRECT.sub(" ", strip_heredocs(command))
    for segment in split_segments(stripped):
        tokens = _tokens(segment)
        if not tokens:
            continue
        program = tokens[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
        if program not in _READ_PROGRAMS:
            continue
        for argument in _file_arguments(tokens):
            skill = skill_name_of(argument)
            if skill is not None:
                return skill
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
        skill = bash_reads_skill_body(command)
        return None if skill is None else _deny(_refusal(skill))
    return None


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
