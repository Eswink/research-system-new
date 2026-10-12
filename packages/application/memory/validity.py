"""记忆**时效**的判定（GOAL-20261008-039 EC-04）。

**为什么是纯函数**：判定必须**可复现** ⇒ 时点由**调用方给出**（`now`），
本模块**不读挂钟**。同一份记录 + 同一时点 ⇒ 判定必相同（判据据此把三态打满）。

三态（AGENTS.md §8「有过期/复核策略」的可判定形态）：

- `EXPIRED`：`expires_at <= now`（已过期）；
- `REVIEW_DUE`：`review_after <= now`（该复核了）—— 在未过期的前提下；
- `None`：两者都未到，**或都没声明** ⇒ **不猜**（未声明不得被当成「已到期」）。

`expires_at` 优先于 `review_after`（过期是更强的状态）。
"""

from __future__ import annotations

from enum import StrEnum

from packages.domain.core import Timestamp
from packages.domain.memory import MemoryRecord


class ValidityState(StrEnum):
    """一条记忆在给定时点上的时效状态（`None` 形态见 `validity_at` 的返回类型）。"""

    EXPIRED = "EXPIRED"
    REVIEW_DUE = "REVIEW_DUE"


def validity_at(record: MemoryRecord, now: Timestamp) -> ValidityState | None:
    """给定时点上该记录的时效状态（`None` = 未到期且无需复核，**或**未声明时效）。

    **不读挂钟**：`now` 由调用方给（可复现）。未声明 ⇒ `None`（**不**当成已到期）。
    """
    if record.expires_at is not None and record.expires_at.value <= now.value:
        return ValidityState.EXPIRED
    if record.review_after is not None and record.review_after.value <= now.value:
        return ValidityState.REVIEW_DUE
    return None


class ConflictTimelinessState(StrEnum):
    """**冲突声明本身**在给定时点上的时效状态（GOAL-20261012-061 EC-02）。

    与 `ValidityState` **同一族但**说的是另一件事：那里是**记录**的时效
    （「这条记忆过期了吗」），这里是**冲突声明**的时效（「这条记录当年声明的那个
    分歧**还算不算数**」）—— 两者**互不顶替**（记录的时效到了不代表冲突声明失效）。
    """

    REVIEW_DUE = "REVIEW_DUE"
    """`conflict_review_after <= now`（这条冲突声明该复核了）—— 在未失效的前提下。"""

    STALE = "STALE"
    """`conflict_expires_at <= now`（这条冲突声明**已失效**）—— 读面仍披露声明本身，
    但处置面据此判「不再算作当前冲突」。**不**自动删除 / **不**自动消解。"""


def conflict_timeliness_at(record: MemoryRecord, now: Timestamp) -> ConflictTimelinessState | None:
    """给定时点上该记录的**冲突声明**时效（`None` = 未到期且无需复核，**或**未声明）。

    三态**互不混用**（承 `validity_at` 的同一纪律）：

    - `STALE`：`conflict_expires_at <= now` —— **失效**（更强的状态，优先判）；
    - `REVIEW_DUE`：`conflict_review_after <= now` —— **该复核**（在未失效的前提下）；
    - `None`：两者都未到，**或都没声明** ⇒ **不猜**（未声明**不得**被当成「已失效」——
      那是 `X-3` 反证臂的形态）。

    **不读挂钟**：`now` 由调用方给（可复现）；**未声明冲突** ⇒ 也返回 `None`
    （没有冲突声明就没有「冲突时效」可言 —— 与 `_validate_conflict_timeliness` 的
    「声明了时效却没有冲突」点名拒绝互为两面）。
    """
    if not record.contradictions:
        return None
    expires_at = record.conflict_expires_at
    if expires_at is not None and expires_at.value <= now.value:
        return ConflictTimelinessState.STALE
    review_after = record.conflict_review_after
    if review_after is not None and review_after.value <= now.value:
        return ConflictTimelinessState.REVIEW_DUE
    return None


__all__ = ["ConflictTimelinessState", "ValidityState", "conflict_timeliness_at", "validity_at"]
