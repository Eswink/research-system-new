"""GOAL-20261018-083 EC-01 判据：**内容级冲突判定**是确定性纯函数，且射程边界明确。

**它判什么**：`detect_content_conflict` 对**三种可机械判**的形态给出稳定判词，且对
**不该判**的形态保持 `None`（不误报）。

判据分三组：

1. **正向**（应判出）：否定极性 / 数值方向 / 反义谓词；
2. **反向**（不该判出）：同义、无关、互相包含、完全相同、空正文 —— 这一组是**误报防线**，
   与正向**同等重要**（EC-04 会在真实语料上再压一遍）；
3. **确定性 + 无副作用**：同一对输入重复调用结果**逐字相同**；判定函数**不读**时钟 /
   随机数 / 网络 / 模型（由源码级断言钉住 —— 见 `test_the_decider_has_no_io_imports`）。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from packages.application.memory.content_conflict import (
    FORM_ANTONYM,
    FORM_NEGATION,
    FORM_NUMERIC,
    detect_content_conflict,
)

_MODULE = "packages/application/memory/content_conflict.py"
_ROOT = Path(__file__).resolve().parents[3]


def _verdict(first: str, second: str) -> tuple[str, str] | None:
    found = detect_content_conflict(first, second)
    return (found.form, found.shared) if found is not None else None


# ------------------------------------------------------------------ 正向（应判出）


@pytest.mark.parametrize(
    ("first", "second", "form"),
    (
        ("X supports Y", "X does not support Y", FORM_NEGATION),
        (
            "duplicate pairs inflate support",
            "duplicate pairs do not inflate support",
            FORM_NEGATION,
        ),
        ("该药有效", "该药无效", FORM_ANTONYM),
        ("the ratio increases with n", "the ratio decreases with n", FORM_ANTONYM),
        ("the metric is 2.0 ms", "the metric is 0.5 ms", FORM_NUMERIC),
        ("the value is 10 items", "the value is 3 items", FORM_NUMERIC),
    ),
)
def test_opposed_statements_are_detected(first: str, second: str, form: str) -> None:
    """**说法相反 ⇒ 判出**，且形态标签与预期一致（判词稳定，读面按它对齐）。"""
    found = _verdict(first, second)
    assert found is not None, (first, second)
    assert found[0] == form, found
    assert found[1], "共享断言核必须非空（判词要点得出「在哪句话上相反」）"


def test_detection_is_symmetric() -> None:
    """**对称**：`(a, b)` 与 `(b, a)` 给同一个形态与同一个断言核（不依赖参数顺序）。"""
    pairs = (
        ("X supports Y", "X does not support Y"),
        ("the metric is 2.0", "the metric is 0.5"),
        ("the ratio increases with n", "the ratio decreases with n"),
    )
    for first, second in pairs:
        assert _verdict(first, second) == _verdict(second, first), (first, second)


# ------------------------------------------------------- 反向（不该判出；误报防线）


@pytest.mark.parametrize(
    ("first", "second"),
    (
        # 同一断言
        ("X supports Y", "X supports Y"),
        ("the metric is 2.0 ms", "the metric is 2.0 ms"),
        # 不同主语 / 不同宾语 —— 不是同一句话
        ("X supports Y", "X supports Z"),
        ("alpha is beta", "alpha is gamma"),
        # 无关
        ("A", "B"),
        ("temperature is 5", "pressure is 9"),
        # 一侧为空
        ("", "X supports Y"),
        ("X supports Y", "   "),
        # 数值相等（不是「相反」）
        ("the value is 2.0 ms and 3.0 ms", "the value is 2.0 ms and 3.0 ms"),
        # 量纲不一致（同一对里既有更大又有更小 ⇒ 不判）
        # 量纲不一致（同一对里既有更大又有更小 ⇒ 不判）
        ("the value is 10 ms and 2 ms", "the value is 5 ms and 7 ms"),
        # **射程边界**（W-2）：无单位数字既可能是量值也可能是编号 ⇒ 不判
        ("the metric is 2.0", "the metric is 0.5"),
        ("mem-1", "mem-2"),
        ("pipeline A finishes in 3 minutes", "pipeline B finishes in 40 minutes"),
    ),
)
def test_unjdugeable_or_consistent_statements_are_not_flagged(first: str, second: str) -> None:
    """**不相反 ⇒ 返回 `None`**（误报会把记忆写入掐死，与「不判」同样有害）。"""
    assert _verdict(first, second) is None, (first, second)


def test_blank_and_identical_inputs_are_none() -> None:
    """空 / 完全相同 ⇒ `None`（`None` 的语义是「判不出或不相反」，不是「没有冲突」）。"""
    assert detect_content_conflict("", "") is None
    assert detect_content_conflict("   ", "   ") is None
    assert detect_content_conflict("same", "same") is None


# ------------------------------------------------------------- 确定性 + 无副作用


def test_repeated_calls_are_byte_identical() -> None:
    """**确定性**：同一对输入重复 50 次，判词与断言核**逐字相同**。"""
    first, second = ("the metric is 2.0 ms", "the metric is 0.5 ms")
    verdicts = {_verdict(first, second) for _ in range(50)}
    assert len(verdicts) == 1, verdicts


def test_the_decider_has_no_io_imports() -> None:
    """**纯函数**（源码级）：判定模块**不得** import 任何 IO / 时间 / 随机 / 模型依赖。

    这是本 GOAL `forbidden` 的机械形态：用 LLM 或网络判「说法是否相反」会让门链变成
    不可复现、不可离线判的东西。
    """
    source = (_ROOT / _MODULE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {
        "socket",
        "http",
        "httpx",
        "requests",
        "urllib",
        "random",
        "datetime",
        "time",
        "openai",
        "anthropic",
        "litellm",
        "openhands",
    }
    assert not (imported & forbidden), sorted(imported & forbidden)


def test_the_decider_reads_no_clock_or_randomness() -> None:
    """**无时钟 / 无随机**（源码级）：模块正文里不得出现那两类调用。"""
    source = (_ROOT / _MODULE).read_text(encoding="utf-8")
    for needle in ("time.time(", "datetime.now(", "utcnow(", "random."):
        assert needle not in source, needle
