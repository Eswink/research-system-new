"""ProgramStore Port：研究程序的声明与推进决策存储（GOAL-20261008-037 EC-01）。

职责：
- `ResearchProgram` 的持久化（程序声明 = 项目 + 协议 + 上界护栏 + 声明式续跑规则）；
- `ProgramDecision` 的 **append-only** 记录（每次推进一条，含被引 canonical 事实的
  **原文**）。

**非职责**（边界写进 Port，防止第二套真相）：

- **不**存「程序 → run」的映射：run 的归属在 `ResearchRun.program_id` /
  `program_index` 上，查询走 `RunStore.for_program`（canonical 唯一来源）。
- **不**重算结论、**不**决定业务规则：续跑规则由 domain `ProgramContinueRule` 表达，
  判定的输入是**已落库**的 run 事实与评审判词。
- 决策是**事实**（append-only）：重复推进产生的是**多条**决策（各自带时间），
  而不是覆盖 —— 去重（不重复起 run）由 run 面承担（序号已存在 ⇒ `DEDUP` 决策）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.domain.program import ProgramDecision, ResearchProgram


@runtime_checkable
class ProgramStore(Protocol):
    """研究程序声明 + 推进决策的存储。"""

    def create(self, program: ResearchProgram) -> None: ...

    def get(self, program_id: str) -> ResearchProgram: ...

    def for_project(self, project_id: str) -> tuple[ResearchProgram, ...]: ...

    def record_decision(self, decision: ProgramDecision) -> None: ...

    def decisions_of(self, program_id: str) -> tuple[ProgramDecision, ...]: ...

    def close(self) -> None: ...
