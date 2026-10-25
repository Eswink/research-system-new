#!/usr/bin/env python3
"""GOAL-20261024-096 收口复检的**本轮特有断言集**（EC-01…EC-05）。

与 GOAL-023…095 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件只写本轮特有的断言。

三条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01/EC-02 的六相声明面**：新协议在树、六相齐备、`experiment`/`report` **不**声明
   跨相 `inputs`（C-1）、三处跨相边逐字在位、三处「两向」判据文件在树且用例数不被削。
2. **EC-03 的报告问题面**：读取模块**在树**且被 `report_facts` 真的调用；`objective=None`
   的旧写死**不在**；渲染器两处口径都改成「本 run 自提」；无制品时的点名句在位。
3. **EC-05 的收口资产面**：本轮两个 `tools/` 脚本在 `IN_SCOPE`；
   `_VERIFIERS` 收录本轮验证器；跨 GOAL 的验证器覆盖判据在树。

**判据规则**（承 GOAL-027…095）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 用例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/contracts/test_direction_to_report_protocol.py", 5),
    ("tests/application/run_orchestration/test_direction_to_report_cross_phase_edges.py", 3),
    ("tests/application/run_orchestration/test_report_question_objective.py", 6),
    ("tests/e2e/test_direction_to_report_arc_offline.py", 6),
    ("tests/tooling/test_terminal_goals_have_closeout_verifiers.py", 4),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py",
    "tests/tooling/test_goal_ledger_covers_every_commit.py",
    "tests/tooling/test_goal_commit_chain_reaches_the_ledger.py",
    "tests/tooling/test_mainline_research_ladder_advances.py",
    "tests/tooling/test_mainline_program_is_intact.py",
    "tests/tooling/test_python_source_limits.py",
    "tests/tooling/test_tooling_scripts_meet_product_gates.py",
    "tests/contracts/test_direction_to_question_protocol.py",
    "tests/e2e/test_research_report_arc_offline.py",
)

#: 落点常量（逐条点名；缺一即判红）。
PROTOCOL = "examples/protocols/direction_to_report_v1.yaml"
QUESTION_MODULE = "packages/application/run_orchestration/report_question.py"
REPORT_FACTS = "packages/application/run_orchestration/report_facts.py"
RENDERER = "packages/application/deliverable/research_report.py"
NARRATIVE_RENDERER = "packages/application/deliverable/report_narrative.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_REGISTRY = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
CROSS_GOAL_JUDGE = "tests/tooling/test_terminal_goals_have_closeout_verifiers.py"
LIVE_JUDGE = "tests/e2e/test_direction_to_report_live.py"
#: 本轮的 `tools/` 交付件（**只有**这些要进四道门射程）。
TOOL_SCRIPTS: tuple[str, ...] = (
    "tools/verify_goal096_closeout.py",
    "tools/goal096_closeout_assertions.py",
)
#: 本轮协议必须声明的三处跨相边（读取方 ← 产出方）。
CROSS_PHASE_EDGES: tuple[tuple[str, str], ...] = (
    ("retrieval", "question:research_question"),
    ("plan", "retrieval:retrieval_report"),
    ("review", "plan:research_plan"),
)
#: C-1 的两个执行体（不得声明跨相 `inputs`）。
NON_CONSUMING_PHASES: tuple[str, ...] = ("experiment", "report")
PROTOCOL_PHASES: tuple[str, ...] = (
    "question",
    "retrieval",
    "plan",
    "experiment",
    "review",
    "report",
)

GOAL = ".cursor/plans/goals/GOAL-20261024-096-direction-to-report-in-one-run.md"
CHARTER = ".cursor/plans/goals/MAINLINE.md"
LADDER_DOMAIN = "| 报告 |"
LADDER_GOAL = "GOAL-20261024-096"
PROGRAM_SEQ = 64
#: 上一轮（序 63）的残余 —— 读取器拒绝后按它逐条处置，本 GOAL 必须逐条在位。
PRIOR_WS = 4
PRIOR_GOAL = "GOAL-20261023-095"
#: 本轮新增的残余（逐条明写）。
RESIDUAL_MARKERS: tuple[str, ...] = ("`W-1`", "`W-2`", "`W-3`")

# 同时认模块级与 class 内的用例（e2e 常按类分组；只认模块级会把它们数成 0）。
_CASE_DEF = re.compile(r"^\s*def test_", re.MULTILINE)


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _case_count(text: str) -> int:
    return len(_CASE_DEF.findall(text))


def _phase_block(protocol: str, phase_id: str) -> str:
    """协议文本里某个 phase 的块（`- id: <x>` 到下一个 `- id:` 或文件尾）。"""
    marker = f"  - id: {phase_id}\n"
    index = protocol.find(marker)
    if index == -1:
        return ""
    tail = protocol[index + len(marker) :]
    stop = tail.find("\n  - id: ")
    return tail[: stop if stop != -1 else len(tail)]


def _protocol_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：六相齐备、依赖链、C-1（两个执行体不声明跨相 inputs）。"""
    protocol = _text(root, PROTOCOL)
    verdicts: list[Any] = [
        toolbox.verdict(
            "the-six-phase-protocol-is-in-the-tree",
            bool(protocol.strip()),
            f"六相协议不在树：{PROTOCOL}",
        )
    ]
    verdicts.extend(
        toolbox.verdict(
            f"protocol-declares-phase-{phase_id}",
            f"  - id: {phase_id}\n" in protocol,
            f"协议缺 phase `{phase_id}`",
        )
        for phase_id in PROTOCOL_PHASES
    )
    for reader, reference in CROSS_PHASE_EDGES:
        block = _phase_block(protocol, reader)
        verdicts.append(
            toolbox.verdict(
                f"cross-phase-edge-{reader}",
                f"inputs: [{reference}]" in block,
                f"phase `{reader}` 必须声明 `inputs: [{reference}]`（跨相边）",
            )
        )
    for phase_id in NON_CONSUMING_PHASES:
        block = _phase_block(protocol, phase_id)
        verdicts.append(
            toolbox.verdict(
                f"c1-{phase_id}-declares-no-cross-phase-inputs",
                bool(block) and "inputs:" not in block,
                f"phase `{phase_id}` 的执行体不消费声明输入 ⇒ 不得声明 `inputs:`（C-1）",
            )
        )
    return verdicts


def _judge_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01/02/03 的判据面：文件在树、用例数不被削、两向判据的谓词在位。"""
    edges = _text(
        root,
        "tests/application/run_orchestration/test_direction_to_report_cross_phase_edges.py",
    )
    e2e = _text(root, "tests/e2e/test_direction_to_report_arc_offline.py")
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        count = _case_count(_text(root, relative))
        verdicts.append(
            toolbox.verdict(
                f"cases-{Path(relative).stem}",
                count >= floor,
                f"{relative} 的判据用例数 {count} 低于下界 {floor}",
            )
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(
                f"prior-judge-{Path(relative).stem}",
                (root / relative).is_file(),
                f"本轮引用的既有判据必须仍在树：{relative}",
            )
        )
    # 两向判据的**谓词**在位（不是「有一个同名文件」）：改写产出 ⇒ 检索词变；
    # 改检索产出 ⇒ plan 提示词材料变；摘上游 ⇒ 编译期点名。
    verdicts.extend([
        toolbox.verdict(
            "the-question-to-query-direction-is-judged",
            "queries == [query]" in edges,
            "跨相判据必须断言「改问题产出 ⇒ 检索词随之变」（逐字）",
        ),
        toolbox.verdict(
            "the-retrieval-to-plan-direction-is-judged",
            "prompts[0] != prompts[1]" in e2e,
            "编排判据必须断言「改检索产出 ⇒ plan 的提示词材料随之变」",
        ),
        toolbox.verdict(
            "removing-the-producer-is-a-compile-time-failure",
            "CROSS_PHASE_INPUT_INVALID" in edges,
            "反证臂必须判**编译期**点名（CROSS_PHASE_INPUT_INVALID）",
        ),
    ])
    return verdicts


def _report_question_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：读取模块在树并被真的调用；旧写死不在；两处渲染口径都改；缺席点名在位。"""
    module = _text(root, QUESTION_MODULE)
    facts = _text(root, REPORT_FACTS)
    renderer = _text(root, RENDERER)
    narrative = _text(root, NARRATIVE_RENDERER)
    return [
        toolbox.verdict(
            "the-question-reader-module-is-in-the-tree",
            "def question_objective(" in module,
            f"问题读取面不在树：{QUESTION_MODULE}",
        ),
        toolbox.verdict(
            "the-reader-reads-canonical-only",
            "artifacts.get(artifact_id)" in module and "http" not in module,
            "读取面必须只读 canonical（制品店字节），不得触网",
        ),
        toolbox.verdict(
            "report-facts-calls-the-question-reader",
            "objective=question_objective(artifacts, evidence)" in facts,
            "`report_facts.report_inputs` 必须用本 run 的问题正文填 `objective`（EC-03）",
        ),
        toolbox.verdict(
            "the-hardcoded-none-objective-is-gone",
            "objective=None" not in facts,
            "`objective=None` 的旧写死必须消失（否则第 1 节仍恒空）",
        ),
        toolbox.verdict(
            "both-renderers-say-the-question-is-the-runs-own",
            "研究问题（本 run 自提；逐字引用）" in renderer
            and "研究问题（本 run 自提；逐字引用）" in narrative,
            "两处渲染器的抬头必须如实改成「本 run 自提」（旧文案说「协议声明」会变成假话）",
        ),
        toolbox.verdict(
            "the-absence-is-named-not-invented",
            "本 run 没有 research_question 制品" in renderer,
            "无该制品时第 1 节必须**点名**缺席，不得编造",
        ),
        toolbox.verdict(
            "the-live-judge-is-in-the-tree",
            "direction_to_report_v1.yaml" in _text(root, LIVE_JUDGE),
            f"live 判据不在树：{LIVE_JUDGE}",
        ),
    ]


def _closeout_asset_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：验证器 / 断言集 / `IN_SCOPE` / `_VERIFIERS` / 跨 GOAL 判据。"""
    scope = _text(root, SCOPE_JUDGE)
    registry = _text(root, VERIFIER_REGISTRY)
    verdicts: list[Any] = [
        toolbox.verdict(
            "the-cross-goal-verifier-judge-is-in-the-tree",
            "def " in _text(root, CROSS_GOAL_JUDGE),
            f"跨 GOAL 收口验证器判据不在树：{CROSS_GOAL_JUDGE}",
        ),
        toolbox.verdict(
            "the-verifier-registry-lists-this-round",
            '"tools/verify_goal096_closeout.py"' in registry,
            "`_VERIFIERS` 必须收录本轮验证器（否则分类判据看不见它）",
        ),
    ]
    for relative in TOOL_SCRIPTS:
        verdicts.append(
            toolbox.verdict(
                f"{Path(relative).name}-is-in-the-four-gate-scope",
                f'"{relative}"' in scope,
                f"`{relative}` 不在 `IN_SCOPE` 里 ⇒ 四道门看不见它",
            )
        )
    return verdicts


def _record_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05 的记录面：阶梯「报告」行收录本 GOAL、程序表有序 64、上一轮 W 逐条处置。"""
    charter = _text(root, CHARTER)
    goal = _text(root, GOAL)
    covered = sum(1 for number in range(1, PRIOR_WS + 1) if f"`W-{number}`" in goal)
    verdicts: list[Any] = [
        toolbox.verdict(
            "the-ladder-report-row-records-this-goal",
            any(
                line.startswith(LADDER_DOMAIN) and LADDER_GOAL in line
                for line in charter.splitlines()
            ),
            "阶梯「报告」行的 `依据 GOAL` 没有收录本 GOAL（每轮必须更近科研）",
        ),
        toolbox.verdict(
            "the-program-table-has-row-sixty-four",
            f"| {PROGRAM_SEQ} | {LADDER_GOAL} |" in charter,
            f"宪章程序表必须有序 {PROGRAM_SEQ} = 本 GOAL 那一行",
        ),
        toolbox.verdict(
            "prior-residuals-all-disposed",
            covered == PRIOR_WS,
            f"上一轮（{PRIOR_GOAL}）的残余应 {PRIOR_WS}/{PRIOR_WS} 有处置，读到 {covered}",
        ),
        toolbox.verdict(
            "the-reader-refusal-is-recorded",
            "RESIDUAL_SECTION_MISSING" in goal,
            "读取器的拒绝码必须在 GOAL 里如实登记（本轮的输入材料处置）",
        ),
    ]
    missing = [marker for marker in RESIDUAL_MARKERS if marker not in goal]
    verdicts.append(toolbox.verdict("residuals-enumerated", not missing, ",".join(missing)))
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """全部本轮特有断言（收口验证器只调这一个入口）。"""
    return [
        *_protocol_verdicts(root, toolbox),
        *_judge_verdicts(root, toolbox),
        *_report_question_verdicts(root, toolbox),
        *_closeout_asset_verdicts(root, toolbox),
        *_record_verdicts(root, toolbox),
    ]


__all__ = ["assertion_verdicts"]
