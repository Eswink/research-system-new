#!/usr/bin/env python3
"""两树复检入口（GOAL-20260928-022 EC-01）。

对「当前树 + 干净 checkout」跑**同一个**复检脚本、**同一组断言**，只取**判词行**逐行比对，
并给出两份判词文件的 `sha256`。GOAL-020 / GOAL-021 各自踩过一次的三个环境坑写在这里，
而不是只写在文档里：

1. **共用解释器** —— 两棵树都用**本进程的解释器**（`sys.executable`，即主树 `.venv`）。
   干净 checkout 没有自己的 `.venv`；现场建会超时，而且那等于在比两套环境。
2. **输出纯度** —— 整份输出含耗时与路径，两棵树天然不同 ⇒ 只接受**判词行**
   （每行以 `PASS` / `FAIL` 开头）。出现任何别的行即**判失败**（非 0 退出），
   而不是把它过滤掉：静默过滤会把真差异一起丢掉。
3. **路径无关** —— 判词行里出现任一棵树的绝对路径即**判失败**。两棵树的路径必然不同，
   所以这类判词不是「结论」而是「现场坐标」；把它规范化成占位符会掩盖真差异，
   因此选择**拒绝**而不是**改写**。

**只跑一路是不可能的**：本入口没有「单树」模式。拿不到干净树就**非 0 退出**
（`EXIT_SETUP`），绝不会降级成「只跑当前树的 PASS」——这正是 GOAL-021 `W-0` 的形态。

用法：

    python tools/two_tree_recheck.py --script tools/recheck_x.py \\
        --root . --base-ref HEAD \\
        --verdict-current OUT-a.txt --verdict-clean OUT-b.txt

`--clean-root` 已存在时直接用（判据的 hermetic 用法）；缺省时用
`git worktree add --detach` 在 `--worktree-dir` 建一棵同 tip 的干净树，跑完移除。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

#: 判词行的前缀。只认这两种，其余一行都算「不纯」。
VERDICT_PREFIXES: tuple[str, ...] = ("PASS", "FAIL")

#: 单棵树复检的超时（秒）。超时按进程树整棵杀（Windows 要 `/T`）。
DEFAULT_TIMEOUT_SECONDS = 1800

EXIT_GREEN = 0
EXIT_RED = 1
EXIT_SETUP = 2


class RecheckError(RuntimeError):
    """入口自身的失败（用法 / 环境 / 判词形态），与「判据红」区分开。"""


@dataclass(frozen=True, slots=True)
class TreeRun:
    """一棵树上的一次复检：判词行 + 判词摘要 + 退出码。"""

    root: Path
    exit_code: int
    lines: tuple[str, ...]

    @property
    def verdict_text(self) -> str:
        return "".join(f"{line}\n" for line in self.lines)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.verdict_text.encode("utf-8")).hexdigest()

    @property
    def failed_lines(self) -> tuple[str, ...]:
        return tuple(line for line in self.lines if line.startswith("FAIL"))


def verdict_lines(stdout: str) -> tuple[str, ...]:
    """提取判词行；出现任何非判词行即抛错（纯度是判据，不是清洗）。"""
    lines: list[str] = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        if not line.startswith(VERDICT_PREFIXES):
            raise RecheckError(f"输出不纯：出现非判词行 -> {line!r}")
        lines.append(line)
    if not lines:
        raise RecheckError("复检脚本没有产出任何判词行")
    return tuple(lines)


def assert_path_independent(lines: Sequence[str], roots: Sequence[Path]) -> None:
    """判词行不得嵌入任一棵树的绝对路径。"""
    for line in lines:
        for root in roots:
            if str(root) in line:
                raise RecheckError(f"判词与路径相关（含 {root}）-> {line!r}")


def script_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_script(tree: Path, script: str, shared: bool) -> Path:
    """定位该树上的复检脚本。

    `tree` 模式：脚本相对**该树根**解析（同 tip ⇒ 两棵树拿到同一份字节）。
    `shared` 模式：脚本相对**调用方 cwd** 解析并绝对化 —— 相对路径会因
    `cwd=<tree>` 被解释成「树内的同名文件」，那是两回事。
    """
    candidate = Path(script).resolve() if shared else (tree / script).resolve()
    if not candidate.is_file():
        raise RecheckError(f"复检脚本不存在：{candidate}")
    return candidate


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    """超时后连**整棵树**杀（承 GOAL-020 的 96 孤儿教训）。"""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(process.pid)],
            capture_output=True,
            check=False,
        )
    else:
        process.kill()
    process.wait()


def run_one_tree(
    tree: Path,
    script: Path,
    extra_args: Sequence[str],
    timeout: int,
) -> TreeRun:
    """在一棵树上跑复检脚本，只收判词行。"""
    command = (
        sys.executable,
        "-B",
        str(script),
        "--root",
        str(tree),
        "--verdict-only",
        *extra_args,
    )
    process = subprocess.Popen(
        command,
        cwd=str(tree),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        terminate_process_tree(process)
        raise RecheckError(f"复检超时（{timeout}s）：{tree}") from None
    if process.returncode != 0 and not stdout.strip():
        raise RecheckError(
            f"复检脚本未产出判词即失败（exit={process.returncode}）：{stderr.strip()}"
        )
    return TreeRun(root=tree, exit_code=process.returncode, lines=verdict_lines(stdout))


def materialize_clean_tree(root: Path, base_ref: str, worktree_dir: Path) -> tuple[Path, bool]:
    """确保干净 checkout 存在。返回 (树, 是否由本入口创建)。"""
    if worktree_dir.exists():
        if not (worktree_dir / "VERSION").is_file():
            raise RecheckError(f"目录已存在但不是仓库树：{worktree_dir}")
        return worktree_dir, False
    if shutil.which("git") is None:
        raise RecheckError("找不到 git，无法建干净 checkout")
    worktree_dir.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree_dir), base_ref],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RecheckError(f"建干净 checkout 失败：{result.stderr.strip()}")
    return worktree_dir, True


def remove_clean_tree(root: Path, worktree_dir: Path) -> None:
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(worktree_dir)],
        cwd=str(root),
        capture_output=True,
        check=False,
    )


def compare_runs(current: TreeRun, clean: TreeRun) -> tuple[bool, list[str]]:
    """逐行比对 + 报告；返回 (是否一致, 差异行说明)。"""
    differences: list[str] = []
    if current.exit_code != clean.exit_code:
        differences.append(f"退出码不同：current={current.exit_code} clean={clean.exit_code}")
    limit = max(len(current.lines), len(clean.lines))
    for index in range(limit):
        left = current.lines[index] if index < len(current.lines) else "<缺失>"
        right = clean.lines[index] if index < len(clean.lines) else "<缺失>"
        if left != right:
            differences.append(f"第 {index + 1} 行：current={left!r} clean={right!r}")
    return (not differences), differences


def failing_reasons(current: TreeRun, clean: TreeRun) -> list[str]:
    """两棵树各自的「不绿」理由（退出码 / FAIL 行）。"""
    reasons: list[str] = []
    for run in (current, clean):
        label = "current" if run is current else "clean"
        if run.exit_code != 0:
            reasons.append(f"{label} 退出码 {run.exit_code}")
        for line in run.failed_lines:
            reasons.append(f"{label} {line}")
    return reasons


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="两树复检入口（同一组断言 + 逐行判词比对）")
    parser.add_argument("--script", required=True, help="复检脚本，相对树根（tree 模式）或绝对路径")
    parser.add_argument("--root", required=True, help="当前树（主树）根目录")
    parser.add_argument("--clean-root", default=None, help="已存在的干净 checkout；缺省则新建")
    parser.add_argument("--base-ref", default="HEAD", help="干净 checkout 的提交（缺省 HEAD）")
    parser.add_argument(
        "--worktree-dir",
        default=None,
        help="干净 checkout 落点（缺省 <root>/../<name>-clean-tree）",
    )
    parser.add_argument("--script-mode", choices=("tree", "shared"), default="tree")
    parser.add_argument("--verdict-current", default=None, help="当前树判词落点")
    parser.add_argument("--verdict-clean", default=None, help="干净树判词落点")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("script_args", nargs="*", help="透传给复检脚本的额外参数")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"SETUP 当前树不存在：{root}")
        return EXIT_SETUP
    default_dir = root.parent / f"{root.name}-clean-tree"
    worktree_dir = Path(args.worktree_dir).resolve() if args.worktree_dir else default_dir
    shared = args.script_mode == "shared"
    created = False
    try:
        if args.clean_root:
            clean_root = Path(args.clean_root).resolve()
            if not clean_root.is_dir():
                raise RecheckError(f"干净树不存在：{clean_root}")
        else:
            clean_root, created = materialize_clean_tree(root, args.base_ref, worktree_dir)
        current_script = resolve_script(root, args.script, shared)
        clean_script = resolve_script(clean_root, args.script, shared)
        if script_sha256(current_script) != script_sha256(clean_script):
            raise RecheckError("两树的复检脚本字节不同 ⇒ 比的不是同一组断言")
        current = run_one_tree(root, current_script, args.script_args, args.timeout)
        clean = run_one_tree(clean_root, clean_script, args.script_args, args.timeout)
        assert_path_independent((*current.lines, *clean.lines), (root, clean_root))
    except RecheckError as error:
        print(f"SETUP 入口失败：{error}")
        if created:
            remove_clean_tree(root, worktree_dir)
        return EXIT_SETUP
    try:
        for run, dest in ((current, args.verdict_current), (clean, args.verdict_clean)):
            if dest:
                Path(dest).write_text(run.verdict_text, encoding="utf-8", newline="")
        identical, differences = compare_runs(current, clean)
        reasons = failing_reasons(current, clean)
        for run, label in ((current, "current"), (clean, "clean")):
            print(
                f"TREE {label}={run.root} exit={run.exit_code} "
                f"verdicts={len(run.lines)} sha256={run.sha256}"
            )
        print(f"COMPARE identical={identical}")
        for line in differences:
            print(f"DIFF {line}")
        for line in reasons:
            print(f"NOT-GREEN {line}")
        if identical and not reasons:
            print("TWO-TREE PASS")
            return EXIT_GREEN
        print("TWO-TREE RED")
        return EXIT_RED
    finally:
        if created:
            remove_clean_tree(root, worktree_dir)


if __name__ == "__main__":
    raise SystemExit(main())
