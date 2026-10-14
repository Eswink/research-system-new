#!/usr/bin/env python3
"""GOAL-20261014-077 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…075 的断言集同形：公共面**一行都不重写**（`standard_verdicts`）；
本文件**只写 GOAL-077 特有的断言**。

三条主轴（逐条对 GOAL-077 的 EC）：

1. **EC-01 汇编器在树且判据成对**：`build_research_report` + 四条节标题 +
   制品名/MIME 常量在位；汇编器判据 ≥ 7 例。
2. **EC-02 报告经**产品路径**产出**：`TaskContract.report` 声明 + 派发点按声明分流 +
   报告汇编器缝 + `report_facts` 的四条读法（指标与 HTTP 读面**同一份字节**）+
   e2e 判据在树且覆盖「四节 / 逐字溯源 / 内容寻址 / 两条反证」。
3. **EC-03 立题由检索派生**：新协议在树（4 phase、立题格声明 `run_chain`）+
   两个新合约在树（`research_report_plan` 带**性质维**）+ 判据面覆盖覆盖两维。

**五条纪律**（承 GOAL-027…075）：不读两树判词做一致性断言（那是输入即输出）；
判词行不含绝对路径；f-string 分片按**子串**；`defines` 收**含类方法**的版本；
**一律判关系**（抽函数会让钉调用点的判据假红）。
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

#: 本轮**新增 / 修改**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/test_research_report_assembler.py", 7),
    ("tests/e2e/test_research_report_arc_offline.py", 7),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal075_closeout.py",
    "tests/architecture/python/test_run_chain_capability_exposure.py",
    "tests/architecture/python/test_session_tool_bindings_exposure.py",
    "tests/architecture/python/test_declared_input_sources.py",
)

#: EC-01 / EC-02 / EC-03 的落点。
ASSEMBLER = "packages/application/deliverable/research_report.py"
REPORT_TASK = "packages/application/run_orchestration/report_task.py"
REPORT_FACTS = "packages/application/run_orchestration/report_facts.py"
TASK_DISPATCH = "packages/application/run_orchestration/task_dispatch.py"
RUNNER_WIRING = "packages/application/run_orchestration/runner_wiring.py"
REPORT_SUPPORT = "services/api/report_support.py"
DOMAIN_TASKS = "packages/domain/tasks.py"
CONTRACTS = "examples/contracts/task_contracts.yaml"
PROTOCOL = "examples/protocols/research_report_chain_v1.yaml"
NEW_JUDGE = "tests/e2e/test_research_report_arc_offline.py"

#: 本轮引入的形态（**逐条点名**；缺一即判红）。
DISPATCH_BY_DECLARATION = "if tctx.contract.report is not None:"
MUTUAL_EXCLUSION = "must not declare both an experiment and a report assembly"
FAIL_CLOSED = "no report assembler is wired into this assembly"
SAME_BYTES_METRICS = "RESULT_FILE"
RUN_LEVEL_ARTIFACT = "def report_artifact_id("
RUN_IN_SPEC = "run: ResearchRun | None = None"

#: EC-04 的 live 判据与它的交付面。
LIVE_JUDGE = "tests/e2e/test_research_report_chain_live.py"
LIVE_REPORT_PREFIX = "goal077-ec04-"

#: 两处射程判据（本 GOAL 的收口面必须已登记）。
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
SELF = "tools/verify_goal077_closeout.py"
ASSERTIONS = "tools/goal077_closeout_assertions.py"

#: 本轮按压（**逐条**）：受判面必须在判据面，读数由归档承担。
_PRESS_JUDGES: tuple[tuple[str, str], ...] = (
    ("V7-1", "test_removing_the_retrieval_wiring_rejects_the_plan_phase"),
    ("V7-2", "test_removing_the_report_seam_stops_the_run_and_leaves_no_report"),
    ("V7-3", "test_every_number_in_the_report_traces_back_to_persisted_facts"),
    ("V7-4", "test_the_declared_report_contract_is_the_one_that_declares_the_assembler"),
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
    """EC-01：汇编器 + 四条节标题 + 制品名 / MIME 常量。"""
    assembler = _text(root, ASSEMBLER)
    return [
        toolbox.verdict(
            "ec01-the-assembler-is-in-tree",
            toolbox.defines(assembler, "build_research_report")
            and toolbox.defines(assembler, "ReportInputs"),
            "`build_research_report` 与它的输入参数对象都必须在树",
        ),
        toolbox.verdict(
            "ec01-the-four-sections-are-declared",
            "SECTION_HEADINGS" in assembler and assembler.count('"## ') >= 4,
            "四条二级标题必须逐条声明（节的**存在**是合约）",
        ),
        toolbox.verdict(
            "ec01-the-artifact-name-and-mime-are-constants",
            'REPORT_ARTIFACT_NAME = "research_report.md"' in assembler
            and 'REPORT_MIME = "text/markdown"' in assembler,
            "制品名与 MIME 是合约的一部分（改即改契约）",
        ),
        toolbox.verdict(
            "ec01-the-reflection-is-honest-about-time",
            "**汇编时状态**" in assembler,
            "报告在 run 内汇编 ⇒ 抬头不得冒充终态（如实读数）",
        ),
    ]


def _ec02_declaration_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02 前半：执行体声明 + 互斥 + 按声明分流。"""
    tasks = _text(root, DOMAIN_TASKS)
    dispatch = _text(root, TASK_DISPATCH)
    return [
        toolbox.verdict(
            "ec02-the-contract-declares-the-execution-body",
            "class ReportAssemblySpec" in tasks and "report: ReportAssemblySpec | None" in tasks,
            "「谁执行这件工作」必须是契约声明（不是合约 id 字面量）",
        ),
        toolbox.verdict(
            "ec02-the-two-declarations-are-mutually-exclusive",
            MUTUAL_EXCLUSION in tasks,
            "两个执行体声明同时在场 ⇒ 构造期点名拒绝",
        ),
        toolbox.verdict(
            "ec02-the-dispatch-follows-the-declaration",
            DISPATCH_BY_DECLARATION in dispatch,
            "派发点必须按**声明**分流（报告 / 实验 / 会话）",
        ),
    ]


def _ec02_wiring_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02 后半：汇编器缝 + 同一份字节的指标 + run 级制品 + 判据覆盖。"""
    report_task = _text(root, REPORT_TASK)
    facts = _text(root, REPORT_FACTS)
    judge = _text(root, NEW_JUDGE)
    return [
        toolbox.verdict(
            "ec02-a-missing-assembly-is-named-not-silently-skipped",
            FAIL_CLOSED in report_task,
            "缺装配 ⇒ 点名拒绝（fail-closed，不静默回退到会话）",
        ),
        toolbox.verdict(
            "ec02-the-metrics-come-from-the-same-bytes-as-the-read-face",
            SAME_BYTES_METRICS in facts,
            "报告的指标必须读**与 HTTP 读面同一份字节**（两处各读一份必然漂移）",
        ),
        toolbox.verdict(
            "ec02-the-report-artifact-is-run-scoped",
            RUN_LEVEL_ARTIFACT in report_task,
            "报告是 **run 级**交付物（不是某一 phase 的中间产物）",
        ),
        toolbox.verdict(
            "ec02-the-judge-covers-sections-traces-and-both-refutations",
            all(
                name in judge
                for name in (
                    "test_the_run_succeeds_and_the_report_is_on_the_read_face",
                    "test_every_number_in_the_report_traces_back_to_persisted_facts",
                    "test_the_metric_table_matches_the_experiment_read_face",
                )
            )
            and "SECTION_HEADINGS" in judge,
            "四节 / 逐字溯源 / 指标对齐的受判面都必须在判据面",
        ),
    ]


def _ec03_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：新协议在树（立题格声明运行链）+ 两个合约在树 + 性质维判据。"""
    protocol = _text(root, PROTOCOL)
    contracts = _text(root, CONTRACTS)
    judge = _text(root, NEW_JUDGE)
    return [
        toolbox.verdict(
            "ec03-the-protocol-is-in-tree-with-a-run-chain-plan-phase",
            bool(protocol)
            and "capability_execution: run_chain" in protocol
            and "research_report_plan" in protocol,
            "新协议的立题格必须由运行链执行（立题站在真检索上）",
        ),
        toolbox.verdict(
            "ec03-the-nature-dimension-is-declared",
            "minimum_retrieved_sources: 1" in contracts,
            "性质维（系统取得的来源）必须是合约声明的一部分",
        ),
        toolbox.verdict(
            "ec03-the-report-phase-does-not-build-a-session",
            "report: {}" in contracts and "research_report_deliverable" in contracts,
            "报告格的合约必须声明 `report: {}`（不建会话）",
        ),
        toolbox.verdict(
            "ec03-the-two-coverage-dimensions-are-judged",
            "test_the_plan_phase_passes_both_coverage_dimensions" in judge,
            "覆盖两维（计数 + 性质）的受判面必须在判据面",
        ),
    ]


def _ec04_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：live 判据在树且受判面含落盘 + **反证四条各自的受判面** + 归档形态。"""
    judge = _text(root, NEW_JUDGE)
    live = _text(root, LIVE_JUDGE)
    press = _text(root, PRESS_ARCHIVE)
    verdicts: list[Any] = [
        toolbox.verdict(
            "ec04-the-live-judge-is-in-tree",
            bool(live) and "def _assert_live_report(" in live,
            "live 判据必须在树（新站真实 run + 报告落盘）",
        ),
        toolbox.verdict(
            "ec04-the-live-judge-writes-the-report-to-disk",
            LIVE_REPORT_PREFIX in live and "write_text(" in live,
            "报告正文必须**落盘**（本 EC 的交付面）",
        ),
    ]
    verdicts.extend([
        toolbox.verdict(
            f"ec04-the-{label.lower()}-arm-is-asserted",
            name in judge,
            f"`{label}` 的受判面必须在树",
        )
        for label, name in _PRESS_JUDGES
    ])
    verdicts.extend([
        toolbox.verdict(
            "ec04-the-baseline-gate-is-in-the-archive",
            "BASELINE" in press and "GREEN" in press,
            "归档必须含**基线行**（未按压不得红 —— 一级纪律）",
        ),
        toolbox.verdict(
            "ec04-every-press-is-red-in-the-archive",
            press.count("按压 RED") >= 4 and "all_red_and_restored=True" in press,
            "四条的读数必须全红且复原一致",
        ),
        toolbox.verdict(
            "ec04-the-archive-records-byte-exact-restore",
            press.count("sha 复原一致=True") >= 4,
            "逐条 raw sha256 复原一致（二进制读写）",
        ),
    ])
    return verdicts


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
    """逐字节判 CR（**不**经过文本模式；承 GOAL-023…075 的教训）。"""
    return bytes([13]) in raw


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """记录面：按压判词归档形态（非空、`CR=0`）。**不读内容做一致性断言**（输入即输出）。"""
    path = root / PRESS_ARCHIVE
    raw = path.read_bytes() if path.is_file() else b""
    return [
        toolbox.verdict(
            "press-archive-is-binary-safe",
            bool(raw) and not _has_carriage_return(raw),
            "missing/empty" if not raw else "contains CR",
        )
    ]


def _scope_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """两处射程**纯收紧**：`IN_SCOPE`（四道门）与**验证器注册清单**（判据面）。"""
    literal = toolbox.module_literal(_text(root, SCOPE_JUDGE), "IN_SCOPE")
    declared = set(literal) if isinstance(literal, tuple) else set()
    missing = [item for item in (SELF, ASSERTIONS) if item not in declared]
    verifiers = toolbox.module_literal(_text(root, VERIFIER_JUDGE), "_VERIFIERS")
    registered = isinstance(verifiers, tuple) and SELF in verifiers
    return [
        toolbox.verdict("scope-in-scope-pure-tightening", not missing, ",".join(missing)),
        toolbox.verdict("scope-verifier-registered", registered),
    ]


#: 本轮按压判词的归档落点（**进树**，二进制写盘）。
PRESS_ARCHIVE = ".cursor/plans/goals/evidence/GOAL-20261014-077-press-two-way.txt"


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 的特有断言（收口验证器唯一入口）。"""
    return [
        *_ec01_verdicts(root, toolbox),
        *_ec02_declaration_verdicts(root, toolbox),
        *_ec02_wiring_verdicts(root, toolbox),
        *_ec03_verdicts(root, toolbox),
        *_ec04_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_scope_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
