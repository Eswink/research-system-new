"""`W-0` 起头的残余节必须读得出（GOAL-20261103-104 的第一个靶子的前置）。

**为什么单列**：`tests/tooling/test_next_round_charter.py` 已 415 行，贴近 450 行硬上限；
本组用例属于**同一口径的另一个方向**（起点，不是形态），单列不改变射程。

**它补哪一格**：2026-11-03 实测 —— GOAL-103 的残余节是 `W-0`…`W-5`，`W-0` 记的是
「**真跑才发现并已修**」的那条实现缺陷（刻意留在表里，与「仍未修」的残余并列）。
`charter_parse.check_residuals` 只认 `1…N` ⇒ 读取器拒于 `REFUSED RESIDUAL_GAP`，
下一轮的 charter **生不出来**。判据的本意是「**不得断号**」（删一条却忘改编号才可辨），
不是「必须从 1 开始」⇒ 起点 0/1 都接受，断号照拒。

**反证臂**（每个用例自带）：放宽起点 ≠ 放弃断号检测 —— 从中间抽掉一条，仍判
`RESIDUAL_GAP` 并报出**读到**的编号序列。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


_MODULE: ModuleType | None = None


def _parse() -> ModuleType:
    """按路径加载解析原语（`tools/` 不是包；先写 `sys.modules` 再 `exec_module`）。

    **只加载一次**：重复 `exec_module` 会造出**新的** `Refusal` 类对象，
    `pytest.raises(<旧类>)` 就接不住新类抛的异常（本文件第一版正是这样假红的）。
    """
    global _MODULE
    if _MODULE is not None:
        return _MODULE
    path = ROOT / "tools" / "charter_parse.py"
    spec = importlib.util.spec_from_file_location("charter_parse_w0", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["charter_parse_w0"] = module
    spec.loader.exec_module(module)
    _MODULE = module
    return module


def test_a_residual_list_that_starts_at_w_zero_is_read() -> None:
    """0 起点读得出 3 条；中间抽掉一条仍判 `RESIDUAL_GAP`（放宽起点不改断号检测）。"""
    text = "# GOAL\n\n## 残余与未覆盖范围\n\n- `W-0`｜甲。\n- `W-1`｜乙。\n- `W-2`｜丙。\n"
    parse = _parse()
    items = parse.residual_section(text)
    assert [item.number for item in items] == [0, 1, 2], items
    assert items[0].raw.startswith("- `W-0`"), items[0].raw

    gapped = text.replace("- `W-1`｜乙。\n", "")
    with pytest.raises(parse.Refusal) as raised:
        parse.residual_section(gapped)
    assert raised.value.code == "RESIDUAL_GAP", raised.value
    assert "读到 [0, 2]" in raised.value.detail, raised.value


def test_a_residual_list_that_starts_beyond_one_is_refused() -> None:
    """起点既不是 0 也不是 1 ⇒ 拒绝（任意起点就不叫编号了）。"""
    text = "# GOAL\n\n## 残余与未覆盖范围\n\n- `W-2`｜甲。\n- `W-3`｜乙。\n"
    with pytest.raises(_parse().Refusal) as raised:
        _parse().residual_section(text)
    assert raised.value.code == "RESIDUAL_GAP", raised.value
    assert "既不是 0 也不是 1" in raised.value.detail, raised.value


def test_the_real_goal_103_residuals_are_read() -> None:
    """真文件回归钉：GOAL-103 的残余节读得出 6 条（`W-0`…`W-5`）。"""
    path = (
        ROOT
        / ".cursor"
        / "plans"
        / "goals"
        / "GOAL-20261101-103-phase-events-and-frontend-visible-chain.md"
    )
    items = _parse().residual_section(path.read_text(encoding="utf-8"))
    assert [item.number for item in items] == [0, 1, 2, 3, 4, 5], items
