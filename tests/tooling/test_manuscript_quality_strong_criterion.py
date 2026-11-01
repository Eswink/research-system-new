"""`MANUSCRIPT_QUALITY.md` §7「强口径判定」的**结构判据**（GOAL-20261101-103 EC-05）。

**它封住的失败形态**：一份"论证"文档最容易的腐化是**变成散文** —— 五项的结论被写成
"大部分只能人评"，既不逐项、也不可核对；或者写着写着把某项从 `NOT_JUDGED` 里悄悄删掉
（那样 `test_the_quality_module_declares_what_it_does_not_judge` 仍绿，而它的**内容**
已经变了）。

四条判据（缺一即判红）：

1. §7 小节在树，且**先于**任何后续小节（它的位置本身是"这是最后一段论证"的声明）；
2. `NOT_JUDGED` 的**每一项**都在 §7 的表格里逐字出现（五项全覆盖，不许合并成一句）；
3. 每一项的判定 ∈ **闭集** `{可机械判, 只能人评}`（含弱口径说明的写法），
   且表格是 5 行判据（不是一张随手写的清单）；
4. **本轮不实现**这件事本身可核：`manuscript_quality.NOT_JUDGED` 仍是五项
   （§7 是论证，不是新判据 —— 实现了就必须同轮从该常量移出并改判据）。
"""

from __future__ import annotations

from pathlib import Path

from packages.application.deliverable.manuscript_quality import NOT_JUDGED

_ROOT = Path(__file__).resolve().parents[2]
_DOC = _ROOT / "docs" / "architecture" / "MANUSCRIPT_QUALITY.md"
_SECTION = "## 7. 强口径判定"

#: 判定词的**闭集**（含弱口径前缀）。写在这里而不是从文档里读 —— 否则文档改词即判据改。
_VERDICTS = ("可机械判", "只能人评")


def _section_text() -> str:
    text = _DOC.read_bytes().decode("utf-8")
    assert _SECTION in text, "§7 必须在树（GOAL-103 EC-05 的交付物）"
    return text[text.index(_SECTION) :]


def test_the_section_exists_and_is_the_last_one() -> None:
    """§7 在树，且其后**没有**新的一级小节（位置 = 「这是最后一段论证」）。"""
    section = _section_text()
    later = [
        line
        for line in section.splitlines()[1:]
        if line.startswith("## ") and not line.startswith("### ")
    ]
    assert later == [], f"§7 之后不应再有 ## 小节（它是最末一段论证）: {later}"


def test_every_not_judged_item_appears_verbatim_in_the_table() -> None:
    """`NOT_JUDGED` 的**每一项**逐字出现在 §7 里（合并成一句即判红）。"""
    section = _section_text()
    missing = [item for item in NOT_JUDGED if item not in section]
    assert missing == [], (
        "§7 必须逐项覆盖 `NOT_JUDGED`（不许合并成一句）",
        missing,
    )


def test_the_table_has_one_verdict_row_per_item() -> None:
    """每一项一行，且每行的判定词落在闭集里（`可机械判` / `只能人评`）。"""
    section = _section_text()
    rows = [
        line
        for line in section.splitlines()
        if line.startswith("| ") and not line.startswith("| # ") and not line.startswith("| --- ")
    ]
    assert len(rows) == len(NOT_JUDGED), (
        f"§7 的表格应当恰有 {len(NOT_JUDGED)} 行（每项一行），实测 {len(rows)}",
        rows,
    )
    for row in rows:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        assert any(verdict in cells[2] for verdict in _VERDICTS), (
            "每行的判定必须落在闭集内（可机械判 / 只能人评）",
            cells[:3],
        )


def test_nothing_was_implemented_under_the_cover_of_the_argument() -> None:
    """**本轮不实现**：`NOT_JUDGED` 仍是五项 —— §7 是论证，不是新判据上线。

    若将来真的实现了某一项，本条会红 —— 那时正确的做法是：把那一项从 `NOT_JUDGED`
    移到 §2、同轮改 `test_the_quality_module_declares_what_it_does_not_judge`，
    并**在本文件**同步行数。这正是"论证不等于实现"这条纪律的机械形态。
    """
    assert len(NOT_JUDGED) == 5, (
        "本轮只做论证：`NOT_JUDGED` 必须仍是五项（实现了就要同轮移出并改判据）",
        NOT_JUDGED,
    )


def test_the_argument_names_its_own_evidence_criteria() -> None:
    """论证给出**可核对的依据**（P1…P4），而不是一句"我们认为"。

    为什么要判这个：§7 的价值全在"可机械判"有一个**定义**。没有依据清单，
    「可机械判/只能人评」就只是两种说法。
    """
    section = _section_text()
    for criterion in ("P1 确定性", "P2 反证可写", "P3 不需要外部知识", "P4 不冒充语义"):
        assert criterion in section, f"§7 必须给出依据 {criterion} 的定义"
