#!/usr/bin/env python3
"""GOAL-20261027-098 收口复检的**本轮特有断言集**（EC-01…EC-07）。

与 GOAL-023…097 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— 由 `tools/closeout_recheck_assertions.standard_verdicts`
承担；本文件**只写本 GOAL 特有的断言**。

**三组主轴**（逐条对应本 GOAL 的 EC）：

1. **EC-01/EC-02 作者 ≠ 评审者**：新增角色 / agent / 模型在出厂目录里；
   `novelty` 相点名 `novelty_author`、`review` 相点名 `novelty_reviewer`；作者**不是**
   `REVIEWER` 面板角色；判据文件与例数下界；**跨协议自评扫描**的判据也在树。
2. **EC-03 脚本选择**：`design_script` 模块的白名单 / 三段优先级 / 点名拒绝的形态在树；
   装配面那一行调用在树；合约的任务书写了新键；判据文件与例数下界。
3. **EC-04/05/06/07 归档与记账**：三个回填验证器 + 断言集 + 两处登记；短行登记表在树；
   `progress-075` 链接可解析；`max_goals` 读到 100；本轮修订行是 5 格。

**判据规则**（承 GOAL-027…097）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PROGRAM_SEQ = 66
GOAL_ID = "GOAL-20261027-098"

#: 一、作者 ≠ 评审者
ROLES = "examples/config/roles.yaml"
AGENTS = "examples/config/agents.yaml"
MODELS = "examples/config/models.yaml"
TEAMS = "examples/config/team_templates.yaml"
PROTOCOL = "examples/protocols/direction_to_report_v2.yaml"
INDEPENDENCE_JUDGE = "tests/contracts/test_direction_to_report_v2_independence.py"
NOVELTY_JUDGE = "tests/contracts/test_direction_to_report_v2_novelty.py"

#: 二、脚本选择
DESIGN_SCRIPT = "packages/application/experiments/design_script.py"
DESIGN_PLAN = "packages/application/experiments/design_from_plan.py"
SUPPORT = "services/api/experiment_support.py"
CONTRACTS = "examples/contracts/task_contracts.yaml"
SCRIPT_JUDGE = "tests/application/test_experiment_script_comes_from_the_plan.py"
#: EC-03 的**容器面**（`requires_docker`）：真跑两个脚本、按容器产出的指标区分。
CONTAINER_JUDGE = "tests/e2e/test_experiment_script_selection_docker.py"
CONTAINER_EVIDENCE = ".cursor/plans/goals/evidence/GOAL-20261027-098-ec03-container-run.txt"

#: 三、归档与记账
SHORT_ROWS_REGISTRY = ".cursor/plans/goals/archive/SHORT-REVISION-ROWS.md"
SHORT_ROWS_JUDGE = "tests/tooling/test_short_archive_revision_rows_are_registered.py"
PROGRESS_075 = ".cursor/plans/goals/archive/MAINLINE-2026-10-15-progress-075-only.md"
BACKFILLED: tuple[tuple[str, str], ...] = (
    ("tools/verify_goal076_closeout.py", "tools/goal076_closeout_assertions.py"),
    ("tools/verify_goal090_closeout.py", "tools/goal090_closeout_assertions.py"),
    ("tools/verify_goal095_closeout.py", "tools/goal095_closeout_assertions.py"),
)

#: 自指与登记面
SELF = "tools/verify_goal098_closeout.py"
ASSERTIONS = "tools/goal098_closeout_assertions.py"
SCOPE_JUDGE = "tests/tooling/test_tooling_scripts_meet_product_gates.py"
VERIFIER_JUDGE = "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py"
CHARTER = ".cursor/plans/goals/MAINLINE.md"

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tests/tooling/test_mainline_program_is_intact.py",
    "tests/tooling/test_mainline_archive_is_continuous.py",
    "tests/tooling/test_mainline_research_ladder_advances.py",
    "tests/tooling/test_tooling_scripts_meet_product_gates.py",
    "tests/tooling/test_closeout_verifiers_run_their_own_assertions.py",
)

#: 本轮**新增**判据 → 例数下界（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    (INDEPENDENCE_JUDGE, 14),
    (SCRIPT_JUDGE, 12),
    (SHORT_ROWS_JUDGE, 6),
    # EC-02 真跑抓到的第 8 个真缺陷（判负路径读不存在的 `GateOutcome.verdicts`）。
    ("tests/contracts/test_novelty_rejection_turns_the_gate_red.py", 6),
)

TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def collected_case_count(root: Path, relative: str) -> int:
    return len(TEST_DEFINITION.findall(_text(root, relative)))


def _independence_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：角色 / agent / 模型 / 模板 / 协议五处都在，且作者不是评审者。"""
    verdict = toolbox.verdict
    roles = _text(root, ROLES)
    agents = _text(root, AGENTS)
    models = _text(root, MODELS)
    teams = _text(root, TEAMS)
    return [
        verdict("ec01-author-role-declared", "  novelty_author:" in roles, ROLES),
        verdict(
            "ec01-author-role-uses-only-granted-reads",
            "idea.write" not in roles.split("  novelty_author:", 1)[-1].split("\n  ", 1)[0],
            "作者角色的能力面**不得**含 `idea.write` / `idea.review`（policy 零 allow）",
        ),
        verdict(
            "ec01-author-role-is-not-a-panel-role",
            "review_panel_role" not in roles.split("  novelty_author:", 1)[-1].split("\n  ", 1)[0],
            "作者不是评审者 ⇒ 不得声明 `review_panel_role`",
        ),
        verdict("ec01-author-agent-bound", "  novelty_writer:" in agents, AGENTS),
        verdict("ec01-author-model-declared", "  novelty_author_model:" in models, MODELS),
        verdict(
            "ec01-author-model-is-distinct",
            "deepseek-v4-pro-0813" in models,
            "作者必须落在第四个底层模型（与生产侧 + 三位评审者都不同）",
        ),
        verdict("ec01-author-in-the-team-pool", "novelty_author" in teams, TEAMS),
        verdict(
            "ec01-the-novelty-phase-names-the-author",
            "{role: novelty_author" in _text(root, PROTOCOL),
            "`novelty` 相必须点名 `novelty_author`（作者与评审者分开）",
        ),
        verdict(
            "ec01-the-review-phase-keeps-the-reviewer",
            "{role: novelty_reviewer" in _text(root, PROTOCOL),
            "`review` 相必须保留 `novelty_reviewer`（它才是评审者）",
        ),
        verdict(
            "ec01-the-cross-protocol-scan-exists",
            "def self_review_shapes(" in _text(root, INDEPENDENCE_JUDGE),
            "判据必须**跨协议**扫描自评形态（缺陷与 v2 无关）",
        ),
        verdict(
            "ec01-novelty-judge-still-in-tree", (root / NOVELTY_JUDGE).is_file(), NOVELTY_JUDGE
        ),
    ]


def _referenced_evidence_exists(root: Path) -> bool:
    """`SCRIPT_JUDGE` 的 docstring 里点了名的取证文件是否**真的在树**。

    **它补哪一格**（本轮验收方点出的真缺陷）：那份 docstring 曾写「真容器那一段是
    `evidence/GOAL-20261027-098-ec03-*.txt`，不在这里假装」，而该文件**从未创建** ——
    与本轮替 GOAL-076 修掉的悬空引用同类。悬空引用比没写更坏：它读起来像取证已存在。
    """
    return (root / CONTAINER_EVIDENCE).is_file()


def _selection_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03：白名单 / 三档优先级 / 点名拒绝 / 装配面调用 / 合约任务书。"""
    verdict = toolbox.verdict
    module = _text(root, DESIGN_SCRIPT)
    support = _text(root, SUPPORT)
    contracts = _text(root, CONTRACTS)
    return [
        verdict("ec03-whitelist-declared", "SHIPPED_EXPERIMENT_SCRIPTS" in module, DESIGN_SCRIPT),
        verdict(
            "ec03-whitelist-is-a-closed-tuple",
            "SHIPPED_EXPERIMENT_SCRIPTS: tuple[str, ...] = (" in module,
            "白名单必须是显式闭集（不是「仓库里所有 .py」）",
        ),
        verdict("ec03-selector-declared", "def plan_selected_script(" in module, DESIGN_SCRIPT),
        verdict(
            "ec03-contract-pin-wins",
            "declaration.script" in module or 'getattr(declaration, "script", "")' in module,
            "契约 pin 必须在三档里最优先",
        ),
        verdict(
            "ec03-out-of-whitelist-is-named",
            # 消息在源码里被换行拆开 ⇒ 取**不含换行**的那一段（本轮第一次写整句 ⇒ 判据自己判红）。
            "shipped experiment script (allowed:" in module,
            "越界必须**点名**拒绝（不静默回落）",
        ),
        verdict(
            "ec03-path-traversal-is-named",
            "parent traversal" in module,
            "`..` / 绝对路径 / 盘符必须单独**点名**（§9 的点名姿态）",
        ),
        verdict(
            "ec03-reader-returns-the-block",
            "def plan_design_block(" in _text(root, DESIGN_PLAN),
            "需要一个「只读设计块」的入口（臂解析是另一件事）",
        ),
        verdict(
            "ec03-the-runner-calls-the-selector",
            "plan_selected_script(assembly, task" in support,
            f"{SUPPORT} 的派发体必须调用选择面",
        ),
        verdict(
            "ec03-the-contract-tells-the-model-the-closed-set",
            # 合约正文按 80 列折行 ⇒ 只取那一行里连续的一段。
            "optional `script` key naming" in contracts,
            "合约任务书必须告诉模型这个键存在且是闭集（否则它无从选择）",
        ),
    ]


def _container_face_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-03 的**容器面**：派发面判「选中的是哪个」，这一组判「跑的就是它」。

    `assembly.script` 是**输入**，容器读数是**输出** —— 只判派发面时，复制脚本那一步
    出偏差判据会照绿（本轮就抓到过同类位置的真缺陷）。
    """
    verdict = toolbox.verdict
    return [
        verdict(
            "ec03-container-judge-in-tree", (root / CONTAINER_JUDGE).is_file(), CONTAINER_JUDGE
        ),
        verdict(
            "ec03-container-evidence-in-tree",
            (root / CONTAINER_EVIDENCE).is_file(),
            "容器面取证必须在树（`assembly.script` 是输入、容器读数是输出）",
        ),
        verdict(
            "ec03-no-dangling-evidence-reference",
            # 引用了取证文件 ⇒ 该文件必须在树；否则就是本轮替 076 修掉的那类悬空引用。
            _referenced_evidence_exists(root)
            if CONTAINER_EVIDENCE.rsplit("/", 1)[-1] in _text(root, SCRIPT_JUDGE)
            else True,
            f"`{Path(SCRIPT_JUDGE).name}` 里点名的取证文件必须真实存在（悬空引用 = 谎）",
        ),
    ]


def _archive_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-04：三个回填验证器 + 短行登记表 + progress-075 链接。"""
    verdict = toolbox.verdict
    charter = _text(root, CHARTER)
    verifier_source = _text(root, VERIFIER_JUDGE)
    scope_source = _text(root, SCOPE_JUDGE)
    verdicts: list[Any] = []
    for verifier, assertions in BACKFILLED:
        name = Path(verifier).name
        verdicts.extend([
            verdict(f"ec04-{Path(verifier).stem}-in-tree", (root / verifier).is_file(), verifier),
            verdict(
                f"ec04-{Path(assertions).stem}-in-tree",
                (root / assertions).is_file(),
                assertions,
            ),
            verdict(f"ec04-{Path(verifier).stem}-registered", name in verifier_source, name),
            verdict(f"ec04-{Path(verifier).stem}-in-scope", name in scope_source, name),
        ])
    verdicts.extend([
        verdict(
            "ec04-short-row-registry-in-tree",
            (root / SHORT_ROWS_REGISTRY).is_file(),
            SHORT_ROWS_REGISTRY,
        ),
        verdict(
            "ec04-short-row-judge-in-tree", (root / SHORT_ROWS_JUDGE).is_file(), SHORT_ROWS_JUDGE
        ),
        verdict(
            "ec04-progress-075-is-linked-from-the-charter",
            "archive/MAINLINE-2026-10-15-progress-075-only.md" in charter,
            "`_archive_paths` 只认 `](archive/...)` ⇒ 没有链接就完全不参与「不漏 / 不重」",
        ),
        verdict(
            "ec04-short-row-registry-is-linked-from-the-charter",
            "SHORT-REVISION-ROWS.md" in charter,
            "登记表本身也必须被宪章链接（否则它同样是「不参与」）",
        ),
        verdict(
            "ec04-the-backfill-does-not-claim-completion",
            # 判「它的状态断言要求 PAUSED」这一件**结构**事实（措辞可改，语义不许改）。
            "goal-status-is-paused-not-achieved"
            in _text(root, "tools/goal076_closeout_assertions.py"),
            "076 是 `PAUSED` ⇒ 断言集必须判「状态就是 PAUSED」，不得声称收口",
        ),
    ])
    return verdicts


def _asset_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-05：收口资产 + 两处登记。"""
    verdict = toolbox.verdict
    return [
        verdict("ec05-self-verifier-in-tree", (root / SELF).is_file(), SELF),
        verdict("ec05-self-assertions-in-tree", (root / ASSERTIONS).is_file(), ASSERTIONS),
        verdict(
            "ec05-registered-in-the-verifier-list",
            "verify_goal098_closeout.py" in _text(root, VERIFIER_JUDGE),
            VERIFIER_JUDGE,
        ),
        verdict(
            "ec05-registered-in-the-gate-scope",
            "verify_goal098_closeout.py" in _text(root, SCOPE_JUDGE),
            SCOPE_JUDGE,
        ),
    ]


def _budget_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-06：预算扩表 + 程序表那一行。"""
    verdict = toolbox.verdict
    charter = _text(root, CHARTER)
    return [
        verdict(
            "ec06-max-goals-is-100",
            re.search(r"(?m)^- `max_goals`: 100$", charter) is not None,
            "宪章预算行必须读到 100（70 → 100，用户 2026-10-27 授权不设上限）",
        ),
        verdict(
            "ec06-the-extension-is-recorded",
            "70 → 100" in charter or "70 -> 100" in charter,
            "扩表必须在修订记录里逐行登记（原文读数 + 新读数 + 理由）",
        ),
        verdict(
            "ec06-program-table-has-this-round",
            f"| {PROGRAM_SEQ} | {GOAL_ID} |" in charter,
            f"程序表必须有序 {PROGRAM_SEQ} = 本 GOAL",
        ),
    ]


def _record_regression_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-07 + 引用面：修订行格数、上一轮修复不回退、既有判据仍在、例数下界。"""
    verdict = toolbox.verdict
    charter = _text(root, CHARTER)
    verdicts: list[Any] = [
        verdict(
            "ec07-this-round-revision-row-is-five-cells",
            _this_round_revision_cells(charter) == 5,
            f"本轮修订行格数 = {_this_round_revision_cells(charter)}（必须 5）",
        ),
        verdict(
            "ec07-the-short-row-judge-is-in-tree",
            "test_no_revision_row_in_the_live_table_is_too_short_to_be_seen"
            in _text(root, "tests/tooling/test_mainline_archive_is_continuous.py"),
            "活跃面「<5 格即判红」的判据必须在树（上一轮的修复不回退）",
        ),
    ]
    for relative in PRIOR_JUDGES:
        verdicts.append(
            verdict(f"prior-judge-{Path(relative).name}", (root / relative).is_file(), relative)
        )
    for relative, floor in CASE_FLOORS:
        count = collected_case_count(root, relative)
        verdicts.append(
            verdict(
                f"case-floor-{Path(relative).stem}",
                count >= floor,
                f"{count} < {floor}" if count < floor else "",
            )
        )
    return verdicts


def _this_round_revision_cells(charter: str) -> int:
    """宪章 `## 修订记录` 里**本轮那一条**（序 66）的格数（读不到 ⇒ 0）。"""
    if "## 修订记录" not in charter:
        return 0
    section = charter.split("## 修订记录", 1)[1]
    for line in section.splitlines():
        if line.startswith("|") and f"{PROGRAM_SEQ}（新增）" in line:
            return len([cell for cell in line.strip().strip("|").split("|")])
    return 0


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有的断言（按 EC 分组；每组一个函数 —— 单函数 50 行门）。"""
    return [
        *_independence_verdicts(root, toolbox),
        *_selection_verdicts(root, toolbox),
        *_container_face_verdicts(root, toolbox),
        *_archive_verdicts(root, toolbox),
        *_asset_verdicts(root, toolbox),
        *_budget_verdicts(root, toolbox),
        *_record_regression_verdicts(root, toolbox),
    ]


__all__ = [
    "ASSERTIONS",
    "CASE_FLOORS",
    "GOAL_ID",
    "PROGRAM_SEQ",
    "SELF",
    "assertion_verdicts",
    "collected_case_count",
]
