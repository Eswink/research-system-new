"""研究程序控制面 DTO（GOAL-20261008-037 EC-02）。

三个面（与 `memory.py` / `runs.py` 的诚实边界同一口径）：

- 建程序：声明 = 项目 + 协议路径 + 上界护栏 + **声明式续跑规则**（判词取值域）；
- 推进：一次推进的输入（无参数 —— 判定全取落库事实）+ 结果（决策种类 / 理由 /
  被引 run / 是否起了新 run）；
- 读面：程序 + 各轮 run 摘要 + **逐条决策**（`decisions` 是「为何继续 / 为何停」的
  可读面；`cited_facts` 是被引 canonical 事实的**原文**）。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProgramCreateDto(BaseModel):
    """建程序的输入（协议按 `examples/protocols/` 内路径解析，与启动 run 同一校验）。"""

    protocol_path: str
    max_runs: int = Field(default=3, ge=1, le=20)
    #: 续跑规则：上一轮**落库**评审结论的 `verdict` 命中其中之一 ⇒ 结论面判「续」。
    continue_on_verdicts: list[str] = Field(default_factory=lambda: ["PASS"])
    #: GOAL-20261008-040 EC-02：每个序号允许的尝试数（失败后可按声明重试）。
    #: 缺省 `1` = **不重试**（既有行为逐字不变）。
    max_attempts_per_index: int = Field(default=1, ge=1, le=10)
    #: GOAL-20261010-046 EC-02：**程序级人工闸门**序号（该轮**跑完之后**的推进停下等人）。
    #: 缺省 `None` = **不设闸门**（既有行为逐字不变）。上界由 `max_runs` 在域层校验。
    human_gate_at_index: int | None = Field(default=None, ge=1)


class ProgramDecisionDto(BaseModel):
    """一次推进的 canonical 事实（读面逐条给）。"""

    after_index: int
    kind: str
    reason: str
    cited_run_id: str | None = None
    #: 被引 canonical 事实的**原文**（判词逐字 / 状态逐字）——读面据此回答「为何」。
    cited_facts: list[str]
    decided_at: str


class ProgramRunDto(BaseModel):
    """程序内一轮 run 的摘要（id / 序号 / 状态 / 冻结 digest）。"""

    run_id: str
    program_index: int
    state: str
    manifest_digest: str | None = None


class ProgramDetailDto(BaseModel):
    """程序读面：声明 + 各轮 run + 逐条决策（含「为何继续 / 为何停」）。"""

    id: str
    project_id: str
    protocol_id: str
    max_runs: int
    continue_on_verdicts: list[str]
    #: GOAL-20261008-040 EC-02：每个序号允许的尝试数（缺省 1 = 不重试）。
    max_attempts_per_index: int = 1
    #: GOAL-20261010-046 EC-02：程序级人工闸门序号（缺省 `None` = 不设闸门）。
    human_gate_at_index: int | None = None
    created_at: str
    updated_at: str
    runs: list[ProgramRunDto]
    decisions: list[ProgramDecisionDto]
    #: 程序内 run 数（与 `runs` 同源；冗余字段是给列表页不解析数组的读者）。
    run_count: int


class ProgramAdvanceDto(BaseModel):
    """一次推进的结果（决策 + 是否起了新 run + 程序内 run 数）。"""

    program_id: str
    decision: ProgramDecisionDto
    started_run_id: str | None = None
    run_count: int
