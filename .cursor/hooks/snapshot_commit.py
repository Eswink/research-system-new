#!/usr/bin/env python3
"""Cursor stop hook：会话结束后审计并报告未提交变更。

职责
- 只在 agent 会话结束（stop 事件）时运行，作为 .cursor/rules/43-git-commit-policy.mdc
  语义提交的观测层：无论会话是 completed / aborted / error，只报告残留变更，
  绝不执行 git add / git commit / git push。
- 语义提交只允许由 agent 在任务复检通过、收尾完成后显式执行（见 43 规则）。

范围与安全
- 仅读取 git 状态（git status --porcelain），按白名单目录与敏感文件规则分类：
  - tracked 修改；
  - 白名单目录（.cursor/ docs/ schemas/ examples/ scripts/）下的未跟踪文件；
  - 敏感文件（.env*、*.pem、*.key、*.p12 及内容含密钥模式）与白名单外未跟踪文件，
    仅提示，绝不 add。
- 幂等：无变更时直接退出 0。
- 绝不修改工作区、暂存区或提交历史；失败退出码 0/1 均不影响 agent 会话（fail-open）。

调试
- 直接执行 `python .cursor/hooks/snapshot_commit.py --debug` 可跳过 stdin 在真实工作区跑一次。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# 默认指向仓库根；测试可用环境变量 SNAPSHOT_HOOK_ROOT 覆盖（只读注入，不改默认行为）。
REPO_ROOT = Path(os.environ.get("SNAPSHOT_HOOK_ROOT") or Path(__file__).resolve().parents[2])

ALLOWED_DIRS = (".cursor", "docs", "schemas", "examples", "scripts")
SENSITIVE_NAME_RE = re.compile(
    r"(^|/)(\.env([.-].*)?|.*\.(pem|key|p12))$",
    re.IGNORECASE,
)
SENSITIVE_CONTENT_RE = re.compile(
    r"(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*[^\s]{8,}|"
    r"\bsk-[A-Za-z0-9_-]{20,}\b|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
)


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def is_sensitive_path(relative: str) -> bool:
    if SENSITIVE_NAME_RE.search(relative):
        return True
    path = REPO_ROOT / relative
    try:
        if path.is_file() and SENSITIVE_CONTENT_RE.search(path.read_text(encoding="utf-8", errors="ignore")):
            return True
    except OSError:
        pass
    return False


def classify_status() -> dict[str, list[str]]:
    """返回分类后的变更清单，只读，不执行任何写操作。"""
    result = run_git("status", "--porcelain")
    categories: dict[str, list[str]] = {
        "modified": [],
        "allowed_untracked": [],
        "sensitive": [],
        "outside_whitelist": [],
    }
    if result.returncode != 0:
        return categories
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        xy = line[:2]
        raw_path = line[3:]
        if xy[0] in ("R", "C") or xy[1] in ("R", "C"):
            path = raw_path.split(" -> ", 1)[-1]
        else:
            path = raw_path
        if xy.startswith("??"):
            parts = path.split("/", 1)
            if is_sensitive_path(path):
                categories["sensitive"].append(path)
            elif len(parts) == 2 and parts[0] in ALLOWED_DIRS:
                categories["allowed_untracked"].append(path)
            else:
                categories["outside_whitelist"].append(path)
        else:
            if is_sensitive_path(path):
                categories["sensitive"].append(path)
            else:
                categories["modified"].append(path)
    return categories


def main() -> int:
    if "--debug" in sys.argv:
        event: dict = {}
    else:
        try:
            event = json.loads(sys.stdin.read() or "{}")
        except json.JSONDecodeError:
            return 0
    if event.get("hook_event_name") not in (None, "stop"):
        return 0

    categories = classify_status()
    total = sum(len(items) for items in categories.values())
    if total == 0:
        print("[snapshot-commit] no uncommitted changes", flush=True)
        return 0

    print(f"[snapshot-commit] {total} uncommitted change(s) reported (audit only, no commit)", flush=True)
    for label, items in categories.items():
        for item in items:
            print(f"[snapshot-commit] {label}: {item}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())