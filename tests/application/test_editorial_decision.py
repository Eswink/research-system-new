"""GOAL-20261029-100 EC-02：**投稿决策面**可判（四值闭集 + 两条反证）。

**它补哪一格**（建档实测）：`scientific_editor` 角色在 `roles.yaml` 里早就在
（`ReviewPanelRole.WRITER`），但**从未被任何协议激活**（`grep -rl scientific_editor
examples/protocols/` 零命中）；决定词表当时只有验收门的 `PASS` / `REJECT` 两值。
本文件把「编辑决定」这一面钉成机械事实。

**判据分四组**：

1. **四值各可判**（`ACCEPT` / `MINOR_REVISION` / `MAJOR_REVISION` / `REJECT` 逐个参数化）；
2. **反证：越界值点名拒绝**（含大小写 / 拼写 / 近义词 —— 本模块**不**做宽容匹配）；
3. **反证：要求返修却不说要改什么 ⇒ 点名判红**（`required_changes` 为空）；
4. **面不混用**：`EditorialDecision` 与 `QualityGateVerdict` 是两套词表，取值不重叠。

**零出网 / 零模型**：全部是纯函数输入输出。
"""

from __future__ import annotations

import json

import pytest

from packages.application.deliverable.editorial_decision import (
    CHANGES_FIELD,
    DECISION_FIELD,
    DECISION_KEY,
    RATIONALE_FIELD,
    EditorialDecisionError,
    EditorialOutcome,
    parse_editorial_decision,
)
from packages.domain.enums import EditorialDecision, QualityGateVerdict

_RATIONALE = "the review found the second arm's metric unexplained, and the body does not fix it"


def _block(**overrides: object) -> str:
    body: dict[str, object] = {
        DECISION_FIELD: "accept",
        RATIONALE_FIELD: _RATIONALE,
        CHANGES_FIELD: [],
    }
    body.update(overrides)
    return json.dumps({DECISION_KEY: body})


class TestEveryDeclaredValueIsDecidable:
    """① 四个取值各可判（逐个参数化 —— 少一个就说明词表与判据分叉）。"""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("accept", EditorialDecision.ACCEPT),
            ("minor_revision", EditorialDecision.MINOR_REVISION),
            ("major_revision", EditorialDecision.MAJOR_REVISION),
            ("reject", EditorialDecision.REJECT),
        ],
    )
    def test_the_value_is_parsed(self, raw: str, expected: EditorialDecision) -> None:
        changes = [] if expected is EditorialDecision.ACCEPT else ["add the missing baseline"]
        outcome = parse_editorial_decision(_block(**{DECISION_FIELD: raw, CHANGES_FIELD: changes}))
        assert outcome.decision is expected
        assert outcome.rationale == _RATIONALE
        assert outcome.required_changes == tuple(changes)

    def test_accept_may_carry_no_changes(self) -> None:
        """`accept` **允许**空改动清单（那是「不用改」，不是「要求返修却不说」）。"""
        outcome = parse_editorial_decision(_block(CHANGES_FIELD=[]))
        assert outcome.decision is EditorialDecision.ACCEPT
        assert outcome.required_changes == ()
        assert outcome.decision.requires_changes is False

    @pytest.mark.parametrize(
        "decision",
        [
            EditorialDecision.MINOR_REVISION,
            EditorialDecision.MAJOR_REVISION,
            EditorialDecision.REJECT,
        ],
    )
    def test_every_non_accept_value_requires_changes(self, decision: EditorialDecision) -> None:
        assert decision.requires_changes is True

    def test_the_payload_round_trips(self) -> None:
        """落库载荷与输入块**同形**（取值用枚举的 `value`，不是成员名）。"""
        outcome = EditorialOutcome(
            decision=EditorialDecision.MAJOR_REVISION,
            rationale=_RATIONALE,
            required_changes=("rerun the second arm with the same seed",),
        )
        payload = outcome.as_payload()
        assert payload == {
            DECISION_FIELD: "major_revision",
            RATIONALE_FIELD: _RATIONALE,
            CHANGES_FIELD: ["rerun the second arm with the same seed"],
        }
        # 同一份载荷再走一遍解析 ⇒ 同一个决定（往返稳定）。
        reparsed = parse_editorial_decision(json.dumps({DECISION_KEY: payload}))
        assert reparsed.decision is EditorialDecision.MAJOR_REVISION

    def test_the_markdown_names_the_decision_and_each_change(self) -> None:
        outcome = EditorialOutcome(
            decision=EditorialDecision.MINOR_REVISION,
            rationale=_RATIONALE,
            required_changes=("cite the second retrieved record", "fix the arm label"),
        )
        text = outcome.markdown()
        assert "**minor_revision**" in text
        assert "1. cite the second retrieved record" in text
        assert "2. fix the arm label" in text


class TestAnOutOfVocabularyValueIsRefusedByName:
    """② 反证：越界值点名拒绝 —— 含大小写、拼写、近义词三种形态。"""

    @pytest.mark.parametrize(
        "raw",
        [
            "ACCEPT",  # 大小写变了
            "Accept",
            "accepted",  # 近义词 / 词形变化
            "minor revisions",  # 空格
            "minorrevision",  # 掉了下划线
            "revise",  # 验收门的词（这是**另一个面**的词）
            "PASS",  # 验收门的判词
            "major",  # 半个词
            "",  # 空
        ],
    )
    def test_an_unknown_value_names_the_four_allowed_ones(self, raw: str) -> None:
        with pytest.raises(EditorialDecisionError) as raised:
            parse_editorial_decision(_block(**{DECISION_FIELD: raw, CHANGES_FIELD: ["x"]}))
        message = str(raised.value)
        assert repr(raw) in message, message
        # 判词必须列出**四**个合法取值（读者据此能自己修好）。
        for value in ("accept", "minor_revision", "major_revision", "reject"):
            assert value in message, (value, message)

    def test_the_enum_itself_refuses_without_the_parser(self) -> None:
        """反证的底：`EditorialDecision.parse` 自己就拒（不是靠解析器包一层）。"""
        with pytest.raises(ValueError, match="major"):
            EditorialDecision.parse("major")


class TestAskingForChangesWithoutSayingWhatIsRefused:
    """③ 反证：「要求返修却不说什么要改」⇒ **点名**判红。"""

    @pytest.mark.parametrize("decision", ["minor_revision", "major_revision", "reject"])
    def test_an_empty_change_list_under_a_revision_is_named(self, decision: str) -> None:
        with pytest.raises(EditorialDecisionError) as raised:
            parse_editorial_decision(_block(**{DECISION_FIELD: decision, CHANGES_FIELD: []}))
        message = str(raised.value)
        assert decision in message, message
        assert "required_changes" in message, message
        assert "empty" in message or "not actionable" in message, message

    def test_a_missing_change_list_under_a_revision_is_named(self) -> None:
        """**缺键**与**空列表**同一判决（都不说改什么）。"""
        raw = json.dumps({DECISION_KEY: {DECISION_FIELD: "reject", RATIONALE_FIELD: _RATIONALE}})
        with pytest.raises(EditorialDecisionError, match="required_changes"):
            parse_editorial_decision(raw)

    def test_an_empty_entry_inside_the_list_is_named(self) -> None:
        """列表里混一条空串 ⇒ 点名（不静默丢那一条：那会让「改三件事」变成「改两件事」）。"""
        with pytest.raises(EditorialDecisionError, match="empty entry"):
            parse_editorial_decision(
                _block(**{DECISION_FIELD: "reject", CHANGES_FIELD: ["a real change", "   "]})
            )

    def test_a_non_list_change_field_is_named(self) -> None:
        """`required_changes` 写成字符串 ⇒ 点名（不猜「是不是想表达一条」）。"""
        with pytest.raises(EditorialDecisionError, match="must be a list"):
            parse_editorial_decision(
                _block(**{DECISION_FIELD: "reject", CHANGES_FIELD: "one change"})
            )

    def test_an_empty_rationale_is_named(self) -> None:
        """理由不得为空：没有理由的决定，下游无人可复核。"""
        raw = json.dumps({
            DECISION_KEY: {
                DECISION_FIELD: "accept",
                RATIONALE_FIELD: "   ",
                CHANGES_FIELD: [],
            }
        })
        with pytest.raises(EditorialDecisionError, match="no rationale"):
            parse_editorial_decision(raw)


class TestTheTwoFacesStaySeparate:
    """④ 面不混用：编辑决定 ≠ 验收门判词（词表不重叠、互不改名）。"""

    def test_no_value_is_shared_with_the_quality_gate_verdict(self) -> None:
        editorial = {member.value for member in EditorialDecision}
        gate = {member.value for member in QualityGateVerdict}
        assert editorial & gate == set(), (sorted(editorial & gate), sorted(gate))

    def test_the_gate_words_are_unchanged(self) -> None:
        """既有门判词**逐字**未动（100+ 处引用；本 GOAL 不改它们）。"""
        assert QualityGateVerdict.PASS.value == "PASS"
        assert QualityGateVerdict.REVISE.value == "REVISE"
        assert QualityGateVerdict.BLOCK.value == "BLOCK"
        assert QualityGateVerdict.PASS_WITH_WARNINGS.value == "PASS_WITH_WARNINGS"

    def test_the_four_values_are_exactly_the_four_declared(self) -> None:
        """词表本身就是判据的受判面：四个、不多不少、逐字小写下划线形态。"""
        assert [member.value for member in EditorialDecision] == [
            "accept",
            "minor_revision",
            "major_revision",
            "reject",
        ]


class TestTheEnvelopeFormIsAccepted:
    """真会话的交付物是**信封**（`content` = 模型全文）；受控夹具给直形态。两形态都认。"""

    def test_the_envelope_is_unwrapped(self) -> None:
        """**真形态**：信封 + 正文里的围栏 JSON 块（两层都由既有解包器揭开）。

        判别键 `declared_artifact` **必须在**（那是 `declared_object` 解信封的唯一条件）
        —— 本夹具照抄产品路径上的真实字节形状，不是简化版：实测 `content` 里是
        ```` ```json {…} ``` ```` 这样的围栏块，而不是裸 JSON。
        """
        inner = _block(CHANGES_FIELD=[])
        envelope = json.dumps({
            "content": "A short preamble.\n\n```json\n" + inner + "\n```\n",
            "message_count": 2,
            "contract_id": "editorial_decision",
            "declared_artifact": "editorial_decision",
        })
        outcome = parse_editorial_decision(envelope)
        assert outcome.decision is EditorialDecision.ACCEPT

    def test_the_direct_form_is_accepted(self) -> None:
        outcome = parse_editorial_decision(_block(CHANGES_FIELD=[]))
        assert outcome.decision is EditorialDecision.ACCEPT

    def test_an_empty_artifact_is_named(self) -> None:
        with pytest.raises(EditorialDecisionError, match="empty"):
            parse_editorial_decision("")

    def test_a_missing_block_names_the_keys_it_did_see(self) -> None:
        with pytest.raises(EditorialDecisionError) as raised:
            parse_editorial_decision(json.dumps({"decision": "accept"}))
        message = str(raised.value)
        assert DECISION_KEY in message, message
        assert "decision" in message, message
