#!/usr/bin/env python3
"""GOAL-20261018-083 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…082 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件**只写本 GOAL 特有的断言**。

五条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01 判定是确定性纯函数**：模块在树 + 三种形态标签在树 + **零 IO 依赖**
   （源码级：不得 import 网络/时间/随机/模型）+ 判据里**确有**确定性断言。
2. **EC-02 接进既有门链且不放宽**：`_content_conflict_check` 在树 + 三条边界在树
   （同 scope / 不重复判已声明 / inactive 不参与）+ **既有引用完整性判词仍在**
   （逐字：`does not exist` / `is the proposal itself`）。
3. **EC-03 来源可分**：两种判词形态在各自文件里 + **API 缺口被钉住**
   （`MemoryProposalDto` 不含 `contradictions` 的断言在树）。
4. **EC-04 不 false-positive**：精度判据在树 + 四组语料（同义/无关/真实/射程边界）都在 +
   **非空转对照**在树。
5. **EC-05 自举收口**：本验证器与断言集进两处射程（由 `entry_verdicts` 的规范页断言
   + `standard_verdicts` 的规模门覆盖）。

**五条纪律**（承 GOAL-027…082）：不读两树判词做一致性断言（输入即输出）；
判词行不含绝对路径；f-string 分片按**子串**；`defines` 收**含类方法**的版本；
**一律判关系**；判词名**按序号**（`hash()` 受 `PYTHONHASHSEED` 影响）。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

#: 用例定义（模块级函数与类内方法**都算**）。
TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")


#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
#:
#: **条数以 `pytest --collect-only` 的读数为准**（`parametrize` 会展开成多条）——
#: 初版按「模块级 `def test_` 的个数」写下界，实测 24/21 的差就是 parametrize 展开
#: （7 个函数 → 24 条用例）。下界取**展开后的真实条数**：任何一条被删都会红。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/memory/test_content_conflict_detection.py", 24),
    ("tests/application/memory/test_content_conflict_gate.py", 10),
    ("tests/application/memory/test_content_conflict_read_face.py", 5),
    ("tests/application/memory/test_content_conflict_precision.py", 21),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal082_closeout.py",
    "tests/application/memory/test_conflict_target_integrity.py",
    "tests/api/test_memory_api.py",
)

#: 落点常量（逐条点名；缺一即判红）。
DECIDER = "packages/application/memory/content_conflict.py"
GATE = "packages/application/memory/gate.py"
DETECTION_TEST = "tests/application/memory/test_content_conflict_detection.py"
GATE_TEST = "tests/application/memory/test_content_conflict_gate.py"
READ_FACE_TEST = "tests/application/memory/test_content_conflict_read_face.py"
PRECISION_TEST = "tests/application/memory/test_content_conflict_precision.py"

#: 本轮引入的形态（**逐条点名**）。
DECIDER_ENTRY = "def detect_content_conflict("
FORM_NEGATION = 'FORM_NEGATION = "NEGATION_POLARITY"'
FORM_NUMERIC = 'FORM_NUMERIC = "NUMERIC_DIRECTION"'
FORM_ANTONYM = 'FORM_ANTONYM = "ANTONYM_PREDICATE"'
GATE_ENTRY = "def _content_conflict_check("
SCOPE_HELPER = "def _active_records_in_scope("

#: **既有语义**必须逐字仍在（门链的两条原有判词）。
EXISTING_GATE_WORDINGS: tuple[tuple[str, str], ...] = (
    (GATE, "supersedes target {old_id!r} does not exist"),
    (GATE, "contradiction target {other_id!r} is the proposal itself"),
    (GATE, "contradiction target {other_id!r} does not exist"),
)

#: 三条边界（**关系式**断言：检查的是行为谓词，不是散文）。
BOUNDARY_MARKERS: tuple[tuple[str, str], ...] = (
    (GATE_TEST, "test_only_the_same_scope_is_scanned"),
    (GATE_TEST, "test_inactive_records_do_not_participate"),
    (GATE_TEST, "test_a_declared_conflict_still_wins_over_content"),
)

#: 精度语料的四组 + 非空转对照（缺任一组即判红）。
PRECISION_GROUPS: tuple[str, ...] = (
    "_SYNONYMOUS",
    "_UNRELATED",
    "_REAL_WORLD",
    "_OUT_OF_SCOPE",
    "test_the_corpus_is_not_vacuous",
)

#: 判定模块**不得** import 的依赖（纯函数纪律的机械形态）。
FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "socket",
    "http",
    "httpx",
    "requests",
    "urllib",
    "random",
    "datetime",
    "time",
    "openai",
    "anthropic",
    "litellm",
    "openhands",
)


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def imported_roots(source: str) -> set[str]:
    """模块的顶层 import 根名（AST；解析失败 ⇒ 空集，由另一条断言判「不在树」）。"""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


def collected_case_count(root: Path, relative: str) -> int:
    """模块的**真实用例条数** —— 直接问 pytest 的收集面（`--collect-only -q`）。

    **为什么不用正则数**：`parametrize` 会展开，正则要么漏（只数 `def test_`）要么多
    （把别的括号行算进来）—— 两种实测都偏。收集面是**唯一**与「跑起来有多少条」同源的读数，
    下界拿它比对 ⇒ **删掉任何一条用例（含参数行）都会红**。
    """
    import subprocess
    import sys

    completed = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", str(root / relative), "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=str(root),
        check=False,
    )
    match = re.search(r"(\d+) tests? collected", completed.stdout)
    return int(match.group(1)) if match else 0


def _floor_verdicts(root: Path, toolbox: Any) -> list[Any]:
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        count = collected_case_count(root, relative)
        verdicts.append(
            toolbox.verdict(
                f"case-floor-{Path(relative).stem}", count >= floor, f"{count} < {floor}"
            )
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(f"prior-judge-{Path(relative).stem}", (root / relative).is_file())
        )
    return verdicts


def _placement_verdicts(root: Path, toolbox: Any) -> list[Any]:
    points: tuple[tuple[str, str, str], ...] = (
        (DECIDER, DECIDER_ENTRY, "decider-in-tree"),
        (DECIDER, FORM_NEGATION, "form-negation-named"),
        (DECIDER, FORM_NUMERIC, "form-numeric-named"),
        (DECIDER, FORM_ANTONYM, "form-antonym-named"),
        (GATE, GATE_ENTRY, "gate-hook-in-tree"),
        (GATE, SCOPE_HELPER, "scope-helper-in-tree"),
        (READ_FACE_TEST, "does not exist", "read-face-sees-reference-wording"),
        (READ_FACE_TEST, "content contradicts", "read-face-sees-content-wording"),
        (
            READ_FACE_TEST,
            "test_the_http_proposal_dto_does_not_expose_declarations",
            "api-gap-pinned",
        ),
        (DETECTION_TEST, "test_repeated_calls_are_byte_identical", "determinism-pinned"),
        (DETECTION_TEST, "test_the_decider_has_no_io_imports", "purity-pinned"),
    )
    return [
        toolbox.verdict(name, needle in _text(root, relative), f"{relative} 缺 {needle!r}")
        for relative, needle, name in points
    ]


def _existing_semantics_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """既有门链判词逐字仍在 + 三条边界判据在树。"""
    verdicts = [
        toolbox.verdict(
            f"existing-gate-wording-{index}",
            needle in _text(root, relative),
            f"{relative} 丢了既有判词 {needle!r}（既有语义被改）",
        )
        for index, (relative, needle) in enumerate(EXISTING_GATE_WORDINGS, start=1)
    ]
    verdicts.extend(
        toolbox.verdict(
            f"boundary-{index}",
            needle in _text(root, relative),
            f"{relative} 缺边界判据 {needle!r}",
        )
        for index, (relative, needle) in enumerate(BOUNDARY_MARKERS, start=1)
    )
    return verdicts


def _purity_verdict(root: Path, toolbox: Any) -> Any:
    """**零 IO / 零模型**（源码级）：判定模块的 import 根名不得命中黑名单。"""
    found = imported_roots(_text(root, DECIDER)) & set(FORBIDDEN_IMPORTS)
    return toolbox.verdict(
        "decider-has-no-io-imports",
        not found,
        f"{DECIDER} import 了禁用的依赖: {sorted(found)}",
    )


def _precision_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """四组语料 + 非空转对照都在（`EC-04` 的结构面）。"""
    source = _text(root, PRECISION_TEST)
    return [
        toolbox.verdict(
            f"precision-group-{index}",
            marker in source,
            f"{PRECISION_TEST} 缺 {marker}",
        )
        for index, marker in enumerate(PRECISION_GROUPS, start=1)
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 特有的断言（公共面不在此处）。"""
    return [
        *_floor_verdicts(root, toolbox),
        *_placement_verdicts(root, toolbox),
        *_existing_semantics_verdicts(root, toolbox),
        _purity_verdict(root, toolbox),
        *_precision_verdicts(root, toolbox),
    ]


__all__ = ["CASE_FLOORS", "assertion_verdicts", "imported_roots"]
