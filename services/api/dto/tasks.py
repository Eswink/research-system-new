"""任务级人工干预 DTO（GOAL-20261008-033 EC-01）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TaskRetryDto(BaseModel):
    """人工恢复一条死信任务的结论（ADR-0033 的产品入口）。

    `result` 是**引擎的权威结论**（成功时逐字为 `restored`；三实现同判，由
    `tests/contracts/test_dead_letter_manual_recovery_contract.py` 钉住）。本端点不
    追加第二套结论词表 —— 引擎说什么就带回什么。
    """

    task_id: str = Field(min_length=1)
    result: str = Field(min_length=1)
    note: str = Field(min_length=1)
