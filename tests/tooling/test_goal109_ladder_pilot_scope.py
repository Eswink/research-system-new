"""GOAL-20261111-109 EC-06：阶梯改写——**只动「计划」一格，其余三格逐字不动**。

**为什么单列**：宪章的阶梯行是全仓**最容易被顺手推广**的面——「一格的证据」被写成
「四格都解决了」正是 GOAL-082 EC-04 的教训反过来用。本判据两向钉：

1. 「计划」行的 `下一级` **含新句**（配对消融 / k≥3 / 判分布位移 / 不判采纳）——
   且**不再含**旧句（改写不是追加；旧 bar 沉进历史，本 GOAL 的记录面留档）；
2. 检索 / 复检 / 迭代三行的 `下一级` **逐字保持**改写前的原句（各自的锚点短语在位），
   且**不含**消融句——一格的证据不足以推广，推广了就是越级宣称。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHARTER = ROOT / ".cursor" / "plans" / "goals" / "MAINLINE.md"

#: 「计划」行新 `下一级` 的**三个**必要短语（缺一即没改到位）。
PLAN_NEW_MARKERS: tuple[str, ...] = (
    "配对消融下",
    "输出读数分布发生位移",
    "不判**「模型采纳了 X」",
)
#: 旧 bar 的锚点（改写后**不得**再出现在「计划」行——改写是替换不是追加）。
PLAN_OLD_MARKER = "计划改变下一轮问题"

#: 其余三格各自的**既有锚点**（逐字保持；来自改写前实测，2026-11-12）。
UNCHANGED_ROWS: dict[str, tuple[str, ...]] = {
    "检索": ("检索改变下一轮问题", "检索结果驱动**下一轮**问什么"),
    "复检": ("评审者与作者分开", "改稿与评审点有可判连接"),
    "迭代": ("迭代改变下一轮问题", "模型据上一轮结论提出**新问题**"),
}

#: 消融句的短锚（出现在其余三行 ⇒ 越级推广，判红）。
ABLATION_MARKER = "配对消融"


def _next_level(row_prefix: str) -> str:
    row = next(
        line
        for line in CHARTER.read_text(encoding="utf-8").splitlines()
        if line.startswith(row_prefix)
    )
    cells = row.split("|")
    assert len(cells) == 6, f"{row_prefix} 行不是 5 格：{len(cells) - 2}"
    return cells[4].strip()


def test_the_plan_row_carries_the_new_bar() -> None:
    """「计划」行的 `下一级` 含新句三锚，且旧句**不在**（改写 = 替换）。"""
    level = _next_level("| 计划 |")
    missing = [marker for marker in PLAN_NEW_MARKERS if marker not in level]
    assert not missing, f"计划行缺新 bar 锚点：{missing}"
    assert PLAN_OLD_MARKER not in level, "计划行仍带旧 bar ⇒ 改写成了追加"


def test_the_plan_row_names_the_delivered_mechanism() -> None:
    """新 bar 必须点名本轮交付的机制（否则 bar 没有可追溯的依据）。"""
    level = _next_level("| 计划 |")
    for marker in ("GOAL-20261111-109", "comparison_digest", "MIN_CORPUS=3"):
        assert marker in level, marker


class TestTheOtherThreeRowsAreUntouched:
    """其余三格逐字不动（一格的证据不足以推广）。"""

    def test_each_row_keeps_its_own_bar(self) -> None:
        for prefix, markers in UNCHANGED_ROWS.items():
            level = _next_level(f"| {prefix} |")
            missing = [marker for marker in markers if marker not in level]
            assert not missing, f"{prefix} 行的旧 bar 被动了：{missing}"

    def test_no_row_was_promoted_to_the_ablation_bar(self) -> None:
        for prefix in UNCHANGED_ROWS:
            level = _next_level(f"| {prefix} |")
            assert ABLATION_MARKER not in level, f"{prefix} 行被越级推广了"
