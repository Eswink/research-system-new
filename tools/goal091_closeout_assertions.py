#!/usr/bin/env python3
"""GOAL-20261020-091 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…090 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 /
规范页 / 记录自洽）**一行都不重写** —— 由 `tools/closeout_recheck_assertions.standard_verdicts`
承担；本文件**只写本 GOAL 特有的断言**。

三条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01 判词进判定面**：`evaluation_gate` 里 `declared_review_score` 的路径循环带
   `_unwrap_deliverable(...)`（信封形态）；解包**复用** `phase_input_material.declared_object`
   （不写第二份解析）；取不到仍 `review score unknown`（fail-closed 逐字不变）。
2. **EC-02 被评对象进提示词**：`review_material.py` 的四个公开面在位；`retrieval_prompt`
   有第四段渲染器 + `compose_prompt(review_material=…)`；**缝合线** `_section_of` 在位
   （`str` 原样用 —— 这一条是本轮实测出的既有缺陷的回归锚点）；两个组合根各接一行。
3. **EC-03/04 成对判据与真跑**：`dual_model_review_v1.yaml` 的 review 格 `min_instances: 2`
   + 契约的 `review_panel: COMPLETE_THEN_JUDGE`；e2e 判据与 live 判据在位；
   live 读数文件（判词全文）已在 RECHECK 里逐字抄录。

**判据规则**（承 GOAL-027…090）：一律判**关系**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/run_orchestration/test_review_score_reads_the_envelope.py", 4),
    ("tests/application/run_orchestration/test_review_material_in_prompt.py", 12),
    ("tests/e2e/test_two_models_judge_the_same_artifact.py", 4),
    ("tests/e2e/test_two_models_judge_the_same_artifact_live.py", 1),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/application/test_review_panel_aggregation.py",
    "tests/e2e/test_reviewers_on_one_phase_form_a_panel.py",
    "tests/e2e/test_a_rejecting_reviewer_does_not_cancel_the_panel.py",
    "tests/tooling/test_m0_witness_matches_the_tree.py",
)

#: 落点常量（逐条点名；缺一即判红）。
GATE = "packages/application/run_orchestration/evaluation_gate.py"
MATERIAL = "packages/application/run_orchestration/phase_input_material.py"
REVIEW_MATERIAL = "packages/application/run_orchestration/review_material.py"
PROMPT = "packages/application/run_orchestration/retrieval_prompt.py"
PROTOCOL = "examples/protocols/dual_model_review_v1.yaml"
CONTRACTS = "examples/contracts/task_contracts.yaml"
SQLITE_ROOT = "services/api/composition.py"
PG_ROOT = "services/api/pg_composition.py"
SUPPORT = "services/api/review_material_support.py"
WITNESS_TOOL = "tools/run_m0_with_witness.py"

#: 锚点（逐字；形态改了即判红 —— 逼作者回来改这里而不是让它静默漂）。
ENVELOPE_GUARD = 'if "declared_artifact" not in value or not isinstance(value.get("content"), str):'
UNWRAP_CALL = "_unwrap_deliverable(value, key=part)"
REVISION_SECTION = "REVIEW_MATERIAL_SECTION_TITLE"
SECTION_OF = "def _section_of(value: Any, render: Any) -> str:"
STRING_PASSTHROUGH = "if isinstance(value, str):"
CLI_FLAG = '"--verify-only"'
PANEL_KEY = "review_panel: COMPLETE_THEN_JUDGE"
TWO_INSTANCES = "min_instances: 2, max_instances: 2"

_CASE_DEF = re.compile(r"^def test_", re.MULTILINE)


def _count_cases(text: str) -> int:
    return len(_CASE_DEF.findall(text))


def _has(root: Path, relative: str, needle: str) -> bool:
    path = root / relative
    if not path.is_file():
        return False
    return needle in path.read_text(encoding="utf-8")


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 特有的断言（判关系；判词不含绝对路径）。"""
    verdicts: list[Any] = []

    # ---- EC-01：信封形态的取值面 ----
    verdicts.append(
        toolbox.verdict(
            "review-score-unwraps-the-deliverable-envelope",
            _has(root, GATE, ENVELOPE_GUARD) and _has(root, GATE, UNWRAP_CALL),
            "`declared_review_score` 必须在路径每段上解信封（否则真实会话恒 `review score unknown`）",
        )
    )
    verdicts.append(
        toolbox.verdict(
            "envelope-unwrap-reuses-the-existing-parser",
            _has(root, GATE, "from packages.application.run_orchestration.phase_input_material import")
            and _has(root, GATE, "declared_object"),
            "解包必须复用 `declared_object`（两处各写一份解析必然漂）",
        )
    )
    verdicts.append(
        toolbox.verdict(
            "review-score-stays-fail-closed",
            _has(root, GATE, '"review score unknown"') or _has(root, "packages/domain/acceptance.py", "review score unknown"),
            "解不出来必须仍报 `review score unknown`（不得回落默认分）",
        )
    )
    verdicts.append(
        toolbox.verdict(
            "phase-input-material-format-bug-is-gone",
            not _has(root, MATERIAL, "{'{key}': { {...} }}"),
            "`declared_object` 的 fail-closed 分支不得再用嵌套花括号当格式说明符（会自己抛 ValueError）",
        )
    )

    # ---- EC-02：被评对象进提示词 ----
    for name in (
        "def build_review_material(",
        "def is_reviewer(",
        "def with_review_material(",
        "class ReviewMaterialEntry",
        "class ReviewMaterialView",
    ):
        verdicts.append(
            toolbox.verdict(
                f"review-material-{name.split('(')[0].split()[-1]}",
                _has(root, REVIEW_MATERIAL, name),
                f"`review_material.py` 缺 `{name}`",
            )
        )
    verdicts.append(
        toolbox.verdict(
            "prompt-has-a-fourth-section",
            _has(root, PROMPT, REVISION_SECTION),
            "`retrieval_prompt` 必须有被评对象那一段的标题常量",
        )
    )
    verdicts.append(
        toolbox.verdict(
            "compose-prompt-takes-the-fourth-slot",
            _has(root, PROMPT, "review_material: Any = None,"),
            "`compose_prompt` 必须接受 `review_material=`（并列、不替换既有三段）",
        )
    )
    verdicts.append(
        toolbox.verdict(
            "rendered-strings-pass-through-the-composer",
            _has(root, PROMPT, SECTION_OF) and _has(root, PROMPT, STRING_PASSTHROUGH),
            "`_section_of` 必须在位：`SessionBuilder` 提交的是**已渲染的 str**，只按视图渲染会把段静默丢掉",
        )
    )
    for relative in (SQLITE_ROOT, PG_ROOT):
        verdicts.append(
            toolbox.verdict(
                f"composition-wires-the-review-material-{Path(relative).stem}",
                _has(root, relative, "review_material=review_material_builder("),
                f"{relative} 必须接上被评对象装配器（只有 REVIEWER 会挂）",
            )
        )
    verdicts.append(
        toolbox.verdict(
            "review-material-support-is-a-thin-closure",
            _has(root, SUPPORT, "def review_material_builder("),
            "装配面闭包必须在 `services/api/review_material_support.py`",
        )
    )

    # ---- EC-03/04：协议、契约、真跑 ----
    verdicts.append(
        toolbox.verdict(
            "protocol-declares-two-reviewers",
            _has(root, PROTOCOL, TWO_INSTANCES),
            "评审格必须有**两位**评审者（否则面板无从成立）",
        )
    )
    verdicts.append(
        toolbox.verdict(
            "protocol-feeds-the-upstream-artifact-to-the-reviewers",
            _has(root, PROTOCOL, "inputs: [author:research_plan]"),
            "评审格必须声明跨相输入（被评对象只能是上游产物）",
        )
    )
    verdicts.append(
        toolbox.verdict(
            "review-contract-completes-the-panel-before-judging",
            _has(root, CONTRACTS, PANEL_KEY),
            "评审契约必须声明 `review_panel: COMPLETE_THEN_JUDGE`（一位判负不取消同批）",
        )
    )

    # ---- 判据文件的例数下界 ----
    for relative, floor in CASE_FLOORS:
        path = root / relative
        count = _count_cases(path.read_text(encoding="utf-8")) if path.is_file() else 0
        verdicts.append(
            toolbox.verdict(
                f"cases-{Path(relative).stem}", count >= floor, f"{count} < {floor}（例数掉下去了）"
            )
        )
    for relative in PRIOR_JUDGES:
        verdicts.append(
            toolbox.verdict(f"prior-judge-{Path(relative).stem}", (root / relative).is_file())
        )

    # ---- EC-06：见证的只读面 ----
    verdicts.append(
        toolbox.verdict(
            "witness-tool-has-verify-only",
            _has(root, WITNESS_TOOL, CLI_FLAG),
            "见证工具必须有 `--verify-only`（纯读、三态退出码）",
        )
    )
    verdicts.append(
        toolbox.verdict(
            "verify-only-does-not-write-the-witness",
            _has(root, WITNESS_TOOL, "def verify_only() -> int:") and _has(root, WITNESS_TOOL, "_rows("),
            "`verify_only` 必须只读（不得写见证）——写它会改变它所描述的对象",
        )
    )
    return verdicts


__all__ = ["CASE_FLOORS", "PRIOR_JUDGES", "assertion_verdicts"]
