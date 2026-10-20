"""GOAL-20261020-091 EC-01：**评审者自己写下的判词真的进判定面**（信封形态）。

**它咬住的缺口（建档实测）**：真实会话的交付物是**信封**
（`adapters/openhands/runtime_adapter.py::_deliverable` ⇒
`{declared_artifact: {content, message_count, …}}`，模型正文在 `content` 里），而
`evaluation_gate.declared_review_score` 从**顶层**结构化输出按点分路径取值 ⇒ 信封形态下
恒 `None` ⇒ 判词恒 `review score unknown` ⇒ 恒判负。后果不是「评审不严」，而是
**两个评审模型无论各自判什么，判定面看到的都是同一个「不知道」** —— 阶梯「复检」域的
`下一级`（评审真的用不同模型判出负）因此**结构不可达**。

**四条读数（成对）**：

1. **直形态逐字不变**：`{"review_decision": {"score": 0.5}}` ⇒ `0.5`（既有口径，零回归）；
2. **信封形态**：正文里那份 JSON 的分数被取到（`0.5` / `0.95` 两个方向）；
3. **fail-closed 逐字不变**：正文里没有 JSON / 分数不是数 / 分数是布尔 / 路径缺失 ⇒
   `None`（**不**回落默认分，「没有评审结论」与「评审结论很差」必须相反）；
4. **信封不是直形态的替代**：解包只发生在那两个判别键同时成立时；直形态的普通对象
   （键名恰好也叫 `content`）**不**被当成信封。
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from packages.application.run_orchestration.evaluation_gate import declared_review_score
from packages.domain.enums import AcceptanceCriterionType, ComparisonOperator
from packages.domain.tasks import AcceptanceCriterion, TaskContract

_PATH = "review_decision.score"


def _contract() -> TaskContract:
    """声明了 `REVIEW_SCORE` 的合约（与出厂 `review_scored_deliverable` 同形）。"""
    return TaskContract(
        id="review_scored_deliverable",
        version="1.0.0",
        purpose="judge the artifact and state a score",
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.REVIEW_SCORE,
                metric=_PATH,
                operator=ComparisonOperator.GTE,
                threshold=Decimal("0.8"),
            )
        ],
    )


def _envelope(content: str) -> dict[str, dict[str, object]]:
    """**真实会话交付物**的信封（七个恒发键；正文在 `content` 里）。"""
    return {
        "review_decision": {
            "content": content,
            "message_count": 1,
            "conversation_id": "conv-1",
            "session_id": "sess-1",
            "fact_name": "session_message",
            "declared_artifact": "review_decision",
            "contract_id": "review_scored_deliverable",
        }
    }


def _score(payload: Mapping[str, Any]) -> Decimal | None:
    return declared_review_score(_contract(), payload)


def test_the_plain_shape_is_unchanged() -> None:
    """① 直形态（受控执行体给的形状）逐字不变 ⇒ 既有判据零回归。"""
    assert _score({"review_decision": {"verdict": "ACCEPT", "score": 0.5}}) == Decimal("0.5")
    assert _score({"review_decision": {"verdict": "ACCEPT", "score": 0.95}}) == Decimal("0.95")


def test_the_score_inside_the_envelope_is_read() -> None:
    """② 信封形态：模型正文里写下的分数**取得到**（这是两个模型能判出不同结论的前提）。"""
    low = _envelope(
        'My verdict.\n```json\n{"review_decision": {"verdict": "REJECT", "score": 0.5}}\n```'
    )
    high = _envelope('{"review_decision": {"verdict": "ACCEPT", "score": 0.95}}')
    assert _score(low) == Decimal("0.5")
    assert _score(high) == Decimal("0.95")
    assert _score(low) != _score(high), "同一份被评对象上的两个不同判分必须读出两个不同的数"


def test_an_unreadable_envelope_stays_fail_closed() -> None:
    """③ fail-closed 逐字不变：读不到 ⇒ `None`（**不**回落默认分）。"""
    assert _score(_envelope("no json in this reply")) is None
    assert _score(_envelope('{"review_decision": {"score": "high"}}')) is None
    assert _score(_envelope('{"review_decision": {"score": true}}')) is None
    assert _score(_envelope('{"review_decision": {"verdict": "ACCEPT"}}')) is None
    assert _score(_envelope('{"other_artifact": {"score": 0.9}}')) is None
    assert _score({}) is None
    assert _score({"review_decision": {"content": "text but no envelope mark"}}) is None


def test_a_plain_object_that_happens_to_have_content_is_not_an_envelope() -> None:
    """④ 解包只认**两个判别键同时成立**：普通对象不被当成信封（不猜）。"""
    plain: dict[str, Any] = {"review_decision": {"content": "some notes", "score": 0.5}}
    assert _score(plain) == Decimal("0.5")
    # 只有 `content` 没有 `declared_artifact` ⇒ 不解包 ⇒ 正文里的分数**不**被当成顶层分数。
    only_content = _envelope('{"review_decision": {"score": 0.9}}')
    inner = dict(only_content["review_decision"])
    inner.pop("declared_artifact")
    assert _score({"review_decision": inner}) is None
