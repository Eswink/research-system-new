#!/usr/bin/env python3
"""GOAL-20261011-054 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…053 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal054_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-054 特有的断言**。

三条主轴（逐条对 GOAL-054 的 EC）：

1. **EC-02 gate 对齐**：`_contradiction_check` 里 `contradictions` **也**过存在性 + **不得自指**；
   `supersedes` 那一侧**判词逐字未动**（用 **AST** 读那个字面量，不按文本包含判）。
2. **EC-03 读面一致**：读面**不再**把悬空 / 自指当成 `CONFLICTED`（由 gate 拒绝 ⇒ 读不到）；
   既有键逐字不变。
3. **EC-04 两向**：判据在树，**四条按压 + 基线门**逐条对得上；归档进树。

**三条纪律**（承 GOAL-027…053 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 **AST** 读而不是文本巧合。
- **本文件自身也遵守「判关系不判位置」**（承 `MEM-20261010-215`）**且不得恒假**
  （承 GOAL-051 §8）；**红的那一向由 `scratch/goal054_press.py` 的四条按压证**。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/memory/test_conflict_target_integrity.py", 4),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/memory/test_gate_adversarial.py",
    "tests/api/test_memory_api.py",
)

#: EC-02/EC-03 落点。
GATE = "packages/application/memory/gate.py"
SHARED_SOURCE = "packages/application/memory/disposition.py"
ROUTER = "services/api/routers/memory.py"
DTO = "services/api/dto/memory.py"

#: EC-02：被校验的两侧各自**必须**点名的判词**片段**（逐条；缺一即判红）。
#: **为什么用片段**：判词是 **f-string** ⇒ AST 里被拆成 `Constant` 分片
#: （`"contradiction target "` + `FormattedValue` + `" does not exist"`）
#: ⇒ 按整句核对会**永远失配**（初版就这样 ⇒ 五条判据全假红；实测确认了分片形态）。
SUPERSEDES_FRAGMENTS: tuple[str, ...] = (
    "supersedes target ",
    " does not exist",
)
CONTRADICTION_FRAGMENTS: tuple[str, ...] = (
    "contradiction target ",
    " does not exist",
    " is the proposal itself",
)

#: EC-02：必查的**阶段名**（两侧同属 `contradiction` 阶段 —— 与改动前同一个阶段）。
STAGE = "contradiction"

#: 既有键（**改一个名字即判红**）。
LEGACY_HTTP_FIELDS: tuple[str, ...] = (
    "contradictions",
    "superseded_by",
    "disposition",
    "reason",
    "terminal_state",
    "terminal_ids",
)

#: EC-04 判据 / 归档落点。
NEW_JUDGE = "tests/application/memory/test_conflict_target_integrity.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261011-054-press-two-way.txt"
VERDICT_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261011-054-verdict-current.txt"
VERDICT_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261011-054-verdict-clean.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal054_closeout.py"
ASSERTIONS = "tools/goal054_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _module_string_literals(source: str) -> set[str]:
    """模块里出现的**字符串字面量**集合（AST 读 —— 不按文本包含判，避免注释/散文偶然命中）。"""
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


def _field_names(source: str, class_name: str) -> set[str]:
    """类体里的**注解名**（AST 读 —— 不靠行首正则，那会随缩进/换行静默失配）。"""
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
    """EC-02：两侧**同一条纪律**（存在性 + 不得自指）且 `supersedes` 判词**逐字未动**。"""
    literals = _module_string_literals(_text(root, GATE))
    missing = [item for item in CONTRADICTION_FRAGMENTS if item not in literals]
    missing_super = [item for item in SUPERSEDES_FRAGMENTS if item not in literals]
    return [
        toolbox.verdict(
            "ec02-the-contradiction-targets-are-checked-for-existence",
            {"contradiction target ", " does not exist"} <= literals,
            "`contradictions` 的被引 id 必须查存在性（承 `W-2` 声明面完整性）",
        ),
        toolbox.verdict(
            "ec02-a-self-referential-target-is-rejected-by-name",
            " is the proposal itself" in literals,
            "被引 id == 提案自身 ⇒ 点名拒绝（不是静默丢弃）",
        ),
        toolbox.verdict(
            "ec02-no-contradiction-verdict-is-missing",
            not missing,
            ",".join(missing),
        ),
        toolbox.verdict(
            "ec02-the-supersedes-verdict-is-unchanged-verbatim",
            # **回归锚**：那一侧是**基准**，判词逐字保持（两个片段都在）。
            not missing_super,
            ",".join(missing_super),
        ),
        toolbox.verdict(
            "ec02-both-sides-still-report-the-same-stage",
            STAGE in literals,
            "两侧同属既有 `contradiction` 阶段（不新建阶段）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：读面既有键逐字不变（悬空 / 自指已由 gate 拒绝 ⇒ 读面看不到）。"""
    dto = _text(root, DTO)
    fields = _field_names(dto, "MemoryRecordDto")
    missing = [name for name in LEGACY_HTTP_FIELDS if name not in fields]
    return [
        toolbox.verdict(
            "ec03-the-http-face-keys-are-unchanged",
            not missing,
            ",".join(missing),
        ),
        toolbox.verdict(
            "ec03-the-read-face-still-uses-the-application-layer",
            "disposition_of" in _text(root, ROUTER)
            and "disposition_of" in _text(root, SHARED_SOURCE),
            "读面判定仍取自应用层（不各写一套）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    judge = _text(root, NEW_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-dangling-case-is-asserted",
            "test_a_dangling_conflict_target_is_rejected_by_name" in judge,
            "`Q-1` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-self-reference-case-is-asserted",
            "test_a_self_referential_conflict_target_is_rejected_by_name" in judge,
            "`Q-2` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-not-misfiring-case-is-asserted",
            "test_a_real_conflict_target_is_accepted" in judge,
            "`Q-3` 的受判面必须在树（校验不误伤正常声明）",
        ),
        toolbox.verdict(
            "ec04-the-supersedes-regression-anchor-is-asserted",
            "test_the_supersedes_side_is_unchanged_verbatim" in judge,
            "`Q-4` 的受判面必须在树（`supersedes` 面逐字）",
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023…053 的教训）。"""
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
