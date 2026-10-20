#!/usr/bin/env python3
"""跑全量 m0 并留下**可校验的见证**（GOAL-20261020-090）。

**它补哪一格**：m0 的证据**只在它实际运行的那棵工作树上成立**。既有协议
（`docs/architecture/LOCAL_GATE_PROTOCOL.md` 的「记录面覆盖」）规定了顺序
「写记录 → 记录面判据 → 全量门」，但那条纪律此前**只靠人记住**：GOAL-089 的收口
为此多跑了三次全量 m0（每次约 16 分钟独占），因为每多一次记录提交，上一次的终态行
就失效一次。散文没有咬住它 —— 本入口给纪律装上一个**证据面**。

**做法**（三步，全部机械）：

1. 跑门前算**受判面指纹**：`git rev-parse HEAD` + 工作树的脏文件清单（路径 + 状态码）
   + 每个脏文件的 `sha256`。它回答「门跑的是**哪棵树**」。
2. 跑 `run_all_checks --profile m0 --keep-going`（canonical 调用，`uv run` 语义由调用方保证）。
3. 无论红绿，把 `{verdict, terminal_line, fingerprint}` 写进
   `.cursor/plans/goals/evidence/M0-WITNESS.json`（**树内**、内容寻址、可复核）。

**判据**（`tests/tooling/test_m0_witness_matches_the_tree.py`）读这份见证并重算**当前**树的
指纹，两者相等 ⇒ 「最后一次 m0 覆盖的就是现在这棵树」。不相等 ⇒ 判红并点名差在哪个文件
⇒ 「记录写完又改了树却没重跑门」这一类不再隐形。

**边界（如实登记）**：

* 见证是**过程事实**，不是「门一定过了」：`verdict` 字段如实记录红绿，红也照记
  （否则「跑过但红了」会退化成「没跑过」）。
* 它**不**校验 `run_all_checks` 有没有真的执行完 23 项 —— 那是终态行的职责
  （`PASS: profile=m0; 23 deterministic checks`），本入口只把该行原样抄进见证。
* 它**不**替代 CI：本地见证说明「本地这棵树跑过」，CI 说明「推送后的树跑过」，两者
  覆盖的对象不同。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WITNESS = ROOT / ".cursor" / "plans" / "goals" / "evidence" / "M0-WITNESS.json"
#: **进行中标记**（见 `main` 的注释）：存在 ⇒ 本次 m0 正由本入口运行，见证尚未写。
#: 落点与见证同目录；`SELF_REFERENTIAL` 里一并排除（否则它自己会改动受判面）。
MARKER = ROOT / ".cursor" / "plans" / "goals" / "evidence" / "M0-WITNESS.in-progress"
RUNNER = ROOT / ".cursor" / "skills" / "cursor-framework-check" / "scripts" / "run_all_checks.py"
GREEN = "PASS: profile=m0; 23 deterministic checks"

#: 受判面的根：门实际检查的那些目录。见证只对这些目录里的改动敏感 ——
#: 改 `docs/` 里的普通说明页也算（`docs-consistency` 会读），所以这里取**门的收集面**
#: 而不是「产品代码」的窄面。`scratch/` 与 `.venv` 在 gitignore 里，天然不出现。
WATCHED_PREFIXES: tuple[str, ...] = (
    "apps/",
    "services/",
    "packages/",
    "adapters/",
    "tests/",
    "tools/",
    "examples/",
    "schemas/",
    "docs/",
    ".cursor/",
    "Makefile",
    "pyproject.toml",
    "package.json",
    "pnpm-lock.yaml",
    "uv.lock",
)


#: **自我指涉边界**：见证文件本身**不在**受判面里。
#: 若把见证算进去，写见证这个动作就改变了它所描述的那棵树 ⇒ 每次写都自我失效
#: （GOAL-090 实测：`--skip-run` 写完立刻判红，差的正是这个文件）。
#: 这与宪章「自我指涉边界在收口 tip 那一行闭合」是同一手法：被描述者不参与描述。
SELF_REFERENTIAL: frozenset[str] = frozenset({
    ".cursor/plans/goals/evidence/M0-WITNESS.json",
    ".cursor/plans/goals/evidence/M0-WITNESS.in-progress",
})


def _git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args), cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False
    )
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {result.stderr.strip()[:300]}")
    return result.stdout


def _watched(relative: str) -> bool:
    if relative in SELF_REFERENTIAL:
        return False
    return any(relative == prefix or relative.startswith(prefix) for prefix in WATCHED_PREFIXES)


def tree_fingerprint() -> dict[str, object]:
    """当前树的指纹：HEAD + **受判面文件内容**的 sha256 清单。

    **为什么是「内容清单」而不是「脏文件清单」**（GOAL-090 CI 实测的缺陷）：
    第一版只记 `git status` 的脏文件。本地跑门时工作树有 24 个未提交改动，
    而 CI 是**干净检出**（0 个脏文件）⇒ 同一个提交在两处的指纹**永远不相等**
    ⇒ 判据在 CI 上恒红。这不只是噪声：它让「覆盖关系」与「有没有未提交改动」
    被错误地绑在一起，而后者根本不是这条纪律要问的东西。

    正确的语义是「门看到的**内容**现在还在不在」。所以指纹按**文件内容**算：
    对受判面下每个被跟踪文件取 `git ls-files` 的路径、读工作树字节算 sha256。
    ⇒ 干净检出与「已提交 + 工作树同内容」得到**同一个**指纹；只有**内容**变了
    才变。未提交但内容相同的改动不影响（那是 git 的状态问题，不是覆盖问题）。
    """
    head = _git("rev-parse", "HEAD").strip()
    tracked = [line for line in _git("ls-files", "-z").split("\0") if line]
    files: list[dict[str, str]] = []
    for relative in tracked:
        if not _watched(relative):
            continue
        target = ROOT / relative
        if not target.is_file():
            # 被跟踪但工作树里已删除 ⇒ 记录为缺失（这也是一种内容状态）。
            files.append({"path": relative, "sha256": ""})
            continue
        files.append({"path": relative, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    files.sort(key=lambda item: item["path"])
    return {"head": head, "files": files}


def fingerprint_digest(fingerprint: dict[str, object]) -> str:
    """指纹的稳定摘要（见证与判据用同一个算法，避免两边各算一套）。"""
    canonical = json.dumps(fingerprint, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _terminal_line(log: str) -> str:
    for line in log.splitlines():
        if line.startswith("PASS: profile=m0;") or line.startswith("FAILED:"):
            return line.strip()
    return ""


def _run_gate(head: str) -> tuple[str, int]:
    """跑一次 canonical 全量 m0（带**进行中标记**）；返回（日志, 退出码）。

    **标记为什么必须在 `subprocess.run` 之前写下、在 `finally` 里删**：
    见证在门**跑完之后**才写，而见证判据**本身就在门里**跑 ⇒ 结构上不可能在同一次
    运行里判绿。标记让判据区分「没跑过」（判红）与「正由见证入口跑着」（跳过并点名）。
    """
    MARKER.write_bytes(json.dumps({"pid": os.getpid(), "head": head}).encode("utf-8"))
    command = [sys.executable, "-B", str(RUNNER), "--profile", "m0", "--keep-going"]
    print(f"$ {' '.join(command)}", flush=True)
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        log = (completed.stdout or "") + (completed.stderr or "")
        sys.stdout.write(log)
        return log, completed.returncode
    finally:
        MARKER.unlink(missing_ok=True)


def _record(
    before: dict[str, object],
    after: dict[str, object],
    log: str,
    code: int,
) -> dict[str, object]:
    """见证的内容（纯数据；写盘与打印都用它，避免两边各算一套）。"""
    terminal = _terminal_line(log)
    return {
        "ran_at_head": before["head"],
        "fingerprint_before": before,
        "fingerprint_after": after,
        "tree_changed_during_the_run": before != after,
        "terminal_line": terminal,
        "green": terminal == GREEN,
        "exit_code": code,
        "note": (
            "见证绑定的是**跑门那一刻**的树。之后任何受判文件改动都会让 "
            "tests/tooling/test_m0_witness_matches_the_tree.py 判红"
            "（除非重跑本入口）。"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run m0 and write a tree-bound witness.")
    parser.add_argument(
        "--keep-going", action="store_true", default=True, help="传给 runner（默认开）"
    )
    parser.add_argument("--skip-run", action="store_true", help="只重算并写指纹（调试用）")
    args = parser.parse_args(argv)

    before = tree_fingerprint()
    log, code = ("", 0) if args.skip_run else _run_gate(str(before["head"]))
    after = tree_fingerprint()

    record = _record(before, after, log, code)
    WITNESS.parent.mkdir(parents=True, exist_ok=True)
    WITNESS.write_bytes(
        (json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    )
    print(f"\nwitness: {WITNESS.relative_to(ROOT)}", flush=True)
    print(f"fingerprint: {fingerprint_digest(after)}", flush=True)
    print(f"tree changed during the run: {record['tree_changed_during_the_run']}", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
