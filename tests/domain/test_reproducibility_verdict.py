"""结论口径词表（GOAL-008 EC-04 / AGENTS.md §4）。

判的是**词表本身**：「完全可复现」这类宣称在类型上不可表达。把读面改成能说
「完全可复现」，必须先让枚举多一个成员——这几条判据就是那道门。
"""

from __future__ import annotations

from packages.domain.enums import ModelReproducibilityVerdict

#: 「完全可复现」类宣称会在成员名里留下的痕迹。
_OVERCLAIM_TOKENS: tuple[str, ...] = (
    "REPRODUCIBLE",
    "FULL",
    "EXACT",
    "IDENTICAL",
    "PROVEN",
    "CONFIRMED",
    "GUARANTEED",
)


def test_verdict_is_exactly_the_two_states() -> None:
    """两态穷举：多一个成员（例如「完全可复现」）就判红。"""
    assert {member.value for member in ModelReproducibilityVerdict} == {
        "REPEATABLE_CONFIGURATION",
        "NOT_VERIFIED",
    }


def test_no_member_can_express_a_fully_reproducible_claim() -> None:
    for member in ModelReproducibilityVerdict:
        found = [token for token in _OVERCLAIM_TOKENS if token in member.name]
        assert not found, f"{member.name} 让「完全可复现」类宣称变得可表达：{found}"


def test_repeatable_configuration_is_the_strongest_statement() -> None:
    """最强的一档也只能是「配置可重复」——不是「模型可复现」。"""
    strongest = ModelReproducibilityVerdict.REPEATABLE_CONFIGURATION.name
    assert "CONFIGURATION" in strongest
    assert "MODEL" not in strongest


def test_not_verified_is_distinct_from_the_verified_state() -> None:
    assert ModelReproducibilityVerdict.NOT_VERIFIED is not (
        ModelReproducibilityVerdict.REPEATABLE_CONFIGURATION
    )
