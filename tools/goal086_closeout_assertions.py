#!/usr/bin/env python3
"""GOAL-20261018-086 收口复检的**本轮特有断言集**（EC-05）。

与 GOAL-023…085 的断言集同形：公共面（受保护判据 / 规模门 / 产品根 / m0 条数 /
两树入口 / 规范页 / 记录自洽）**一行都不重写** —— 由
`tools/closeout_recheck_assertions.standard_verdicts` 承担；本文件**只写本 GOAL 特有的断言**。

三条主轴（逐条对应本 GOAL 的 EC）：

1. **EC-01 分组键换了**：`review_read._panel_rows` 按**被评对象**（`"PHASE", str(phase_id)`）
   聚合；旧的任务口径**逐字保留**为第二档（`"TASK", str(scoped.task_id)`）——
   两条**都必须在位**（只认一条会让另一条被悄悄删掉）。
2. **EC-02 被评对象落库**：`ScopedReviewFinding` 带 `phase_id`；落库链**搬运**它；
   sqlite 有该列 + 增量 `ALTER`；PG 的 `_SELECT`/insert 都有；迁移 `029` 在树；
   读面每行露出 `phase_id` 与每组的 `scope`。
3. **EC-03/EC-04 成对用例**：运行链判据（同 phase 聚合 / 同模型按压 / 不同 phase 不聚合）
   与读面判据（射程可读 / 旧行不并组）都在树，例数下界逐条钉住。

**判据规则**（承 GOAL-027…085）：一律判**关系**；判词名**按序号或语义**；
判词行**不含绝对路径**。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: 本轮**新增**的判据文件 → 例数**下界**（掉下去即判红；只上调不下调）。
CASE_FLOORS: tuple[tuple[str, int], ...] = (
    ("tests/e2e/test_reviewers_on_one_phase_form_a_panel.py", 3),
    ("tests/e2e/test_review_panel_on_the_run_path.py", 8),
    ("tests/contracts/test_review_finding_store_contracts.py", 5),
)

#: 本轮**引用**（而非重复）的既有判据 —— 必须仍在树。
PRIOR_JUDGES: tuple[str, ...] = (
    "tests/tooling/test_python_source_limits.py",
    "tools/verify_goal085_closeout.py",
    "tests/application/test_review_panel_aggregation.py",
)

#: 落点常量（逐条点名；缺一即判红）。
PORT = "packages/application/ports/review_finding_store.py"
OBSERVATION = "packages/application/run_orchestration/acceptance_observation.py"
READ_FACE = "adapters/canonical/review_read.py"
SQLITE = "adapters/sqlite/review_finding_store.py"
POSTGRES = "adapters/postgres/review_finding_store.py"
MIGRATION = "adapters/postgres/migrations/029_review_finding_phase_id.sql"
RUN_PATH_TEST = "tests/e2e/test_reviewers_on_one_phase_form_a_panel.py"
READ_FACE_TEST = "tests/e2e/test_review_panel_on_the_run_path.py"
STORE_TEST = "tests/contracts/test_review_finding_store_contracts.py"

#: EC-01 的形态：两档分组键（**都必须**在位）。
GROUP_BY_PHASE = '("PHASE", str(phase_id), str(scoped.contract_id))'
GROUP_BY_TASK = '("TASK", str(scoped.task_id), str(scoped.contract_id))'
#: 分组前**先**判档位（`if phase_id` 成立才走 PHASE）—— 不是靠 id 形态猜。
PHASE_GATE = "if phase_id"

#: EC-02 的形态（端口 + 落库链 + 两适配器 + 迁移 + 读面）。
PORT_FIELD = "phase_id: str | None = None"
OBSERVATION_PASSES = 'getattr(tctx.spec_context, "phase_id", None)'
OBSERVATION_EMPTY_IS_ABSENT = "phase_id=(phase_id or None),"
SQLITE_COLUMN = "phase_id TEXT"
SQLITE_ALTER = "ADD COLUMN phase_id TEXT"
POSTGRES_READS = "reviewer_model, phase_id FROM review_findings"
POSTGRES_WRITES = "reviewer_model,"
MIGRATION_LINE = "ADD COLUMN IF NOT EXISTS phase_id TEXT"
READ_FACE_FIELD = '"phase_id": getattr(scoped, "phase_id", None),'
READ_FACE_SCOPE = '"scope": scope,'

#: EC-03 / EC-04 的成对用例（逐条点名）。
PAIR_CASES: tuple[tuple[str, str], ...] = (
    (RUN_PATH_TEST, "test_two_reviewers_on_one_phase_form_one_panel"),
    (RUN_PATH_TEST, "test_pressing_the_second_reviewer_to_the_first_model_flips_independence"),
    (RUN_PATH_TEST, "test_reviewers_on_different_phases_do_not_share_a_panel"),
    (READ_FACE_TEST, "test_the_panel_names_the_scope_it_grouped_by"),
    (READ_FACE_TEST, "test_a_phase_panel_does_not_absorb_a_record_without_a_phase"),
    (READ_FACE_TEST, "test_a_single_review_produces_no_panel"),
    (READ_FACE_TEST, "test_panels_never_mix_two_tasks"),
    (STORE_TEST, "test_the_reviewed_object_survives_reopen"),
    (STORE_TEST, "test_an_existing_database_gains_the_phase_column"),
)

TEST_DEFINITION = re.compile(r"(?m)^\s*def test_")


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def collected_case_count(root: Path, relative: str) -> int:
    """模块的**真实用例条数**（正则按 `def test_`；本轮的判据文件不用 parametrize）。"""
    return len(TEST_DEFINITION.findall(_text(root, relative)))


def _grouping_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-01：分组键是**被评对象**，且旧口径**逐字保留**为第二档。"""
    verdict = toolbox.verdict
    read_face = _text(root, READ_FACE)
    return [
        verdict(
            "panels-group-by-the-reviewed-phase",
            GROUP_BY_PHASE in read_face,
            GROUP_BY_PHASE,
        ),
        verdict(
            "panels-keep-the-legacy-task-scope",
            GROUP_BY_TASK in read_face,
            GROUP_BY_TASK,
        ),
        verdict(
            "the-phase-scope-is-gated-by-its-presence",
            PHASE_GATE in read_face,
            PHASE_GATE,
        ),
        verdict(
            "the-cache-key-carries-the-scope",
            "groups: dict[tuple[str, str, str], list[Any]]" in read_face,
            "groups: dict[tuple[str, str, str], list[Any]]",
        ),
    ]


def _storage_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """EC-02：被评对象**落库**（端口 + 搬运 + 两适配器 + 迁移 + 读面）。"""
    verdict = toolbox.verdict
    return [
        verdict("port-carries-the-phase", PORT_FIELD in _text(root, PORT), PORT_FIELD),
        verdict(
            "record-chain-transports-the-phase",
            OBSERVATION_PASSES in _text(root, OBSERVATION),
            OBSERVATION_PASSES,
        ),
        verdict(
            "empty-phase-is-absent-not-blank",
            OBSERVATION_EMPTY_IS_ABSENT in _text(root, OBSERVATION),
            OBSERVATION_EMPTY_IS_ABSENT,
        ),
        verdict("sqlite-table-has-the-column", SQLITE_COLUMN in _text(root, SQLITE), SQLITE_COLUMN),
        verdict(
            "sqlite-alters-an-existing-table",
            SQLITE_ALTER in _text(root, SQLITE),
            SQLITE_ALTER,
        ),
        verdict(
            "postgres-reads-the-column",
            POSTGRES_READS in _text(root, POSTGRES),
            POSTGRES_READS,
        ),
        verdict(
            "postgres-writes-the-column",
            POSTGRES_WRITES in _text(root, POSTGRES),
            POSTGRES_WRITES,
        ),
        verdict(
            "migration-is-in-tree",
            MIGRATION_LINE in _text(root, MIGRATION),
            MIGRATION_LINE,
        ),
        verdict(
            "read-face-exposes-the-phase",
            READ_FACE_FIELD in _text(root, READ_FACE),
            READ_FACE_FIELD,
        ),
        verdict(
            "read-face-names-the-scope", READ_FACE_SCOPE in _text(root, READ_FACE), READ_FACE_SCOPE
        ),
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
        *_grouping_verdicts(root, toolbox),
        *_storage_verdicts(root, toolbox),
        *_case_verdicts(root, toolbox),
    ]


__all__ = [
    "CASE_FLOORS",
    "PAIR_CASES",
    "assertion_verdicts",
    "collected_case_count",
]
