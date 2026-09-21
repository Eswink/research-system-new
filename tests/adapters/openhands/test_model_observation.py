"""GOAL-010 EC-04：adapter 侧的**模型观测**（provider 侧报告了哪个 model 名）。

判据的射程只有一件事：从 adapter 已经在读的 `ConversationStats` 里取出「**返回的**
model 名」——它与请求里写的 model id 是两件事，同名漂移（AGENTS.md §4）正是靠两者的
差才可见。这里**不**判「漂移是否发生」（那要有两次观测才谈得上），只判观测本身：

1. SDK 的默认哨兵 `model_name="default"` **不是**观测值（E-14）——当它当观测值等于把
   哨兵洗成指纹事实；
2. 多个来源的 model 名去重、排序（读面因此可复算）；
3. 空 stats ⇒ 空观测（不是"观测到了空"）。
"""

from __future__ import annotations

from openhands.sdk.conversation.conversation_stats import ConversationStats
from openhands.sdk.llm.utils.metrics import Metrics

from adapters.openhands.usage_mapping import observed_model_names


def _metrics(model_name: str) -> Metrics:
    metrics = Metrics(model_name=model_name)
    return metrics


def test_the_sdk_sentinel_is_not_an_observation() -> None:
    """默认哨兵 `"default"` ⇒ **没有观测**（不得当成一个 model 名写进指纹）。"""
    stats = ConversationStats(usage_to_metrics={"u-1": Metrics()})
    assert Metrics().model_name == "default", "哨兵值变了 ⇒ 本判据要跟着改"
    assert observed_model_names(stats) == ()


def test_observed_names_are_deduplicated_and_sorted() -> None:
    """多个来源给同一个名字 ⇒ 一个值；给不同名字 ⇒ 两个值（原样，不去重成"最新"）。"""
    stats = ConversationStats(
        usage_to_metrics={
            "u-2": _metrics("relay-model-beta"),
            "u-1": _metrics("relay-model-alpha"),
            "u-3": _metrics("relay-model-alpha"),
        }
    )
    assert observed_model_names(stats) == ("relay-model-alpha", "relay-model-beta")


def test_no_usage_means_no_observation() -> None:
    """没有任何 usage 度量 ⇒ 空观测（读面据此点名缺项，而不是拿到一个空字符串）。"""
    assert observed_model_names(ConversationStats()) == ()
