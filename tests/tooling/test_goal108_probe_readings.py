"""GOAL-20261111-108 EC-01：**探针读数在台账里，且四个免费模型逐字可枚举**。

**它补哪一格**：EC-01 的判据当初写在 GOAL 正文的 `verify:` 字段里
（`tests/tooling/test_goal108_probe_readings.py`），但**文件从未落地**——
于是那条 EC 标着 PASS 而没有任何机械判据在看它。本文件补上那个文件。
（这不是「补一个好看的门」：没有它时，把 `## 探针读数` 整节删掉，
全仓没有任何判据会红。）

**判什么**（每一条都是台账里必须同时在场的事实）：

1. 新站地址与「23 个模型」这个读数在台账里；
2. **四个免费模型逐字出现**，且每一个都带 `tool_calls` 的实测结论；
3. 「都返回 `model` 字段」这条结论在台账里（它决定 run 指纹能落
   `REPEATABLE_CONFIGURATION` 而不是 `NOT_VERIFIED`）；
4. `hy4std` 这类**收费**模型被点名为「不用」（否则「只用免费」无法从台账读出）。

**反证臂**（本文件自带，见 `test_a_missing_free_model_is_refused`）：把任一个免费模型名
从台账里抽掉 ⇒ 判据必须红。判据按**行**读，不按「全文出现过」——后者会让
「只在某个注释里提过一次」蒙混过关。
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GOAL = (
    ROOT
    / ".cursor/plans/goals"
    / "GOAL-20261111-108-relay-swap-single-model-test-and-silent-stall-closure.md"
)

#: 四个 `credits: x0.00` 且实测支持 `tool_calls` 的模型（EC-03 的分工就建立在它们之上）。
FREE_MODELS: tuple[str, ...] = ("hy4free", "hy4-preview-f", "hy4flash-exp4", "hy3")

#: 台账里必须出现的新站读数。
STATION_FACTS: tuple[str, ...] = (
    "http://192.168.101.9:8798/v1",
    "23 个模型",
    "x0.00",
)


def _goal() -> str:
    return GOAL.read_text(encoding="utf-8")


def _probe_section(text: str) -> str:
    """`## 探针读数` 一节（到下一个二级标题为止）。

    **标题只认行首**：GOAL 的 frontmatter 里 `verify:` 字段也引用了
    `## 探针读数` 这个**名字**（它与正文标题逐字相同），按子串切会把解析器带到
    frontmatter 里去 —— 那条判据看到的「节」其实是 YAML。既有纪律：
    「判据里引用二级标题名会把按子串切节的解析器带偏 ⇒ 标题只认行首」。
    """
    marker = "## 探针读数"
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(marker)), None)
    assert start is not None, "台账缺 `## 探针读数` 一节（行首）"
    end = next(
        (i for i, line in enumerate(lines[start + 1 :], start=start + 1) if line.startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def test_the_station_readings_are_recorded() -> None:
    section = _probe_section(_goal())
    missing = [fact for fact in STATION_FACTS if fact not in section]
    assert not missing, f"探针节缺站点读数：{missing}"


@pytest.mark.parametrize("model", FREE_MODELS)
def test_each_free_model_appears_with_a_tool_calls_reading(model: str) -> None:
    """逐个模型判：它必须在探针表里，且该行带 `tool_calls` 的实测结论。

    按**行**判而不是按整节判 —— 后者在一个模型名出现两次时也会绿。
    """
    rows = [line for line in _probe_section(_goal()).splitlines() if f"`{model}`" in line]
    assert rows, f"探针表里没有 {model} 这一行"
    assert any("tool_calls" in row or "✅" in row for row in rows), (
        f"{model} 那一行没有 tool_calls 的实测结论：{rows}"
    )


def test_the_returned_model_field_conclusion_is_recorded() -> None:
    """「四个都返回 `model` 字段」是指纹口径的依据，必须写成台账事实。"""
    section = _probe_section(_goal())
    assert "`model` 字段" in section or "返回 `model`" in section, section[:400]
    assert "REPEATABLE_CONFIGURATION" in section, section[:400]


def test_a_paid_model_is_named_as_not_used() -> None:
    """「只用免费」必须能从台账读出来：收费模型被点名，且带「不用」类判定词。"""
    lines = [line for line in _goal().splitlines() if "hy4std" in line]
    assert lines, "台账没有点名收费模型 hy4std"
    assert any("收费" in line or "不用" in line for line in lines), lines


class TestTheCriterionBites:
    """反证臂：判据咬得住（把一条事实抽掉 ⇒ 红）。"""

    def test_a_missing_free_model_is_refused(self, tmp_path: Path) -> None:
        # 必须**全量**替换：`hy3` 在两张表里各出现一次，只换第一处时第二行仍在，
        # 反证臂会假绿（本文件第一版正是这样，被自己抓到）。
        text = _goal().replace("`hy3`", "`hy3-REMOVED`")
        section = _probe_section(text)
        rows = [line for line in section.splitlines() if "`hy3`" in line]
        assert not rows, "反证臂失效：改名后仍能按 `hy3` 找到行"

    def test_an_empty_probe_section_is_refused(self) -> None:
        with pytest.raises(AssertionError):
            _probe_section("# 没有探针节的文档")
