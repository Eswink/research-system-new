"""GOAL-20261104-106 的**记录面**断言集（EC-05 文档同步 + EC-07 宪章记账）。

**为什么单列**：`tools/` 的脚本也受 450 行 / 50 行函数双门约束，而主断言集
（`goal106_closeout_assertions.py`）装的是**产品面**（live 判据 / 真实 run 读数 /
GOAL-105 两件机制的读数 / 失败形态台账）。记录面（文档 + 宪章）与产品面是两类事实，
按面切分即满足规模门，又不把任何判据挪到射程外。

**两向都钉**：
- 文档**写了**「首次真实成立」**与** §7 判定表逐字未动（不得为了那句改口径）；
- 程序表**有序 74 的行**与两表归档**在树且被链接**（归档不得成为断链）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# ── EC-05：文档同步（§7 表逐字不动）────────────────────────────────────────────
QUALITY_DOC = "docs/architecture/MANUSCRIPT_QUALITY.md"
QUALITY_DOC_MARKER = "首次真实"
#: 完成声明的字面（未达成时文档里**不得**出现它）。
QUALITY_DOC_CLAIM = "首次真实 SUCCEEDED"
#: §7 判定表的 5 条判据仍须在场（文档同步不得改口径）。
QUALITY_CRITERION_JUDGE = "tests/tooling/test_manuscript_quality_strong_criterion.py"

# ── EC-07：宪章记账 ────────────────────────────────────────────────────────────
MAINLINE = ".cursor/plans/goals/MAINLINE.md"
PROGRAM_SEQ = 74
ARCHIVE_PROGRESS = ".cursor/plans/goals/archive/MAINLINE-2026-11-04-progress-103-only.md"
ARCHIVE_REVISIONS = ".cursor/plans/goals/archive/MAINLINE-2026-11-04-revisions-71-only.md"


def _verdict(toolbox: Any, name: str, ok: bool, detail: str = "") -> Any:
    return toolbox.verdict(name, ok, "" if ok else detail)


#: 真实 run 的读数文件（与产品面断言集同一个路径；只读它的终态）。
READINGS = ".cursor/plans/goals/evidence/GOAL-20261104-106-manuscript-chain-live.json"


def _run_succeeded(root: Path) -> bool:
    """真实 run 是否真的 `SUCCEEDED`（读那个读数文件；读不到 ⇒ `False`）。"""
    import json

    path = root / READINGS
    if not path.is_file():
        return False
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return False
    return isinstance(parsed, dict) and parsed.get("state") == "SUCCEEDED"


def _text(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


# ── EC-03：GOAL-105 两件机制在真实手稿上的读数 ──────────────────────────────────
#: 读数文件（与产品面断言集同一个路径）。
READINGS_EVIDENCE = ".cursor/plans/goals/evidence/GOAL-20261104-106-manuscript-chain-live.json"
#: GOAL 正文（EC 状态如实性判据要读它）。
GOAL_PATH = ".cursor/plans/goals/GOAL-20261104-106-the-manuscript-chain-runs-live.md"
#: 那三个读数键必须存在且为真（不是散文断言）。
CITATION_READING_KEYS: tuple[str, ...] = (
    "citation_readings",
    "readings_match_body",
    "action_overlap",
)


def _readings(root: Path) -> dict[str, Any] | None:
    """读数文件 → dict（缺失 / 不可解析 ⇒ `None`，由判词点名）。"""
    import json

    path = root / READINGS_EVIDENCE
    if not path.is_file():
        return None
    try:
        parsed: Any = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _goal_ec_status(root: Path, ec_id: str) -> str:
    """从 GOAL 正文取某 EC 的 `status:`（按 EC 块定位，不靠全局搜索）。"""
    goal = _text(root, GOAL_PATH)
    marker = f"  - id: {ec_id}\n"
    index = goal.find(marker)
    if index == -1:
        return "MISSING"
    tail = goal[index:]
    stop = tail.find("\n  - id: ")
    block = tail[: stop if stop != -1 else len(tail)]
    for line in block.splitlines():
        if line.strip().startswith("status:"):
            return line.split(":", 1)[1].strip()
    return "MISSING"


def _overlap_is_clean(overlap: Any) -> bool:
    """`action_overlap` 必须是 `[条数, 有效重叠条数]`、两数相等且 ≥1（单列守函数长度门）。"""
    return (
        isinstance(overlap, list)
        and len(overlap) == 2
        and isinstance(overlap[0], int)
        and isinstance(overlap[1], int)
        and overlap[0] >= 1
        and overlap[0] == overlap[1]
    )


def _goal105_reading_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """EC-03：GOAL-105 两件机制在**真实手稿**上的读数键在场且为真。

    **与 EC-02 同一条如实性纪律**（照 `goal076_closeout_assertions` 的形态）：这一组只在
    真实 run 真的产出过手稿时才要求那三个读数键。run 未达成时，判「读数缺失」是把
    「上游没让我们跑完」记成「资产坏了」—— 而 GOAL 的 `EC-03` 本来就是 `PENDING`，
    如实性由 `goal-ec03-agrees-with-the-run` 一条判（见下）。
    """
    readings = _readings(root)
    if readings is None:
        return [
            _verdict(
                toolbox,
                "goal105-readings-are-recorded",
                False,
                f"{READINGS_EVIDENCE} 缺失 ⇒ 无法证明任何一次真实 run",
            )
        ]
    produced_manuscript = readings.get("state") == "SUCCEEDED"
    ec03 = _goal_ec_status(root, "EC-03")
    agreement = _verdict(
        toolbox,
        "goal-ec03-agrees-with-the-run",
        (ec03 == "PASS") == produced_manuscript,
        f"GOAL 的 EC-03={ec03!r} 但真实 run 终态={readings.get('state')!r} —— 两者必须同向",
    )
    if not produced_manuscript:
        return [agreement]
    return [agreement, *_manuscript_reading_verdicts(toolbox, readings)]


def _manuscript_reading_verdicts(toolbox: Any, readings: dict[str, Any]) -> list[Any]:
    """三个读数键 + 脚注重算 + 应答重叠（单列守函数长度门）。"""
    verdicts = [
        _verdict(
            toolbox,
            f"goal105-reading-{key.replace('_', '-')}-is-recorded",
            readings.get(key) not in (None, [], {}, ""),
            f"读数键 {key!r} 缺失（不是空真：真实 run 必须产出它）",
        )
        for key in CITATION_READING_KEYS
    ]
    verdicts.append(
        _verdict(
            toolbox,
            "goal105-footnote-readings-match-the-body",
            readings.get("readings_match_body") is True,
            "脚注里的引用读数必须与从正文重算的结果相等",
        )
    )
    overlap = readings.get("action_overlap")
    # **空点表是合法状态**：产品在 `render_letter` 的空点表分支里写「review raised no points
    # to answer」，`validate_action_references` 的 docstring 同一条口径。那时逐条重叠
    # **没有对象** ⇒ 判「信如实说了没有点、且重叠读数为 [0, 0]」，而不是要求凭空重叠。
    no_points = readings.get("review_raised_no_points") is True
    verdicts.append(
        _verdict(
            toolbox,
            "goal105-every-action-overlaps-its-point",
            (overlap == [0, 0] if no_points else _overlap_is_clean(overlap)),
            (
                f"空点表时 action_overlap 必须是 [0, 0]（没有要回应的点），实际 {overlap!r}"
                if no_points
                else f"`action_overlap` 应为 [条数, 有效重叠条数] 且两数相等且 ≥1，实际 {overlap!r}"
            ),
        )
    )
    return verdicts


def _doc_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """EC-05：文档写了「首次真实成立」，且 §7 的判据仍全绿面（口径未改）。

    第一条**只在真实 run 达成后才要求**（如实性纪律，与 EC-02 / EC-03 同一条）：链还没跑通
    就要求文档写「已跑通」是**逼人伪造**。未达成时判的是「文档不得已经声称跑通」的**反面**——
    即 `docs-invents-nothing`：文档里不得出现「首次真实 SUCCEEDED / 首次真实成立」这类完成声明，
    因为那会是假的。两条互为反面，任何一侧被违反都判红。
    """
    doc = _text(root, QUALITY_DOC)
    produced = _run_succeeded(root)
    claims_done = QUALITY_DOC_CLAIM in doc
    first = (
        _verdict(
            toolbox,
            "quality-doc-records-the-first-real-run",
            QUALITY_DOC_MARKER in doc,
            f"{QUALITY_DOC} 必须补一句「十一相链首次真实 SUCCEEDED」",
        )
        if produced
        else _verdict(
            toolbox,
            "quality-doc-invents-no-completion",
            not claims_done,
            "真实 run 尚未达成 ⇒ 文档不得声称「首次真实 SUCCEEDED / 成立」（那是伪造）",
        )
    )
    return [
        first,
        _verdict(
            toolbox,
            "quality-doc-keeps-the-seven-section-table",
            "## 7." in doc or "§7" in doc,
            f"{QUALITY_DOC} 的 §7 判定表不得被删（不得为了这句改口径）",
        ),
        _verdict(
            toolbox,
            "quality-criterion-judge-is-in-tree",
            (root / QUALITY_CRITERION_JUDGE).is_file(),
            f"{QUALITY_CRITERION_JUDGE} 不在树 ⇒ §7 口径的既有判据消失",
        ),
    ]


def _charter_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """EC-07：程序表序 74 在场；两表归档文件在树且被宪章链接。"""
    charter = _text(root, ".cursor/plans/goals/MAINLINE.md")
    seq_row = f"| {PROGRAM_SEQ} |" in charter or f"| {PROGRAM_SEQ}（新增）" in charter
    verdicts = [
        _verdict(
            toolbox,
            "charter-program-table-records-sequence-74",
            seq_row,
            f"宪章程序表必须有序 {PROGRAM_SEQ} 的一行",
        ),
    ]
    for archive, label in (
        (ARCHIVE_PROGRESS, "progress"),
        (ARCHIVE_REVISIONS, "revisions"),
    ):
        name = Path(archive).name
        verdicts.append(
            _verdict(
                toolbox,
                f"charter-links-the-{label}-archive",
                name in charter,
                f"宪章必须链接 {name}",
            )
        )
        verdicts.append(
            _verdict(
                toolbox,
                f"{label}-archive-is-in-tree",
                (root / archive).is_file(),
                f"{archive} 不在树",
            )
        )
    return verdicts


def record_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """记录面的全集（EC-03 真实手稿读数 + 文档同步 + 宪章记账）。"""
    return [
        *_goal105_reading_verdicts(toolbox, root),
        *_doc_verdicts(toolbox, root),
        *_charter_verdicts(toolbox, root),
    ]


__all__ = ["record_verdicts"]
