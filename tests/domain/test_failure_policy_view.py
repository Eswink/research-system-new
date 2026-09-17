"""失败策略视图：能消费的键给取值，不能消费的键点名（GOAL-004 cycle 3 = EC-03）。

钉四件事：

1. 缺省（空 dict / None）⇒ `FAIL_RUN`，与既有隐式 fail-fast 逐字一致；
2. 已知键的合法取值被原样读出（`CONTINUE` ⇒ `tolerated is True`）；
3. 已知键的**非法取值**⇒ `ValueError`（响亮，不静默回退）；
4. 未知键进 `unhonored`（确定性排序）且**不影响取值**——"声明了但没人消费"必须可见，
   而不是被当成生效。
"""

from __future__ import annotations

import pytest

from packages.domain.enums import AcceptanceCriterionType
from packages.domain.failure_policy import FailurePolicyView, failure_policy_view
from packages.domain.tasks import AcceptanceCriterion, TaskContract


def _contract(**policy: str | bool | int | list[str]) -> TaskContract:
    return TaskContract(
        id="failure-policy-contract",
        version="1.0",
        purpose="failure policy must have a consumer",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        failure_policy=dict(policy),
    )


def test_an_undeclared_policy_means_fail_run() -> None:
    for policy in (None, {}):
        view = failure_policy_view(policy)
        assert view == FailurePolicyView()
        assert view.on_task_failure == "FAIL_RUN"
        assert view.tolerated is False
        assert view.declared == () and view.unhonored == ()


def test_declared_continue_is_read_back_as_tolerated() -> None:
    view = _contract(on_task_failure="CONTINUE").failure_policy_view()

    assert view.on_task_failure == "CONTINUE"
    assert view.tolerated is True
    assert view.declared == ("on_task_failure",)
    assert view.unhonored == ()


def test_an_illegal_value_fails_loudly() -> None:
    with pytest.raises(ValueError, match="unsupported on_task_failure value: 'MAYBE'"):
        _contract(on_task_failure="MAYBE").failure_policy_view()


def test_unknown_keys_are_named_and_do_not_change_the_value() -> None:
    """示例契约里的两个键就是这种：声明了，但本运行时没有消费者 ⇒ 明说，不假装。"""
    view = _contract(
        on_task_failure="CONTINUE",
        on_validation_failure="DEAD_LETTER",
        allow_partial_evidence=False,
    ).failure_policy_view()

    assert view.on_task_failure == "CONTINUE"
    assert view.unhonored == ("allow_partial_evidence", "on_validation_failure")
    assert view.declared == (
        "allow_partial_evidence",
        "on_task_failure",
        "on_validation_failure",
    )


def test_a_declaration_that_is_not_honored_changes_nothing() -> None:
    """钉住诚实边界：声明 `on_validation_failure` 不改变任何判定。"""
    with_extra = _contract(on_validation_failure="DEAD_LETTER").failure_policy_view()
    without = _contract().failure_policy_view()

    assert with_extra.on_task_failure == without.on_task_failure == "FAIL_RUN"
    assert with_extra.tolerated is False
