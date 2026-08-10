#!/usr/bin/env python3
"""Cursor stop hook：会话结束后对未提交变更生成快照提交。

职责
- 只在 agent 会话结束（stop 事件）时运行，作为 .cursor/rules/43-git-commit-policy.mdc
  语义提交的兜底：无论会话是 completed / aborted / error，只要工作区残留未提交变更，
  就生成一个固定消息的快照提交，防止变更堆积。
- 仅本地提交，绝不 push。

范围与安全
- 提交 tracked 文件的修改，以及白名单目录下新增的未跟踪文件；
  白名单目录：.cursor/ docs/ schemas/ examples/ scripts/
- 显式跳过敏感文件：.env*、*.pem、*.key、*.p12，以及内容含密钥模式的文件。
- 白名单之外的未跟踪文件跳过并打印警告，绝不入库。
- 幂等：无变更时直接退出 0。

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

COMMIT_MESSAGE = "chore(worktree): snapshot uncommitted changes"

# 需要排除自动快照的分支名。当前仓库唯一分支 main 必须兜底，因此默认为空；
# 未来如存在禁止自动提交的分支，在此扩展。
SKIP_BRANCHES: tuple[str, ...] = ()


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def current_branch() -> str | None:
    result = run_git("branch", "--show-current")
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


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


def parse_status_porcelain() -> tuple[list[str], list[str]]:
    """返回 (可提交路径, 跳过路径)。

    解析 git status --porcelain（非 -z）输出：
    - 普通行 `XY path`，路径从第 4 列开始，可含空格；
    - 重命名/复制行 `XY old -> new`，提交时只需 add new 路径；
    - 未跟踪（??）仅当位于白名单目录时才纳入。
    """
    result = run_git("status", "--porcelain")
    if result.returncode != 0:
        return [], []
    commitable: list[str] = []
    skipped: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        xy = line[:2]
        raw_path = line[3:]
        if xy[0] in ("R", "C") or xy[1] in ("R", "C"):
            path = raw_path.split(" -> ", 1)[-1]
        else:
            path = raw_path
        status = "untracked" if xy.startswith("??") else "modified"
        if is_sensitive_path(path):
            skipped.append(f"{path} (敏感文件)")
            continue
        parts = path.split("/", 1)
        if status == "untracked" and not (len(parts) == 2 and parts[0] in ALLOWED_DIRS):
            skipped.append(f"{path} (白名单目录之外)")
        else:
            commitable.append(path)
    return commitable, skipped


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

    branch = current_branch() or "detached"
    if branch in SKIP_BRANCHES:
        print(f"[snapshot-commit] skip on branch {branch}", flush=True)
        return 0

    commitable, skipped = parse_status_porcelain()
    if not commitable:
        print("[snapshot-commit] no changes to commit", flush=True)
        return 0

    add_result = run_git("add", "--", *commitable)
    if add_result.returncode != 0:
        print(f"[snapshot-commit] git add failed: {add_result.stderr.strip()}", flush=True)
        return 1

    commit_result = run_git("commit", "-m", COMMIT_MESSAGE)
    if commit_result.returncode != 0:
        print(f"[snapshot-commit] git commit failed: {commit_result.stderr.strip()}", flush=True)
        return 1

    print(f"[snapshot-commit] committed: {COMMIT_MESSAGE}", flush=True)
    for item in skipped:
        print(f"[snapshot-commit] skipped: {item}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())