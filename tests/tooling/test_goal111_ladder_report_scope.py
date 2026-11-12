"""GOAL-20261111-111 EC-04：阶梯改写——**只动「报告」一行，其余六行逐字不动**。

与 `test_goal109_ladder_pilot_scope.py`（只动计划）/ `test_goal110_ladder_evidence_scope.py`
（只动证据）同一条纪律的第三个用例。三轮合起来是「逐格推进」的三点证据：
如果有人把「判词可反驳」也写进检索 / 复检 / 迭代，三个锚点判据都会红。

**判两件**：

1. 「报告」行的 `下一级` 含本轮的新 bar（judgeable / `panel_grounding` / 降级），
   且旧 bar 的**射程声明**仍在（「这段写得好不好仍无判据」——本轮**不**消灭它，
   只把它说得更精确）；
2. 其余六行**逐字保持**各自的锚点，且**不含**本轮的短锚。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHARTER = ROOT / ".cursor" / "plans" / "goals" / "MAINLINE.md"

#: 「报告」行新 bar 的必要锚（缺一即没改到位）。
REPORT_NEW_MARKERS: tuple[str, ...] = (
    "面板判词本身可被反驳",
    "panel_grounding.py",
    "降级",
)
#: 旧射程声明必须**仍在**（本轮不消灭它）：
REPORT_KEPT_MARKER = "这段写得好不好"
#: 本轮的短锚（出现在其余六行 ⇒ 越级推广，判红）。
GROUNDING_MARKER = "面板判词本身可被反驳"

#: 其余六行的既有锚点（逐字保持；取自 2026-11-12 改写后实测）。
UNCHANGED_ROWS: dict[str, tuple[str, ...]] = {
    "检索": ("检索改变下一轮问题",),
    "计划": ("配对消融下", "输出读数分布发生位移"),
    "复检": ("评审者与作者分开",),
    "证据": ("处置闭环成立（策略闭集 + 可判依据）",),
    "实验": ("脚本也从计划里选",),
    "迭代": ("迭代改变下一轮问题",),
}


def _next_level(prefix: str) -> str:
    row = next(
        line for line in CHARTER.read_text(encoding="utf-8").splitlines() if line.startswith(prefix)
    )
    cells = row.split("|")
    assert len(cells) == 6, f"{prefix} 行不是 5 格：{len(cells) - 2}"
    return cells[4].strip()


def test_the_report_row_carries_the_new_bar() -> None:
    level = _next_level("| 报告 |")
    missing = [marker for marker in REPORT_NEW_MARKERS if marker not in level]
    assert not missing, f"报告行缺新 bar 锚点：{missing}"


def test_the_old_scope_statement_survives() -> None:
    """「这段写得好不好仍无判据」**仍在**——本轮把 bar 说得更精确，不是宣称它消失了。"""
    assert REPORT_KEPT_MARKER in _next_level("| 报告 |")


def test_the_report_row_records_its_goal() -> None:
    row = next(
        line
        for line in CHARTER.read_text(encoding="utf-8").splitlines()
        if line.startswith("| 报告 |")
    )
    assert "GOAL-20261111-111" in row


class TestTheOtherSixRowsAreUntouched:
    def test_each_row_keeps_its_own_bar(self) -> None:
        for prefix, markers in UNCHANGED_ROWS.items():
            level = _next_level(f"| {prefix} |")
            missing = [marker for marker in markers if marker not in level]
            assert not missing, f"{prefix} 行的旧 bar 被动了：{missing}"

    def test_no_row_was_promoted_to_the_grounding_bar(self) -> None:
        for prefix in UNCHANGED_ROWS:
            level = _next_level(f"| {prefix} |")
            assert GROUNDING_MARKER not in level, f"{prefix} 行被越级推广了"
