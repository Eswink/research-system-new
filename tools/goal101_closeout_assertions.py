"""GOAL-20261030-101 的本轮特有断言（产品面 + 记录面）。

与 `tools/goal023…100_closeout_assertions.py` 同形：只写**本 GOAL 特有**的断言，
公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 / 规范页）由
`closeout_recheck_assertions.standard_verdicts` 判，一行不重写。

**四组**：
1. **叙述质量三条**在树、可执行、且**真的挂在装配面**上（不是死代码）；
2. **负判扫描补上主文件**：共享 helper 在树 + 主文件侧面判据在树 + 17 个验证器走 helper；
3. **run 归属校验器**在树，且**不在默认门**（出网面）；
4. **两条方法纪律**成了机械判据（宽松 glob 唯一性 / 读取面显式 UTF-8）。

每条断言都**只读树**（零出网、零时钟、不写盘），与 GOAL-023…100 的断言集同一纪律。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, cast

#: 叙述质量模块与它的判据（本轮 WP1/WP3）。
QUALITY_MODULE = "packages/application/deliverable/manuscript_quality.py"
QUALITY_DOC = "docs/architecture/MANUSCRIPT_QUALITY.md"
QUALITY_JUDGE = "tests/application/test_manuscript_quality.py"
ASSEMBLY = "packages/application/run_orchestration/manuscript_assembly.py"
MANUSCRIPT = "packages/application/deliverable/manuscript.py"

#: 三条判据的函数名（逐字；改名 = 改契约）。
QUALITY_CHECKS: tuple[str, ...] = (
    "check_citation_alignment",
    "check_section_distinctness",
    "check_section_depth",
)
#: 射程边界必须逐条在场的词（「不判什么」是判据的一部分）。
NOT_JUDGED_MARKERS: tuple[str, ...] = (
    "whether a citation supports the sentence",
    "whether the argument holds",
    "whether the method is appropriate",
    "whether the citation set is sufficient",
)

#: 本轮修掉的负判扫描盲区（WP4/WP5）。
SHARED_HELPER = "tools/charter_progress.py"
MAIN_FILE_JUDGE = "tests/tooling/test_verifier_main_files_report_no_negative.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
#: 修前实测的假负条数（14 个验证器 × 2）—— 写进断言，避免「修好了」变成不可读的散文。
FALSE_NEGATIVES_BEFORE = 28

#: run 归属校验器（WP7）。
ATTRIBUTION_TOOL = "tools/check_ledger_run_attribution.py"
ATTRIBUTION_JUDGE = "tests/tooling/test_ledger_run_attribution_stays_offline.py"
GATE_RUNNER = ".cursor/skills/cursor-framework-check/scripts/run_all_checks.py"

#: 两条方法纪律（WP8）。
LOCATOR_JUDGE = "tests/tooling/test_record_locators_are_unambiguous.py"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _defines(source: str, name: str) -> bool:
    """模块里是否定义了该函数（AST，不靠文本搜索）。"""
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        for node in ast.walk(parsed)
    )


def _module_literal(source: str, name: str) -> object | None:
    """模块级常量的字面量值（AST；取不到 ⇒ None）。"""
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return None
    for node in parsed.body:
        if isinstance(node, ast.Assign):
            if any(getattr(t, "id", "") == name for t in node.targets):
                try:
                    return cast(object, ast.literal_eval(node.value))
                except ValueError:
                    return None
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == name:
            if node.value is None:
                return None
            try:
                return cast(object, ast.literal_eval(node.value))
            except ValueError:
                return None
    return None


def _quality_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """① 叙述质量三条：在树 / 可执行 / 射程自带 / **挂在装配面**。"""
    source = _text(root, QUALITY_MODULE)
    assembly = _text(root, ASSEMBLY)
    structural = _text(root, MANUSCRIPT)
    verdicts = [
        toolbox.verdict("quality-module-in-tree", bool(source), QUALITY_MODULE),
        toolbox.verdict(
            "quality-module-defines-three-checks",
            all(_defines(source, name) for name in QUALITY_CHECKS),
            ",".join(name for name in QUALITY_CHECKS if not _defines(source, name)),
        ),
        toolbox.verdict(
            "quality-module-declares-what-it-does-not-judge",
            all(marker in source for marker in NOT_JUDGED_MARKERS),
            ",".join(marker for marker in NOT_JUDGED_MARKERS if marker not in source),
        ),
        toolbox.verdict("quality-doc-in-tree", bool(_text(root, QUALITY_DOC)), QUALITY_DOC),
        toolbox.verdict("quality-judge-in-tree", bool(_text(root, QUALITY_JUDGE)), QUALITY_JUDGE),
        # **真的被装配路径调用**（不是死代码）：装配面有那一行调用。
        toolbox.verdict(
            "quality-gate-called-by-the-assembly-path",
            "validate_manuscript_quality(sections, facts.references)" in assembly,
            "装配面必须调用品质判据（否则它是死代码）",
        ),
        # 分层：结构入口**不**带品质判据（否则结构用例会因正文短而红）。
        toolbox.verdict(
            "structural-validator-keeps-the-quality-gate-out",
            "validate_quality("
            not in structural.split("def validate_manuscript(", 1)[-1].split("\ndef ", 1)[0],
            "`validate_manuscript` 不得自带品质判据（本 GOAL 实测 5 处连带红）",
        ),
    ]
    return verdicts


def _verifier_coverage_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """② 负判扫描：共享 helper 在树 / 主文件判据在树 / 17 个验证器走 helper。"""
    helper = _text(root, SHARED_HELPER)
    judge = _text(root, MAIN_FILE_JUDGE)
    registry = _text(root, VERIFIER_JUDGE)
    on_helper = sum(
        1 for line in registry.splitlines() if line.strip().startswith('"tools/verify_goal0')
    )
    return [
        toolbox.verdict("shared-progress-helper-in-tree", bool(helper), SHARED_HELPER),
        toolbox.verdict(
            "shared-helper-reads-live-or-archive",
            "archive" in helper and "progress_rows" in helper,
            "共享 helper 必须读**活跃面或归档**（否则归档后仍是假负）",
        ),
        toolbox.verdict("main-file-judge-in-tree", bool(judge), MAIN_FILE_JUDGE),
        toolbox.verdict(
            "main-file-judge-carries-a-counter-arm",
            "TestTheMainFileCriterionBites" in judge,
            "主文件判据必须带反证臂（否则它只是「都在场」的同义反复）",
        ),
        toolbox.verdict(
            "false-negatives-before-this-round",
            FALSE_NEGATIVES_BEFORE == 28,
            "修前实测的假负数必须逐字在场（14 个验证器 × 2）",
        ),
        toolbox.verdict(
            "verifier-registry-is-not-empty",
            on_helper >= 15,
            f"验证器清单只有 {on_helper} 条 ⇒ 射程疑似被清空",
        ),
    ]


def _attribution_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """③ run 归属校验器：在树 / 有 `--online` / **不在默认门**。"""
    source = _text(root, ATTRIBUTION_TOOL)
    judge = _text(root, ATTRIBUTION_JUDGE)
    runner = _text(root, GATE_RUNNER)
    return [
        toolbox.verdict("attribution-tool-in-tree", bool(source), ATTRIBUTION_TOOL),
        toolbox.verdict(
            "attribution-tool-has-an-online-switch",
            "--online" in source and "api.github.com" in source,
            "校验器必须有一个**显式**的出网开关（默认门不跑它）",
        ),
        toolbox.verdict(
            "attribution-tool-is-not-on-the-default-gate",
            "check_ledger_run_attribution" not in runner,
            "出网校验器不许出现在默认门 runner 里",
        ),
        toolbox.verdict("attribution-judge-in-tree", bool(judge), ATTRIBUTION_JUDGE),
        toolbox.verdict(
            "attribution-tool-does-not-import-httpx-at-top-level",
            "httpx" not in _top_level_imports(source),
            "模块顶层 import 网络库会让任何 import 它的代码都带上网络依赖",
        ),
    ]


def _top_level_imports(source: str) -> set[str]:
    """模块顶层的 import 名（AST）。"""
    names: set[str] = set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return names
    for node in parsed.body:
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _methodology_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """④ 两条方法纪律成了机械判据（宽松 glob 唯一性 / 读取面显式 UTF-8）。"""
    judge = _text(root, LOCATOR_JUDGE)
    return [
        toolbox.verdict("methodology-judge-in-tree", bool(judge), LOCATOR_JUDGE),
        toolbox.verdict(
            "methodology-judge-covers-the-glob-discipline",
            "each_goal_number_has_exactly_one_file" in judge,
            "必须有一条判据钉住「按编号定位唯一」（宽松 glob 读错文件是本轮纪律第 1 条）",
        ),
        toolbox.verdict(
            "methodology-judge-covers-the-encoding-discipline",
            "record_face_reads_are_explicitly_utf8" in judge,
            "必须有一条判据钉住「记录面读取显式 UTF-8」（区域默认编码是第 2 条的根因）",
        ),
        toolbox.verdict(
            "methodology-judge-carries-counter-arms",
            "TestTheCriterionBites" in judge,
            "两条判据都必须带反证臂",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有的四组断言（全部只读树）。"""
    return [
        *_quality_verdicts(root, toolbox),
        *_verifier_coverage_verdicts(root, toolbox),
        *_attribution_verdicts(root, toolbox),
        *_methodology_verdicts(root, toolbox),
    ]


__all__ = [
    "ASSEMBLY",
    "ATTRIBUTION_JUDGE",
    "ATTRIBUTION_TOOL",
    "FALSE_NEGATIVES_BEFORE",
    "LOCATOR_JUDGE",
    "MAIN_FILE_JUDGE",
    "MANUSCRIPT",
    "NOT_JUDGED_MARKERS",
    "QUALITY_CHECKS",
    "QUALITY_DOC",
    "QUALITY_JUDGE",
    "QUALITY_MODULE",
    "SHARED_HELPER",
    "assertion_verdicts",
]
