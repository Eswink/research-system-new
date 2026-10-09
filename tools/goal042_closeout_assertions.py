#!/usr/bin/env python3
"""GOAL-20261009-042 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…041 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— `tools/verify_goal042_closeout.py` 直接调用
`tools/closeout_recheck_assertions.standard_verdicts`；本文件**只写 GOAL-042 特有的断言**。

三条主轴（逐条对 GOAL-042 的 EC）：

1. **EC-01/EC-02 承接与判定**：`memory.read` 五件套齐（目录声明 / 实现模块 /
   描述子与映射 / 双组合根绑定 / 一条只读 allow）；读面按**调用方给的时点**给三态与处置。
2. **EC-03/EC-04 消费**：`memory_validity_gate` 声明在场且**缺省 False**；
   `memory_gate_verdict` 的三态分派在树（`SKIP` / `ANNOTATE` / `USE` **互不混用**）；
   判定序列「用尽/去重」类排序不适用本 GOAL，但**门的 skip 与 notes 分列**要钉住；
   载荷**唯一构造点**（消除两处手写字段清单）。
3. **记录面**：判词归档在树（两份、非空、`CR=0`）；`IN_SCOPE` 纯收紧。

**两条纪律**（承 GOAL-027…041 的实测教训）：

- **不读两树写出的判词做断言**（输入即输出 ⇒ 永不收敛）；归档的**形态**由专属判据负责，
  本文件只判**存在性**与非空、`CR=0`；
- **判词行不含本树绝对路径**（两树入口会拒绝），且需要时用 AST 读而不是文本巧合。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮新增 / 相关的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/adapters/canonical/test_memory_read_dispositions.py", 15),
    ("tests/application/run_orchestration/test_memory_validity_gate.py", 12),
    ("tests/application/run_orchestration/test_memory_gate_on_the_run_chain.py", 6),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/application/run_orchestration/test_run_chain_capabilities.py",
    "tests/architecture/python/test_capability_coverage_is_implemented.py",
    "tests/application/preflight/test_release_expansion_is_read_only.py",
    "tests/adapters/sqlite/test_memory_scope_and_validity.py",
    "tests/tooling/test_python_source_limits.py",
    "tests/architecture/python/test_delivery_semantics_wording.py",
)

#: EC-01/EC-02 落点（承接五件套）。
MEMORY_READ = "adapters/canonical/memory_read.py"
READ_PROVIDER = "adapters/canonical/read_provider.py"
READ_SURFACE = "adapters/canonical/read_surface.py"
CAPABILITIES = "examples/config/capabilities.yaml"
PROVIDERS = "examples/config/tool_providers.yaml"
POLICY = "examples/config/policy.yaml"
BINDINGS = "services/api/session_tool_support.py"
SQLITE_ROOT = "services/api/composition.py"
PG_ROOT = "services/api/pg_composition.py"

#: EC-03/EC-04 落点（消费面）。
RUNNER = "packages/application/run_orchestration/phase_capabilities.py"
TRIGGERS = "packages/application/run_orchestration/phase_capability_triggers.py"
PAYLOAD = "packages/application/run_orchestration/run_completion_payload.py"
PHASE_RUNNER = "packages/application/run_orchestration/phase_runner.py"
ROUND_LOOP = "packages/application/run_orchestration/round_loop_runner.py"
DRIVER_JUDGE = "tests/application/run_orchestration/test_memory_validity_gate.py"
CHAIN_JUDGE = "tests/application/run_orchestration/test_memory_gate_on_the_run_chain.py"
READ_JUDGE = "tests/adapters/canonical/test_memory_read_dispositions.py"

#: EC-05 记录面（本轮的脚本与判据）。
SELF = "tools/verify_goal042_closeout.py"
ASSERTIONS = "tools/goal042_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"

#: 归档（收口 cycle 由两树入口写入）。
ARCHIVE_CURRENT = ".cursor/plans/goals/evidence/GOAL-20261009-042-verdict-current.txt"
ARCHIVE_CLEAN = ".cursor/plans/goals/evidence/GOAL-20261009-042-verdict-clean.txt"


def _text(root: Path, relative: str) -> str:
    path = root.joinpath(*relative.split("/"))
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def _calls_wall_clock(source: str) -> bool:
    """模块代码里是否**调用**了 `Timestamp.now()`（AST 判，不判 docstring 里的说明文字）。"""
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return True
    for node in ast.walk(parsed):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "now":
            owner = func.value
            if isinstance(owner, ast.Name) and owner.id == "Timestamp":
                return True
    return False


def _ec01_02_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01/EC-02：五件套齐 + 三态与处置在场 + 不读挂钟。"""
    return [
        toolbox.verdict(
            "ec02-five-piece-set-is-wide",
            all(
                marker in _text(root, relative)
                for relative, marker in (
                    (MEMORY_READ, "def memory_read("),
                    (READ_PROVIDER, "memory_read"),
                    (READ_SURFACE, "memory_read"),
                    (CAPABILITIES, "memory.read"),
                    (PROVIDERS, "memory.read"),
                    (POLICY, "memory.read"),
                    (BINDINGS, "memory.read"),
                    (SQLITE_ROOT, "memory_store"),
                    (PG_ROOT, "memory.read"),
                )
            ),
        ),
        toolbox.verdict(
            "ec02-three-dispositions-are-explicit",
            all(
                marker in _text(root, MEMORY_READ)
                for marker in ("DISPOSITION_USE", "DISPOSITION_ANNOTATE", "DISPOSITION_SKIP")
            ),
        ),
        toolbox.verdict(
            "ec02-the-moment-is-required-so-the-decision-is-reproducible",
            "requires an explicit 'now'" in _text(root, MEMORY_READ)
            # **代码**里不得读挂钟（docstring 提到它是说明，不是调用 ⇒ 用 AST 判，不判散文）。
            and not _calls_wall_clock(_text(root, MEMORY_READ)),
        ),
        toolbox.verdict(
            "ec02-undeclared-validity-is-not-guessed",
            "未声明" in _text(root, MEMORY_READ) and "不得被当成已到期" in _text(root, MEMORY_READ),
        ),
    ]


def _ec03_04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03/EC-04：门的声明 + 三态分派 + 两条通道分列 + 载荷唯一构造点。"""
    runner = _text(root, RUNNER)
    triggers = _text(root, TRIGGERS)
    return [
        toolbox.verdict(
            "ec03-the-gate-is-declared-and-defaults-to-off",
            "memory_validity_gate: bool = False" in runner,
        ),
        toolbox.verdict(
            "ec03-the-gate-runs-inside-the-chain-loop",
            "memory_step_gate(call, previous)" in runner,
        ),
        toolbox.verdict(
            "ec03-three-dispositions-are-dispatched-separately",
            "MEMORY_SKIP" in triggers
            and "MEMORY_ANNOTATE" in triggers
            and "MEMORY_USE" in triggers
            and "def memory_gate_verdict(" in triggers,
        ),
        toolbox.verdict(
            "ec03-skip-and-annotations-are-two-channels",
            "skip=verdict == MEMORY_SKIP" in triggers
            and "def memory_step_gate(" in triggers
            and "annotations" in runner,
        ),
        toolbox.verdict(
            "ec03-the-payload-has-one-construction-point",
            "def run_completion_payload(" in _text(root, PAYLOAD)
            and "run_completion_payload(" in _text(root, PHASE_RUNNER)
            and "run_completion_payload(" in _text(root, ROUND_LOOP),
        ),
        toolbox.verdict(
            "ec04-the-two-moment-case-is-asserted",
            "before_the_declared_boundary" in _text(root, CHAIN_JUDGE)
            and "after_the_declared_boundary" in _text(root, CHAIN_JUDGE),
        ),
        toolbox.verdict(
            "ec04-the-tool-call-count-is-asserted",
            'provider.calls == ["memory_read"]' in _text(root, CHAIN_JUDGE),
        ),
        toolbox.verdict(
            "ec04-fail-closed-is-asserted",
            "unknown disposition" in _text(root, DRIVER_JUDGE)
            and "is not an object" in _text(root, DRIVER_JUDGE),
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
    verdicts.append(toolbox.verdict("read-face-judge-present", (root / READ_JUDGE).is_file()))
    return verdicts


def _has_carriage_return(raw: bytes) -> bool:
    """逐字节判 CR（**不**经过文本模式 —— 那正是要防的形态；承 GOAL-023/035…041 的教训）。"""
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
        *_ec01_02_verdicts(root, toolbox),
        *_ec03_04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]
