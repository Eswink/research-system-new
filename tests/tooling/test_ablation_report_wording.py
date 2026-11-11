"""GOAL-20261111-109 EC-05：报告输出的**措辞边界机械化**。

**边界**：报告判「读数分布的位移」，**不判**「模型采纳了 X」。后者是意图归因——
AGENTS.md §4「不越级宣称」在同一条线上的机械化形态：`tools/ablation_report.py` 的
报告文本里**不得**出现 `adopt` / `采纳` 类词，由工具**出口自检**（`render_report`
命中闭集即抛，fail-closed）+ 本判据**两向按压**：

1. 正例：`render_report` 的真实输出对闭集**零命中**（k=3 与 k=2 两种形态都扫）；
2. **反证**：往报告文本里注入闭集词 ⇒ 工具自己的出口守卫**判红**（证明守卫在出口、
   不在别处——绕过出口的调用点由「守卫函数是模块内唯一渲染出口」这条断言钉住）；
3. **闭集非空**：词表本身不得为空（空真不算边界）；
4. **工具源码**：除词表定义处外，模块正文不含这些词（防止有人「顺手」把结论写死）。
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]

_MODULE: ModuleType | None = None


def _tool() -> ModuleType:
    global _MODULE
    if _MODULE is not None:
        return _MODULE
    path = ROOT / "tools" / "ablation_report.py"
    spec = importlib.util.spec_from_file_location("ablation_report_wording", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["ablation_report_wording"] = module
    spec.loader.exec_module(module)
    _MODULE = module
    return module


def _pairs(count: int) -> dict[str, object]:
    def obs() -> dict[str, object]:
        return {
            "comparison_digest": "sha256:a",
            "design_block": 1,
            "arm_count": 2,
            "parameter_count": 3,
            "citation_count": 1,
        }

    return {
        "slot": "retrieval",
        "pairs": [
            {"label": f"k{i}", "present": obs(), "absent": obs()} for i in range(1, count + 1)
        ],
    }


def test_the_word_list_is_a_non_empty_closed_set() -> None:
    """闭集非空、只含意图归因词（`adopt` / `采纳` 类）；空真不算边界。"""
    words = _tool().forbidden_words()
    assert len(words) >= 4
    assert any("adopt" in word for word in words)
    assert "采纳" in words


@pytest.mark.parametrize("count", [3, 2, 0])
def test_rendered_reports_never_contain_intent_words(count: int) -> None:
    """正例：真实渲染的报告（足 / 不足 / 空）对闭集**零命中**。"""
    tool = _tool()
    text = tool.render_report(tool.build_report(_pairs(count)))
    offenders = [word for word in tool.forbidden_words() if word in text]
    assert not offenders, (offenders, text)


def test_the_exit_guard_refuses_injected_wording() -> None:
    """**反证**：注入闭集词 ⇒ `render_report` 出口守卫判红（守卫在出口，fail-closed）。

    注入点选 `slot`：它是报告文本里**唯一**由输入携带的自由文本（列名与 verdict 都是
    模块自有常量）——守卫必须连它都压住。
    """
    tool = _tool()
    report = tool.build_report(_pairs(3))
    poisoned = report.__class__(
        slot=f"{report.slot}（模型采纳了它）",
        gate=report.gate,
        shifts=report.shifts,
        labels=report.labels,
    )
    with pytest.raises(tool.AblationError, match="forbidden wording"):
        tool.render_report(poisoned)


def test_the_tool_module_itself_is_clean_outside_the_word_list() -> None:
    """工具源码（除词表定义行外）不含闭集词——防止有人把结论词写死进报告文案。"""
    source = (_tool_root() / "tools" / "ablation_report.py").read_text(encoding="utf-8")
    tool = _tool()
    lines = source.splitlines()
    offenders: list[str] = []
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith(("#", '"', "'")):
            continue  # 词表定义 / docstring 行放行
        if "forbidden" in stripped or "_FORBIDDEN_WORDS" in stripped:
            continue
        for word in tool.forbidden_words():
            if re.search(rf"\b{re.escape(word)}\b", line):
                offenders.append(f"line {number}: {word}")
    assert not offenders, offenders


def _tool_root() -> Path:
    return ROOT


def test_render_is_the_only_text_exit() -> None:
    """文本出口唯一：`main` 只经 `render_report` 写 stdout（守卫因此压得住所有输出）。"""
    source = (_tool_root() / "tools" / "ablation_report.py").read_text(encoding="utf-8")
    assert source.count("sys.stdout.write") == 1, "stdout 只允许一个写点"
    write_line = next(line for line in source.splitlines() if "sys.stdout.write" in line)
    assert "render_report(report)" in write_line, write_line
    # 且渲染函数自己以出口守卫收尾（返回前自检）。
    render_body = source.split("def render_report", 1)[1].split("\ndef ", 1)[0]
    assert "forbidden wording" in render_body
