#!/usr/bin/env python3
"""GOAL-20261026-097 收口复检的**本轮特有断言集**（EC-01…EC-06）。

与 GOAL-023…096 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件只写本轮特有的断言。

四条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01 的接缝面**：两个组合根都经同一份 `*_executor_seams`；三道缝（实验 / 报告 /
   运行链检索）在 seam 构造器里；两个根都没有在装配期构造 Docker 后端。
2. **EC-03 的声明优先面**：`declared_or_assembled` 存在且含「声明优先」那两行；出厂
   `m12_experiment_execution` 仍 pin 脚本+镜像；空合约仍是 `{}`。
3. **EC-04 的创新点两面**：七相协议在树且 `novelty` 在 `retrieval` 与 `plan` 之间；
   `novelty_reviewer` 有 `review_panel_role: REVIEWER`；`novelty_a` 绑第三个模型
   （`minimax-m3`）；协议 `required_roles` 点名它；新合约在树。
4. **EC-05/EC-06 的收口资产与记录面**：本轮两个 `tools/` 脚本在 `IN_SCOPE`；
   `_VERIFIERS` 收录本轮验证器；残差节与记录更正都在位。

**判据规则**（承 GOAL-027…096）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 用例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/api/test_product_roots_carry_the_execution_seams.py", 9),
    ("tests/api/test_contract_pinned_experiment_spec_takes_effect.py", 9),
    ("tests/contracts/test_direction_to_report_v2_novelty.py", 15),
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
)

#: 落点常量（逐条点名；缺一即判红）。
SQLITE_ROOT = "services/api/composition.py"
PG_ROOT = "services/api/pg_composition.py"
SEAM_BUILDER = "services/api/executor_wiring.py"
EXPERIMENT_FACTORIES = "services/api/experiment_factories.py"
EXPERIMENT_SUPPORT = "services/api/experiment_support.py"
RETRIEVAL_WIRING = "services/api/retrieval_wiring.py"
NOVELTY_READER = "packages/application/run_orchestration/novelty_claim.py"
NOVELTY_STEP = "packages/application/run_orchestration/novelty_claim_step.py"
PROTOCOL = "examples/protocols/direction_to_report_v2.yaml"
CONTRACTS = "examples/contracts/task_contracts.yaml"
ROLES = "examples/config/roles.yaml"
AGENTS = "examples/config/agents.yaml"
MODELS = "examples/config/models.yaml"
TEMPLATES = "examples/config/team_templates.yaml"
VERIFIER_REGISTRY = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
LIVE_JUDGE = "tests/e2e/test_productive_entry_runs_the_whole_chain.py"
#: 本轮的 `tools/` 交付件（**只有**这些要进四道门射程）。
TOOL_SCRIPTS: tuple[str, ...] = (
    "tools/verify_goal097_closeout.py",
    "tools/goal097_closeout_assertions.py",
)

PROTOCOL_PHASES: tuple[str, ...] = (
    "question",
    "retrieval",
    "novelty",
    "plan",
    "experiment",
    "review",
    "report",
)
#: 本轮协议必须声明的跨相边（读取方 ← 产出方）。
CROSS_PHASE_EDGES: tuple[tuple[str, str], ...] = (
    ("retrieval", "question:research_question"),
    ("novelty", "retrieval:retrieval_report"),
    ("plan", "novelty:novelty_claim"),
    ("review", "novelty:novelty_claim"),
)
#: C-1 的两个执行体（不得声明跨相 `inputs`）。
NON_CONSUMING_PHASES: tuple[str, ...] = ("experiment", "report")

GOAL = ".cursor/plans/goals/GOAL-20261026-097-productive-entry-and-novelty.md"
CHARTER = ".cursor/plans/goals/MAINLINE.md"
EVIDENCE = ".cursor/plans/goals/evidence/GOAL-20261026-097-productive-entry-run.txt"
LADDER_DOMAIN = "| 实验 |"
LADDER_GOAL = "GOAL-20261026-097"
PROGRAM_SEQ = 65
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


def _seam_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：两个根都走同一份 seam 构造器；三道缝齐；装配期零 Docker。"""
    sqlite = _text(root, SQLITE_ROOT)
    pg = _text(root, PG_ROOT)
    seams = _text(root, SEAM_BUILDER)
    return [
        toolbox.verdict(
            "sqlite-root-uses-the-shared-seam-builder",
            "sqlite_executor_seams(" in sqlite,
            "SQLite 组合根必须经 `sqlite_executor_seams(...)` 接缝（不是各写一套）",
        ),
        toolbox.verdict(
            "pg-root-uses-the-shared-seam-builder",
            "pg_executor_seams(" in pg,
            "PG 组合根必须经 `pg_executor_seams(...)` 接缝",
        ),
        toolbox.verdict(
            "the-seam-builder-yields-three-slots",
            all(
                f'"{name}"' in seams for name in ("capabilities", "experiment_task", "report_task")
            ),
            "seam 构造器必须给出三道缝：运行链检索 / 实验 / 报告",
        ),
        toolbox.verdict(
            "the-lazy-factory-exists",
            "lazy_docker_experiment_assembly" in _text(root, EXPERIMENT_FACTORIES),
            "组合根用的惰性工厂必须在树（装配期零 Docker 连接）",
        ),
        toolbox.verdict(
            "the-eager-factory-is-still-there",
            "DockerExecutionBackend(image=image)" in _text(root, EXPERIMENT_FACTORIES),
            "判据/工具侧的急切工厂必须仍在（既有用法不改）",
        ),
        toolbox.verdict(
            "the-root-wires-the-retrieval-face",
            "retrieval_providers(" in sqlite and "retrieval_providers(" in pg,
            "两个根都必须造出厂检索 provider（运行链执行面）",
        ),
    ]


def _pin_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：声明优先分支在；出厂 pin 在；空合约仍是 `{}`。"""
    support = _text(root, EXPERIMENT_SUPPORT)
    contracts = _text(root, CONTRACTS)
    return [
        toolbox.verdict(
            "the-declaration-priority-branch-exists",
            "declaration.script or script" in support and "declaration.image or image" in support,
            "`declared_or_assembled` 必须有「契约非空 ⇒ 用契约的」两行",
        ),
        toolbox.verdict(
            "the-shipped-pin-is-still-authored",
            "m12_experiment_execution:" in contracts
            and "examples/experiments/m12_reference_classification.py" in contracts,
            "出厂 `m12_experiment_execution` 仍 pin 脚本（这不是本判据造的事实）",
        ),
        toolbox.verdict(
            "the-generic-contract-stays-empty",
            re.search(r"\n  experiment_execution:\n(?:.*\n)*?    experiment: \{\}", contracts)
            is not None,
            "`experiment_execution` 的 `experiment: {}`（装配面兜底语义）必须逐字保持",
        ),
        toolbox.verdict(
            "the-deferred-execution-exists",
            "class _DeferredExecution" in support,
            "惰性取后端必须是一个具名结构（装配期零连接的可判形态）",
        ),
    ]


def _novelty_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04 的**声明面**：七相、跨相边、C-1、合约、读取模块。"""
    protocol = _text(root, PROTOCOL)
    verdicts: list[Any] = [
        toolbox.verdict(
            "the-seven-phase-protocol-is-in-the-tree",
            all(f"  - id: {phase}\n" in protocol for phase in PROTOCOL_PHASES),
            "新协议必须真的写七相（novelty 插在 retrieval 与 plan 之间）",
        ),
        toolbox.verdict(
            "the-novelty-phase-sits-between",
            "depends_on: [retrieval]" in _phase_block(protocol, "novelty")
            and "novelty" in _phase_block(protocol, "plan"),
            "`novelty` 的上游是 retrieval，下游是 plan（依赖链可判）",
        ),
        toolbox.verdict(
            "the-cross-phase-edges-are-declared",
            all(
                reference in _phase_block(protocol, reader)
                for reader, reference in CROSS_PHASE_EDGES
            ),
            "四条跨相边必须逐字在位（含 plan/review 读 novelty 声明）",
        ),
        toolbox.verdict(
            "the-two-non-consuming-phases-declare-no-inputs",
            all("inputs:" not in _phase_block(protocol, phase) for phase in NON_CONSUMING_PHASES),
            "C-1：`experiment` / `report` 两个执行体不声明跨相 inputs",
        ),
        toolbox.verdict(
            "the-novelty-contract-is-authored",
            "novelty_claim_proposal:" in _text(root, CONTRACTS),
            "新合约 `novelty_claim_proposal` 必须在出厂合约文件里",
        ),
        toolbox.verdict(
            "the-novelty-reader-is-in-the-tree",
            bool(_text(root, NOVELTY_READER)) and bool(_text(root, NOVELTY_STEP)),
            "声明面的判定模块与门接线都必须在树",
        ),
    ]
    return verdicts


def _novelty_review_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04 的评审面：面板角色 / 第三模型 / 模板 / 协议点名。"""
    protocol = _text(root, PROTOCOL)
    roles = _text(root, ROLES)
    agents = _text(root, AGENTS)
    models = _text(root, MODELS)
    templates = _text(root, TEMPLATES)
    verdicts: list[Any] = [
        toolbox.verdict(
            "the-novelty-role-is-a-reviewer",
            "review_panel_role: REVIEWER" in _phase_block_roles(roles, "novelty_reviewer"),
            "`novelty_reviewer` 必须有 `review_panel_role: REVIEWER`（否则被评对象不进提示词）",
        ),
        toolbox.verdict(
            "the-novelty-agent-binds-a-third-model",
            "novelty_a:" in agents and "novelty_review_model" in agents,
            "`novelty_a` 必须绑第三个模型实例（与生产侧及另两位评审者都不同）",
        ),
        toolbox.verdict(
            "the-third-model-is-declared",
            "model_name: minimax-m3" in models,
            "第三个评审模型的底层 `model_name` 必须在目录里",
        ),
        toolbox.verdict(
            "the-role-is-in-the-standard-template",
            _standard_template_names_the_role(templates)
            and "role: novelty_reviewer" in _phase_block(protocol, "review"),
            "角色必须进 `standard` 模板**且**被协议的 review 相点名（缺一即编译期 ROLE_CAPACITY）",
        ),
        toolbox.verdict(
            "the-protocol-names-the-role",
            "role: novelty_reviewer" in _phase_block(protocol, "review"),
            "协议的 `review.required_roles` 必须点名 `novelty_reviewer`",
        ),
    ]
    return verdicts


def _standard_template_names_the_role(templates: str) -> bool:
    """`standard` 模板的 roles 里是否有点名 `novelty_reviewer`（缩进两段的块，按块判）。

    为什么不能全局搜：`rigorous`（`extends: standard`）里**也**有一行 `novelty_reviewer`；
    全局搜会在「standard 里没有、只有 rigorous 里有」时假绿 —— 而 `project.yaml` 用的正是
    `standard`。
    """
    marker = "\n  standard:\n"
    index = templates.find(marker)
    if index == -1:
        return False
    tail = templates[index + len(marker) :]
    stop = tail.find("\n  rigorous:\n")
    block = tail[: stop if stop != -1 else len(tail)]
    return "novelty_reviewer:" in block


def _phase_block_roles(text: str, key: str) -> str:
    """`roles.yaml` 里某个角色的块（到下一个两空格缩进的键为止）。"""
    marker = f"  {key}:\n"
    index = text.find(marker)
    if index == -1:
        return ""
    tail = text[index + len(marker) :]
    match = re.search(r"\n  [a-z_0-9]+:\n", tail)
    return tail[: match.start()] if match else tail


def _asset_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：本轮 `tools/` 脚本在 `IN_SCOPE`；`_VERIFIERS` 收录本轮验证器。"""
    registry = _text(root, VERIFIER_REGISTRY)
    scope = _text(root, "tests/tooling/test_tooling_scripts_meet_product_gates.py")
    return [
        toolbox.verdict(
            "the-rounds-verifier-is-registered",
            "tools/verify_goal097_closeout.py" in registry,
            "`_VERIFIERS` 必须收录本轮验证器（跨 GOAL 判据按受判面点名它）",
        ),
        toolbox.verdict(
            "the-verifier-loads-its-own-assertions",
            "goal097_closeout_assertions.py" in _text(root, "tools/verify_goal097_closeout.py"),
            "本轮验证器必须加载**自己那份**断言集（GOAL-078 的教训：自洽地加载上一轮那份）",
        ),
        toolbox.verdict(
            "the-tool-scripts-are-in-scope",
            all(script in scope for script in TOOL_SCRIPTS),
            "本轮两个 `tools/` 脚本必须先登记进四道门的 `IN_SCOPE`",
        ),
        toolbox.verdict(
            "the-live-judge-is-in-the-tree",
            bool(_text(root, LIVE_JUDGE)),
            "EC-02 的真跑判据必须在树（它不进默认门：`requires_live_llm`）",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """全部本轮特有断言（收口验证器只调这一个入口）。"""
    verdicts: list[Any] = [*_seam_verdicts(root, toolbox), *_pin_verdicts(root, toolbox)]
    verdicts.extend(_novelty_verdicts(root, toolbox))
    verdicts.extend(_novelty_review_verdicts(root, toolbox))
    verdicts.extend(_asset_verdicts(root, toolbox))
    goal = _text(root, GOAL)
    for relative, floor in CASE_FLOORS:
        count = _case_count(_text(root, relative))
        verdicts.append(
            toolbox.verdict(
                f"cases-{Path(relative).stem}-at-least-{floor}",
                count >= floor,
                f"{relative} 的用例数 {count} < 下界 {floor}（判据被削）",
            )
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(
                f"prior-judge-{Path(relative).stem}-in-tree",
                (root / relative).is_file(),
                f"{relative} 必须仍在树（本轮引用而非重复它）",
            )
        )
    missing_residual = [item for item in RESIDUAL_MARKERS if item not in goal]
    verdicts.append(
        toolbox.verdict("residuals-enumerated", not missing_residual, ",".join(missing_residual))
    )
    verdicts.append(
        toolbox.verdict(
            "the-evidence-file-is-in-the-tree",
            (root / EVIDENCE).is_file(),
            "EC-02 的取证文件必须在树（skip 也留下读数）",
        )
    )
    return verdicts


__all__ = ["CASE_FLOORS", "PRIOR_JUDGES", "PROTOCOL_PHASES", "TOOL_SCRIPTS", "assertion_verdicts"]
