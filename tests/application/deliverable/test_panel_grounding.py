"""GOAL-20261111-111 EC-01/02/03：面板判词的**引用面**与 `REFUTED` 的降级。

**判什么**（EC-03 的四条 + 两条结构性边界）：

1. **正例**：`REFUTED` 的 rationale 指向真实句子（`S<n>` 命中 / 真实子串）⇒ 通过，
   判词**保持** `REFUTED`；
2. **反证**：rationale 指向**不存在**的句子（`S99`）⇒ `NOT_GROUNDED` 并**点名越界**；
   经 `ground_verdict` ⇒ 降级 `AMBIGUOUS` + `UNGROUNDED_MARK`；
3. **反证**：rationale **空** ⇒ `EMPTY_RATIONALE`，且与「不存在」**点名不同**
   （两种「不成立」分得开）；经 `ground_verdict` ⇒ 同样降级；
4. **面板仍 advisory**：`grounding` 不 import `Decision`，`manuscript_panel` 也不把判词
   写进验收面（既有 advisory 判据仍绿——本文件再钉一次源码面）。

**另一条钉住的东西**：本模块的句子切分正则与 `manuscript_quality._SENTENCE_SPLIT`
**逐字相同** —— 两处切句不同会让「编号」与「判据看的句子」错位。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from packages.application.deliverable.manuscript_panel import (
    UNGROUNDED_MARK,
    PanelVerdict,
    ground_verdict,
)
from packages.application.deliverable.panel_grounding import (
    EMPTY_RATIONALE,
    GROUNDED,
    NOT_GROUNDED,
    SENTENCE_SPLIT,
    grounded_in,
    grounding_of,
    number_sentences,
)

ROOT = Path(__file__).resolve().parents[3]

_MANUSCRIPT = (
    "The proposed method combines retrieval with a reranking stage. "
    "Results show a twenty percent gain over the baseline. "
    "We conclude that the hypothesis holds for the tested cohort."
)


def _refuted(rationale: str) -> PanelVerdict:
    return PanelVerdict(
        rubric_id="argument_holds",
        verdict="REFUTED",
        rationale=rationale,
        reviewer_model="main/hy4free",
    )


class TestGrounding:
    """EC-01：核验本身（不经面板）。"""

    def test_sentences_are_numbered_from_one(self) -> None:
        """切句确定性：从 `S1` 起，编号与顺序一致，句数 = 句末标点数。"""
        sentences = number_sentences(_MANUSCRIPT)
        assert [item.marker for item in sentences] == ["S1", "S2", "S3"]
        assert sentences[1].text.startswith("Results show")

    def test_an_empty_manuscript_yields_no_sentences(self) -> None:
        assert number_sentences("") == ()
        assert number_sentences("   \n  ") == ()

    def test_a_named_sentence_inside_range_is_grounded(self) -> None:
        """**正例（判据 ①）**：`S2` 在范围内 ⇒ `GROUNDED`。"""
        result = grounded_in("S2 overstates what the measurements show.", _MANUSCRIPT)
        assert result.outcome == GROUNDED
        assert result.sentences == (2,)
        assert result.missing == ()

    def test_a_quoted_substring_is_grounded(self) -> None:
        """正例（第二条通路）：引用正文真实子串 ⇒ `GROUNDED`（旧稿件没有 `S<n>` 时可用）。"""
        quote = "Results show a twenty percent gain over the baseline."
        result = grounded_in(f'The sentence "{quote}" is unsupported.', _MANUSCRIPT)
        assert result.outcome == GROUNDED

    def test_an_out_of_range_sentence_is_not_grounded_and_named(self) -> None:
        """**反证（判据 ②）**：`S99` ⇒ `NOT_GROUNDED` 且点名越界。"""
        result = grounded_in("S99 contradicts the abstract.", _MANUSCRIPT)
        assert result.outcome == NOT_GROUNDED
        assert any("S99" in item and "1..3" in item for item in result.missing)

    def test_a_quote_not_in_the_manuscript_is_not_grounded(self) -> None:
        """反证：引用一段正文里**不存在**的话 ⇒ `NOT_GROUNDED` 并点名那段话。"""
        result = grounded_in('The text "we prove the theorem for all n" is false.', _MANUSCRIPT)
        assert result.outcome == NOT_GROUNDED
        assert any("not a substring" in item for item in result.missing)

    def test_a_rationale_naming_nothing_is_not_grounded(self) -> None:
        result = grounded_in("The argument is weak.", _MANUSCRIPT)
        assert result.outcome == NOT_GROUNDED
        assert any("names no sentence" in item for item in result.missing)

    def test_an_empty_rationale_is_its_own_outcome(self) -> None:
        """**反证（判据 ③）**：空 rationale ⇒ `EMPTY_RATIONALE`，与 `NOT_GROUNDED` **点名不同**。"""
        empty = grounding_of("", number_sentences(_MANUSCRIPT))
        assert empty.outcome == EMPTY_RATIONALE
        assert any("empty" in item for item in empty.missing)
        missing = grounding_of("The argument is weak.", number_sentences(_MANUSCRIPT))
        assert missing.outcome == NOT_GROUNDED
        assert empty.outcome != missing.outcome
        assert empty.missing != missing.missing


class TestRefutedMustBePointed:
    """EC-02：`REFUTED` 在写出前过核验；其余三态**原样通过**。"""

    def test_a_grounded_refutation_survives(self) -> None:
        """正例：指向真实句子 ⇒ 判词**保持** `REFUTED`（不被降级）。"""
        verdict = ground_verdict(_refuted("S3 generalises beyond the tested cohort."), _MANUSCRIPT)
        assert verdict.verdict == "REFUTED"
        assert verdict.rationale == "S3 generalises beyond the tested cohort."

    def test_an_unsupported_refutation_is_degraded_and_named(self) -> None:
        """**反证**：`S99` ⇒ 降级 `AMBIGUOUS` + `UNGROUNDED_MARK` + 保留模型原话。"""
        verdict = ground_verdict(_refuted("S99 contradicts the abstract."), _MANUSCRIPT)
        assert verdict.verdict == "AMBIGUOUS"
        assert verdict.rationale.startswith(UNGROUNDED_MARK)
        assert "S99" in verdict.rationale
        assert "model said:" in verdict.rationale
        assert verdict.reviewer_model == "main/hy4free"

    def test_an_empty_rationale_refutation_is_degraded(self) -> None:
        """**反证**：空 rationale ⇒ 同样降级（两种不成立都拦，但点名不同）。"""
        verdict = ground_verdict(_refuted(""), _MANUSCRIPT)
        assert verdict.verdict == "AMBIGUOUS"
        assert "empty" in verdict.rationale

    def test_supported_is_not_constrained(self) -> None:
        """边界：`SUPPORTED` 不指句子 ⇒ **不**被这条约束（空 rationale 也原样通过）。"""
        supported = PanelVerdict(
            rubric_id="method_appropriate",
            verdict="SUPPORTED",
            rationale="",
            reviewer_model="main/hy4free",
        )
        assert ground_verdict(supported, _MANUSCRIPT) is supported

    def test_ambiguous_and_facility_failures_pass_through(self) -> None:
        """边界：`AMBIGUOUS` 与设施失败**原样返回**（约束只落在 `REFUTED`）。"""
        ambiguous = PanelVerdict(
            rubric_id="argument_holds", verdict="AMBIGUOUS", rationale="", reviewer_model=None
        )
        assert ground_verdict(ambiguous, _MANUSCRIPT) is ambiguous
        unavailable = PanelVerdict(
            rubric_id="argument_holds",
            verdict="PANEL_UNAVAILABLE",
            rationale="TimeoutError: boom",
            reviewer_model=None,
        )
        assert ground_verdict(unavailable, _MANUSCRIPT) is unavailable


class TestTheAdvisoryBoundaryStillHolds:
    """EC-03 判据 ④：面板仍 advisory —— 可核验**不**等于参与验收。"""

    def test_grounding_does_not_reach_into_decisions(self) -> None:
        source = (ROOT / "packages/application/deliverable/panel_grounding.py").read_text(
            encoding="utf-8"
        )
        assert "Decision" not in source, "引用核验面不得触及 Decision"
        assert "acceptance_gate" not in source

    def test_the_panel_still_only_constructs_findings(self) -> None:
        source = (ROOT / "packages/application/deliverable/manuscript_panel.py").read_text(
            encoding="utf-8"
        )
        assert "Decision(" not in source, "面板不得构造 Decision"
        assert "as_review_findings" in source


class TestTheSentenceSplitIsSingleSourced:
    """两处切句必须**逐字相同**（编号与判据看的句子不能错位）。"""

    def test_the_regex_matches_the_quality_module(self) -> None:
        """比较的是**正则本身**（按源码里的字面量取，不比较变量名——名称可不同）。"""
        quality = (ROOT / "packages/application/deliverable/manuscript_quality.py").read_text(
            encoding="utf-8"
        )
        pattern = SENTENCE_SPLIT.pattern
        assert f'_SENTENCE_SPLIT = re.compile(r"{pattern}")' in quality, (
            "两处切句正则不一致：编号会与确定性判据看的句子错位"
        )


@pytest.mark.parametrize("marker", ["S1", "s1", "S2"])
def test_sentence_refs_are_case_insensitive(marker: str) -> None:
    """`S<n>` 大小写不敏感（模型会写 `s2`）；越界仍判负。"""
    result = grounded_in(f"{marker} is wrong.", _MANUSCRIPT)
    assert result.outcome == GROUNDED
