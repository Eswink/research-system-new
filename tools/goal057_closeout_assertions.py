#!/usr/bin/env python3
"""GOAL-20261011-057 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…056 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写**：`tools/verify_goal057_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-057 特有的断言**。

三条主轴（逐条对 GOAL-057 的 EC）：

1. **EC-02 端口与静默缺省**：`NudgeSink` / `NullNudgeSink` 在位；载荷**只收摘要**
   （**不**收内容 / 凭据 —— 逐个字段核对）。
2. **EC-03 接线与只读纪律**：超期交付在**调用方那侧**（桥模块）；**只读判定面不得**出现端口调用；
   送失败**点名**（「not delivered」在树）。
3. **EC-04 两向**：判据在树，**四条按压 + 基线门**逐条对得上；归档进树。

**四条纪律**（承 GOAL-027…056 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；
- **判词行不含本树绝对路径**；用 **AST** 读而不是文本巧合；
- **f-string 的 AST 分片**按**子串**核对（承序 22/23）；**`defines`** 收含类方法的版本（承序 23）；
- **抽函数会让「钉调用点写法/落点」的既有判据假红**（承序 24）⇒ 本文件一律**判关系**。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_nudge_exit_on_the_run_path.py", 8),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/application/run_orchestration/test_gate_nudge_on_the_run_path.py",
    "tests/application/run_orchestration/test_program_waiting_on_the_run_path.py",
)

#: EC-02/EC-03 落点。
PORT = "packages/application/ports/nudge_sink.py"
BRIDGE = "packages/application/run_orchestration/program_gate_evaluation.py"
WAITING = "packages/application/run_orchestration/program_waiting.py"

#: EC-02：端口那一族的名字（逐条点名；缺一即判红）。
PORT_NAMES: tuple[str, ...] = ("NudgeNotice", "NudgeSink", "NullNudgeSink")

#: EC-02：载荷字段（**逐条**；「只收摘要」由**没有别的字段**证）。
NOTICE_FIELDS: tuple[str, ...] = (
    "program_id",
    "run_id",
    "index",
    "waited_seconds",
    "declared_bound_seconds",
)

#: EC-02：**刻意不得出现**的内容类字段（隐私 §10）—— 出现任一即判红。
FORBIDDEN_FIELDS: tuple[str, ...] = ("content", "prompt", "token", "credential", "secret")

#: EC-03：交付事实的两句话（f-string ⇒ 子串核对）。
DELIVERED_FRAGMENT = "nudge delivered"
NOT_DELIVERED_FRAGMENT = "nudge not delivered"

#: EC-04 判据 / 归档落点。
NEW_JUDGE = "tests/application/run_orchestration/test_nudge_exit_on_the_run_path.py"
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261011-057-press-two-way.txt"
VERDICT_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261011-057-verdict-current.txt"
VERDICT_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261011-057-verdict-clean.txt"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal057_closeout.py"
ASSERTIONS = "tools/goal057_closeout_assertions.py"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _module_string_literals(source: str) -> set[str]:
    """模块里的**字符串字面量**（AST 读；f-string 会被拆成 `Constant` **分片**）。"""
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
    """某个**片段**是否出现在那些字面量里（**子串**匹配 —— 不是集合成员；承序 22/23）。"""
    return any(fragment in literal for literal in literals)


def _class_annotations(source: str, class_name: str) -> set[str]:
    """类体的**注解名**（AST 读 —— 不 import 那个包；两树入口按**路径**加载 `tools/`）。"""
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


def _defines(source: str, name: str) -> bool:
    """该模块里有**任何**同名函数（**含类方法** —— 缩进不判；承序 23）。"""
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
    """EC-02：端口那一族在位 + 载荷**只收摘要**（**不**含内容类字段）。"""
    port = _text(root, PORT)
    notice_fields = _class_annotations(port, "NudgeNotice")
    missing = [name for name in PORT_NAMES if name not in port]
    absent = [name for name in NOTICE_FIELDS if name not in notice_fields]
    forbidden = [name for name in FORBIDDEN_FIELDS if name in notice_fields]
    return [
        toolbox.verdict(
            "ec02-the-port-family-is-present",
            not missing,
            ",".join(missing),
        ),
        toolbox.verdict(
            "ec02-the-notice-carries-exactly-the-summary-fields",
            not absent and not forbidden,
            "缺:" + ",".join(absent) + " 违禁:" + ",".join(forbidden),
        ),
        toolbox.verdict(
            "ec02-the-null-implementation-is-silent",
            # **判关系**：静默实现存在**且**它的调用日志恒空（静默的可复核证据）。
            "class NullNudgeSink" in port and "return ()" in port,
            "缺省实现必须静默（`calls` 恒空）",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：交付在调用方那侧 + 只读判定面干净 + 送失败点名。"""
    bridge_literals = _module_string_literals(_text(root, BRIDGE))
    waiting = _text(root, WAITING)
    return [
        toolbox.verdict(
            "ec03-the-bridge-delivers-the-notice",
            _defines(_text(root, BRIDGE), "_deliver_nudge"),
            "交付必须在**调用方那侧**（桥模块）—— 判定面不得调端口",
        ),
        toolbox.verdict(
            "ec03-the-delivery-outcome-is-recorded-either-way",
            # **判关系**：成功与失败**各自**留下一条可读事实（不是只报成功）。
            _contains(bridge_literals, DELIVERED_FRAGMENT)
            and _contains(bridge_literals, NOT_DELIVERED_FRAGMENT),
            f"缺 {DELIVERED_FRAGMENT!r} 或 {NOT_DELIVERED_FRAGMENT!r}",
        ),
        toolbox.verdict(
            "ec03-the-read-only-face-stays-clean",
            # **判关系**：只读判定面里**不得**出现端口调用或它的 import。
            ".nudge(" not in waiting and "NudgeSink" not in waiting,
            "只读判定面被塞进写方法（序 12/14 起的既有判据钉住）",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：四条按压各自的受判面逐条点名 + **基线门** + 归档形态。"""
    judge = _text(root, NEW_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    return [
        toolbox.verdict(
            "ec04-the-silent-default-case-is-asserted",
            "test_without_an_injected_sink_the_overdue_wait_is_silently_dropped" in judge,
            "`T-1` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-not-delivered-case-is-asserted",
            "test_a_broken_sink_is_named_not_swallowed" in judge,
            "`T-3` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-delivery-case-is-asserted",
            "test_an_overdue_wait_is_handed_to_the_injected_sink" in judge,
            "`T-2` 的受判面必须在树",
        ),
        toolbox.verdict(
            "ec04-the-read-only-case-is-asserted",
            "test_the_judgment_face_stays_read_only" in judge,
            "`T-4` 的受判面必须在树",
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
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023…056 的教训）。"""
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
