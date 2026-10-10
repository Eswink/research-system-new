#!/usr/bin/env python3
"""GOAL-20261010-047 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…046 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal047_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-047 特有的断言**。

三条主轴（逐条对 GOAL-047 的 EC）：

1. **EC-02 注册面**：程序面**经既有 Port** 注册待决（`ApprovalStore.register`）+ `action`
   用**本 GOAL 自己的前缀**（与 phase 面的 `human-gate:` 区分）+ **幂等**（同 action 在场不重注册）
   + 只读面 / 注册失败 / 查询失败**三种形态各自点名**。
2. **EC-03 接回面**：`decide` 的准入**按前缀两分支**（新前缀 ⇒ run 终态；其余**逐字保持**），
   且**窄**（同 run 上前缀决定 200 / 409）；程序闸门**不**走状态机、**不**续跑。
3. **EC-04 两向**：判据在树，且**五条**按压（拦住 / 已裁决仍停 / 只读面冒充 / 幂等失效 /
   准入放宽）**逐条对得上用例**；归档进树。

**两条纪律**（承 GOAL-027…046 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
  **本文件自身也遵守「判关系不判位置」**（承 `MEM-20261010-215`）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_program_waiting_on_the_run_path.py", 20),
    ("tests/e2e/test_program_advance_on_the_run_path.py", 11),
    ("tests/api/test_approvals_api.py", 12),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树（既有规则一字未松的回归网）。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
    "tests/contracts/test_openapi_snapshot.py",
)

#: EC-02 落点（**注册面**：有副作用的半件事单列成模块；**可能落点清单** 承 MEM-20261010-215）。
#: **为什么不在 `program_waiting.py`**：那一份是**只读判定面**，被序 12/14 的既有判据钉住
#: （「不得出现写方法」）—— 注册落进去会当场撞红它们（实测：`goal044` / `goal046` 各一条）。
#: 分列与 `phase_pause.py` 之于 `phase_runner.py` 同一手法。
REGISTRATION_SOURCES: tuple[str, ...] = (
    "packages/application/run_orchestration/program_gate_registration.py",
)
WAITING_SOURCES: tuple[str, ...] = ("packages/application/run_orchestration/program_waiting.py",)
RUNNER = "packages/application/run_orchestration/program_runner.py"

#: EC-03 落点（裁决面）。
DECIDE_MODULE = "services/api/approvals.py"
DECIDE_ROUTER = "services/api/routers/approvals.py"

#: EC-02 必须点名的形态（逐条；缺一即判红）。
NAMED_FORMS: tuple[str, ...] = ("只读", "注册失败", "注册前查询失败")

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal047_closeout.py"
ASSERTIONS = "tools/goal047_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"

#: EC-04 判据文件（逐条点名）。
WAITING_JUDGE = "tests/application/run_orchestration/test_program_waiting_on_the_run_path.py"
E2E_JUDGE = "tests/e2e/test_program_advance_on_the_run_path.py"
API_JUDGE = "tests/api/test_approvals_api.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261010-047-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261010-047-verdict-clean.txt"

#: 本轮的两向反证归档（按压读数）。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261010-047-press-two-way.txt"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _joined(root: Path, relatives: tuple[str, ...]) -> str:
    """多落点的合并文本（判关系不判位置）。"""
    return "\n".join(_text(root, relative) for relative in relatives)


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


def _first_call_line(source: str, function_name: str) -> int | None:
    """源码里**首次调用**该函数名的行号（AST；看被调名，不看实参）。"""
    if not source:
        return None
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return None
    lines = [
        node.lineno
        for node in ast.walk(parsed)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == function_name
    ]
    return min(lines) if lines else None


def _ec02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：注册面（既有 Port + 自有前缀 + 幂等 + 三种点名形态）。"""
    waiting = _joined(root, REGISTRATION_SOURCES)
    reader = _joined(root, WAITING_SOURCES)
    names = _function_names(waiting)
    return [
        toolbox.verdict(
            "ec02-the-register-helper-exists",
            "register_declared_gate" in names,
            ",".join(sorted(names & {"register_declared_gate"})),
        ),
        toolbox.verdict(
            "ec02-the-registration-uses-the-existing-port",
            "ApprovalSpec" in waiting and "register(" in waiting,
            "必须复用既有 ApprovalStore.register（不新建第二套存储）",
        ),
        toolbox.verdict(
            "ec02-the-action-prefix-is-its-own",
            'PROGRAM_GATE_ACTION = "program-gate:"' in waiting,
            "程序闸门必须有自己的 action 前缀（与 phase 面的 human-gate: 区分）",
        ),
        toolbox.verdict(
            "ec02-the-metadata-mirrors-the-phase-face",
            'risk="HUMAN_GATE"' in waiting and "policy_source=" in waiting,
            "risk / policy_source 必须与 phase 面同源可对照",
        ),
        toolbox.verdict(
            "ec02-every-missing-form-is-named",
            all(marker in waiting for marker in NAMED_FORMS),
            ",".join(item for item in NAMED_FORMS if item not in waiting),
        ),
        toolbox.verdict(
            "ec02-the-registration-is-idempotent",
            'getattr(row, "action"' in waiting,
            "同 action 的记录在场 ⇒ 不重复注册（幂等）",
        ),
        toolbox.verdict(
            "ec02-the-driver-registers-before-judging",
            _register_precedes_judging(_text(root, RUNNER)),
            "驱动必须先**注册**（有副作用）再**判定**（只读）",
        ),
        toolbox.verdict(
            "ec02-the-judgment-face-stays-read-only",
            "register(" not in reader and "replace(" not in reader,
            "只读判定面不得出现写方法（序 12/14 的既有判据钉住这件事）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：准入两分支（新前缀 ⇒ run 终态；其余逐字保持）+ 不迁移、不续跑。"""
    decide = _text(root, DECIDE_MODULE)
    router = _text(root, DECIDE_ROUTER)
    names = _function_names(decide)
    return [
        toolbox.verdict(
            "ec03-the-admissibility-helper-exists",
            "_require_admissible" in names,
            ",".join(sorted(names & {"_require_admissible"})),
        ),
        toolbox.verdict(
            "ec03-the-new-branch-keys-on-the-prefix",
            "PROGRAM_GATE_ACTION_PREFIX" in decide
            and "startswith(PROGRAM_GATE_ACTION_PREFIX)" in decide,
            "新分支必须由前缀（而不是别的条件）分派",
        ),
        toolbox.verdict(
            "ec03-the-new-branch-requires-a-terminal-run",
            "is_terminal" in decide and "program-gate approval expects a terminal run" in decide,
            "新分支的准入 = run 终态（闸门是跑完之后才拦的）",
        ),
        toolbox.verdict(
            "ec03-the-existing-rule-is-preserved-verbatim",
            "cannot decide approval in run state" in decide
            and "run.state != ResearchRunState.State.WAITING_FOR_APPROVAL" in decide,
            "既有准入规则必须逐字保留（它是受判面）",
        ),
        toolbox.verdict(
            "ec03-the-router-skips-the-state-machine-for-the-new-prefix",
            "PROGRAM_GATE_ACTION_PREFIX" in router and _router_returns_before_transition(router),
            "程序闸门**不**走 run 状态机（接回是程序面的推进决定）",
        ),
    ]


def _router_returns_before_transition(router: str) -> bool:
    """`program-gate:` 的提前返回必须在 `run.transition(...)` **之前**（AST 行号）。

    **按被调名取行号**，且两种调用形态都认：`startswith(...)` 是**属性调用**
    （`node.func` 是 `Attribute`），`transition(...)` 是**名字调用** —— 只认名字形态
    会让本判据恒假（实测：初版 `_first_call_line` 只匹配 `ast.Name` ⇒ 这条判负）。
    """
    prefix_line = _first_call_line_any(router, {"startswith", "PROGRAM_GATE_ACTION_PREFIX"})
    transition = _first_call_line_any(router, {"transition"})
    if prefix_line is None or transition is None:
        return False
    return prefix_line < transition


def _first_call_line_any(source: str, names: set[str]) -> int | None:
    """源码里**首次调用**这些名字之一的行号（AST；`Name` 与 `Attribute` 两种形态都认）。"""
    if not source:
        return None
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return None
    lines: list[int] = []
    for node in ast.walk(parsed):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        called = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if called in names:
            lines.append(node.lineno)
    return min(lines) if lines else None


def _register_precedes_judging(runner: str) -> bool:
    """注册的**调用行**必须早于判定的**调用行**（AST 取行号，两种调用形态都认）。"""
    register_line = _first_call_line_any(runner, {"register_declared_gate"})
    judge_line = _first_call_line_any(runner, {"declared_gate_verdict"})
    if register_line is None or judge_line is None:
        return False
    return register_line < judge_line


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：判据在树 + 五条按压各自的用例逐条点名 + 归档形态。"""
    waiting = _text(root, WAITING_JUDGE)
    e2e = _text(root, E2E_JUDGE)
    api = _text(root, API_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    raw = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-registration-case-is-asserted",
            "test_a_declared_gate_registers_a_decidable_approval" in waiting,
        ),
        toolbox.verdict(
            "ec04-the-idempotence-case-is-asserted",
            "test_a_repeated_advance_does_not_register_a_second_pending" in waiting
            and "test_a_decided_gate_is_not_re_registered" in waiting,
        ),
        toolbox.verdict(
            "ec04-the-read-only-case-is-asserted",
            "test_a_read_only_face_is_named_not_silently_treated_as_registered" in waiting,
        ),
        toolbox.verdict(
            "ec04-the-undeclared-case-is-asserted",
            "test_an_undeclared_gate_registers_nothing" in waiting
            and "test_the_gate_does_not_register_before_its_round" in waiting,
        ),
        toolbox.verdict(
            "ec04-the-full-resume-loop-is-asserted",
            "test_a_declared_gate_can_be_decided_and_the_program_resumes" in e2e
            and "test_an_undecided_gate_still_stops_the_program" in e2e,
            "实跑回路（拦住 → 裁决 → 续跑）必须在 e2e 上成环",
        ),
        toolbox.verdict(
            "ec04-the-narrow-branch-case-is-asserted",
            "test_program_gate_approval_is_accepted_only_on_a_terminal_run" in api
            and "test_a_non_program_gate_approval_on_a_terminal_run_is_still_refused" in api,
            "准入分支的**窄性**必须成对断言（同 run 上前缀决定 200/409）",
        ),
        toolbox.verdict(
            "ec04-every-press-is-red-in-the-archive",
            press.count("按压 RED") >= 5 and "all_red_and_restored=True" in raw,
            "五条按压的读数必须全红且复原一致",
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023/035…046 的教训）。"""
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
    verifier_text = _text(root, VERIFIER_JUDGE)
    return [
        toolbox.verdict("scope-declares-this-rounds-scripts", not missing, ",".join(missing)),
        toolbox.verdict(
            "scope-still-pins-the-entry",
            {"tools/two_tree_recheck.py", "tools/closeout_recheck_assertions.py"} <= declared,
        ),
        toolbox.verdict(
            "verifier-scope-declares-this-rounds-scripts",
            SELF in verifier_text,
            "GOAL-043 立的射程分区清单也必须登记本轮验证器",
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
