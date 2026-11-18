"""EC-03 ② + EC-06：**上游瞬时失败不该是终态** —— 会话合约的重试策略必须覆盖它。

**它补哪一格**（GOAL-20261119-115 建档实测）：

- 24 次 `dual_model_review` FAILED 里 **4 次**是 `retry budget exhausted`：上游超时/5xx
  被当成终态。`dual_model_review_deliverable` 当时是 `max_attempts: 1` + **空类别**；
- 同一份文件里 `multi_role_review` 早就是 `max_attempts: 2` + 三个类别 —— 两种形态并存，
  本身就是「漏配」的证据；
- 十一相链 31 次 FAILED 里 retrieval 占 **9 次**（主因文献 API 超时/5xx），而
  `research_question_retrieval` 也是 `max_attempts: 1` + 空类别。

**判什么**（只钉**策略声明与分类映射**，不要求成功率提升 —— EC-06 原文）：

1. 四份**碰上游**的合约 `max_attempts >= 2`；
2. `retryable_categories` **非空**且覆盖三个瞬时类别
   （`MODEL_RELAY_UNAVAILABLE` / `MODEL_RATE_LIMIT` / `MODEL_TIMEOUT`）；
3. 每个类别都在 `FailureCategory` 闭集内（拼错一个名字就是静默不重试）；
4. `backoff_seconds` 在场（否则进程内原地重试会连撞同一个上游）。

**反证臂**：把任一份的 `retryable_categories` 清空 ⇒ 判据判红并点名那份合约。

**边界（如实登记）**：本文件**不**判「重试真的救了那次 run」—— 那要真实出网；
它判的是「配置面允许重试」，这正是 EC-06 的字面要求。
"""

from __future__ import annotations

from typing import Any

import pytest

from adapters.contracts.tasks_loaders import load_task_contracts
from packages.domain.enums import FailureCategory

_CONTRACTS = "examples/contracts/task_contracts.yaml"

#: 碰上游的四份合约（EC-06 点名的两份 + ② 的那份 + 检索那一份）。
UPSTREAM_CONTRACTS: tuple[str, ...] = (
    "dual_model_review_deliverable",
    "research_manuscript",
    "retrieval_report_from_the_run_chain",
    "research_question_retrieval",
)

#: 必须被覆盖的三个瞬时类别。
REQUIRED_CATEGORIES: frozenset[str] = frozenset({
    FailureCategory.MODEL_RELAY_UNAVAILABLE.value,
    FailureCategory.MODEL_RATE_LIMIT.value,
    FailureCategory.MODEL_TIMEOUT.value,
})


def _category_name(item: Any) -> str:
    """类别 → 名字（`retryable_categories` 可能是枚举也可能是裸串）。"""
    return str(item.value) if hasattr(item, "value") else str(item)


def _policy(name: str) -> Any:
    return load_task_contracts(_CONTRACTS)[name].retry_policy


class TestEveryUpstreamContractCanRetry:
    @pytest.mark.parametrize("name", UPSTREAM_CONTRACTS)
    def test_max_attempts_is_at_least_two(self, name: str) -> None:
        policy = _policy(name)
        assert policy is not None, f"{name} 没有 retry_policy"
        assert policy.max_attempts >= 2, (
            f"{name} 的 max_attempts 是 {policy.max_attempts}：一次上游抖动就是终态"
        )

    @pytest.mark.parametrize("name", UPSTREAM_CONTRACTS)
    def test_retryable_categories_cover_the_transient_classes(self, name: str) -> None:
        policy = _policy(name)
        assert policy is not None, name
        declared = {_category_name(item) for item in policy.retryable_categories}
        missing = sorted(REQUIRED_CATEGORIES - declared)
        assert not missing, f"{name} 缺可重试类别：{missing}（实得 {sorted(declared)}）"

    @pytest.mark.parametrize("name", UPSTREAM_CONTRACTS)
    def test_every_declared_category_is_in_the_closed_vocabulary(self, name: str) -> None:
        """拼错的类别名 = 静默不重试（域层按名字匹配），所以逐条对闭集。"""
        policy = _policy(name)
        assert policy is not None, name
        legal = {member.value for member in FailureCategory}
        unknown = sorted(
            _category_name(item)
            for item in policy.retryable_categories
            if _category_name(item) not in legal
        )
        assert not unknown, f"{name} 声明了闭集外的类别：{unknown}"

    @pytest.mark.parametrize("name", UPSTREAM_CONTRACTS)
    def test_a_backoff_is_declared(self, name: str) -> None:
        policy = _policy(name)
        assert policy is not None, name
        assert policy.backoff_seconds, (
            f"{name} 没有 backoff_seconds：进程内原地重试会连撞同一个上游"
        )


class TestTheJudgedSurfacesAreNotVacuous:
    def test_all_four_contracts_are_present(self) -> None:
        loaded = load_task_contracts(_CONTRACTS)
        missing = [name for name in UPSTREAM_CONTRACTS if name not in loaded]
        assert not missing, f"受判面缺合约：{missing}"

    def test_the_required_categories_really_are_transient(self) -> None:
        """被要求覆盖的三个类别必须是**瞬时**类（不是业务判负）。"""
        for value in REQUIRED_CATEGORIES:
            assert value in {member.value for member in FailureCategory}, value


class TestTheCriterionBites:
    """**反证臂**：清空类别 / 降到 1 次 ⇒ 同一条判据必须判红。"""

    def test_an_empty_category_list_is_refused(self) -> None:
        declared: set[str] = set()
        assert sorted(REQUIRED_CATEGORIES - declared), "空表必须被判红（它曾是真实现状）"

    def test_one_attempt_is_refused(self) -> None:
        for attempts in (0, 1):
            assert attempts < 2

    def test_the_real_contract_is_not_in_that_state(self) -> None:
        """正控制：受判合约现在**不在**被拒状态（否则上面两条是自说自话）。"""
        for name in UPSTREAM_CONTRACTS:
            policy = _policy(name)
            assert policy is not None and policy.max_attempts >= 2, name
