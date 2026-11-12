"""GOAL-20261111-110 EC-04：阶梯改写——**只动「证据」一行，其余六行逐字不动**。

**为什么单列**：与 `test_goal109_ladder_pilot_scope.py` 同一条纪律的反面用例——
序 77 只改「计划」一格，本轮只改「证据」一格。两轮合起来证明**逐格推进**是真的：
如果有人顺手把「处置闭环」推到检索 / 复检 / 迭代，本轮与上轮的锚点判据都会红。

**判两件**：

1. 「证据」行的 `下一级` 含新 bar（策略闭集 / 可判依据 / 缺省 REQUIRE_HUMAN / 路由），
   且**不再**是旧句的形态（「仍无判据」那一段必须消失——改写不是追加）；
2. 其余六行（检索 / 计划 / 复检 / 实验 / 报告 / 迭代）**逐字保持**各自的锚点，
   且**不含**本轮的新 bar 短语。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHARTER = ROOT / ".cursor" / "plans" / "goals" / "MAINLINE.md"

#: 「证据」行新 `下一级` 的必要锚（缺一即没改到位）。
EVIDENCE_NEW_MARKERS: tuple[str, ...] = (
    "处置闭环成立（策略闭集 + 可判依据）",
    "NEWER_WINS",
    "SOURCE_TRUST_WINS",
    "REQUIRE_HUMAN",
    "resolve",
)
#: 旧 bar 的锚（改写后**不得**出现——替换不是追加）。
EVIDENCE_OLD_MARKER = "仍无判据"

#: 其余六行的既有锚点（逐字保持；取自 2026-11-12 改写后实测）。
UNCHANGED_ROWS: dict[str, tuple[str, ...]] = {
    "检索": ("检索改变下一轮问题",),
    "计划": ("配对消融下", "输出读数分布发生位移"),
    "复检": ("评审者与作者分开", "改稿与评审点有可判连接"),
    "实验": ("脚本也从计划里选", "这仍是「选择级」，不是「生成级」"),
    "报告": ("叙述质量与事实一致性可判",),
    "迭代": ("迭代改变下一轮问题",),
}

#: 本轮新 bar 的短锚（出现在其余六行 ⇒ 越级推广，判红）。
ARBITRATION_MARKER = "处置闭环成立"


def _next_level(prefix: str) -> str:
    row = next(
        line for line in CHARTER.read_text(encoding="utf-8").splitlines() if line.startswith(prefix)
    )
    cells = row.split("|")
    assert len(cells) == 6, f"{prefix} 行不是 5 格：{len(cells) - 2}"
    return cells[4].strip()


def test_the_evidence_row_carries_the_new_bar() -> None:
    """「证据」行含新 bar 五锚，且旧句「仍无判据」**不在**（改写 = 替换）。"""
    level = _next_level("| 证据 |")
    missing = [marker for marker in EVIDENCE_NEW_MARKERS if marker not in level]
    assert not missing, f"证据行缺新 bar 锚点：{missing}"
    assert EVIDENCE_OLD_MARKER not in level, "证据行仍带旧 bar ⇒ 改写成了追加"


def test_the_evidence_row_records_its_goal() -> None:
    """新 bar 必须点名本 GOAL（否则 bar 没有可追溯的依据）。"""
    assert "GOAL-20261111-110" in _next_level("| 证据 |")


class TestTheOtherSixRowsAreUntouched:
    """其余六行逐字不动（一轮只推进一格；越级推广判红）。"""

    def test_each_row_keeps_its_own_bar(self) -> None:
        for prefix, markers in UNCHANGED_ROWS.items():
            level = _next_level(f"| {prefix} |")
            missing = [marker for marker in markers if marker not in level]
            assert not missing, f"{prefix} 行的旧 bar 被动了：{missing}"

    def test_no_row_was_promoted_to_the_arbitration_bar(self) -> None:
        for prefix in UNCHANGED_ROWS:
            level = _next_level(f"| {prefix} |")
            assert ARBITRATION_MARKER not in level, f"{prefix} 行被越级推广了"
