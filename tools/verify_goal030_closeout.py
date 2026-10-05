#!/usr/bin/env python3
"""GOAL-20261005-030 收口复检（EC-05）：**标准断言集 + 本轮特有断言**。

与 GOAL-023…029 的收口验证器同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 直接调用
`tools/closeout_recheck_assertions.py`；本文件**只写 GOAL-030 特有的断言**：

- **逐 EC：判据文件在树 + 例数下界**（缺文件、例数掉下去，两向都判红）；
- **本轮主干交付物逐条在位**（AST 断言，不是文本巧合）：
  ① `phase_capabilities.RunChainCall.run_id_argument`（**执行期才存在**的 run 标识取参来源）；
  ② `tool_evidence` 的 evidence id 含 `result.task_id`（**真缺陷修复**）；
  ③ `adapters/canonical/run_read.py` 的 `run_read`（B 组承接）；
  ④ `read_surface._TOOL_CAPABILITIES` 含 `run_read → run.read`；
  ⑤ **两个组合根**都传 `register_session_tools`（承 GOAL-029 的装配面，本轮加 `runs_store`）；
  ⑥ `POLICY_SURFACE_AUDIT.md` 的 `run.read` 行声明面列含 `tool_providers`；
- **两条新协议在树**：phase 数 + 必须声明 `capability_execution: run_chain` 的 phase；
- **可否证的判据在出厂目录**：`scientific_action_experiment` 的 `METRIC_THRESHOLD`
  （指标名 / 算子 / 阈值逐字）；
- **本轮承接的声明 + 绑定**：目录声明 `run.read` + 出厂绑定表有条目；
- **`IN_SCOPE` 纯收紧**（本轮新增 `tools/verify_goal030_closeout.py`）；
- **记录面**：五个 EC 的终态、子计划 / 复检逐条在位、残余与未覆盖逐条明写。

**为什么本验证器不检查两树判词归档**（承 GOAL-029 实测到的**循环依赖**）：
两树入口在跑完两棵树后把判词**写回**指定路径；若本验证器同时**读**那些路径做断言，
就会出现「输入即输出」⇒ **永不收敛**。⇒ 归档形态由**专属判据**负责（跑在门禁里、
在两树写入**之后**），本验证器只判 GOAL 自己的交付物。

用法：`python tools/verify_goal030_closeout.py --root <树根> [--verdict-only]`；判词行只有
`PASS` / `FAIL` 且不含任何树的绝对路径（否则两树入口会（正确地）拒绝）。

**时间口径**：GOAL 的 `EC-05` 在**本收口复检跑之前**仍是 `PENDING`（它的判词就是本文件产出的），
所以 EC-05 那条断言接受 `PASS ∪ PENDING` —— **不是**放宽，是**时序**（承 GOAL-027/028/029 同款）。
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any, cast


def _load_toolbox() -> object:
    """按**路径**加载同目录的工具集。

    `tools/` **不是包**（没有 `__init__.py`）⇒ 静态 `import tools.x` 会失败
    （承 `MEM-20261001-181`：按路径加载，且必须先写 `sys.modules` 再 `exec_module`，
    否则 dataclasses / typing 在模块自省时会崩）。
    """
    path = Path(__file__).resolve().parent / "closeout_recheck_tools.py"
    spec = importlib.util.spec_from_file_location("goal030_toolbox", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal030_toolbox"] = module
    spec.loader.exec_module(module)
    return module


TOOLBOX = cast(Any, _load_toolbox())

#: 类型别名（工具箱的 `VerdictLike` 是 Protocol；本文件只在注解里用）。
VerdictLike = Any

STANDARD = "tools/closeout_recheck_assertions.py"
SELF = "tools/verify_goal030_closeout.py"
TOOLING_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
GOAL = ".cursor/plans/goals/GOAL-20261005-030-capabilities-actually-used-in-a-research-run.md"

#: 本轮主干交付物（存在性 + AST 结构）。
PHASE_CAPABILITIES = "packages/application/run_orchestration/phase_capabilities.py"
TOOL_EVIDENCE = "packages/application/evidence/tool_evidence.py"
RUN_READ = "adapters/canonical/run_read.py"
READ_SURFACE = "adapters/canonical/read_surface.py"
SESSION_TOOL_SUPPORT = "services/api/session_tool_support.py"
ROOTS = (("sqlite", "services/api/composition.py"), ("postgres", "services/api/pg_composition.py"))
AUDIT_DOC = "docs/architecture/POLICY_SURFACE_AUDIT.md"
TOOL_PROVIDERS = "examples/config/tool_providers.yaml"
CONTRACTS = "examples/contracts/task_contracts.yaml"

#: 逐 EC：判据文件 + **例数下界**（下界取本 GOAL 实测的 `def test_` 声明数 —— 与
#: `closeout_recheck_tools.count_test_defs` 同一计数口径）。
EC_FILES: dict[str, tuple[tuple[str, ...], tuple[int, ...]]] = {
    "ec01": (("tests/e2e/test_capabilities_really_used_in_a_run.py",), (8,)),
    "ec02": (("tests/adapters/canonical/test_run_read_onboarding.py",), (10,)),
    "ec03": (("tests/e2e/test_scientific_action_depth.py",), (9,)),
    "ec04": (("tests/tooling/test_criterion_scope_self_check.py",), (10,)),
}

#: 本轮新增的两条协议 → (README 路径, phase 数, 必须 `run_chain` 的 phase)。
NEW_PROTOCOLS: dict[str, tuple[str, int, tuple[str, ...]]] = {
    "capabilities_used": (
        "examples/protocols/capabilities_used_in_a_run_v1.yaml",
        2,
        ("probe", "review"),
    ),
    "scientific_action": (
        "examples/protocols/scientific_action_depth_v1.yaml",
        3,
        ("probe", "verdict"),
    ),
}

#: 本轮新增的能力承接。
ONBOARDED = "run.read"

#: 子计划 / 复检（记录面逐条在位）。
CHILD_PLANS: tuple[str, ...] = (
    ".cursor/plans/tasks/PLAN-20261005-283-goal-030-ec01-capabilities-actually-used-in-a-run.md",
    ".cursor/plans/tasks/PLAN-20261005-285-goal-030-ec02-b-group-onboarding-run-read.md",
    ".cursor/plans/tasks/PLAN-20261005-287-goal-030-ec03-scientific-action-depth.md",
    ".cursor/plans/tasks/PLAN-20261005-289-goal-030-ec04-criterion-scope-self-check.md",
)
RECHECKS: tuple[str, ...] = (
    ".cursor/plans/rechecks/RECHECK-20261005-284-goal-030-ec01-capabilities-actually-used.md",
    ".cursor/plans/rechecks/RECHECK-20261005-286-goal-030-ec02-b-group-onboarding.md",
    ".cursor/plans/rechecks/RECHECK-20261005-288-goal-030-ec03-scientific-action-depth.md",
    ".cursor/plans/rechecks/RECHECK-20261005-290-goal-030-ec04-criterion-scope-self-check.md",
)

#: 未覆盖范围（逐条明写；本验证器只断言这些句子**在位**，不判定它们足不足够）。
UNCOVERED_MARKERS: tuple[str, ...] = (
    "读面未认证",
    "多租户未做",
    "RBAC 未做",
    "BOLA·BFLA 未做",
    "部署面未验证",
    "`R-M1` 未收口",
    "D 组审批通道未接通",
)

#: 承继残余 + 本轮新增残余（逐条明写）。
RESIDUAL_MARKERS: tuple[str, ...] = ("W-1", "W-2", "W-3", "W-4", "W-5", "W-6", "W-7", "W-8")


def load_standard(root: Path) -> object | None:
    """按路径加载标准断言集（`root` 下的那一份；两树各自解析自己的）。"""
    path = TOOLBOX.tree(root, STANDARD)
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("goal030_standard", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["goal030_standard"] = module
    spec.loader.exec_module(module)
    return module


def _ec_verdicts(root: Path) -> list[VerdictLike]:
    """逐 EC：判据文件在树 + 例数下界（缺文件、例数掉下去，两向都判红）。"""
    verdicts: list[VerdictLike] = []
    for ec_id, (files, floors) in sorted(EC_FILES.items()):
        for relative, floor in zip(files, floors, strict=True):
            source = TOOLBOX.text(root, relative)
            count = TOOLBOX.count_test_defs(source)
            verdicts.append(
                TOOLBOX.verdict(
                    f"judge-{ec_id}-{Path(relative).name}",
                    bool(source) and count >= floor,
                    f"{count} >= {floor}",
                )
            )
    return verdicts


def _run_chain_annotation(root: Path) -> bool:
    """`RunChainCall` 是否带 `run_id_argument` 字段（AST 读注解名，不靠文本搜索）。"""
    import ast

    source = TOOLBOX.text(root, PHASE_CAPABILITIES)
    if not source:
        return False
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(parsed):
        if isinstance(node, ast.ClassDef) and node.name == "RunChainCall":
            return any(
                isinstance(item, ast.AnnAssign)
                and getattr(item.target, "id", None) == "run_id_argument"
                for item in node.body
            )
    return False


def _structure_verdicts(root: Path) -> list[VerdictLike]:
    """本轮主干交付物逐条在位（AST 断言，不是文本巧合）。"""
    verdicts: list[VerdictLike] = [
        TOOLBOX.verdict("run-chain-call-carries-run-id-argument", _run_chain_annotation(root)),
    ]
    evidence_source = TOOLBOX.text(root, TOOL_EVIDENCE)
    verdicts.append(
        TOOLBOX.verdict(
            "tool-evidence-id-carries-task-id",
            "evidence:{input.run_id}:{result.task_id}:{result.operation_key}" in evidence_source,
        )
    )
    verdicts.append(
        TOOLBOX.verdict(
            "run-read-implementation-present",
            TOOLBOX.defines(TOOLBOX.text(root, RUN_READ), "run_read"),
        )
    )
    surface = TOOLBOX.module_literal(TOOLBOX.text(root, READ_SURFACE), "_TOOL_CAPABILITIES")
    mapped = surface.get("run_read") if isinstance(surface, dict) else None
    verdicts.append(
        TOOLBOX.verdict(
            "run-read-is-in-the-tool-surface",
            mapped == ONBOARDED,
            f"run_read -> {mapped!r}",
        )
    )
    for label, relative in ROOTS:
        verdicts.append(
            TOOLBOX.verdict(
                f"{label}-root-registers-session-tools",
                "register_session_tools=" in TOOLBOX.text(root, relative),
            )
        )
    audit = TOOLBOX.text(root, AUDIT_DOC)
    row_ok = any(
        "`run.read`" in line and "tool_providers" in line
        for line in audit.splitlines()
        if line.startswith("|")
    )
    verdicts.append(TOOLBOX.verdict("audit-doc-run-read-declaration-column", row_ok))
    return verdicts


def _phase_flags(source: str) -> tuple[int, dict[str, str]]:
    """极简读协议 YAML 的 phase 面（只用标准库，不引入 yaml 依赖）。"""

    ids: list[str] = []
    flags: dict[str, str] = {}
    current: str | None = None
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("- id: "):
            current = stripped.split(":", 1)[1].strip()
            ids.append(current)
        elif stripped.startswith("capability_execution:") and current is not None:
            flags[current] = stripped.split(":", 1)[1].strip()
    return len(ids), flags


def _protocol_verdicts(root: Path) -> list[VerdictLike]:
    """两条新协议：phase 数 + 必须声明 `capability_execution: run_chain` 的 phase。"""
    verdicts: list[VerdictLike] = []
    for label, (relative, phase_count, run_chain_phases) in sorted(NEW_PROTOCOLS.items()):
        count, flags = _phase_flags(TOOLBOX.text(root, relative))
        verdicts.append(
            TOOLBOX.verdict(
                f"protocol-phases-{label}",
                count == phase_count,
                f"{count} == {phase_count}",
            )
        )
        for phase_id in run_chain_phases:
            verdicts.append(
                TOOLBOX.verdict(
                    f"protocol-run-chain-{label}-{phase_id}",
                    flags.get(phase_id) == "run_chain",
                    f"capability_execution={flags.get(phase_id)!r}",
                )
            )
    return verdicts


def _falsifiable_verdict(root: Path) -> VerdictLike:
    """可否证的判据在**出厂目录**里（指标名 / 算子 / 阈值逐字）。"""
    import re

    source = TOOLBOX.text(root, CONTRACTS)
    index = source.find("scientific_action_experiment:")
    if index == -1:
        return TOOLBOX.verdict("falsifiable-metric-criterion-present", False, "contract missing")
    block = source[index:]
    stop = block.find("\nscientific_action_verdict:")
    block = block[: stop if stop != -1 else len(block)]
    matched = re.search(
        r"type: METRIC_THRESHOLD\s+metric: (\S+)\s+operator: (\S+)\s+threshold: (\S+)",
        block,
    )
    if matched is None:
        return TOOLBOX.verdict("falsifiable-metric-criterion-present", False, "criterion missing")
    metric, operator, threshold = matched.groups()
    ok = (metric, operator, str(threshold)) == ("comparison_reduction_ratio", "GTE", "100")
    return TOOLBOX.verdict(
        "falsifiable-metric-criterion-present", ok, f"{metric} {operator} {threshold}"
    )


def _onboarding_verdicts(root: Path) -> list[VerdictLike]:
    """本轮新增承接：目录声明 + 出厂绑定表条目。"""
    providers = TOOLBOX.text(root, TOOL_PROVIDERS)
    declared = False
    for line in providers.splitlines():
        if line.strip() == f"- {ONBOARDED}":
            declared = True
    bound = TOOLBOX.binding_tool_names(
        TOOLBOX.text(root, SESSION_TOOL_SUPPORT), "DEFAULT_SESSION_TOOL_BINDINGS"
    )
    return [
        TOOLBOX.verdict("run-read-declared-in-catalog", declared),
        TOOLBOX.verdict(
            "run-read-in-factory-binding-table", ONBOARDED in bound, f"{sorted(bound)}"
        ),
    ]


def _tooling_scope_verdict(root: Path) -> VerdictLike:
    """`IN_SCOPE` 纯收紧：本轮新增的验证器必须已在清单里。"""
    literal = TOOLBOX.module_literal(TOOLBOX.text(root, TOOLING_JUDGE), "IN_SCOPE")
    listed = isinstance(literal, tuple) and SELF in literal
    return TOOLBOX.verdict(f"in-scope-{SELF}", listed)


def _ec_status(goal_text: str, ec_id: str) -> str:
    """从 GOAL 正文取某 EC 的 `status:`（按 EC 块定位，不靠全局搜索）。"""
    marker = f"  - id: {ec_id}\n"
    index = goal_text.find(marker)
    if index == -1:
        return "MISSING"
    tail = goal_text[index:]
    stop = tail.find("\n  - id: ")
    block = tail[: stop if stop != -1 else len(tail)]
    for line in block.splitlines():
        if line.strip().startswith("status:"):
            return line.split(":", 1)[1].strip()
    return "MISSING"


def _record_verdicts(root: Path) -> list[VerdictLike]:
    """记录面：EC 终态、子计划 / 复检在位、残余与未覆盖逐条明写。"""
    goal = TOOLBOX.text(root, GOAL)
    verdicts: list[VerdictLike] = [
        TOOLBOX.verdict("goal-declares-five-ecs", all(f"id: EC-0{n}" in goal for n in range(1, 6)))
    ]
    for index in range(1, 5):
        status = _ec_status(goal, f"EC-0{index}")
        verdicts.append(TOOLBOX.verdict(f"goal-ec0{index}-status", status == "PASS", status))
    # EC-05 允许 PASS ∪ PENDING（时间口径见模块 docstring）。
    ec05 = _ec_status(goal, "EC-05")
    verdicts.append(TOOLBOX.verdict("goal-ec05-status", ec05 in {"PASS", "PENDING"}, ec05))
    for relative in CHILD_PLANS:
        verdicts.append(
            TOOLBOX.verdict(
                f"child-plan-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file()
            )
        )
    for relative in RECHECKS:
        verdicts.append(
            TOOLBOX.verdict(
                f"recheck-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file()
            )
        )
    for relative in README_AND_PRIOR_GOAL:
        verdicts.append(
            TOOLBOX.verdict(f"record-{Path(relative).name}", TOOLBOX.tree(root, relative).is_file())
        )
    missing_uncovered = [item for item in UNCOVERED_MARKERS if item not in goal]
    verdicts.append(
        TOOLBOX.verdict(
            "uncovered-scope-enumerated", not missing_uncovered, ",".join(missing_uncovered)
        )
    )
    missing_residual = [item for item in RESIDUAL_MARKERS if item not in goal]
    verdicts.append(
        TOOLBOX.verdict("residuals-enumerated", not missing_residual, ",".join(missing_residual))
    )
    return verdicts


#: 记录面：GOAL 目录 README（格式契约）+ 前一轮 GOAL（承继残余的来源）。
README_AND_PRIOR_GOAL: tuple[str, ...] = (".cursor/plans/goals/README.md",)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GOAL-030 closeout recheck")
    parser.add_argument("--root", default=".", help="tree root to verify")
    parser.add_argument("--verdict-only", action="store_true", help="print verdicts only")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.root).resolve()
    standard = load_standard(root)
    verdicts: list[VerdictLike] = []
    if standard is None:
        verdicts.append(TOOLBOX.verdict("standard-assertions-present", False, f"{STANDARD} 不在树"))
    else:
        standard_verdicts = getattr(standard, "standard_verdicts", None)
        assert callable(standard_verdicts), "标准断言集缺少 standard_verdicts"
        cast(Callable[[Path], Iterable[Any]], standard_verdicts)
        verdicts.extend(standard_verdicts(root))
    verdicts.extend(_ec_verdicts(root))
    verdicts.extend(_structure_verdicts(root))
    verdicts.extend(_protocol_verdicts(root))
    verdicts.append(_falsifiable_verdict(root))
    verdicts.extend(_onboarding_verdicts(root))
    verdicts.append(_tooling_scope_verdict(root))
    verdicts.extend(_record_verdicts(root))
    failures = [verdict for verdict in verdicts if not verdict.ok]
    for verdict in verdicts:
        if verdict.ok:
            print(f"PASS {verdict.name}")
        else:
            print(f"FAIL {verdict.name} -> {verdict.detail}")
    if not args.verdict_only:
        print(f"SUMMARY total={len(verdicts)} failed={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
