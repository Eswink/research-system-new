"""GOAL-20261015-079 EC-03 判据：**臂间可比**（同一指标求差；缺指标**点名**，不折算成 0）。

**被测对象**：`experiments/arm_comparison.compare_arms`（纯函数；输入两臂的指标映射）。

**五件事逐条取证**：

1. **差由落库值算**：`right - left` 的符号约定**写在读数的字段语义里**
   （`delta` 字段注释逐字声明），判据按该约定核对具体数值；
2. **同名列才比**：只在两侧都有的指标上求差；只在单侧出现的指标**列表点名**
   （`missing_in_left` / `missing_in_right`）；
3. **缺指标**不**折算成 0**：一条只在一侧出现的指标**不得**产生 `delta` 条目
   （把「没测」当「测出 0」会伪造一个很大的差值——判据两向都钉）；
4. **非数值指标**（布尔 / 字符串 / 嵌套对象）**排除并点名**（`not_numeric`）：
   `True - False = 1` 是算术上成立、语义上荒唐的比较；
5. **空对比**（没有任何可比指标）⇒ `comparable is False`（这次对比**没有内容**，
   不是「差值为 0」）。
"""

from __future__ import annotations

from decimal import Decimal

from packages.application.experiments.arm_comparison import compare_arms


class TestTheDeltaIsArithmeticOnThePersistedValues:
    """① 差由落库值算（含符号约定与逐字读数）。"""

    def test_the_delta_is_right_minus_left(self) -> None:
        comparison = compare_arms("control", {"ratio": 7990.0}, "treatment", {"ratio": 178.5})
        assert len(comparison.deltas) == 1, comparison
        delta = comparison.deltas[0]
        assert delta.metric == "ratio", delta
        assert delta.left_arm == "control" and delta.right_arm == "treatment", delta
        assert delta.delta == "-7811.5", delta  # right - left = 178.5 - 7990.0
        # 逐字读数保留（不被重算成整数）。
        assert delta.left_value == "7990.0", delta
        assert delta.right_value == "178.5", delta

    def test_a_positive_delta_reads_correctly(self) -> None:
        comparison = compare_arms("a", {"m": 1}, "b", {"m": 3})
        assert comparison.deltas[0].delta == "2", comparison.deltas

    def test_integer_and_decimal_values_are_both_supported(self) -> None:
        comparison = compare_arms("a", {"m": Decimal("1.25")}, "b", {"m": 2})
        assert comparison.deltas[0].delta == "0.75", comparison.deltas


class TestOnlySharedMetricsAreCompared:
    """② 同名列才比；单侧出现的**逐臂点名**。"""

    def test_metrics_missing_on_one_side_are_named_not_compared(self) -> None:
        comparison = compare_arms(
            "control",
            {"shared": 1, "only_control": 5},
            "treatment",
            {"shared": 2, "only_treatment": 9},
        )
        assert [delta.metric for delta in comparison.deltas] == ["shared"], comparison.deltas
        assert comparison.missing_in_left == ("only_treatment",), comparison.missing_in_left
        assert comparison.missing_in_right == ("only_control",), comparison.missing_in_right

    def test_a_one_sided_metric_produces_no_delta_at_all(self) -> None:
        """③ **缺指标不折算成 0**：单侧指标**不得**出现在差值里（两向都钉）。

        方向口径（写在这里免得读者猜）：`missing_in_left` = **左臂缺**的那些指标
        （即右臂有、左臂没有）；反之亦然。
        """
        comparison = compare_arms("a", {"only_a": 100}, "b", {})
        assert comparison.deltas == (), comparison.deltas
        assert comparison.comparable is False, comparison
        assert comparison.missing_in_right == ("only_a",), comparison.missing_in_right
        assert comparison.missing_in_left == (), comparison.missing_in_left

    def test_an_empty_side_names_every_metric_of_the_other(self) -> None:
        comparison = compare_arms("a", {"x": 1, "y": 2}, "b", {})
        assert comparison.missing_in_right == ("x", "y"), comparison.missing_in_right
        assert comparison.missing_in_left == (), comparison.missing_in_left
        assert comparison.deltas == (), comparison.deltas


class TestNonNumericValuesAreNamedNotForced:
    """④ 非数值指标排除并点名（布尔**不**当 0/1 —— 那会伪造差值）。"""

    def test_booleans_are_not_treated_as_zero_and_one(self) -> None:
        comparison = compare_arms("a", {"agreement": True}, "b", {"agreement": False})
        assert comparison.deltas == (), comparison.deltas
        assert comparison.not_numeric == ("agreement",), comparison.not_numeric
        assert comparison.comparable is False, comparison

    def test_a_boolean_is_excluded_even_next_to_numeric_metrics(self) -> None:
        comparison = compare_arms(
            "a", {"agreement": True, "n": 1}, "b", {"agreement": True, "n": 4}
        )
        assert [delta.metric for delta in comparison.deltas] == ["n"], comparison.deltas
        assert comparison.deltas[0].delta == "3", comparison.deltas
        assert comparison.not_numeric == ("agreement",), comparison.not_numeric
        assert comparison.comparable is True, comparison

    def test_strings_and_nested_objects_are_excluded(self) -> None:
        comparison = compare_arms(
            "a", {"label": "x", "nested": {"k": 1}}, "b", {"label": "y", "nested": {"k": 2}}
        )
        assert comparison.deltas == (), comparison.deltas
        assert comparison.not_numeric == ("label", "nested"), comparison.not_numeric

    def test_numeric_strings_count_as_numbers(self) -> None:
        """读面可能把数值给成字符串（JSON 的既有形态）⇒ 能解析就算数。"""
        comparison = compare_arms("a", {"m": "1.5"}, "b", {"m": "2.5"})
        assert comparison.deltas and comparison.deltas[0].delta == "1", comparison.deltas


class TestTheEmptyComparisonIsNotAZero:
    """⑤ 空对比 ⇒ `comparable is False`（没有内容 ≠ 差值为 0）。"""

    def test_two_empty_sides_are_not_comparable(self) -> None:
        comparison = compare_arms("a", {}, "b", {})
        assert comparison.comparable is False, comparison
        assert comparison.deltas == () and not comparison.missing_in_left, comparison

    def test_a_comparable_pair_reports_true(self) -> None:
        assert compare_arms("a", {"m": 1}, "b", {"m": 1}).comparable is True

    def test_a_zero_delta_is_still_comparable(self) -> None:
        """差为 **0** 与「没有可比指标」是两件事（前者是结论，后者是没有结论）。"""
        comparison = compare_arms("a", {"m": 1}, "b", {"m": 1})
        assert comparison.deltas[0].delta == "0", comparison.deltas
        assert comparison.comparable is True, comparison
