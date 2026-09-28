#!/usr/bin/env python3
"""标准收口断言集（GOAL-20260928-023 EC-01）。

**为什么进树**：GOAL-022 的收口复检断言集落在 gitignored 的 `scratch/` ⇒ **可复跑但不可归档**
（`RECHECK-20260928-218` 的 `W-3`：他人 clone 仓库后无法直接复核那些判词）。本模块把
「**任何 GOAL 的收口复检都要断言的公共事实**」收进树，使未来的收口复检**只写自己特有的断言**。

用法（与两树入口的协议一致）：

    python tools/closeout_recheck_assertions.py --root <树根> --verdict-only

公开面：`Verdict` / `standard_verdicts(root)` / `emit(verdicts)` —— 收口复检脚本 import 它、
再拼上自己的判词即可。

**判词纯度与路径无关**是硬要求（规范页第 ② / ⑥ 条）：判词行只有 `PASS` / `FAIL` 两种前缀，
且**不含任何树的绝对路径** —— 两棵树的路径必然不同，嵌路径的判词不是结论而是「现场坐标」，
两树入口会（正确地）拒绝它。
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import re
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import cast

#: 受保护的既有判据（本仓「不得修改」清单的机械代理）。缺一个即判红。
PROTECTED_JUDGES: tuple[str, ...] = (
    "tests/architecture/python/test_control_plane_auth_same_source.py",
    "tests/architecture/python/test_reproducibility_wording.py",
    "tests/architecture/python/test_record_face_is_covered_by_the_gate.py",
    "tests/architecture/python/test_declared_recheck_paths_have_evidence.py",
    "tests/architecture/python/test_recheck_script_conventions_are_pinned.py",
    "tests/tooling/test_two_tree_recheck_entry.py",
    "tests/tooling/test_python_source_limits.py",
    "tests/application/test_m2_audit.py",
    "tests/egress_guard.py",
    "tests/tooling/test_m0_ci_coverage.py",
)

#: 两树复检入口与其行为判据（GOAL-022 EC-01 的交付面）。
ENTRY = "tools/two_tree_recheck.py"
ENTRY_JUDGE = "tests/tooling/test_two_tree_recheck_entry.py"

#: 本断言集与其判据（**自指**：改名 / 搬走即判红）。
ASSERTIONS = "tools/closeout_recheck_assertions.py"
ASSERTIONS_JUDGE = "tests/tooling/test_closeout_assertions_are_in_tree.py"

#: 规范页 / 治理校验器 / 门运行器 / 规模门判据。
CONVENTIONS = "docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md"
INDEX = "docs/INDEX.md"
GOVERNANCE = ".cursor/skills/governance-check/scripts/validate.py"
RUNNER = ".cursor/skills/cursor-framework-check/scripts/run_all_checks.py"
SCALE_JUDGE = "tests/tooling/test_python_source_limits.py"
PLANS_DIR = ".cursor/plans/tasks"
GOALS_DIR = ".cursor/plans/goals"

#: 产品根（既有形态）。`tools` **不在**其中 —— 这正是本 GOAL 用**有界判据**而不是
#: 改 `PRODUCT_ROOTS` 的原因；本断言把它钉住，防止有人顺手把 `tools` 加进去。
PRODUCT_ROOTS: tuple[str, ...] = ("apps", "services", "packages", "adapters", "tests")

#: 规范页「收口复检必须两树」条款小节的结构性锚点。
CLAUSE_SECTION = "## 收口复检必须两树"

#: 规范页六条环境口径的条目标签。
SIX_ITEMS: tuple[str, ...] = (
    "共用解释器",
    "纯度",
    "文本 vs 二进制读写",
    "落点断言",
    "进程卫生",
    "路径无关输出",
)

#: m0 的终态条数契约（`PASS: profile=m0; 23 deterministic checks`）。
M0_CHECK_COUNT = 23

#: 结果字段的通过取值。
PASSING_RESULTS = frozenset({"PASS", "PASS_WITH_WARNINGS"})

#: 绝对路径（盘符）在判词类脚本里的形态；出现即说明脚本可能硬编码了某一棵树。
_DRIVE_LETTER = re.compile(r"[A-Za-z]:[\\/]")


@dataclass(frozen=True, slots=True)
class Verdict:
    """一条判词；`name` 必须与路径无关（两树逐行比对的就是它）。"""

    name: str
    ok: bool
    detail: str = ""


def verdict_line(verdict: Verdict) -> str:
    """判词行：只有 `PASS` / `FAIL` 两种前缀（纯度是判据，不是清洗）。"""
    if verdict.ok:
        return f"PASS {verdict.name}"
    return f"FAIL {verdict.name} -> {verdict.detail}"


def emit(verdicts: Iterable[Verdict]) -> bool:
    """打印判词行并返回是否全绿。供收口复检脚本复用。"""
    items = list(verdicts)
    for verdict in items:
        print(verdict_line(verdict))
    return all(item.ok for item in items)


def tree_path(root: Path, relative: str) -> Path:
    """把仓库相对路径挂到给定树根上（不硬编码任何仓库根）。"""
    return root.joinpath(*relative.split("/"))


def read_text(root: Path, relative: str) -> str:
    path = tree_path(root, relative)
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def parse_ast(text: str) -> ast.Module | None:
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def defines(text: str, name: str) -> bool:
    """按 **AST 读声明**（不是「文本里出现过这个名字」）。"""
    tree = parse_ast(text)
    if tree is None:
        return False
    return any(isinstance(node, ast.FunctionDef) and node.name == name for node in ast.walk(tree))


def integer_literals(text: str) -> set[int]:
    tree = parse_ast(text)
    if tree is None:
        return set()
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            if not isinstance(node.value, bool):
                found.add(node.value)
    return found


def _tuple_of_strings(node: ast.expr) -> tuple[str, ...] | None:
    if not isinstance(node, ast.Tuple) or not node.elts:
        return None
    values: list[str] = []
    for element in node.elts:
        if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
            return None
        values.append(element.value)
    return tuple(values)


def module_tuple_constant(text: str, name: str) -> tuple[str, ...] | None:
    """读模块级 `NAME = ("a", "b")` 形态的元组常量（不 import，避免副作用）。"""
    tree = parse_ast(text)
    if tree is None:
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            continue
        return _tuple_of_strings(node.value)
    return None


def load_module(path: Path, name: str) -> ModuleType | None:
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:  # 加载失败 ⇒ 该条判词判红，而不是整轮崩掉
        return None
    return module


def presence_verdict(root: Path, relative: str, name: str) -> Verdict:
    exists = tree_path(root, relative).is_file()
    return Verdict(name, exists, f"交付物不在树：{relative}")


def contains_verdict(root: Path, relative: str, needle: str, name: str) -> Verdict:
    ok = needle in read_text(root, relative)
    return Verdict(name, ok, f"{relative} 里没有 {needle}")


def protected_judges_verdict(root: Path) -> Verdict:
    missing = [item for item in PROTECTED_JUDGES if not tree_path(root, item).is_file()]
    return Verdict("protected-judges-present", not missing, f"缺少受保护判据：{missing}")


def scale_gate_verdict(root: Path) -> Verdict:
    """规模门的上限来自**AST 里的整数字面量**，不是文本巧合。"""
    missing = sorted({450, 50} - integer_literals(read_text(root, SCALE_JUDGE)))
    return Verdict("scale-gate-limits-present", not missing, f"{SCALE_JUDGE} 缺少上限 {missing}")


def product_roots_verdicts(root: Path) -> list[Verdict]:
    """两个载体各自声明同一组产品根，且**都不含** `tools`。"""
    verdicts: list[Verdict] = []
    for relative, label in ((RUNNER, "runner"), (SCALE_JUDGE, "scale-judge")):
        declared = module_tuple_constant(read_text(root, relative), "PRODUCT_ROOTS")
        verdicts.append(
            Verdict(
                f"{label}-product-roots-unchanged",
                declared == PRODUCT_ROOTS,
                f"{relative} 声明 {declared}，契约是 {PRODUCT_ROOTS}",
            )
        )
    return verdicts


def m0_count_verdict(root: Path) -> Verdict:
    """m0 条数由**门运行器自己算**（不是「文档里写着 23」）。"""
    module = load_module(tree_path(root, RUNNER), "goal023_runner")
    if module is None:
        return Verdict("m0-check-count-stable", False, f"无法加载门运行器：{RUNNER}")
    counter = cast("Callable[[str, Path], Sequence[object]]", getattr(module, "checks_for"))
    count = len(counter("m0", root))
    return Verdict(
        "m0-check-count-stable",
        count == M0_CHECK_COUNT,
        f"m0 组合算出 {count} 项，契约是 {M0_CHECK_COUNT} 项",
    )


def evidence_scripts_verdict(root: Path) -> Verdict:
    """判词类脚本不得硬编码某一棵树的绝对路径（否则「两树」退化成「同一棵树跑两次」）。"""
    offenders = [
        relative
        for relative in (ENTRY, ASSERTIONS)
        if _DRIVE_LETTER.search(read_text(root, relative))
    ]
    return Verdict(
        "evidence-scripts-are-path-independent",
        not offenders,
        f"这些脚本里出现盘符绝对路径：{offenders}",
    )


def entry_verdicts(root: Path) -> list[Verdict]:
    """两树入口：行为判据在树、无单树模式、且反证用例真的存在。"""
    entry = read_text(root, ENTRY)
    judge = read_text(root, ENTRY_JUDGE)
    return [
        presence_verdict(root, ENTRY_JUDGE, "entry-judge-present"),
        Verdict(
            "entry-refuses-degradation",
            "TWO-TREE PASS" in entry and "taskkill" in entry,
            f"{ENTRY} 不再声明「两树同结论」与「连整棵树杀」",
        ),
        Verdict(
            "entry-carries-a-reverse-proof-case",
            defines(judge, "test_second_tree_differing_makes_the_entry_red"),
            f"{ENTRY_JUDGE} 缺少「第二树不同 ⇒ 判红」的反证用例",
        ),
        Verdict(
            "entry-refuses-single-tree-pass",
            defines(judge, "test_missing_clean_tree_never_degrades_to_single_tree_pass"),
            f"{ENTRY_JUDGE} 缺少「只跑一路 ⇒ 非 0」的用例",
        ),
    ]


def conventions_verdicts(root: Path) -> list[Verdict]:
    """规范页：条款小节 + 六条口径 + `INDEX` 登记 + 已点名入口与本断言集。"""
    doc = read_text(root, CONVENTIONS)
    missing_items = [item for item in SIX_ITEMS if item not in doc]
    return [
        Verdict(
            "conventions-clause-and-six-items",
            CLAUSE_SECTION in doc and not missing_items,
            f"规范页缺少条款小节或这些口径：{missing_items}",
        ),
        contains_verdict(
            root, INDEX, "architecture/RECHECK_SCRIPT_CONVENTIONS.md", "conventions-registered"
        ),
        Verdict(
            "conventions-name-the-entry-and-the-assertions",
            ENTRY in doc and ASSERTIONS in doc,
            f"规范页没有点名 {ENTRY} 与 {ASSERTIONS}",
        ),
    ]


def record_path_problems(
    parser: Callable[[Path], tuple[dict[str, object], str]],
    root: Path,
    path: Path,
    label: str,
) -> list[str]:
    """单条记录的问题清单（空 = 合格）。

    `latest_recheck` 必须是**仓库相对路径**（不是裸 ID）且**真的存在**，
    其 `result` 还必须是**通过取值** —— 这是「已收口」记录的最低自洽性，与哪个 GOAL 无关。
    """
    metadata, _body = parser(path)
    raw = metadata.get("latest_recheck")
    if not isinstance(raw, str) or "/" not in raw:
        return [f"{label} {path.name}: latest_recheck 不是仓库相对路径（{raw!r}）"]
    target = tree_path(root, raw)
    if not target.is_file():
        return [f"{label} {path.name}: 复检不存在（{raw}）"]
    recheck, _body = parser(target)
    if recheck.get("result") not in PASSING_RESULTS:
        return [f"{label} {path.name}: 复检结果不是通过取值（{recheck.get('result')!r}）"]
    return []


def record_path_verdicts(root: Path) -> list[Verdict]:
    """记录自洽：**已收口**的 GOAL / **已完成**的 PLAN 的 `latest_recheck` 逐条可解析。"""
    module = load_module(tree_path(root, GOVERNANCE), "goal023_governance")
    if module is None:
        return [Verdict("record-paths-are-checkable", False, f"无法加载 {GOVERNANCE}")]
    parser = cast(
        "Callable[[Path], tuple[dict[str, object], str]]",
        getattr(module, "parse_frontmatter"),
    )
    problems: list[str] = []
    pairs = ((GOALS_DIR, "GOAL-", "ACHIEVED", "goal"), (PLANS_DIR, "PLAN-", "DONE", "plan"))
    for folder, prefix, wanted, label in pairs:
        for path in sorted(tree_path(root, folder).glob(f"{prefix}*.md")):
            metadata, _body = parser(path)
            if metadata.get("status") == wanted:
                problems.extend(record_path_problems(parser, root, path, label))
    return [Verdict("records-declare-existing-rechecks", not problems, "; ".join(problems[:4]))]


def standard_verdicts(root: Path) -> list[Verdict]:
    """公共断言集。收口复检脚本 = 本函数 + 自己特有的断言。"""
    verdicts: list[Verdict] = [
        protected_judges_verdict(root),
        scale_gate_verdict(root),
        *product_roots_verdicts(root),
        m0_count_verdict(root),
        presence_verdict(root, ASSERTIONS, "closeout-assertions-present"),
        presence_verdict(root, ASSERTIONS_JUDGE, "closeout-assertions-judge-present"),
        presence_verdict(root, ENTRY, "two-tree-entry-present"),
        presence_verdict(root, GOVERNANCE, "governance-validator-present"),
        evidence_scripts_verdict(root),
        *entry_verdicts(root),
        *conventions_verdicts(root),
        *record_path_verdicts(root),
    ]
    return verdicts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="标准收口断言集（两树入口的复检脚本协议）")
    parser.add_argument("--root", required=True, help="树根（不硬编码仓库根 ⇒ 可跑任意树）")
    parser.add_argument("--verdict-only", action="store_true", help="只打印判词行")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        print("FAIL assertions-root-missing -> 树根不存在")
        return 2
    verdicts = standard_verdicts(root)
    if args.verdict_only:
        return 0 if emit(verdicts) else 1
    reds = [item for item in verdicts if not item.ok]
    for verdict in verdicts:
        state = "PASS" if verdict.ok else "FAIL"
        print(f"{state} {verdict.name}: {verdict.detail or 'ok'}")
    print(f"TOTAL {len(verdicts)} verdicts; {len(reds)} red")
    return 1 if reds else 0


if __name__ == "__main__":
    raise SystemExit(main())
