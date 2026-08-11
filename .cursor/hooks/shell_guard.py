#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass

from common import allow, ask, contains_sensitive_reference, deny, read_event_result


@dataclass(frozen=True)
class ShellRule:
    pattern: re.Pattern[str]
    message: str


def rule(pattern: str, message: str) -> ShellRule:
    return ShellRule(re.compile(pattern, re.IGNORECASE | re.VERBOSE), message)


ROOT_TARGET = r"(?:[A-Za-z]:[\\/](?:\*)?|\\\\[^\\/\s]+[\\/][^\\/\s]+[\\/]?)"
DENY_RULES = (
    rule(
        r"\brm\b(?=[^;\r\n]*(?:-[A-Za-z]*r|--recursive\b))"
        r"(?=[^;\r\n]*(?:-[A-Za-z]*f|--force\b))[^;\r\n]*"
        r"(?:['\"]?/(?:\*)?['\"]?|['\"]?(?:~|\$HOME)['\"]?)(?=\s|$|[;&|])",
        "禁止递归强制删除 POSIX 根目录或用户主目录。",
    ),
    rule(
        rf"\b(?:Remove-Item|ri|rm)\b(?=[^;\r\n]*(?:-Recurse|-r)\b)"
        rf"(?=[^;\r\n]*(?:-Force|-f)\b)[^;\r\n]*['\"]?{ROOT_TARGET}['\"]?(?=\s|$|[;&|])",
        "禁止递归强制删除 Windows 驱动器或共享根目录。",
    ),
    rule(
        rf"\b(?:rd|rmdir|del|erase)\b(?=[^&|\r\n]*/s\b)"
        rf"(?=[^&|\r\n]*/q\b)[^&|\r\n]*['\"]?{ROOT_TARGET}['\"]?(?=\s|$|[&|])",
        "禁止通过 cmd 递归静默删除 Windows 驱动器或共享根目录。",
    ),
    rule(r"\bgit\s+reset\s+--hard\b", "禁止 destructive git reset --hard。"),
    rule(
        r"\bgit\s+clean\b(?=[^;\r\n]*(?:-[A-Za-z]*f|--force\b))",
        "禁止 destructive git clean --force。",
    ),
    rule(
        r"\bgit\s+add\s+(?:-A|--all|\.(?:\s|$))",
        "禁止广域 git add；必须按白名单路径显式暂存。",
    ),
)

ASK_RULES = (
    rule(
        r"\bgit(?:\s+(?:-C|--git-dir|--work-tree)\s+\S+)*\s+push\b",
        "git push 会修改远端仓库，需要用户显式授权。",
    ),
    rule(
        r"\b(?:pip(?:3(?:\.\d+)?)?|python(?:3(?:\.\d+)?)?\s+-m\s+pip|py\s+-m\s+pip)\s+install\b|"
        r"\buv\s+(?:add|sync|pip\s+install)\b|"
        r"\b(?:poetry|pdm)\s+(?:add|install|sync)\b|"
        r"\b(?:npm|pnpm|yarn|bun)\s+(?:install|i|ci|add)\b|"
        r"\bcargo\s+(?:add|install)\b|\bgo\s+get\b|\bdotnet\s+add\s+\S+\s+package\b",
        "依赖安装会修改环境或锁文件，需要用户显式授权。",
    ),
    rule(
        r"\b(?:npm|pnpm|yarn|cargo|uv)\s+publish\b|"
        r"\b(?:twine\s+upload|docker\s+push|gh\s+release\s+create|dotnet\s+nuget\s+push)\b",
        "发布命令会修改外部系统，需要用户显式授权。",
    ),
)


def first_match(command: str, rules: tuple[ShellRule, ...]) -> ShellRule | None:
    return next((candidate for candidate in rules if candidate.pattern.search(command)), None)


def main() -> int:
    event, error = read_event_result()
    if error is not None:
        deny(
            f"安全门禁无法解析 Cursor Hook 输入，已按 fail-closed 拒绝命令：{error}",
            "修复 Hook JSON 协议后重试。",
        )
        return 0
    assert event is not None

    command = event.get("command")
    if not isinstance(command, str) or not command.strip():
        deny(
            "安全门禁缺少非空 command 字段，已按 fail-closed 拒绝命令。",
            "beforeShellExecution 事件必须提供待执行命令。",
        )
        return 0

    if contains_sensitive_reference(command):
        deny(
            "禁止 shell 命令访问或引用真实凭据/私钥路径。使用脱敏示例或受控 credential mechanism。"
        )
        return 0

    denied = first_match(command, DENY_RULES)
    if denied is not None:
        deny(denied.message, "选择更小范围、可回滚且不访问凭据的命令。")
        return 0

    approval = first_match(command, ASK_RULES)
    if approval is not None:
        ask(approval.message, "等待用户确认；不要通过其他工具或改写命令绕过授权。")
        return 0

    allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
