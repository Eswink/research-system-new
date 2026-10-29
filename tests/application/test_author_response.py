"""GOAL-20261029-100 EC-03：**返修闭环的底座**——可编号的评审点 + 逐条应答。

**它补哪一格**（建档实测）：`ReviewFinding.findings` 是扁平的判据渲染串，**没有可应答的
条目 id**；`weakest_link` 从未被解析成记录；`rebuttal` 全仓零命中。于是「作者逐条回应、
编辑据此判断返修是否到位」在结构上不存在。

**三条反证**（缺一不算，逐条按在真对象上）：

1. **漏答**：有评审点却少一条应答 ⇒ 点名判红；
2. **编造 `point_id`**：应答引用了评审从未提出的编号 ⇒ 点名判红；
3. **删一条应答**：把一条真的应答删掉 ⇒ 判据**必须**红（这条证明判据真的在数，
   而不是只在看「有没有应答」）。

另判：重复应答点名、`point_id` 对同一份产物**稳定**（排序键不含 uuid / 时间）、
应答信逐条成段、`response_letter.md` 从**产品入口**产出（见 e2e 文件）。
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from packages.application.deliverable.author_response import (
    RESPONSES_KEY,
    AuthorResponse,
    ResponseError,
    ReviewerRemark,
    ReviewPoint,
    parse_responses,
    points_of,
    remarks_of,
    response_letter,
    validate_responses,
)
from packages.application.run_orchestration.retrieval_prompt import (
    REVIEW_POINTS_SECTION_TITLE,
    render_review_points_prompt,
)

_POINTS = (
    ReviewPoint(point_id="P1", severity="must_fix", text="FAIL: EVIDENCE_COVERAGE 0 >= 1"),
    ReviewPoint(point_id="P2", severity="should_fix", text="the rationale is thin"),
)


def _record(*texts: str, reviewer: str = "gate:reviewer_a") -> Any:
    """一条**意见**（`points_of` 的输入形状：审稿人 + 原文 + 严重性）。

    严重性按**判据行首那个词**给（`FAIL…` ⇒ `must_fix`，其余 `should_fix`）——
    与产品侧 `_severity_of` 同一机械口径，但**在测试里独立写一遍**（不 import 产品
    的映射当预言机：那样映射改错时判据会跟着绿）。
    """
    return tuple(
        ReviewerRemark(
            reviewer=reviewer,
            text=text,
            severity="must_fix" if text.upper().startswith("FAIL") else "should_fix",
        )
        for text in texts
    )


def _answers(*pairs: tuple[str, str]) -> str:
    return json.dumps({
        RESPONSES_KEY: [
            {"point_id": point_id, "response": text, "action_taken": f"changed {point_id}"}
            for point_id, text in pairs
        ]
    })


class TestThePointsAreExplicitAndStable:
    """点表：编号、严重性、原文三件都在，且**同一份评审产物 ⇒ 同一份点表**。"""

    def test_two_findings_become_two_numbered_points(self) -> None:
        records = _record("FAIL: EVIDENCE_COVERAGE 0 >= 1", "the rationale is thin")
        points = points_of(records)
        assert [point.point_id for point in points] == ["P1", "P2"]
        assert {point.text for point in points} == {
            "FAIL: EVIDENCE_COVERAGE 0 >= 1",
            "the rationale is thin",
        }

    def test_a_failing_criterion_is_must_fix_and_the_rest_are_should_fix(self) -> None:
        """严重性是**机械**映射（只看行首那个词），不是语义判断。"""
        points = points_of(_record("FAIL: EVIDENCE_COVERAGE 0 >= 1", "PASS: ARTIFACT_EXISTS x"))
        by_text = {point.text: point.severity for point in points}
        assert by_text["FAIL: EVIDENCE_COVERAGE 0 >= 1"] == "must_fix"
        assert by_text["PASS: ARTIFACT_EXISTS x"] == "should_fix"

    def test_the_same_review_yields_the_same_point_table(self) -> None:
        """**稳定性**：两次派生（含记录顺序颠倒）⇒ 逐条相同（id 与顺序都不变）。"""
        texts = ("beta finding", "alpha finding", "gamma finding")
        first = points_of(_record(*texts))
        second = points_of(_record(*reversed(texts)))
        assert first == second, (first, second)

    def test_two_reviewers_do_not_collide(self) -> None:
        """两位评审者各自提出的点**都**被编号（不是按 reviewer 分表丢弃）。"""
        points = points_of(
            _record("same text", reviewer="gate:a") + _record("same text", reviewer="gate:b")
        )
        assert [point.point_id for point in points] == ["P1", "P2"], points
        # 同一个句子出自两位评审者 ⇒ **两条**点（各有各的编号）：它们是两个人的意见，
        # 合并会让「这条是谁提的」不可读，而编辑恰恰要按人核对返修是否到位。
        assert {point.reviewer for point in points} == {"gate:a", "gate:b"}

    def test_an_empty_review_yields_no_points(self) -> None:
        assert points_of(()) == ()
        assert points_of(_record()) == ()

    def test_the_prompt_lists_every_id_with_its_severity(self) -> None:
        """提示词那一段逐条带编号与严重性（模型不必自己数）。"""
        section = render_review_points_prompt(_POINTS)
        assert REVIEW_POINTS_SECTION_TITLE in section
        assert "- P1 (must_fix): FAIL: EVIDENCE_COVERAGE 0 >= 1" in section
        assert "- P2 (should_fix): the rationale is thin" in section

    def test_no_points_means_no_section(self) -> None:
        assert render_review_points_prompt(()) == ""


class TestEveryPointMustBeAnswered:
    """① **漏答** ⇒ 点名判红。"""

    def test_a_complete_set_passes(self) -> None:
        validate_responses(
            _POINTS,
            (
                AuthorResponse(point_id="P1", response="fixed the coverage", action_taken="added"),
                AuthorResponse(point_id="P2", response="expanded it", action_taken="rewrote"),
            ),
        )

    def test_a_missing_point_is_named(self) -> None:
        with pytest.raises(ResponseError) as raised:
            validate_responses(
                _POINTS,
                (AuthorResponse(point_id="P1", response="fixed", action_taken="added"),),
            )
        message = str(raised.value)
        assert "P2" in message, message
        assert "unanswered" in message, message

    def test_removing_one_answer_makes_the_verdict_red(self) -> None:
        """③ **删一条应答** ⇒ 判据**必须**红（证明它在逐条数，不是只看非空）。"""
        responses = parse_responses(
            _answers(("P1", "fixed the coverage"), ("P2", "expanded the rationale"))
        )
        validate_responses(_POINTS, responses)
        dropped = responses[:-1]
        with pytest.raises(ResponseError, match="P2"):
            validate_responses(_POINTS, dropped)

    def test_a_run_with_no_points_needs_no_answers(self) -> None:
        """没有评审点的 run：空应答是**正确**读数（不是漏答）。"""
        validate_responses((), ())


class TestAnInventedPointIdIsRefused:
    """② **编造 `point_id`** ⇒ 点名判红。"""

    def test_an_id_the_review_never_raised_is_named(self) -> None:
        with pytest.raises(ResponseError) as raised:
            validate_responses(
                _POINTS,
                (
                    AuthorResponse(point_id="P1", response="r1", action_taken="a"),
                    AuthorResponse(point_id="P2", response="r2", action_taken="a"),
                    AuthorResponse(point_id="P9", response="invented", action_taken="a"),
                ),
            )
        message = str(raised.value)
        assert "P9" in message, message
        assert "never raised" in message, message

    def test_the_message_lists_the_points_the_review_did_raise(self) -> None:
        """判词要让读者能自己修好：列出真实点表。"""
        with pytest.raises(ResponseError) as raised:
            validate_responses(
                _POINTS, (AuthorResponse(point_id="P7", response="x", action_taken="y"),)
            )
        assert "P1" in str(raised.value) and "P2" in str(raised.value)


class TestDuplicateAnswersAreRefused:
    def test_two_answers_to_one_point_are_named(self) -> None:
        with pytest.raises(ResponseError, match="more than once"):
            validate_responses(
                _POINTS,
                (
                    AuthorResponse(point_id="P1", response="a", action_taken="x"),
                    AuthorResponse(point_id="P1", response="b", action_taken="y"),
                    AuthorResponse(point_id="P2", response="c", action_taken="z"),
                ),
            )


class TestTheResponsePayloadIsParsedStrictly:
    def test_a_fenced_envelope_is_unwrapped(self) -> None:
        """真形态：信封 + 围栏 JSON 块（与决定块同一处解包器）。"""
        inner = _answers(("P1", "fixed"))
        envelope = json.dumps({
            "content": "Preamble.\n\n```json\n" + inner + "\n```\n",
            "declared_artifact": RESPONSES_KEY,
            "message_count": 2,
        })
        parsed = parse_responses(envelope)
        assert parsed == (
            AuthorResponse(point_id="P1", response="fixed", action_taken="changed P1"),
        )

    def test_a_missing_block_is_named(self) -> None:
        with pytest.raises(ResponseError, match=RESPONSES_KEY):
            parse_responses(json.dumps({"something": "else"}))

    def test_an_empty_response_text_is_named(self) -> None:
        with pytest.raises(ResponseError, match="says nothing"):
            parse_responses(_answers(("P1", "   ")))

    def test_an_entry_without_an_id_is_named(self) -> None:
        with pytest.raises(ResponseError, match="cannot be matched"):
            parse_responses(json.dumps({RESPONSES_KEY: [{"response": "x"}]}))


class TestTheLetterIsItemised:
    def test_every_point_gets_its_own_section(self) -> None:
        letter = response_letter(
            _POINTS,
            (
                AuthorResponse(point_id="P1", response="we added a source", action_taken="Methods"),
                AuthorResponse(point_id="P2", response="we rewrote it", action_taken="Discussion"),
            ),
        )
        assert "### P1 (must_fix)" in letter
        assert "### P2 (should_fix)" in letter
        assert "> FAIL: EVIDENCE_COVERAGE 0 >= 1" in letter
        assert "**Response.** we added a source" in letter
        assert "**Action taken.** Methods" in letter

    def test_an_unanswered_point_refuses_to_render(self) -> None:
        """**判据在渲染点**：漏答时不产出「看起来像应答信」的残件。"""
        with pytest.raises(ResponseError, match="unanswered"):
            response_letter(
                _POINTS, (AuthorResponse(point_id="P1", response="x", action_taken="y"),)
            )

    def test_a_run_without_points_renders_an_explicit_statement(self) -> None:
        text = response_letter((), ())
        assert "raised no points" in text


class TestTheReviewArtifactYieldsThePoints:
    """点表的**真正来源**：评审交付物里的 `weakest_link`（此前从未被解析成记录）。"""

    def test_the_weakest_link_becomes_a_point(self) -> None:
        remarks = remarks_of((
            ("gate:reviewer_a", {"verdict": "REJECT", "weakest_link": "no baseline"}),
        ))
        assert len(remarks) == 1
        assert remarks[0].text == "no baseline"
        assert remarks[0].reviewer == "gate:reviewer_a"
        # 判负的那位评审者提出的点更重（机械映射：只看 verdict 那个词）。
        assert remarks[0].severity == "must_fix"

    def test_an_accepting_review_speaks_should_fix(self) -> None:
        remarks = remarks_of((("gate:b", {"verdict": "ACCEPT", "weakest_link": "thin"}),))
        assert remarks[0].severity == "should_fix"

    def test_both_carriers_are_read(self) -> None:
        """`weakest_link` 与判词自述的 `findings[]` 都读（同一位评审者的两个面）。"""
        remarks = remarks_of((
            (
                "gate:a",
                {
                    "verdict": "REJECT",
                    "weakest_link": "no baseline",
                    "findings": ["the second arm is unexplained"],
                },
            ),
        ))
        assert [item.text for item in remarks] == ["no baseline", "the second arm is unexplained"]

    def test_an_empty_weakest_link_adds_nothing(self) -> None:
        assert remarks_of((("gate:a", {"verdict": "ACCEPT", "weakest_link": "  "}),)) == ()

    def test_two_reviewers_keep_their_own_points(self) -> None:
        """两位评审者各自的意见**都**进点表 —— 不合并（编辑按人核对返修）。"""
        points = points_of(
            remarks_of((
                ("gate:a", {"verdict": "REJECT", "weakest_link": "same"}),
                ("gate:b", {"verdict": "REJECT", "weakest_link": "same"}),
            ))
        )
        assert [point.point_id for point in points] == ["P1", "P2"]
        assert {point.reviewer for point in points} == {"gate:a", "gate:b"}
