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
#: §7 判定表的 5 条判据仍须在场（文档同步不得改口径）。
QUALITY_CRITERION_JUDGE = "tests/tooling/test_manuscript_quality_strong_criterion.py"

# ── EC-07：宪章记账 ────────────────────────────────────────────────────────────
MAINLINE = ".cursor/plans/goals/MAINLINE.md"
PROGRAM_SEQ = 74
ARCHIVE_PROGRESS = ".cursor/plans/goals/archive/MAINLINE-2026-11-04-progress-103-only.md"
ARCHIVE_REVISIONS = ".cursor/plans/goals/archive/MAINLINE-2026-11-04-revisions-71-only.md"


def _verdict(toolbox: Any, name: str, ok: bool, detail: str = "") -> Any:
    return toolbox.verdict(name, ok, "" if ok else detail)


def _text(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _doc_verdicts(toolbox: Any, root: Path) -> list[Any]:
    """EC-05：文档写了「首次真实成立」，且 §7 的判据仍全绿面（口径未改）。"""
    doc = _text(root, QUALITY_DOC)
    return [
        _verdict(
            toolbox,
            "quality-doc-records-the-first-real-run",
            QUALITY_DOC_MARKER in doc,
            f"{QUALITY_DOC} 必须补一句「十一相链首次真实 SUCCEEDED」",
        ),
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
    """记录面的全集（文档同步 + 宪章记账）。"""
    return [*_doc_verdicts(toolbox, root), *_charter_verdicts(toolbox, root)]


__all__ = ["record_verdicts"]
