"""退避时延是策略面的纯函数（GOAL-003 cycle 16 / PLAN-20260915-079）。

收口前：策略面根本没有时延字段（`retryPolicy` 只有 `max_attempts` +
`retryable_categories`，schema `additionalProperties: false`），"重排"等于"立刻再派发"——
失败快的任务会在 `max_attempts` 内热循环。本文件把时延钉成**可算的数**：
指数增长、能被上限封顶、没写字段就是零、非法值在构造时就被拒。
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from packages.domain.enums import AcceptanceCriterionType, FailureCategory
from packages.domain.tasks import AcceptanceCriterion, RetryPolicy, TaskContract


def _contract(policy: RetryPolicy | None) -> TaskContract:
    return TaskContract(
        id="backoff-contract",
        version="1.0",
        purpose="retry backoff",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=policy,
    )


def test_backoff_grows_exponentially_from_the_base() -> None:
    contract = _contract(
        RetryPolicy(
            max_attempts=5,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=30,
        )
    )

    assert contract.retry_delay(attempt=1) == timedelta(seconds=30)
    assert contract.retry_delay(attempt=2) == timedelta(seconds=60)
    assert contract.retry_delay(attempt=3) == timedelta(seconds=120)


def test_the_cap_only_caps_it_never_lowers_the_base() -> None:
    contract = _contract(
        RetryPolicy(
            max_attempts=9,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=30,
            max_backoff_seconds=100,
        )
    )

    assert contract.retry_delay(attempt=1) == timedelta(seconds=30)
    assert contract.retry_delay(attempt=2) == timedelta(seconds=60)
    assert contract.retry_delay(attempt=3) == timedelta(seconds=100), "被上限封顶"
    assert contract.retry_delay(attempt=8) == timedelta(seconds=100)


@pytest.mark.parametrize(
    "policy",
    [
        None,
        RetryPolicy(max_attempts=3, retryable_categories=[FailureCategory.MODEL_TIMEOUT]),
        RetryPolicy(
            max_attempts=3,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=0,
        ),
    ],
)
def test_no_backoff_declared_means_no_wait(policy: RetryPolicy | None) -> None:
    """没策略 / 没写基数 / 基数为 0 ⇒ 零时延（退避字段出现之前的行为）。"""
    assert _contract(policy).retry_delay(attempt=1) == timedelta(0)


def test_illegal_backoff_values_are_rejected_at_construction() -> None:
    with pytest.raises(ValueError, match="backoff_seconds must be >= 0"):
        RetryPolicy(max_attempts=3, backoff_seconds=-1)
    with pytest.raises(ValueError, match="max_backoff_seconds must be >= 0"):
        RetryPolicy(max_attempts=3, backoff_seconds=5, max_backoff_seconds=-1)
    with pytest.raises(ValueError, match="max_backoff_seconds must be >= backoff_seconds"):
        RetryPolicy(max_attempts=3, backoff_seconds=30, max_backoff_seconds=5)


def test_attempt_must_be_a_real_attempt_number() -> None:
    contract = _contract(RetryPolicy(max_attempts=3, backoff_seconds=10))
    with pytest.raises(ValueError, match="attempt must be >= 1"):
        contract.retry_delay(attempt=0)
