#!/usr/bin/env python3
"""GOAL-20261011-056 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…055 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal056_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-056 特有的断言**。

三条主轴（逐条对 GOAL-056 的 EC）：

1. **EC-02 始点**：等待面**报时长**；两个时点都由**调用方**给（`GateClock`）⇒ **不读挂钟**。
2. **EC-03 超期可判定**：域上有 `gate_nudge_after_seconds`；**正整数**校验在位；
   等待面**有界的超期点名**在位（「等太久了」+「决定权仍在人」）。
3. **EC-04 两向**：判据在树，**四条按压 + 基线门**逐条对得上；归档进树。

**四条纪律**（承 GOAL-027…055 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责；
- **判词行不含本树绝对路径**（两树入口会拒绝），且用 **AST** 读而不是文本巧合；
- **f-string 的 AST 分片**：按**子串**核对（片段可能只是某个分片的一部分 —— 承序 22/23）；
- **`defines` 若要求模块级会让「方法」恒假**（承序 23）⇒ 本文件用含方法的版本。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    # 下界按**函数数**钉（7 个函数；其中坏界那条**参数化 2 例** ⇒ 收集 8 例）。
    ("tests/application/run_orchestration/test_gate_nudge_on_the_run_path.py", 7),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/run_orchestration/test_program_waiting_on_the_run_path.py",
    "tests/application/run_orchestration/test_program_runner.py",
    "tests/domain/test_research_program.py",
)

#: EC-02/EC-03 落点。
DOMAIN = "packages/domain/program.py"
WAITING = "packages/application/run_orchestration/program_waiting.py"
BRIDGE = "packages/application/run_orchestration/program_gate_evaluation.py"
RUNNER = "packages/application/run_orchestration/program_runner.py"

#: EC-03：域字段名（逐条点名；缺一即判红）。
FIELD = "gate_nudge_after_seconds"

#: EC-02/EC-03：判词**片段**（f-string ⇒ 子串核对；见模块 docstring）。
NOTE_FRAGMENTS: tuple[str, ...] = (
    "已等待",
    "秒",
)
OVERDUE_FRAGMENTS: tuple[str, ...] = (
    "等太久了",
    "决定权仍在人",
)
BOUND_REJECT_FRAGMENTS: tuple[str, ...] = ("must be a positive integer",)

#: EC-02：参数对象（两个时点都由调用方给 ⇒ 不读挂钟）。
CLOCK_OBJECT = "GateClock"
CLOCK_FIELDS: tuple[str, ...] = ("now", "waited_since")

#: EC-04 判据 / 归档落点。
NEW_JUDGE = "tests/application/run_orchestration/test_gate_nudge_on_the_run_path.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261011-056-press-two-way.txt"
VERDICT_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261011-056-verdict-current.txt"
VERDICT_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261011-056-verdict-clean.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal056_closeout.py"
ASSERTIONS = "tools/goal056_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _module_string_literals(source: str) -> set[str]:
    """模块里的**字符串字面量**（AST 读 —— 不按文本包含判，避免注释/散文偶然命中）。

    f-string 会被 AST 拆成 `Constant` 分片 ⇒ 返回的是**片段集合**（调用方按片段核对）。
    """
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    return {
        node.value
        for node in ast.walk(parsed)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _contains(literals: set[str], fragment: str) -> bool:
    """某个**片段**是否出现在那些字符串字面量里（**子串**匹配 —— 不是集合成员）。

    承序 22/23 的实测：判词多是 f-string ⇒ 片段可能只是某个分片的一部分 ⇒
    按「集合成员」核对会**永远失配**。
    """
    return any(fragment in literal for literal in literals)


def _defines(source: str, name: str) -> bool:
    """该模块里有**任何**同名函数（**含类方法** —— 缩进不判；承序 23 的教训）。"""
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        for node in ast.walk(parsed)
    )


def _class_annotations(source: str, class_name: str) -> set[str]:
    """类体的**注解名**（AST 读 —— 不 import 那个包：本文件被两树入口按**路径**加载）。"""
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance((target := item.target), ast.Name)
            }
    return set()


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    parsed = ast.parse(source)
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：时长可报 + **两个时点都由调用方给**（不读挂钟）。"""
    waiting_literals = _module_string_literals(_text(root, WAITING))
    missing = [item for item in NOTE_FRAGMENTS if not _contains(waiting_literals, item)]
    clock_fields = _class_annotations(_text(root, WAITING), CLOCK_OBJECT)
    return [
        toolbox.verdict(
            "ec02-the-waiting-face-reports-the-elapsed-time",
            not missing,
            ",".join(missing),
        ),
        toolbox.verdict(
            "ec02-the-clock-object-carries-both-moments",
            # **判关系**：那个参数对象带**两个**时点（现在 / 何时开始等）⇒ 不读挂钟。
            set(CLOCK_FIELDS) <= clock_fields,
            ",".join(sorted(set(CLOCK_FIELDS) - clock_fields)),
        ),
        toolbox.verdict(
            "ec02-the-elapsed-helper-does-not-consult-the-wall-clock",
            _defines(_text(root, WAITING), "_elapsed_note")
            and "Timestamp.now("
            not in _text(root, WAITING).split("def _elapsed_note")[1].split("\ndef ")[0],
            "时长助手不得读挂钟（时点由调用方给 ⇒ 可复现）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：域界 + 正整数校验 + **有界的超期点名**（只点名，不自动放行）。"""
    waiting_literals = _module_string_literals(_text(root, WAITING))
    domain_literals = _module_string_literals(_text(root, DOMAIN))
    missing_overdue = [item for item in OVERDUE_FRAGMENTS if not _contains(waiting_literals, item)]
    missing_bound = [
        item for item in BOUND_REJECT_FRAGMENTS if not _contains(domain_literals, item)
    ]
    return [
        toolbox.verdict(
            "ec03-the-domain-declares-the-bound",
            FIELD in _class_annotations(_text(root, DOMAIN), "ResearchProgram"),
            f"域上必须有 `{FIELD}`（等待的时限界）",
        ),
        toolbox.verdict(
            "ec03-a-non-positive-bound-is-rejected-by-name",
            not missing_bound,
            ",".join(missing_bound),
        ),
        toolbox.verdict(
            "ec03-the-overdue-case-is-named-not-auto-released",
            # **判关系**：超期那一支**点名**「等太久了」**且**写明「决定权仍在人」
            # （后者是「不自动放行」的**可读证据**）。
            not missing_overdue,
            ",".join(missing_overdue),
        ),
        toolbox.verdict(
            "ec03-the-undeclared-bound-is-read-as-none",
            # **判关系**：界为 `None` 时**提前返回**（只报时长）—— 既有行为逐字不变。
            "if bound is None" in _text(root, WAITING),
            "未声明界 ⇒ 不报超期（逐字不变）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    judge = _text(root, NEW_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-elapsed-case-is-asserted",
            "test_the_waiting_face_reports_how_long_it_has_waited" in judge,
            "`S-1` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-overdue-case-is-asserted",
            "test_at_or_beyond_the_bound_is_named_as_nudging" in judge,
            "`S-2` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-undeclared-bound-case-is-asserted",
            "test_an_undeclared_bound_never_names_overdue" in judge,
            "`S-3` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-bad-bound-case-is-asserted",
            "test_a_non_positive_bound_is_rejected_by_name" in judge,
            "`S-4` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-baseline-gate-is-in-the-archive",
            "BASELINE" in press and "GREEN" in press,
            "归档必须含**基线行**（未按压不得红 —— 承 §8 的一级纪律）",
        ),
        toolbox.verdict(
            "ec04-every-press-is-red-in-the-archive",
            press.count("按压 RED") >= 4 and "all_red_and_restored=True" in press,
            "四条的读数必须全红且复原一致",
        ),
    ]


def _judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判据面：例数下界 + 既有判据仍在树（引用而非重复）。"""
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        count = _count_test_cases(root, relative)
        verdicts.append(
            toolbox.verdict(f"cases-{Path(relative).stem}", count >= floor, f"{count} < {floor}")
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(f"prior-judge-{Path(relative).stem}", (root / relative).is_file())
        )
    return verdicts


def _has_carriage_return(raw: bytes) -> bool:
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023…055 的教训）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：判词归档形态（两份、非空、CR=0）。**不读内容做断言**（输入即输出）。"""
    verdicts: list[Any] = []
    for label, relative in (("current", VERDICT_CURRENT), ("clean", VERDICT_CLEAN)):
        path = root / relative
        raw = path.read_bytes() if path.is_file() else b""
        verdicts.append(
            toolbox.verdict(
                f"verdict-archive-{label}",
                bool(raw) and not _has_carriage_return(raw),
                "missing/empty" if not raw else "contains CR",
            )
        )
    press_path = root / PRESS_ARCHIVE
    press_raw = press_path.read_bytes() if press_path.is_file() else b""
    verdicts.append(
        toolbox.verdict(
            "press-archive-is-binary-safe",
            bool(press_raw) and not _has_carriage_return(press_raw),
            "missing/empty" if not press_raw else "contains CR",
        )
    )
    return verdicts


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """两处射程**纯收紧**：`IN_SCOPE`（四道门）与**射程分区清单**（判据面）。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    verifiers = toolbox.module_literal(_text(root, VERIFIER_JUDGE), "_VERIFIERS")
    registered = isinstance(verifiers, tuple) and SELF in verifiers
    return [
        toolbox.verdict("scope-in-scope-covers-this-round", not missing, ",".join(missing)),
        toolbox.verdict(
            "scope-verifier-registry-covers-this-round",
            registered,
            "收口验证器必须已登记进射程清单",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言全集（顺序稳定；判词名不带路径）。"""
    return [
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
