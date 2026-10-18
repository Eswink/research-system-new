#!/usr/bin/env python3
"""GOAL-20261018-085 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…084 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件**只写本 GOAL 特有的断言**。

四条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01 归因**：`ReviewFinding.reviewer_model` 在域里；门的签名带 `reviewer_model`；
   运行链调用点**真的传了**（不是只有参数）；`review_attribution.reviewer_model_of`
   在树且取 `endpoint`/`model`；落库链搬运（`acceptance_observation` 里有 `reviewer_model=`）；
   两个存储适配器都写/读该列；迁移 `028` 在树。
2. **EC-02 聚合**：`panel_verdict.aggregate_panel` 在树；平票/无票/单评审三条边界在树
   （源码级）；**advisory 不夺真相权**（模块内不得出现 `Decision(` / `decided_by`）。
3. **EC-03 独立性**：目标形态 `endpoint/model_name` 在树；同目标判非独立的理由串在树；
   三条成对用例（异目标 / 同目标 / 按压翻转）在位。
4. **EC-04 产品路径**：`review_read` 读面新增 `reviewer_model` 与 `panels`；
   **单评审不聚合**（`panel_verdict` 里 `len(findings) < 2` 的早退在树）；读面分组键
   `(task_id, contract_id)` 在树。

**判据规则**（承 GOAL-027…084）：一律判**关系**；判词名**按序号**；判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/application/test_review_attribution.py", 10),
    ("tests/application/test_review_panel_aggregation.py", 13),
    ("tests/e2e/test_review_panel_on_the_run_path.py", 6),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal084_closeout.py",
    "tests/application/test_m4_heterogeneity.py",
)

#: 落点常量（逐条点名；缺一即判红）。
EVIDENCE_DOMAIN = "packages/domain/evidence.py"
GATE = "packages/application/run_orchestration/evaluation_gate.py"
HELPERS = "packages/application/run_orchestration/task_phase_helpers.py"
ATTRIBUTION = "packages/application/run_orchestration/review_attribution.py"
OBSERVATION = "packages/application/run_orchestration/acceptance_observation.py"
PANEL = "packages/application/evaluation/panel_verdict.py"
READ_FACE = "adapters/canonical/review_read.py"
SQLITE = "adapters/sqlite/review_finding_store.py"
POSTGRES = "adapters/postgres/review_finding_store.py"
MIGRATION = "adapters/postgres/migrations/028_review_finding_reviewer_model.sql"
ATTRIBUTION_TEST = "tests/application/test_review_attribution.py"
PANEL_TEST = "tests/application/test_review_panel_aggregation.py"
RUN_PATH_TEST = "tests/e2e/test_review_panel_on_the_run_path.py"

#: EC-01 的形态（逐条点名）。
DOMAIN_FIELD = "reviewer_model: str | None = None"
GATE_PARAM = "reviewer_model: str | None = None,"
HELPERS_PASSES = "reviewer_model=reviewer_model_of("
ATTRIBUTION_READS = 'getattr(endpoint, "id", None)'
ATTRIBUTION_MODEL = 'getattr(model, "model_name", None)'
OBSERVATION_PASSES = 'getattr(gate.review_finding, "reviewer_model", None)'
READ_FACE_FIELD = '"reviewer_model": finding.reviewer_model,'
SQLITE_COLUMN = "reviewer_model TEXT"
POSTGRES_COLUMN = "reviewer_model)"

#: EC-02 的形态。
PANEL_ENTRY = "def aggregate_panel("
PANEL_EARLY_EXIT = "if len(findings) < 2:"
PANEL_TIE = "return None"

#: EC-03 的形态（目标形态 + 同目标判非独立的理由串）。
TARGET_SHAPE = 'return f"{endpoint_id}/{model_name}"'
TARGET_REFUSAL = "if not endpoint_id or not model_name:"
SHARED_TARGET_NOTE = "share the same target"

#: EC-04 的形态（读面 + 分组键）。
READ_FACE_PANELS = '"panels": panels,'
READ_FACE_GROUPS = "groups.setdefault((str(scoped.task_id), str(scoped.contract_id))"

#: 本轮的三条成对用例（逐条点名）。
PAIR_CASES: tuple[tuple[str, str], ...] = (
    (PANEL_TEST, "test_distinct_targets_are_independent"),
    (PANEL_TEST, "test_the_same_target_twice_is_not_an_independent_panel"),
    (PANEL_TEST, "test_pointing_the_second_reviewer_back_flips_the_conclusion"),
    (PANEL_TEST, "test_a_single_review_is_not_aggregated"),
    (RUN_PATH_TEST, "test_a_single_review_produces_no_panel"),
    (RUN_PATH_TEST, "test_panels_never_mix_two_tasks"),
)

#: 聚合面**不得**出现的真相权痕迹。
TRUTH_OWNER_TRACES: tuple[str, ...] = ("Decision(", "decided_by")

TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def collected_case_count(root: Path, relative: str) -> int:
    """模块的**真实用例条数**（正则按 `def test_`；本轮的判据文件不用 parametrize）。"""
    return len(TEST_DEFINITION.findall(_text(root, relative)))


def _attribution_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：归因在域、门、运行链、落库链与两个存储上**都**在。"""
    verdict = toolbox.verdict
    return [
        verdict(
            "domain-carries-reviewer-model",
            DOMAIN_FIELD in _text(root, EVIDENCE_DOMAIN),
            DOMAIN_FIELD,
        ),
        verdict("gate-accepts-reviewer-model", GATE_PARAM in _text(root, GATE), GATE_PARAM),
        verdict(
            "run-chain-passes-the-reviewer-model",
            HELPERS_PASSES in _text(root, HELPERS),
            HELPERS_PASSES,
        ),
        verdict(
            "attribution-reads-the-endpoint-id",
            ATTRIBUTION_READS in _text(root, ATTRIBUTION),
            ATTRIBUTION_READS,
        ),
        verdict(
            "attribution-reads-the-model-name",
            ATTRIBUTION_MODEL in _text(root, ATTRIBUTION),
            ATTRIBUTION_MODEL,
        ),
        verdict(
            "attribution-refuses-half-a-target",
            TARGET_REFUSAL in _text(root, ATTRIBUTION),
            TARGET_REFUSAL,
        ),
        verdict(
            "record-chain-carries-the-attribution",
            OBSERVATION_PASSES in _text(root, OBSERVATION),
            OBSERVATION_PASSES,
        ),
        verdict(
            "read-face-exposes-the-reviewer-model",
            READ_FACE_FIELD in _text(root, READ_FACE),
            READ_FACE_FIELD,
        ),
        verdict(
            "sqlite-store-has-the-column", SQLITE_COLUMN in _text(root, SQLITE), SQLITE_COLUMN
        ),
        verdict(
            "postgres-store-has-the-column",
            POSTGRES_COLUMN in _text(root, POSTGRES),
            POSTGRES_COLUMN,
        ),
        verdict(
            "migration-is-in-tree",
            "ADD COLUMN IF NOT EXISTS reviewer_model" in _text(root, MIGRATION),
            MIGRATION,
        ),
    ]


def _panel_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02 / EC-03：聚合与独立性的形态（含**不夺真相权**的机械判据）。"""
    verdict = toolbox.verdict
    panel = _text(root, PANEL)
    traces = [token for token in TRUTH_OWNER_TRACES if token in panel]
    return [
        verdict("panel-entry-exists", PANEL_ENTRY in panel, PANEL_ENTRY),
        verdict("single-review-is-not-aggregated", PANEL_EARLY_EXIT in panel, PANEL_EARLY_EXIT),
        verdict("panel-does-not-take-truth-ownership", traces == [], ",".join(traces)),
        verdict("target-shape-is-endpoint-model", TARGET_SHAPE in panel, TARGET_SHAPE),
        verdict("shared-target-is-named", SHARED_TARGET_NOTE in panel, SHARED_TARGET_NOTE),
        verdict("read-face-exposes-panels", READ_FACE_PANELS in _text(root, READ_FACE)),
        verdict("panels-group-by-task-and-contract", READ_FACE_GROUPS in _text(root, READ_FACE)),
    ]


def _case_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """成对用例在位 + 例数下界（删掉任一条用例即判红）。"""
    verdict = toolbox.verdict
    verdicts: list[Any] = []
    for relative, name in PAIR_CASES:
        verdicts.append(
            verdict(f"case-{name}", f"def {name}(" in _text(root, relative), f"{relative}:{name}")
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
    for relative in PRIOR_JUDGES:
        verdicts.append(verdict(f"prior-judge-{Path(relative).name}", (root / relative).is_file()))
    return verdicts


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本轮特有的断言（逐条一个判词；按 EC 分组，每组一个函数）。"""
    return [
        *_attribution_verdicts(root, toolbox),
        *_panel_verdicts(root, toolbox),
        *_case_verdicts(root, toolbox),
    ]


__all__ = [
    "CASE_FLOORS",
    "assertion_verdicts",
    "collected_case_count",
]
