#!/usr/bin/env python3
"""GOAL-20261014-078 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…077 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-078 特有的断言**。

四条主轴（逐条对 GOAL-078 的 EC）：

1. **EC-01 接缝在树且判定成对**：`build_retrieval_context` + 有界上限 + 两种空分得开 +
   零出网的**构造性**证据（AST 判传输层名字）。
2. **EC-02 经产品路径到达下游会话**：e2e 在树且覆盖「正向 / 反证 / 射程 / 自检」四条；
   两组合根接线。
3. **EC-03 「进了什么」可复核**：制品落盘 + **同源**（写盘字节即 digest 的源）+ 命名约定
   + 空集合带理由。
4. **EC-04 live 取证**：live 判据断言上下文到达会话 + 读数归档在树（`CR=0`）。

**五条纪律**（承 GOAL-027…077）：不读两树判词做一致性断言（那是输入即输出）；
判词行不含绝对路径；f-string 分片按**子串**；`defines` 收**含类方法**的版本；
**一律判关系**（抽函数会让钉调用点的判据假红）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/test_retrieval_context_seam.py", 16),
    ("tests/application/test_retrieval_context_read_face.py", 5),
    ("tests/e2e/test_retrieval_context_reaches_the_session.py", 7),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal077_closeout.py",
    "tests/e2e/test_research_report_chain_live.py",
)

#: 落点常量（逐条点名；缺一即判红）。
SEAM = "packages/application/run_orchestration/retrieval_context.py"
SUPPORT = "services/api/retrieval_context_support.py"
E2E = "tests/e2e/test_retrieval_context_reaches_the_session.py"
LIVE = "tests/e2e/test_research_report_chain_live.py"
LIVE_SUPPORT = "tests/e2e/retrieval_context_support.py"
COMPOSITION = "services/api/composition.py"
PG_COMPOSITION = "services/api/pg_composition.py"

#: 本轮引入的形态（**逐条点名**）。
ASSEMBLER = "def build_retrieval_context("
PERSIST = "def persist_retrieval_context("
PAYLOAD = "def payload_bytes("
BOUNDS = "DEFAULT_MAX_CHARS"
RUN_IN_VIEW = 'run_id: str = ""'
TRANSPORT_FORBIDDEN = ("urlopen", "socket", "connect", "Client", "Session", "request", "urlencode")

#: EC-02 / EC-03 / EC-04 的判定面（判据文件里必须在场的用例名）。
E2E_CASES: tuple[str, ...] = (
    "test_the_downstream_context_is_not_empty_and_traces_to_retrieved_evidence",
    "test_the_upstream_context_is_empty_and_named",
    "test_the_refs_are_a_subset_of_retrieved_and_not_of_everything",
    "test_the_seam_is_the_one_that_was_wired",
)
READ_FACE_CASES: tuple[str, ...] = (
    "test_the_written_artifact_is_the_digest_source",
    "test_the_artifact_id_is_task_prefixed_and_named",
    "test_an_empty_context_is_written_with_its_reason",
)
LIVE_MARKERS: tuple[str, ...] = (
    "assert_the_context_reached_sessions",
    ":retrieval_context",
)

#: 按压归档（**进树**、二进制写盘）。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261014-078-press-two-way.txt"
#: EC-04 的读数归档。
LIVE_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261014-078-ec04-context-evidence.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal078_closeout.py"
ASSERTIONS = "tools/goal078_closeout_assertions.py"

#: 四条按压：各自的**受判面用例/类**必须在树。
_PRESS_JUDGES: tuple[tuple[str, str], ...] = (
    ("V8-1", "TestTheDownstreamSessionSeesTheRetrievedContent"),
    ("V8-2", "TestTheRunFilterBites"),
    ("V8-3", "TestAToolResultWithoutTheRetrievedLabelDoesNotEnter"),
    ("V8-4", "TestWhatEnteredTheContextIsReadableAftheFact"),
)


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return 0
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _ec01_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：接缝在树 + 有界 + 两种空分得开 + **零出网是构造性的**。"""
    seam = _text(root, SEAM)
    names = (
        {node.id for node in ast.walk(ast.parse(seam)) if isinstance(node, ast.Name)}
        if seam
        else set()
    )
    attributes = (
        {node.attr for node in ast.walk(ast.parse(seam)) if isinstance(node, ast.Attribute)}
        if seam
        else set()
    )
    offenders = sorted(set(TRANSPORT_FORBIDDEN) & (names | attributes))
    return [
        toolbox.verdict(
            "ec01-the-seam-is-in-tree",
            ASSEMBLER and toolbox.defines(seam, "build_retrieval_context"),
            "`build_retrieval_context` 必须在树",
        ),
        toolbox.verdict(
            "ec01-the-bounds-are-declared",
            BOUNDS in seam and "DEFAULT_MAX_ITEMS" in seam,
            "逐条字符上限与条数上限都必须声明（§10 的有界口径）",
        ),
        toolbox.verdict(
            "ec01-the-two-empties-are-distinguishable",
            "no retrieved evidence" in seam and "retrieved evidence record(s)" in seam,
            "「没有证据」与「读不出内容」必须是两句判词（分不开 ⇒ 含混重新回来）",
        ),
        toolbox.verdict(
            "ec01-zero-egress-is-structural",
            offenders == [],
            f"接缝模块不得有任何传输层名字：{offenders}",
        ),
    ]


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：e2e 在树且覆盖四条 + 两组合根接线 + 支持件在树。"""
    e2e = _text(root, E2E)
    missing = [name for name in E2E_CASES if name not in e2e]
    return [
        toolbox.verdict("ec02-the-e2e-is-in-tree", bool(e2e), "e2e 判据文件不在树"),
        toolbox.verdict(
            "ec02-the-e2e-covers-positive-refutation-scope-and-self-check",
            not missing,
            f"缺用例：{missing}",
        ),
        toolbox.verdict(
            "ec02-both-prod-roots-wire-the-seam",
            "retrieval_context=retrieval_context_builder(" in _text(root, COMPOSITION)
            and "retrieval_context=retrieval_context_builder(" in _text(root, PG_COMPOSITION),
            "两个产品组合根都必须接上装配器",
        ),
        toolbox.verdict(
            "ec02-the-support-module-is-in-tree",
            (root / SUPPORT).is_file(),
            "装配决策模块不在树",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：制品落盘 + **同源**（唯一构造/编码点）+ 命名约定 + 空集合带理由。"""
    seam = _text(root, SEAM)
    read_face = _text(root, "tests/application/test_retrieval_context_read_face.py")
    missing = [name for name in READ_FACE_CASES if name not in read_face]
    return [
        toolbox.verdict(
            "ec03-the-persistence-is-in-tree",
            toolbox.defines(seam, "persist_retrieval_context"),
            "`persist_retrieval_context` 必须在树（读面的生产者）",
        ),
        toolbox.verdict(
            "ec03-the-digest-source-is-one-place",
            PAYLOAD in seam and toolbox.defines(seam, "context_payload"),
            "载荷构造与编码必须是**唯一**的两点（同源的前提）",
        ),
        toolbox.verdict(
            "ec03-the-id-is-task-prefixed",
            "def context_artifact_id(" in seam and ":retrieval_context" in seam,
            "制品 id 必须按 task 前缀命名（既有读面靠它收 run 作用域制品）",
        ),
        toolbox.verdict(
            "ec03-the-read-face-is-judged",
            not missing
            and (root / "tests/application/test_retrieval_context_read_face.py").is_file(),
            f"缺读面判据：{missing}",
        ),
        toolbox.verdict(
            "ec03-the-view-carries-the-run-id",
            RUN_IN_VIEW in seam,
            "视图必须带 run 标识（读面载荷要它；这是实测抓到的 AttributeError 修复）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：live 断言 + 支持件 + 读数归档在树（`CR=0`）。"""
    live = _text(root, LIVE)
    support = _text(root, LIVE_SUPPORT)
    raw = (root / LIVE_ARCHIVE).read_bytes() if (root / LIVE_ARCHIVE).is_file() else b""
    missing = [marker for marker in LIVE_MARKERS if marker not in live + support]
    return [
        toolbox.verdict(
            "ec04-the-live-judge-asserts-the-context",
            not missing,
            f"live 判据缺：{missing}",
        ),
        toolbox.verdict(
            "ec04-the-evidence-archive-is-in-tree",
            bool(raw) and bytes([13]) not in raw,
            "missing/empty" if not raw else "contains CR",
        ),
    ]


def _judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """判据面：例数下界 + 既有判据仍在树。"""
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


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：按压归档形态（非空、`CR=0`）+ **四条逐条在场**。

    **不读内容做一致性断言**（输入即输出）—— 只判形态与标签在场。
    """
    path = root / PRESS_ARCHIVE
    raw = path.read_bytes() if path.is_file() else b""
    text = raw.decode("utf-8", errors="replace")
    missing = [label for label, _case in _PRESS_JUDGES if label not in text]
    return [
        toolbox.verdict(
            "press-archive-is-binary-safe",
            bool(raw) and bytes([13]) not in raw,
            "missing/empty" if not raw else "contains CR",
        ),
        toolbox.verdict(
            "press-archive-names-every-arm",
            not missing and "all_red_and_restored=True" in text,
            f"缺标签/未全红：{missing}",
        ),
    ]


def _press_judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """四条按压各自的**受判面**必须在树（判据不被删除/改名才有的保证）。"""
    joined = _text(root, E2E) + _text(root, "tests/application/test_retrieval_context_seam.py")
    return [
        toolbox.verdict(f"press-{label.lower()}-arm-is-asserted", case in joined, case)
        for label, case in _PRESS_JUDGES
    ]


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """两处射程**纯收紧**：`IN_SCOPE`（四道门）与验证器注册清单。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    verifiers = toolbox.module_literal(_text(root, VERIFIER_JUDGE), "_VERIFIERS")
    registered = isinstance(verifiers, tuple) and SELF in verifiers
    return [
        toolbox.verdict("scope-in-scope-pure-tightening", not missing, ",".join(missing)),
        toolbox.verdict("scope-verifier-registered", registered),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的特有断言（收口验证器唯一入口）。"""
    return [
        *_ec01_verdicts(root, toolbox),
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_press_judge_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
