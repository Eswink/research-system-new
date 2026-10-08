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


__all__ = ["ValidityState", "validity_at"]
