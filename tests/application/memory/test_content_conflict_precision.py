"""GOAL-20261018-083 EC-04 判据：**不 false-positive** —— 真实语料上**零误报**。

**为什么这条是硬要求**：内容级判定在**写入时**拒绝提案。一次误报 = 一条**本可写入**的记忆
被掐死。与「漏判」相比，误报对系统的伤害更直接（漏判只是回到旧行为，误报是新增的破坏）。

判据分三组（**逐条列语料与期望**，不是「看起来没问题」）：

1. **同义 / 改写**（应 `None`）：同一件事的两种说法；
2. **无关 / 不同主语**（应 `None`）：不是同一句话；
3. **真实语料**（应 `None`）：仓内既有测试用过的记忆正文形态（短串、中英混排、长句）。

**射程边界**（`W-2`，逐条明写）：本模块**只判三种可机械判的形态**。需要**世界知识**才能判的
矛盾（`the drug is effective` vs `it does not work`）、依赖同义词表的改写（`increase` vs
`rise`）、需要推演的数值关系（`2x` vs `twice`）**均不判** —— 判据在这里**断言它们不判**
（而不是假装判得了），这条与「误报」同等重要：含糊地判会两头都错。
"""

from __future__ import annotations

import pytest

from packages.application.memory.content_conflict import detect_content_conflict

#: 同义 / 改写：同一件事的两种说法 ⇒ **不该**判冲突。
_SYNONYMOUS: tuple[tuple[str, str], ...] = (
    ("the ratio increases with n", "the ratio grows with n"),
    ("duplicate pairs inflate support", "duplicate pairs raise apparent support"),
    ("该药有效", "该药有疗效"),
    ("the metric is 2.0 ms", "the measured metric equals 2.0 ms"),
)

#: 无关 / 不同主语：不是同一句话 ⇒ **不该**判冲突。
_UNRELATED: tuple[tuple[str, str], ...] = (
    ("the ratio increases with n", "the metric is 0.5"),
    ("X supports Y", "Z supports W"),
    ("alpha is beta", "alpha is gamma"),
    ("temperature is 5", "pressure is 9"),
    ("pipeline A finishes in 3 minutes", "pipeline B finishes in 40 minutes"),
)

#: 真实语料（仓内既有测试与文档里出现过的记忆正文形态）⇒ **不该**判冲突。
_REAL_WORLD: tuple[tuple[str, str], ...] = (
    ("A", "B"),
    ("mem-1", "mem-2"),
    ("changed content", "observed sorting baseline is O(n log n)"),
    (
        "First round lesson: duplicate_pairs must be pinned before comparing arms.",
        "Organization policy: pre-register every hypothesis before running.",
    ),
    (
        "Earlier runs found FAIR pipelines reproduce better than ad-hoc ones.",
        "the ratio increases with n",
    ),
    ("内容 1", "内容 2"),
    ("", "observed sorting baseline is O(n log n)"),
)

#: **射程边界**：这些形态**本质上判不了**（需要世界知识 / 同义词表 / 推演）⇒ 必须 `None`。
#: 断言它们 `None` 是**有意的**：含糊地判会两头都错（既误报又不可复核）。
_OUT_OF_SCOPE: tuple[tuple[str, str], ...] = (
    ("the drug is effective", "it does not work"),
    ("the ratio increases with n", "the ratio rises with n"),
    ("the runtime is 2x faster", "the runtime is twice as fast"),
    ("this approach is better", "that approach is worse"),
)


@pytest.mark.parametrize(("first", "second"), _SYNONYMOUS)
def test_synonymous_restatements_are_not_flagged(first: str, second: str) -> None:
    assert detect_content_conflict(first, second) is None, (first, second)


@pytest.mark.parametrize(("first", "second"), _UNRELATED)
def test_unrelated_statements_are_not_flagged(first: str, second: str) -> None:
    assert detect_content_conflict(first, second) is None, (first, second)


@pytest.mark.parametrize(("first", "second"), _REAL_WORLD)
def test_real_world_corpus_has_zero_false_positives(first: str, second: str) -> None:
    assert detect_content_conflict(first, second) is None, (first, second)


@pytest.mark.parametrize(("first", "second"), _OUT_OF_SCOPE)
def test_out_of_scope_forms_are_explicitly_not_judged(first: str, second: str) -> None:
    """**射程边界**：判不了的形态必须 `None`（不假装判得了）。"""
    assert detect_content_conflict(first, second) is None, (first, second)


def test_the_corpus_is_not_vacuous() -> None:
    """语料不得空转：三组都非空，且**至少一条**同组内的正向对照能判出冲突。

    「全是 `None`」的语料即使实现退化成恒 `None` 也会全绿 ⇒ 必须有正向对照。
    """
    assert _SYNONYMOUS and _UNRELATED and _REAL_WORLD and _OUT_OF_SCOPE
    assert detect_content_conflict("X supports Y", "X does not support Y") is not None
    assert detect_content_conflict("the metric is 2.0 ms", "the metric is 0.5 ms") is not None
