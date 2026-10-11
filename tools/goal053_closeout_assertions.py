#!/usr/bin/env python3
"""GOAL-20261011-053 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…052 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal053_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-053 特有的断言**。

四条主轴（逐条对 GOAL-053 的 EC）：

1. **EC-02 链的终点**：应用层有 `terminal_versions` 与**四态**（`CURRENT` / `SUCCEEDED` /
   `CYCLE` / `OUT_OF_VIEW`）；编排读面披露 `terminal` 键；**既有键逐字不变**。
2. **EC-03 同源**：HTTP 面从**应用层**取（`services.api.routers` **不得** import 适配器）；
   两处同源关系（用 **AST** 读 import 指向，不按写法判）。
3. **EC-04 两向**：判据在树，**四条按压 + 基线门**逐条对得上；归档进树。
4. **形态**：判词归档两份（非空、`CR=0`）；按压归档含**基线行**。

**三条纪律**（承 GOAL-027…052 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
- **本文件自身也遵守「判关系不判位置」**（承 `MEM-20261010-215`）**且不得恒假**
  （承 GOAL-051 §8）；**每条断言在本 GOAL 内都跑过两向**（该绿时绿 / 该红时红 ——
  红的那一向由 `scratch/goal053_press.py` 的四条按压证）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (("tests/api/test_memory_chain_end.py", 5),)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/contracts/test_openapi_snapshot.py",
    "tests/architecture/python/test_services_api_boundaries.py",
    "tests/api/test_memory_api.py",
)

#: EC-02/EC-03 落点。
SHARED_SOURCE = "packages/application/memory/disposition.py"
ORCH_FACE = "adapters/canonical/memory_read.py"
ROUTER = "services/api/routers/memory.py"
DTO = "services/api/dto/memory.py"
SNAPSHOT = "docs/api/openapi.m13.json"

#: EC-02：四态**逐条**点名（缺一即判红 —— 「某一态被悄悄删了」是最该响的回归）。
TERMINAL_STATES: tuple[str, ...] = (
    "TERMINAL_CURRENT",
    "TERMINAL_SUCCEEDED",
    "TERMINAL_CYCLE",
    "TERMINAL_OUT_OF_VIEW",
)

#: EC-02：两个读面上的新键（编排面 + HTTP 面）。
ORCH_KEY = '"terminal"'
HTTP_KEYS: tuple[str, ...] = ("terminal_state", "terminal_ids")

#: EC-03：两个读面**必须**从共用来源 import 的名字（同源的实际内容物）。
SHARED_NAMES: tuple[str, ...] = ("terminal_versions",)

#: 既有键（**改一个名字即判红**）。
LEGACY_ORCH_KEYS: tuple[str, ...] = ("supersedes", "superseded_by")
LEGACY_HTTP_FIELDS: tuple[str, ...] = (
    "contradictions",
    "superseded_by",
    "disposition",
    "reason",
)

#: EC-04 判据文件（逐条点名按压各自的受判面）。
CHAIN_JUDGE = "tests/api/test_memory_chain_end.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261011-053-press-two-way.txt"
VERDICT_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261011-053-verdict-current.txt"
VERDICT_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261011-053-verdict-clean.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal053_closeout.py"
ASSERTIONS = "tools/goal053_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _defines(source: str, name: str) -> bool:
    """该模块**自己定义**了该名字（AST —— 判关系不判写法）。"""
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
        and node.col_offset == 0
        for node in ast.walk(parsed)
    )


def _imported_from(source: str, module: str) -> set[str]:
    """`source` 从该模块 import 进来的**名字集合**（AST 读 —— 不靠文本巧合）。"""
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            names.update(alias.name for alias in node.names)
    return names


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


def _module_of(relative: str) -> str:
    """`packages/application/memory/disposition.py` ⇒ `packages.application.memory.disposition`。"""
    return relative[:-3].replace("/", ".")


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
    """EC-02：四态在应用层 + 两个读面都披露 + **既有键逐字不变**。"""
    shared = _text(root, SHARED_SOURCE)
    orch = _text(root, ORCH_FACE)
    router = _text(root, ROUTER)
    missing_states = [name for name in TERMINAL_STATES if f"{name} =" not in shared]
    return [
        toolbox.verdict(
            "ec02-the-terminal-helper-is-in-the-application-layer",
            _defines(shared, "terminal_versions"),
            "链终点的判定必须在应用层（两个读面都能 import 的那一层）",
        ),
        toolbox.verdict(
            "ec02-all-four-terminal-states-are-declared",
            not missing_states,
            ",".join(missing_states),
        ),
        toolbox.verdict(
            "ec02-the-orchestration-face-carries-the-terminal-key",
            ORCH_KEY in orch and "terminal_versions" in orch,
            "编排读面必须披露链终点（且取自应用层同一函数）",
        ),
        toolbox.verdict(
            "ec02-the-http-face-carries-the-terminal-keys",
            all(name in _text(root, DTO) for name in HTTP_KEYS),
            ",".join(name for name in HTTP_KEYS if name not in _text(root, DTO)),
        ),
        toolbox.verdict(
            "ec02-the-http-router-reuses-the-same-helper",
            "terminal_versions" in router,
            "HTTP 路由必须调应用层同一函数（不各写一套）",
        ),
        toolbox.verdict(
            "ec02-the-legacy-keys-are-unchanged",
            # **判关系**：既有键仍在（且仍按**直接**链接的语义被赋值 —— 由既有用例逐条断言）。
            all(f'"{name}"' in orch for name in LEGACY_ORCH_KEYS)
            and all(name in _text(root, DTO) for name in LEGACY_HTTP_FIELDS),
            "既有键一个不改名（改动由既有用例的逐条断言抓住）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：**同源** —— 两个读面都从同一模块 import 那个纯函数；快照同轮。"""
    shared = _module_of(SHARED_SOURCE)
    router = _text(root, ROUTER)
    orch = _text(root, ORCH_FACE)
    missing_router = [name for name in SHARED_NAMES if name not in _imported_from(router, shared)]
    missing_orch = [name for name in SHARED_NAMES if name not in _imported_from(orch, shared)]
    redefined = sorted(
        name for name in SHARED_NAMES if _defines(router, name) or _defines(orch, name)
    )
    return [
        toolbox.verdict(
            "ec03-both-faces-take-the-helper-from-the-one-source",
            not missing_router and not missing_orch,
            "HTTP 缺:" + ",".join(missing_router) + " 编排读面缺:" + ",".join(missing_orch),
        ),
        toolbox.verdict(
            "ec03-neither-face-redefines-a-second-copy",
            not redefined,
            ",".join(redefined),
        ),
        toolbox.verdict(
            "ec03-the-snapshot-carries-the-terminal-facts",
            all(marker in _text(root, SNAPSHOT) for marker in HTTP_KEYS),
            ",".join(marker for marker in HTTP_KEYS if marker not in _text(root, SNAPSHOT)),
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    chain = _text(root, CHAIN_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-chain-end-case-is-asserted",
            "test_the_chain_end_is_decidable_on_the_orchestration_face" in chain,
            "`P-1`（终点算错）的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-current-version-case-is-asserted",
            "test_the_chain_a_record_that_has_no_successor_is_its_own_current_version" in chain,
            "`P-2`（退回直接链接）的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-cycle-case-is-asserted",
            "test_a_cycle_is_named_not_silently_truncated" in chain,
            "`P-4`（环却静默）的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-cross-scope-case-is-asserted",
            "test_an_invisible_successor_is_named_not_read_as_the_current_version" in chain,
            "`P-3` / `OUT_OF_VIEW` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-agreement-case-is-asserted",
            "test_the_http_face_carries_the_chain_end_too" in chain,
            "两处同值的受判面必须在树",
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023…052 的教训）。"""
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
    # **判关系**（AST 读模块级 `_VERIFIERS` 元组，不按文本包含判 —— 文本包含会被
    # 本文件自己的注释/字符串偶然命中 ⇒ 假绿）。
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
