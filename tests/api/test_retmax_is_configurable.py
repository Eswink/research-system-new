"""GOAL-20261029-100 EC-04：`retmax` **可配**，而**默认逐字节不变**。

**它补哪一格**（建档实测）：`retmax` 硬编码在 `services/api/retrieval_wiring.py` 的
`fixed_arguments={"retmax": 3}` 里，没有配置面 ⇒ 一次 run 的 References 恒为 3 条上下，
「Related Work」没有实质内容可写。

**三向判据**：

1. **默认不变**（零回归的机械含义）：不传参数、不设环境变量时，生成的检索调用与改动前的
   字面量 `{"retmax": 3}` **逐字段相同** —— 且第二条调用（read）**不受影响**；
2. **改配置 ⇒ 调用参数变**：`retmax=10` 与 `RESEARCHOS_RETMAX=10` 都让 `fixed_arguments`
   变成 `{"retmax": 10}`（两条通路各判一条，因为它们走的是不同代码路径）；
3. **反证：非法值点名拒绝**（不是静默回落默认）：静默回落会让「调成 50」与「变量名拼错」
   在读数上不可区分。

**零出网**：只构造调用声明对象，不触网。
"""

from __future__ import annotations

from typing import Any

import pytest

from services.api.retrieval_wiring import (
    DEFAULT_RETMAX,
    MAX_RETMAX,
    RETMAX_ENV,
    configured_retmax,
    retrieval_calls,
)


def _search_call(retmax: int | None = None) -> Any:
    """检索那条调用（`Any`：`RunChainCall` 是装配面的形状，本判据只读它的两个字段）。"""
    return retrieval_calls(retmax)[0]


class TestTheDefaultIsByteIdentical:
    """① 默认：与改动前的字面量 `{"retmax": 3}` **逐字段相同**。"""

    def test_the_default_constant_is_three(self) -> None:
        assert DEFAULT_RETMAX == 3

    def test_no_argument_no_environment_yields_three(self) -> None:
        """**零回归的机械含义**：不传参、环境变量未设 ⇒ 调用与改动前逐字段相同。"""
        assert _search_call().fixed_arguments == {"retmax": 3}

    def test_an_empty_environment_value_falls_back_to_the_default(self) -> None:
        """空字符串 = 未设（部署里最常见的形态：变量存在但没有值）。"""
        assert configured_retmax({RETMAX_ENV: ""}) == DEFAULT_RETMAX
        assert configured_retmax({RETMAX_ENV: "   "}) == DEFAULT_RETMAX
        assert configured_retmax({}) == DEFAULT_RETMAX

    def test_the_read_call_is_not_affected(self) -> None:
        """第二条（read）用 `ids_from_previous`，**没有** `retmax` 参数面。"""
        read = retrieval_calls(10)[1]
        assert read.fixed_arguments == {}
        assert read.ids_from_previous == "ids"


class TestTheSettingActuallyMovesTheArgument:
    """② 改配置 ⇒ 调用参数变（显式参数与环境变量各一条）。"""

    def test_an_explicit_value_reaches_the_call(self) -> None:
        assert _search_call(10).fixed_arguments == {"retmax": 10}

    def test_the_environment_value_reaches_the_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`RESEARCHOS_RETMAX` 是**产品**配置面（组合根不传参时读它）。"""
        monkeypatch.setenv(RETMAX_ENV, "12")
        assert _search_call().fixed_arguments == {"retmax": 12}

    def test_the_explicit_value_wins_over_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """显式传值优先（判据据此按压产品装配面接上来的值）。"""
        monkeypatch.setenv(RETMAX_ENV, "12")
        assert _search_call(4).fixed_arguments == {"retmax": 4}

    def test_the_configured_value_is_an_integer(self) -> None:
        assert configured_retmax({RETMAX_ENV: "7"}) == 7


class TestAnIllegalValueIsRefusedByName:
    """③ 反证：非法值**点名**拒绝，不静默回落默认。"""

    @pytest.mark.parametrize("raw", ["abc", "3.5", "-1", "0", str(MAX_RETMAX + 1), "1e3"])
    def test_an_illegal_environment_value_is_named(self, raw: str) -> None:
        with pytest.raises(ValueError) as raised:
            configured_retmax({RETMAX_ENV: raw})
        assert RETMAX_ENV in str(raised.value), str(raised.value)

    @pytest.mark.parametrize("value", [0, -5, MAX_RETMAX + 1])
    def test_an_illegal_explicit_value_is_named(self, value: int) -> None:
        with pytest.raises(ValueError, match="retmax"):
            retrieval_calls(value)

    def test_the_upper_bound_is_a_declared_number(self) -> None:
        """上界是**声明值**（不是「看情况」）：它决定「一次取几条」不会拖垮一次 run。"""
        assert MAX_RETMAX == 100
        assert retrieval_calls(MAX_RETMAX)[0].fixed_arguments == {"retmax": MAX_RETMAX}
