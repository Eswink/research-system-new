#!/usr/bin/env python3
"""GOAL-20261010-044 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…043 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal044_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-044 特有的断言**。

三条主轴（逐条对 GOAL-044 的 EC）：

与 GOAL-023…043 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
   域判据的**集合相等**同轮加了一条（纯加法）。
2. **EC-03 点名面**：`program_waiting.py` 的 `pending_approval` 四态**全点名**
   （查到待决 / 查不到 / 缺审批面 / 面故障）——逐条在树。
3. **EC-04 分派与实跑**：驱动按 run 状态分派（`AWAITING_HUMAN`）；判据文件在树且例数达下界；
   `WAIT` 面**逐字保持**的证据在树（反证用例断言理由串与 `cited_facts`）。

**两条纪律**（承 GOAL-027…043 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_program_waiting_on_the_run_path.py", 7),
    ("tests/application/run_orchestration/test_program_runner.py", 18),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/domain/test_research_program.py",
    "tests/e2e/test_program_advance_on_the_run_path.py",
    "tests/tooling/test_python_source_limits.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-02 落点（判定种类）。
DOMAIN = "packages/domain/program.py"
DOMAIN_JUDGE = "tests/domain/test_research_program.py"
#: EC-03 落点（点名面）。
WAITING = "packages/application/run_orchestration/program_waiting.py"
RUNNER = "packages/application/run_orchestration/program_runner.py"
ROUTER = "services/api/routers/programs.py"
#: EC-04 落点（判据）。
WAIT_JUDGE = "tests/application/run_orchestration/test_program_waiting_on_the_run_path.py"

#: EC-03 必须点名的四个形态（按**点名句的关键词**逐条；缺一即判红）。
NAMED_FORMS: tuple[str, ...] = (
    "未提供审批面",
    "查不到",
    "list_for_run",
)

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal044_closeout.py"
ASSERTIONS = "tools/goal044_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261010-044-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261010-044-verdict-clean.txt"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _function_names(source: str) -> set[str]:
    """模块里定义的函数名（AST 读，不靠文本巧合）。"""
    if not source:
        return set()
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return set()
    return {
        node.name
        for node in ast.walk(parsed)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def _count_test_cases(root: Path, relative: str) -> int:
    source = _text(root, relative)
    if not source:
        return 0
    parsed = ast.parse(source)
    return sum(
        1
        for node in ast.walk(parsed)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
    )


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：新种类在场 + 与 `WAIT` 互不混用的语义**写进域**（不是只在测试里）。"""
    domain = _text(root, DOMAIN)
    domain_judge = _text(root, DOMAIN_JUDGE)
    return [
        toolbox.verdict(
            "ec02-wait-for-approval-is-registered",
            'WAIT_FOR_APPROVAL = "WAIT_FOR_APPROVAL"' in domain,
        ),
        toolbox.verdict(
            "ec02-the-distinction-is-documented-in-the-domain",
            "互不混用" in domain and "人工闸门" in domain,
        ),
        toolbox.verdict(
            "ec02-the-domain-judge-pins-the-new-kind",
            '"WAIT_FOR_APPROVAL",' in domain_judge,
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：点名面**四态全点名**（缺面 / 查不到 / 查到；面故障逐字在树）。"""
    waiting = _text(root, WAITING)
    names = _function_names(waiting)
    return [
        toolbox.verdict(
            "ec03-the-waiting-module-exists-and-exposes-the-decision",
            {"pending_approval", "waiting_round_decision"} <= names,
        ),
        toolbox.verdict(
            "ec03-awaiting-human-is-a-declared-set",
            "AWAITING_HUMAN" in waiting
            and "WAITING_FOR_APPROVAL" in waiting
            and "PAUSED" in waiting,
        ),
        toolbox.verdict(
            "ec03-every-missing-form-is-named",
            all(marker in waiting for marker in NAMED_FORMS),
            ",".join(item for item in NAMED_FORMS if item not in waiting),
        ),
        toolbox.verdict(
            "ec03-the-approval-querier-is-read-only",
            "list_for_run" in waiting and "replace(" not in waiting and "register(" not in waiting,
            "判定面必须**只读**审批面（不得自动批准 / 跳过）",
        ),
        toolbox.verdict(
            "ec03-the-driver-dispatches-by-state",
            "waiting_round_decision(last, last_index, approvals)" in _text(root, RUNNER),
        ),
        toolbox.verdict(
            "ec03-the-router-passes-the-existing-approval-instance",
            "approvals=deps.approvals" in _text(root, ROUTER),
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：判据在树，且**两向**都被断言（新种类 + `WAIT` 逐字保持 + 只读审批面）。"""
    judge = _text(root, WAIT_JUDGE)
    return [
        toolbox.verdict(
            "ec04-the-wait-judge-is-in-tree",
            bool(judge),
        ),
        toolbox.verdict(
            "ec04-both-directions-are-asserted",
            "WAIT_FOR_APPROVAL" in judge
            and "decision.kind.value != ProgramDecisionKind.WAIT.value" in judge,
            "两向：该区分时区分 / 不该改名时逐字保持",
        ),
        toolbox.verdict(
            "ec04-the-verbatim-wait-face-is-pinned",
            "第 1 轮尚未终止（state=RUNNING）⇒ 本轮不推进" in judge,
            "`WAIT` 面必须**逐字**被钉住（否则「保持」只是口头）",
        ),
        toolbox.verdict(
            "ec04-the-approval-ids-are-asserted-in-cited-facts",
            'cited_facts == ("state=WAITING_FOR_APPROVAL", "待审批 id=apr-1")' in judge,
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023/035…043 的教训）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：判词归档形态（两份、非空、CR=0）。**不读内容做断言**（输入即输出）。"""
    verdicts: list[Any] = []
    for label, relative in (("current", ARCHIVE_CURRENT), ("clean", ARCHIVE_CLEAN)):
        path = root / relative
        raw = path.read_bytes() if path.is_file() else b""
        verdicts.append(
            toolbox.verdict(
                f"verdict-archive-{label}",
                bool(raw) and not _has_carriage_return(raw),
                "missing/empty" if not raw else "contains CR",
            )
        )
    return verdicts


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """`IN_SCOPE` 纯收紧：本轮两个新脚本都在必备清单里（**只查在不在**）。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    return [
        toolbox.verdict("scope-declares-this-rounds-scripts", not missing, ",".join(missing)),
        toolbox.verdict(
            "scope-still-pins-the-entry",
            {"tools/two_tree_recheck.py", "tools/closeout_recheck_assertions.py"} <= declared,
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有断言（每条都能被单变量按压判红）。"""
    return [
        *_ec02_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
