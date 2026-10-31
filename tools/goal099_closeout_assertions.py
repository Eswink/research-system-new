#!/usr/bin/env python3
"""GOAL-20261028-099 收口复检的**本轮特有断言集**（EC-01…EC-06）。

与 GOAL-023…098 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件只写本轮特有的断言。

五条主轴：**EC-01** 八相相集 + 手稿相是会话相（合约不声明 `report:`/`experiment:`）+
三条跨相边 + C-1；**EC-02** 八键 / 七条 IMRaD 标题 / References / 数据表，且数字禁令先剥
引用标记、引用双向闭合；**EC-03** 两种作者形态 + 四条必填字段 + 渲染里无占位符；
**EC-04** 开关从组合根传到执行体、缺省关、判据文件用例数不低于下界；**EC-05/EC-06**
两个 `tools/` 脚本在 `IN_SCOPE` 与 `_VERIFIERS`、残差与拒绝码在位。

**判据规则**（承 GOAL-027…098）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 用例数**下界**（口径 = `def test_` 的条数，不是参数化展开数；
#: 取本轮实测值 ⇒ 删掉任何一条即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/contracts/test_direction_to_manuscript_protocol.py", 11),
    ("tests/application/test_manuscript_assembler.py", 17),
    ("tests/application/test_manuscript_references.py", 20),
    ("tests/application/test_manuscript_reference_order.py", 2),
    ("tests/application/test_manuscript_assembly.py", 5),
    ("tests/e2e/test_direction_to_manuscript_product_path.py", 7),
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
    "tests/tooling/test_terminal_goals_have_closeout_verifiers.py",
    "tests/contracts/test_direction_to_report_protocol.py",
    "tests/contracts/test_direction_to_report_v2_novelty.py",
    "tests/application/test_report_task_narrator_behaviour.py",
)

#: 落点常量（逐条点名；缺一即判红）。
REFERENCES = "packages/application/deliverable/references.py"
MANUSCRIPT = "packages/application/deliverable/manuscript.py"
MANUSCRIPT_FACTS = "packages/application/run_orchestration/manuscript_facts.py"
MANUSCRIPT_ASSEMBLY = "packages/application/run_orchestration/manuscript_assembly.py"
REPORT_TASK = "packages/application/run_orchestration/report_task.py"
REPORT_SUPPORT = "services/api/report_support.py"
EXECUTOR_WIRING = "services/api/executor_wiring.py"
PROTOCOL = "examples/protocols/direction_to_manuscript_v1.yaml"
CONTRACTS = "examples/contracts/task_contracts.yaml"
VERIFIER_REGISTRY = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
GATE_SCOPE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
EVIDENCE_DIR = ".cursor/plans/goals/evidence"
#: 本轮的 `tools/` 交付件（**只有**这些要进四道门射程）。
TOOL_SCRIPTS: tuple[str, ...] = (
    "tools/verify_goal099_closeout.py",
    "tools/goal099_closeout_assertions.py",
)

PROTOCOL_PHASES: tuple[str, ...] = (
    "question",
    "retrieval",
    "novelty",
    "plan",
    "experiment",
    "review",
    "manuscript",
    "editorial",  # GOAL-20261029-100 EC-02：投稿决策相。
    "revision",  # GOAL-20261029-100 EC-03：逐条应答相。
    "submission",  # GOAL-20261031-102 EC-03：投稿包相（申报过的扩展并留归因；不是放宽）。
    "report",
)
#: 手稿相必须声明的跨相边（读取方 ← 产出方:产物名）。
MANUSCRIPT_EDGES: tuple[str, ...] = (
    "retrieval:retrieval_report",
    "novelty:novelty_claim",
    "plan:research_plan",
)
#: C-1 的两个执行体（不得声明跨相 `inputs`）。
NON_CONSUMING_PHASES: tuple[str, ...] = ("experiment", "report")
#: IMRaD 的七条二级标题（**逐字**）。
IMRAD_HEADINGS: tuple[str, ...] = (
    "## Abstract",
    "## 1. Introduction",
    "## 2. Related Work",
    "## 3. Methods",
    "## 4. Results",
    "## 5. Discussion",
    "## 6. Conclusion",
)
#: 手稿的八个叙述键（**逐字**）。
MANUSCRIPT_KEYS: tuple[str, ...] = (
    "title",
    "abstract",
    "introduction",
    "related_work",
    "methods",
    "results",
    "discussion",
    "conclusion",
)
#: 参考文献必填字段（缺一即点名）与渲染里**不得出现**的占位符词表
#: （`fix_policy` 禁「补造缺失的作者/年份」）。
REQUIRED_FIELDS: tuple[str, ...] = ("authors", "title", "journal", "year")
PLACEHOLDER_TOKENS: tuple[str, ...] = ("Unknown", "N/A", "n.d.", "Anonymous", "TBD")
#: 本轮用的证据文件（引用了就必须在树）。
EVIDENCE_FILES: tuple[str, ...] = (
    f"{EVIDENCE_DIR}/GOAL-20261028-099-ec03-metadata-census.txt",
    f"{EVIDENCE_DIR}/GOAL-20261028-099-ec04-product-path.txt",
    f"{EVIDENCE_DIR}/GOAL-20261028-099-two-tree-current.txt",
    f"{EVIDENCE_DIR}/GOAL-20261028-099-two-tree-clean.txt",
)

GOAL = ".cursor/plans/goals/GOAL-20261028-099-submission-shaped-manuscript.md"
CHARTER = ".cursor/plans/goals/MAINLINE.md"
LADDER_DOMAIN = "| 报告 |"
LADDER_GOAL = "GOAL-20261028-099"
PROGRAM_SEQ = 67
#: 阶梯那一行必须写明的边界（**不许**声称叙述质量已判）。
LADDER_MARKERS: tuple[str, ...] = ("手稿层", "IMRaD", "手稿层 ≠ 报告层")
LADDER_NEXT_LEVEL = "叙述质量与事实一致性可判"
#: 本轮新增的残余（逐条明写）。
RESIDUAL_MARKERS: tuple[str, ...] = ("`W-1`", "`W-2`", "`W-3`", "`W-4`", "`W-5`")
#: 未覆盖范围（逐条明写）。
UNCOVERED_MARKERS: tuple[str, ...] = ("`U-1`", "`U-2`", "`U-3`")
#: 读取器的拒绝码（第八节要求记它）。
REFUSAL_MARKERS: tuple[str, ...] = ("REFUSED RESIDUAL_EMPTY",)

# 同时认模块级与 class 内的用例（e2e 常按类分组；只认模块级会把它们数成 0）。
_CASE_DEF = re.compile(r"^\s*(?:async )?def test_", re.MULTILINE)


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _case_count(text_body: str) -> int:
    return len(_CASE_DEF.findall(text_body))


def _phase_block(protocol: str, phase_id: str) -> str:
    """协议文本里某个 phase 的块（`- id: <x>` 到下一个 `- id:` 或文件尾）。"""
    marker = f"  - id: {phase_id}\n"
    index = protocol.find(marker)
    if index == -1:
        return ""
    tail = protocol[index + len(marker) :]
    stop = tail.find("\n  - id: ")
    return tail[: stop if stop != -1 else len(tail)]


def _contract_block(contracts: str, contract_id: str) -> str:
    """合约文本里某一份合约的块（`  <id>:` 到下一个同级键或文件尾）。"""
    marker = f"  {contract_id}:\n"
    index = contracts.find(marker)
    if index == -1:
        return ""
    tail = contracts[index + len(marker) :]
    stop = re.search(r"\n  [a-z_]+:\n", tail)
    return tail[: stop.start() if stop is not None else len(tail)]


def _declaration_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：八相协议 + 手稿相是会话相 + 三条跨相边 + C-1。"""
    protocol = _text(root, PROTOCOL)
    contracts = _text(root, CONTRACTS)
    phases = tuple(re.findall(r"^  - id: ([a-z_]+)$", protocol, re.MULTILINE))
    manuscript = _phase_block(protocol, "manuscript")
    block = _contract_block(contracts, "research_manuscript")
    return [
        toolbox.verdict(
            "header-099-declares-eight-phases-in-order",
            phases == PROTOCOL_PHASES,
            f"相集 {list(phases)} 与契约不符" if phases != PROTOCOL_PHASES else "",
        ),
        toolbox.verdict(
            "manuscript-phase-is-the-session-phase",
            "strategy: single_agent" in manuscript
            and "task_contract: research_manuscript" in manuscript,
            "" if "task_contract: research_manuscript" in manuscript else "手稿相没点名本合约",
        ),
        toolbox.verdict(
            "manuscript-contract-declares-no-report-executor",
            bool(block) and "\n    report:" not in block and "\n    experiment:" not in block,
            "合约声明了 report:/experiment: ⇒ 跨相 inputs 会被编译期拒绝",
        ),
        toolbox.verdict(
            "manuscript-phase-declares-its-three-cross-phase-edges",
            all(edge in manuscript for edge in MANUSCRIPT_EDGES),
            ",".join(edge for edge in MANUSCRIPT_EDGES if edge not in manuscript),
        ),
        toolbox.verdict(
            "c1-non-consuming-phases-declare-no-inputs",
            all(
                "inputs:" not in _phase_block(protocol, phase_id)
                for phase_id in NON_CONSUMING_PHASES
            ),
            "experiment/report 两相不得声明跨相 inputs",
        ),
        toolbox.verdict(
            "manuscript-contract-requires-a-retrieved-source",
            "minimum_retrieved_sources: 1" in block,
            "手稿必须站在真实检索之上（覆盖的性质维）",
        ),
    ]


def _structure_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：八键 + 七条 IMRaD 标题 + References + 数据表 + 数字禁令 + 引用双向闭合。"""
    manuscript = _text(root, MANUSCRIPT)
    return [
        toolbox.verdict(
            "header-099-manuscript-declares-the-eight-keys",
            all(f'"{key}"' in manuscript for key in MANUSCRIPT_KEYS),
            ",".join(f'"{key}"' for key in MANUSCRIPT_KEYS if f'"{key}"' not in manuscript),
        ),
        toolbox.verdict(
            "manuscript-declares-seven-imrad-headings",
            all(f'"{heading}"' in manuscript for heading in IMRAD_HEADINGS),
            ",".join(h for h in IMRAD_HEADINGS if f'"{h}"' not in manuscript),
        ),
        toolbox.verdict(
            "manuscript-declares-the-references-and-table-headings",
            '"## References"' in manuscript and "### Table 1." in manuscript,
            "References / 数据表标题必须逐字在场",
        ),
        toolbox.verdict(
            "manuscript-strips-citation-marks-before-the-digit-ban",
            "CITATION_PATTERN.sub" in manuscript,
            "数字禁令必须先剥引用标记（否则每个 [n] 都会被误判）",
        ),
        toolbox.verdict(
            "manuscript-refuses-out-of-range-and-orphan-citations",
            "out_of_range" in manuscript and "orphans" in manuscript,
            "引用必须双向闭合（越界 / 孤儿各点名）",
        ),
        toolbox.verdict(
            "manuscript-dataset-columns-are-the-existing-four",
            '"类别", "名称", "值", "来源"'
            in _text(root, "packages/application/deliverable/report_narrative.py"),
            "事实表列头必须逐字沿用既有四列（扩展而非新造）",
        ),
    ]


def _reference_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：两种作者形态 + 四条必填字段 + 占位符不在渲染里 + Vancouver 形状。"""
    references = _text(root, REFERENCES)
    return [
        toolbox.verdict(
            "references-handles-both-author-shapes",
            '"authors"' in references and '"author_string"' in references,
            "必须同时处理 NCBI 的 authors[] 与 Europe PMC 的 authorString",
        ),
        toolbox.verdict(
            "references-requires-four-fields",
            all(f'"{field}"' in references for field in REQUIRED_FIELDS)
            and "REQUIRED_FIELDS" in references,
            "作者 / 题名 / 刊名 / 年份 缺一即点名",
        ),
        toolbox.verdict(
            "references-renders-vancouver-identifiers",
            "doi:" in references and "PMID:" in references,
            "Vancouver 行必须带 doi / PMID",
        ),
        toolbox.verdict(
            "references-source-is-the-persisted-tool-result",
            'parsed.get("articles")' in references,
            "元数据只能来自落盘的 tool-result 字节（不许出网、不许猜）",
        ),
        toolbox.verdict(
            "references-names-missing-fields-instead-of-filling-them",
            "_entry_of" in references
            and "missing = tuple(name for name in REQUIRED_FIELDS" in references,
            "缺失必须由 REQUIRED_FIELDS 逐条算出（点名），而不是填一个占位符顶上",
        ),
        toolbox.verdict(
            "references-renderer-never-substitutes-a-placeholder",
            not any(
                pattern in references
                for pattern in (
                    'or ("Unknown"',
                    'or ["Unknown"',
                    '= ("Unknown"',
                    'or ("N/A"',
                    'or ("n.d."',
                    'or ("Anonymous"',
                )
            ),
            "渲染面不得用占位符顶替缺失字段（判的是**代码里的替换**，不是文档里提这个词）",
        ),
    ]


def _product_path_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：装配开关三跳 + 缺省语义 + 判据文件与证据在位。"""
    wiring = _text(root, EXECUTOR_WIRING)
    support = _text(root, REPORT_SUPPORT)
    task = _text(root, REPORT_TASK)
    assembly = _text(root, MANUSCRIPT_ASSEMBLY)
    verdicts = [
        toolbox.verdict(
            "root-passes-the-manuscript-switch-to-the-report-seam",
            "manuscript=manuscript" in wiring and "manuscript: bool = True" in wiring,
            "组合根必须把开关传给报告缝（缺省开）",
        ),
        toolbox.verdict(
            "seam-defaults-the-switch-off",
            "manuscript: bool = False" in support,
            "report_task_runner 的缺省必须是关（既有五处调用点逐字沿用旧语义）",
        ),
        toolbox.verdict(
            "report-task-carries-the-switch-on-its-deps",
            "manuscript: bool = False" in task,
            "ReportTaskDeps 必须带手稿开关（缺省关 ⇒ 既有调用点零回归）",
        ),
        toolbox.verdict(
            "assembly-honours-the-switch",
            'getattr(deps, "manuscript", False)' in assembly,
            "装配面必须按开关决定是否装手稿",
        ),
        toolbox.verdict(
            "assembly-returns-none-without-a-narrative-artifact",
            "if block is None:" in assembly and "return None" in assembly,
            "本 run 没走手稿相 ⇒ 不产手稿（正确读数，不是失败）",
        ),
        toolbox.verdict(
            "assembly-records-a-mixed-authorship-prefix",
            "model_assisted:" in assembly,
            "created_by 必须区分「模型正文 + 汇编器数字」，两个方向都不许冒充",
        ),
    ]
    for relative in EVIDENCE_FILES:
        verdicts.append(
            toolbox.verdict(
                f"evidence-{Path(relative).name}", toolbox.tree(root, relative).is_file()
            )
        )
    return verdicts


def _case_floor_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮判据文件的用例数下界（掉下去即判红；只上调不下调）。"""
    verdicts: list[Any] = []
    for relative, floor in CASE_FLOORS:
        body = _text(root, relative)
        count = _case_count(body)
        verdicts.append(
            toolbox.verdict(
                f"cases-{Path(relative).stem}",
                count >= floor,
                f"{relative} 只有 {count} 条用例（下界 {floor}）",
            )
        )
    return verdicts


def _asset_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：两个 `tools/` 脚本在树、在 `IN_SCOPE`、在 `_VERIFIERS`。"""
    registry = _text(root, VERIFIER_REGISTRY)
    gate = _text(root, GATE_SCOPE)
    verifiers = toolbox.module_literal(registry, "_VERIFIERS")
    in_scope = toolbox.module_literal(gate, "IN_SCOPE")
    listed_verifiers = tuple(verifiers or ())
    listed_scope = tuple(in_scope or ())
    return [
        toolbox.verdict(
            f"tool-present-{Path(relative).name}", toolbox.tree(root, relative).is_file()
        )
        for relative in TOOL_SCRIPTS
    ] + [
        toolbox.verdict(
            "verifier-registered-in-the-registry",
            "tools/verify_goal099_closeout.py" in listed_verifiers,
            "`_VERIFIERS` 未收录本轮验证器（跨 GOAL 判据按它点名）",
        ),
        toolbox.verdict(
            "verifier-and-assertions-are-in-the-gate-scope",
            all(item in listed_scope for item in TOOL_SCRIPTS),
            ",".join(item for item in TOOL_SCRIPTS if item not in listed_scope),
        ),
        toolbox.verdict(
            "prior-judges-still-in-tree",
            all(toolbox.tree(root, item).is_file() for item in PRIOR_JUDGES),
            ",".join(item for item in PRIOR_JUDGES if not toolbox.tree(root, item).is_file()),
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有的断言（EC-01…EC-06 的产品面与记录面）。"""
    return [
        *_declaration_verdicts(root, toolbox),
        *_structure_verdicts(root, toolbox),
        *_reference_verdicts(root, toolbox),
        *_product_path_verdicts(root, toolbox),
        *_case_floor_verdicts(root, toolbox),
        *_asset_verdicts(root, toolbox),
    ]


def ladder_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-06：阶梯「报告」行收录本 GOAL、写明「手稿层 ≠ 报告层」，且 `下一级` **未被冒认**。"""
    charter = _text(root, CHARTER)
    rows = [line for line in charter.splitlines() if line.startswith(LADDER_DOMAIN)]
    recorded = [line for line in rows if LADDER_GOAL in line]
    joined = " ".join(recorded)
    return [
        toolbox.verdict("ladder-report-row-exists", bool(rows), "宪章阶梯必须有「报告」域那一行"),
        toolbox.verdict(
            "ladder-report-row-records-this-goal",
            bool(recorded),
            "「报告」行的依据 GOAL 必须收录本 GOAL",
        ),
        toolbox.verdict(
            "ladder-report-row-names-the-manuscript-layer",
            all(marker in joined for marker in LADDER_MARKERS),
            ",".join(marker for marker in LADDER_MARKERS if marker not in joined),
        ),
        toolbox.verdict(
            "ladder-report-row-keeps-the-next-level-unchanged",
            LADDER_NEXT_LEVEL in joined,
            "`下一级` 必须保持「叙述质量与事实一致性可判」——不许声称已判",
        ),
    ]


__all__ = [
    "CASE_FLOORS",
    "LADDER_MARKERS",
    "MANUSCRIPT_EDGES",
    "MANUSCRIPT_KEYS",
    "IMRAD_HEADINGS",
    "PRIOR_JUDGES",
    "PROTOCOL_PHASES",
    "RESIDUAL_MARKERS",
    "UNCOVERED_MARKERS",
    "REFUSAL_MARKERS",
    "assertion_verdicts",
    "ladder_verdicts",
]
