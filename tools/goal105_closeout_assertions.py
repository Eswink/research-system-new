"""GOAL-20261103-105 的产品面断言集（收口复检的**本轮特有**部分）。

公共面（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 / 规范页 / 记录自洽）一行都
不重写 —— 由 `tools/closeout_recheck_assertions.standard_verdicts` 给；本文件只判
**本轮七条 EC 的交付**在树上的事实。

**每一组都钉两侧**（本轮三件交付各有「实现存在」与「不冒充」两面）：
- 读数存在 **与** 阈值仍留 `None`（有读数 ≠ 判了「充分」）；
- 缺陷修好 **与** 「未声明」是一等事实（不是又叠了一层覆盖）；
- 重叠判据存在 **与** 空真会点名（不是静默通过）。

**判词不绑定树的绝对路径**（两树入口会正确地拒绝这种输出）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ── EC-01 / EC-02：引用充分性的结构读数 + 脚注透出 ────────────────────────────────

READINGS_MODULE = "packages/application/deliverable/citation_sufficiency.py"
READINGS_MARKERS: tuple[str, ...] = (
    # 三个读数各自的函数名（合约名，改它要同轮改本文件与文档）。
    "def mark_counts_per_sentence(",
    "def citations_per_reference(",
    "def single_support_sections(",
    "def measure_citation_sufficiency(",
    # 三个阈值常量必须在（值另判）。
    "MIN_MARKS_PER_SENTENCE",
    "MIN_CITATIONS_PER_REFERENCE",
    "MIN_SUPPORT_PER_SECTION",
    "CALIBRATION_SOURCES",
    # 复用的切分器与引用语法（不写第三份）。
    "from packages.application.deliverable.manuscript_quality import _SENTENCE_SPLIT",
    "_CITATION = re.compile",
)
#: 三个常量**必须是 `None`**（仓内零真实语料 ⇒ 不许拍阈值）。
THRESHOLD_ASSIGNMENTS: tuple[str, ...] = (
    "MIN_MARKS_PER_SENTENCE: int | None = None",
    "MIN_CITATIONS_PER_REFERENCE: int | None = None",
    "MIN_SUPPORT_PER_SECTION: int | None = None",
)
#: 读数**不得**改变 `NOT_JUDGED`（五项逐字）。
NOT_JUDGED_FILE = "packages/application/deliverable/manuscript_quality.py"
NOT_JUDGED_COUNT_MARKER = "NOT_JUDGED: tuple[str, ...] = ("
#: 脚注透出（EC-02）。
FOOTNOTE_FILE = "packages/application/deliverable/manuscript.py"
FOOTNOTE_MARKERS: tuple[str, ...] = (
    "def _citation_readings_line(",
    "Citation distribution (readings, not a judgement)",
    "whether the citation set is **sufficient** is not decided here",
)
#: EC-01 / EC-02 的判据文件与它们必须带的断言（反证臂的存在是判据的一部分）。
READINGS_JUDGE = "tests/application/test_citation_sufficiency.py"
READINGS_JUDGE_MARKERS: tuple[str, ...] = (
    "def test_the_three_readings_match_their_expected_values(",
    "def test_adding_one_citation_moves_both_readings(",
    "def test_a_body_with_no_marks_is_not_an_error_when_not_enforcing(",
    "def test_all_three_thresholds_are_none_by_default(",
    "def test_a_threshold_without_a_calibration_source_is_named(",
)
FOOTNOTE_JUDGE = "tests/application/test_manuscript_citation_readings.py"
FOOTNOTE_JUDGE_MARKERS: tuple[str, ...] = (
    "def test_the_footnote_numbers_equal_the_function_return_values(",
    "def test_changing_the_body_moves_the_footnote_numbers(",
)

# ── EC-03：retmax 缺省抹平 + 协议相级 ────────────────────────────────────────────

CATALOG_FILE = "packages/application/ports/resource_catalog.py"
CATALOG_MARKERS: tuple[str, ...] = (
    "if raw is None:\n        return None",
    "_retmax_of(project_id: str, raw: object) -> int | None:",
)
#: 字段缺省必须是 `None`（不是 3 —— 那是被修掉的缺陷）。
CATALOG_FIELD = "    retmax: int | None = None"
#: 协议相级的三处搬运 + schema。
PROTOCOL_FIELD_FILES: dict[str, tuple[str, ...]] = {
    "packages/domain/protocols.py": ("run_chain_arguments: dict[str, object] | None = None",),
    "packages/application/protocol_compile/compiler.py": (
        "run_chain_arguments=phases[phase_id].run_chain_arguments,",
    ),
    "packages/application/run_orchestration/task_executor.py": (
        "run_chain_arguments: dict[str, object] | None = None",
    ),
    "packages/application/run_orchestration/session_resolution.py": (
        "run_chain_arguments=phase.run_chain_arguments,",
    ),
    "adapters/contracts/protocol_loaders.py": (
        'run_chain_arguments=_run_chain_arguments(raw.get("run_chain_arguments"))',
    ),
}
SCHEMA_FILE = "schemas/protocol.schema.json"
SCHEMA_KEY = "run_chain_arguments"
#: 取值顺序的**唯一**实现点（协议 > 项目；都未声明 ⇒ None）。
PRECEDENCE_FILE = "packages/application/run_orchestration/phase_call_arguments.py"
PRECEDENCE_MARKERS: tuple[str, ...] = (
    "def declared_retmax(",
    "def retmax_for_phase(",
    'getattr(deps, "retmax", None)',
)
#: EC-03 的两组判据。
RETMAX_JUDGES: dict[str, tuple[str, ...]] = {
    "tests/application/test_retmax_undeclared_is_a_fact.py": (
        "def test_the_environment_survives_an_undeclared_project_at_runtime(",
        "def test_an_explicit_argument_survives_an_undeclared_project_at_runtime(",
        "def test_a_declared_project_still_beats_the_environment_at_runtime(",
        "def test_the_undeclared_path_does_not_even_allocate_a_new_deps(",
    ),
    "tests/application/test_retmax_protocol_phase.py": (
        "def test_a_protocol_phase_value_reaches_the_outgoing_request(",
        "def test_without_a_phase_value_the_project_declaration_still_applies(",
        "def test_the_environment_survives_when_the_protocol_says_nothing(",
        "def test_an_illegal_phase_value_is_named_as_a_protocol_phase_value(",
        "def test_the_protocol_phase_count_is_unchanged(",
    ),
}
#: 十一相（**本轮不许改相集**）。
PHASES: tuple[str, ...] = (
    "question",
    "retrieval",
    "novelty",
    "plan",
    "experiment",
    "review",
    "manuscript",
    "editorial",
    "revision",
    "submission",
    "report",
)

# ── EC-04：判词驱动的改稿 ────────────────────────────────────────────────────────

REVISION_FILE = "packages/application/run_orchestration/revision_assembly.py"
REVISION_MARKERS: tuple[str, ...] = (
    "def _require_overlap_with_its_point(",
    "points: tuple[Any, ...] | None = None,",
    "review_points_of_run(artifacts, ledger, run_id)",
    "no comparable content word",
    "this criterion proves 'not unrelated', never 'solved'",
)
REVISION_JUDGE = "tests/application/test_revision_review_points.py"
REVISION_JUDGE_MARKERS: tuple[str, ...] = (
    "def test_an_action_that_names_a_word_from_its_point_passes(",
    "def test_an_action_with_no_shared_word_names_the_point_id(",
    "def test_the_criterion_really_compares_words(",
    "def test_a_point_without_content_words_is_named_not_passed(",
)

# ── EC-05：文档同步（§6 补句；§7 表逐字不动） ─────────────────────────────────────

DOC = "docs/architecture/MANUSCRIPT_QUALITY.md"
DOC_MARKERS: tuple[str, ...] = (
    "citation_sufficiency.py",
    "充分性仍未判",
    "取值待 ≥3 份真实手稿的量分布",
)
#: §7 的关键行（**不得改动**：那是已钉的历史结论，有 5 条判据盯着）。
DOC_FROZEN: tuple[str, ...] = (
    "## 7. 强口径判定（GOAL-20261101-103 EC-05）",
    "| 4 | `whether the citation set is sufficient for each claim` | **可机械判（弱口径）** |",
    "**本轮不改变 `NOT_JUDGED` 的内容**",
)

# ── EC-07：宪章记账 ──────────────────────────────────────────────────────────────

CHARTER = ".cursor/plans/goals/MAINLINE.md"
PROGRAM_SEQ = 73
LADDER_GOAL = "GOAL-20261103-105"
#: 阶梯两行的推进格（措辞必须逐字在场）。
LADDER_STEP_MARKERS: tuple[str, ...] = (
    "引用充分性有结构读数",
    "改稿与评审点有可判连接",
)
#: 阶梯里**不得出现**的过度声称 —— 结构读数不是判据，词重叠不是「改对了」。
FORBIDDEN_LADDER_CLAIMS: tuple[str, ...] = (
    "叙述质量已判",
    "引用充分性已判",
    "充分性判据已实现",
    "判词改写了立题",
    "回应解决了那个问题",
)


def _text(root: Path, relative: str) -> str:
    path = root / relative
    return path.read_bytes().decode("utf-8") if path.is_file() else ""


def _verdict(toolbox: Any, name: str, ok: bool, detail: str = "") -> Any:
    return toolbox.verdict(name, ok, "" if ok else detail)


def _missing(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def _file_verdicts(toolbox: Any, root: Path, cases: dict[str, tuple[str, ...]]) -> list[Any]:
    """逐文件判「标记在场」（一个文件一组，缺谁点名谁）。"""
    verdicts: list[Any] = []
    for relative, markers in cases.items():
        path = toolbox.tree(root, relative)
        if not path.is_file():
            verdicts.append(
                _verdict(toolbox, f"present-{Path(relative).name}", False, f"{relative} 不在树")
            )
            continue
        missing = _missing(_text(root, relative), markers)
        verdicts.append(
            _verdict(toolbox, f"carries-{Path(relative).name}", not missing, ",".join(missing))
        )
    return verdicts


def _threshold_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """三个阈值**必须**留 `None`（不许拍阈值）+ `NOT_JUDGED` 五项逐字不动。"""
    source = _text(root, READINGS_MODULE)
    verdicts = [
        _verdict(
            toolbox,
            f"threshold-{marker.split(':')[0]}-is-none",
            marker in source,
            f"阈值必须留 None（仓内零真实语料）：{marker}",
        )
        for marker in THRESHOLD_ASSIGNMENTS
    ]
    not_judged = _text(root, NOT_JUDGED_FILE)
    start = not_judged.find("NOT_JUDGED: tuple[str, ...] = (")
    block = not_judged[start:] if start != -1 else ""
    end = block.find("\n)")
    entries = block[len(NOT_JUDGED_COUNT_MARKER) : end if end != -1 else len(block)]
    count = len([line for line in entries.splitlines() if line.strip().startswith('"')])
    verdicts.append(
        _verdict(
            toolbox,
            "not-judged-still-has-five-items",
            start != -1 and count == 5,
            f"NOT_JUDGED 必须仍是 5 项（第 4 项**仍留在里面**：有读数 ≠ 判了充分）；实测 {count}",
        )
    )
    verdicts.append(
        _verdict(
            toolbox,
            "not-judged-still-names-sufficiency",
            "whether the citation set is sufficient for each claim" in block,
            "第 4 项必须仍在 NOT_JUDGED 里（移出它 = 冒充）",
        )
    )
    return verdicts


def _catalog_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """`ProjectSettings.retmax` 的缺省必须是 `None`（缺陷的修复形态）。"""
    source = _text(root, CATALOG_FILE)
    return [
        _verdict(toolbox, "catalog-field-is-optional", CATALOG_FIELD in source, "缺省必须是 None"),
        _verdict(
            toolbox,
            "catalog-no-longer-defaults-to-three",
            "    retmax: int = 3" not in source,
            "缺省 3 是**被修掉的缺陷形态**，不许回来",
        ),
        _verdict(
            toolbox,
            "catalog-absent-key-is-undeclared",
            "def _retmax_of(project_id: str, raw: object) -> int | None:" in source
            and "    if raw is None:\n        return None" in source,
            "`_retmax_of` 缺省必须返回 None（未声明是一等事实）",
        ),
    ]


def _schema_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """schema 的 `$defs.phase` 必须真有该属性，且 `additionalProperties: false` 仍在。"""
    path = toolbox.tree(root, SCHEMA_FILE)
    if not path.is_file():
        return [_verdict(toolbox, "schema-present", False, f"{SCHEMA_FILE} 不在树")]
    data = json.loads(path.read_text(encoding="utf-8"))
    phase = data.get("$defs", {}).get("phase", {})
    return [
        _verdict(
            toolbox,
            "schema-phase-declares-run-chain-arguments",
            SCHEMA_KEY in phase.get("properties", {}),
            f"$defs.phase.properties 必须有 {SCHEMA_KEY}（否则加载期就被拒）",
        ),
        _verdict(
            toolbox,
            "schema-phase-still-closed",
            phase.get("additionalProperties") is False,
            "`additionalProperties: false` 不许被顺手放开",
        ),
    ]


def _phase_set_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """十一相相集**未改**（本轮只加字段、不加相）。"""
    judge = _text(root, "tests/application/test_retmax_protocol_phase.py")
    missing = [phase for phase in PHASES if f'"{phase}"' not in judge]
    return [
        _verdict(
            toolbox,
            "protocol-phase-set-pinned",
            "def test_the_protocol_phase_count_is_unchanged(" in judge and not missing,
            f"相集判据缺相：{missing}",
        )
    ]


def _ladder_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """阶梯：两处推进逐字在场；**不得**出现过度声称。"""
    charter = _text(root, CHARTER)
    rows = [line for line in charter.splitlines() if LADDER_GOAL in line and line.startswith("|")]
    joined = " ".join(rows)
    return [
        _verdict(
            toolbox,
            "ladder-records-this-goal",
            bool(rows),
            f"宪章必须收录 {LADDER_GOAL}",
        ),
        _verdict(
            toolbox,
            "ladder-names-the-two-steps",
            all(marker in joined for marker in LADDER_STEP_MARKERS),
            ",".join(marker for marker in LADDER_STEP_MARKERS if marker not in joined),
        ),
        _verdict(
            toolbox,
            "ladder-next-level-not-claimed",
            not any(claim in joined for claim in FORBIDDEN_LADDER_CLAIMS),
            "结构读数 ≠ 叙述质量已判；词重叠 ≠ 判词改写了立题"
            f"（禁词：{','.join(FORBIDDEN_LADDER_CLAIMS)}）",
        ),
        _verdict(
            toolbox,
            "program-table-has-this-round",
            f"| {PROGRAM_SEQ} | {LADDER_GOAL} |" in charter,
            f"宪章程序表必须有序 {PROGRAM_SEQ} = 本 GOAL 那一行",
        ),
    ]


def assertion_verdicts(root: Path, toolbox: Any) -> list[Any]:
    """本 GOAL 七条 EC 的产品面判据（记录面由 `verify_goal105_closeout.py` 另判）。"""
    verdicts: list[Any] = []
    verdicts.extend(
        _file_verdicts(
            toolbox,
            root,
            {
                READINGS_MODULE: READINGS_MARKERS,
                FOOTNOTE_FILE: FOOTNOTE_MARKERS,
                READINGS_JUDGE: READINGS_JUDGE_MARKERS,
                FOOTNOTE_JUDGE: FOOTNOTE_JUDGE_MARKERS,
                CATALOG_FILE: CATALOG_MARKERS,
                **PROTOCOL_FIELD_FILES,
                PRECEDENCE_FILE: PRECEDENCE_MARKERS,
                **RETMAX_JUDGES,
                REVISION_FILE: REVISION_MARKERS,
                REVISION_JUDGE: REVISION_JUDGE_MARKERS,
                DOC: DOC_MARKERS,
            },
        )
    )
    verdicts.extend(_threshold_verdicts(toolbox, root))
    verdicts.extend(_catalog_verdicts(toolbox, root))
    verdicts.extend(_schema_verdicts(toolbox, root))
    verdicts.extend(_phase_set_verdicts(toolbox, root))
    verdicts.extend(_ladder_verdicts(toolbox, root))
    doc = _text(root, DOC)
    verdicts.extend(
        _verdict(
            toolbox,
            f"doc-section-7-frozen-{index}",
            frozen in doc,
            f"§7 的历史结论逐字不动：{frozen[:40]}",
        )
        for index, frozen in enumerate(DOC_FROZEN)
    )
    return verdicts
