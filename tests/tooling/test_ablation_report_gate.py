"""GOAL-20261111-109 EC-04：**读数表 + `MIN_CORPUS=3` 拒绝门**（`tools/ablation_report.py`）。

四条（判据 ③ 反证 + 正例 + 两处边界）：

1. **反证（判据 ③）**：k=2 ⇒ `corpus_gate` 判「不足」并**点名**
   （`ablation pairs: 2 of 3 required`）；CLI 出口退非零；
2. **正例**：k=3 ⇒ 门「足」并给出四列位移（含 design-block 产出率）；
3. **配对完整性**：同一对的两臂 `comparison_digest` 不等 ⇒ 点名拒绝
   （配对是「只差一个 slot」的汇总面断言，键不等 = 不是同一份装配）；
4. **缺列 / 非整数 / 空 label / 缺键**：逐条点名，**不猜默认值**。

门常量与产品侧 `citation_distribution.MIN_CORPUS` **同值**——判据跨模块比对
（`tools/` 不 import 产品包；两份常量由本判据钉住同值，漂移即红）。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]

_MODULE: ModuleType | None = None


def _tool() -> ModuleType:
    """按路径加载（`tools/` 不是包；**先写 `sys.modules` 再 `exec_module`**）。"""
    global _MODULE
    if _MODULE is not None:
        return _MODULE
    path = ROOT / "tools" / "ablation_report.py"
    spec = importlib.util.spec_from_file_location("ablation_report_under_test", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules["ablation_report_under_test"] = module
    spec.loader.exec_module(module)
    _MODULE = module
    return module


def _obs(digest: str = "sha256:a", **fields: int) -> dict[str, object]:
    base = {"design_block": 1, "arm_count": 2, "parameter_count": 3, "citation_count": 1}
    return {"comparison_digest": digest, **{**base, **fields}}


def _pairs(count: int) -> dict[str, object]:
    return {
        "slot": "retrieval",
        "pairs": [
            {
                "label": f"k{index}",
                "present": _obs(design_block=1, arm_count=2, parameter_count=3, citation_count=2),
                "absent": _obs(design_block=0, arm_count=1, parameter_count=1, citation_count=0),
            }
            for index in range(1, count + 1)
        ],
    }


def test_gate_refuses_two_pairs_by_name() -> None:
    """**反证（判据 ③）**：k=2 ⇒ 门「不足」并点名 `2 of 3 required`。"""
    tool = _tool()
    report = tool.build_report(_pairs(2))
    assert report.gate.sufficient is False
    assert report.gate.pairs == 2
    assert report.gate.missing == ("ablation pairs: 2 of 3 required",)
    text = tool.render_report(report)
    assert "INSUFFICIENT" in text and "2 of 3 required" in text
    assert "no distributional claim is made" in text


def test_cli_exit_code_reflects_the_gate(tmp_path: Path) -> None:
    """CLI 出口：语料不足 ⇒ 退非零；语料足 ⇒ 退零（认证被拒必须是**可观测事实**）。"""
    tool = _tool()
    insufficient = tmp_path / "k2.json"
    insufficient.write_text(json.dumps(_pairs(2)), encoding="utf-8")
    assert tool.main(["--input", str(insufficient)]) == 1
    sufficient = tmp_path / "k3.json"
    sufficient.write_text(json.dumps(_pairs(3)), encoding="utf-8")
    assert tool.main(["--input", str(sufficient)]) == 0


def test_gate_accepts_three_pairs_and_reports_shifts() -> None:
    """正例：k=3 ⇒ 门「足」，四列位移齐全（design-block 产出率 1.0 vs 0.0）。"""
    tool = _tool()
    report = tool.build_report(_pairs(3))
    assert report.gate.sufficient is True
    assert report.gate.missing == ()
    columns = {column.field: column for column in report.shifts}
    assert columns["design_block"].present_mean == 1.0
    assert columns["design_block"].absent_mean == 0.0
    assert columns["design_block"].shifted is True
    assert set(report.shifted_columns) == {
        "design_block",
        "arm_count",
        "parameter_count",
        "citation_count",
    }
    text = tool.render_report(report)
    assert "sufficient" in text and "shifted in 4 of 4 columns" in text


def test_zero_pairs_is_insufficient_and_report_still_renders() -> None:
    """k=0 ⇒ 门「不足」；报告照常渲染（空表 + 拒绝结论），**不抛**。"""
    tool = _tool()
    report = tool.build_report({"slot": "retrieval", "pairs": []})
    assert report.gate.sufficient is False
    assert report.gate.pairs == 0
    assert tool.render_report(report).count("|") >= 5


def test_pair_arms_must_share_one_comparison_digest() -> None:
    """**配对完整性**：两臂键不等 ⇒ 点名拒绝（不是同一份装配的「对」不算对）。"""
    tool = _tool()
    raw = {
        "slot": "retrieval",
        "pairs": [
            {"label": "k1", "present": _obs(digest="sha256:a"), "absent": _obs(digest="sha256:b")},
        ],
    }
    with pytest.raises(tool.AblationError, match="must share one comparison_digest"):
        tool.build_report(raw)


@pytest.mark.parametrize(
    "mutation",
    [
        {"drop": "design_block"},
        {"design_block": True},
        {"design_block": "1"},
        {"drop": "comparison_digest"},
    ],
)
def test_malformed_observations_are_refused_by_name(mutation: dict[str, object]) -> None:
    """缺列 / 布尔冒充整数 / 字符串冒充整数 / 缺 digest——逐条点名，**不猜**。"""
    tool = _tool()
    obs = _obs()
    if "drop" in mutation:
        obs.pop(str(mutation["drop"]))
    else:
        key = str(next(iter(mutation)))
        obs[key] = mutation[key]
    raw = {"slot": "retrieval", "pairs": [{"label": "k1", "present": obs, "absent": _obs()}]}
    with pytest.raises(tool.AblationError):
        tool.build_report(raw)


def test_min_corpus_matches_the_product_constant() -> None:
    """门常量与产品侧 `citation_distribution.MIN_CORPUS` **同值**（跨模块比对，漂移即红）。"""
    tool = _tool()
    assert tool.MIN_CORPUS == 3
    from packages.application.deliverable.citation_distribution import MIN_CORPUS as PRODUCT

    assert tool.MIN_CORPUS == PRODUCT


def test_labels_are_recorded_and_slot_is_carried() -> None:
    """汇总携带 slot 与各对 label（读数表可回溯到第几次重复）。"""
    tool = _tool()
    report = tool.build_report(_pairs(3))
    assert report.slot == "retrieval"
    assert report.labels == ("k1", "k2", "k3")
