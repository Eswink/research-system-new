"""研究程序域实体（GOAL-20261008-037 EC-01/EC-02）。

「研究程序」= 一个项目下、按**结论驱动**顺次推进的**多轮 run** 的编排单位
（MAINLINE 程序表序 5：多轮 run + 跨 run 知识累积）。

两条硬约束（写进类型与校验，而不是靠调用方自律）：

1. **关联落 canonical**：程序 ↔ run 的关联记在 `ResearchRun.program_id` /
   `program_index` 上（与 run 的写入同一次落库），**不**记在日志 / 侧表 / 时间推断里。
2. **决策是事实**：每次推进（含 WAIT / STOP / DEDUP）都落一条
   `ProgramDecision`，其 `cited_facts` 是被引 canonical 事实的**原文**（逐字），
   读面据此能回答「第 N 轮：为何继续 / 为何停」。

**两个边界**（不越界）：

- 本模块**不**定义 run 的状态机（那是 `ResearchRunState` 的权威）；
  「上一轮是否终态」由调用方按 run 事实判定。
- 本模块**不**读存储（纯值对象）；读取与写入由 `ProgramStore` 端口承担。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from packages.domain.core import Timestamp


class ProgramDecisionKind(StrEnum):
    """一次推进的判定种类（**可区分**：结论面与护栏面不混用同一种类）。"""

    START = "START"
    """程序内还没有 run ⇒ 起第 1 轮。"""

    CONTINUE = "CONTINUE"
    """上一轮落库结论命中声明式规则 ⇒ 起下一轮。"""

    STOP_RULE = "STOP_RULE"
    """上一轮落库结论**不**命中规则 ⇒ 按结论停（不是护栏停）。"""

    STOP_GUARDRAIL = "STOP_GUARDRAIL"
    """结论面判「续」，但下一轮序号超过 `max_runs` ⇒ 按**上界护栏**停（可区分）。"""

    WAIT = "WAIT"
    """上一轮**尚未终止** ⇒ 本轮不推进（不重复起 run、不伪造结论）。"""

    DEDUP = "DEDUP"
    """目标序号的 run **已存在** ⇒ 幂等命中：不产生第二个 run，只留一条去重事实。"""

    # GOAL-20261008-040 EC-02：**失败面与取消面各归各的**（「没有结论」不得被读成
    # 「结论说停」—— 前者是执行面故障，后者是科学判断，处置相反）。
    STOP_RUN_FAILED = "STOP_RUN_FAILED"
    """上一轮**执行失败**（`state == FAILED`）：**没有结论可依** ⇒ 失败停（点名「未获结论」）。"""

    STOP_CANCELLED = "STOP_CANCELLED"
    """上一轮被**取消**（`state == CANCELLED`）：取消是**人的决定** ⇒ 停，且**不**自动重试。"""

    RETRY_FAILED_RUN = "RETRY_FAILED_RUN"
    """上一轮失败但**声明允许重试且未用尽** ⇒ 重试**同序号**（有界：计数落决策、超界点名）。"""

    # GOAL-20261009-041 EC-02：**失败重试面的崩溃窗口**（认领了同序号却未落库）。
    # 与结论面的 `DEDUP` **同类不同面**：那里认领的是**下一序号**的新 run，这里认领的是
    # **同一序号**的重试；两者都**不产生第二个 run**，但读面必须分得清是哪一面。
    DEDUP_FAILED_RUN = "DEDUP_FAILED_RUN"
    """上一条重试已认领本序号（run id 记在决策里）但该 run **未落库** ⇒ 幂等命中：
    不再起第二个同序号 run，点名认领的 run 与已认领数；该**认领**同样**计入**尝试数
    （否则声明的上界可被反复的崩溃窗口无限绕过）。"""

    # GOAL-20261010-044 EC-02：**非终态面的两类等待必须可区分**（「等人」≠「等机器」）。
    # 序 8 消灭的是「没有结论 vs 结论说停」；本条是同一病在非终态面：`WAIT` 此前把
    # 「这一轮还在跑」与「停在人工闸门等人拍板」混成一体 ⇒ 恢复路径无法回答「该等谁」。
    WAIT_FOR_APPROVAL = "WAIT_FOR_APPROVAL"
    """上一轮**停在人工闸门**（`state == WAITING_FOR_APPROVAL` / `PAUSED`）⇒ 等**人**拍板：
    与 `WAIT`（等**机器**跑完）**互不混用**；判词点名待审批的标识（查不到也点名）。"""


@dataclass(frozen=True, slots=True)
class ProgramContinueRule:
    """声明式的续跑规则：读上一轮**落库**的评审判词（先结论）。

    `verdict_in` 命中上一轮任一落库评审结论的 `verdict` ⇒ 结论面判「续」；
    否则结论面判「停」。**判词逐字**进决策的 `cited_facts`（读面原文，不再加工）。
    """

    verdict_in: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.verdict_in:
            raise ValueError("continue rule needs at least one verdict")
        if any(not item for item in self.verdict_in):
            raise ValueError("continue rule verdicts must not be empty")


@dataclass(frozen=True, slots=True)
class ResearchProgram:
    """一次「研究程序」的声明（项目内、按协议推进的多轮 run 编排单位）。"""

    id: str
    project_id: str
    protocol_id: str
    max_runs: int
    continue_rule: ProgramContinueRule
    # GOAL-20261008-040 EC-02：**每个序号允许的尝试数**（失败后可按声明重试）。
    # 缺省 `1` = **不重试**（既有行为逐字不变）；>1 = 允许同序号重起，**有界**
    # （计数由 `for_program` 的同序号 run 数算，不落第二套计数存储）。
    max_attempts_per_index: int = 1
    # GOAL-20261010-046 EC-02：**程序级人工闸门**（可选声明；缺省 `None` = **不设闸门**
    # ⇒ 既有行为逐字不变）。语义 = 「第 N 轮**跑完之后**的推进停下等人看结果」——
    # 与 phase 面的 `HUMAN_GATE` 同一件事（那里是 phase 维度，这里是**程序轮次**维度）。
    # 为什么是程序自己声明：此前「人在环」只能由**别人**（协议 phase 闸门 / 外部操作）制造，
    # 编排能力里没有它 ⇒「中断后可接回」缺了**中断可声明**这一半。
    human_gate_at_index: int | None = None
    # GOAL-20261010-048 EC-02：**条件式人工闸门**（可选声明；缺省 `None` = **不设**
    # ⇒ 既有行为逐字不变）。语义 = 「上一轮落库的**判词取值命中其中之一**时，停下等人看结果」
    # —— 与 `continue_rule.verdict_in` **同一族**（那里是「命中 ⇒ 续」，这里是「命中 ⇒ 停」），
    # 形态**照抄**它：**可机检的取值集合**，不是自由文本、不引入表达式引擎。
    # 与 `human_gate_at_index` **互斥**（同时声明 ⇒ 点名拒绝）：两条闸门声明各有各的
    # 求值时序（按序号 / 按落库事实），并存会让「为什么停」读不出是哪一条**要求**的。
    human_gate_on_verdicts: tuple[str, ...] | None = None
    created_at: Timestamp = field(default_factory=Timestamp.now)
    updated_at: Timestamp = field(default_factory=Timestamp.now)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("program id must not be empty")
        if not self.project_id:
            raise ValueError("program project_id must not be empty")
        if not self.protocol_id:
            raise ValueError("program protocol_id must not be empty")
        if self.max_runs < 1:
            raise ValueError("max_runs must be >= 1")
        if self.max_attempts_per_index < 1:
            raise ValueError("max_attempts_per_index must be >= 1")
        _validate_gate_declarations(self)

    @property
    def condition_gate_hit(self) -> bool:
        """是否声明了**条件式**闸门（读面 / 判定面用来区分两条声明的**来源**）。"""
        return self.human_gate_on_verdicts is not None


def _validate_gate_declarations(program: ResearchProgram) -> None:
    """两条闸门声明的校验（序 14 的序号 / GOAL-20261010-048 的条件）——**坏声明必须点名**。

    抽出成模块级函数是为了守住**函数 ≤ 50 行 / 复杂度 ≤ 10** 两道门（`__post_init__`
    此前已 8 个分支，再加 4 个就触顶）—— 与「行为独立即单列」同一手法，语义未变。
    """
    if program.human_gate_at_index is not None and not (
        1 <= program.human_gate_at_index <= program.max_runs
    ):
        raise ValueError(
            "human_gate_at_index must be within 1..max_runs when declared "
            f"(got {program.human_gate_at_index}, max_runs={program.max_runs})"
        )
    declared = program.human_gate_on_verdicts
    if declared is None:
        return
    if not declared:
        raise ValueError("human_gate_on_verdicts must name at least one verdict when declared")
    if any(not item for item in declared):
        raise ValueError("human_gate_on_verdicts must not be empty strings")
    if program.human_gate_at_index is not None:
        raise ValueError(
            "human_gate_at_index and human_gate_on_verdicts are mutually exclusive "
            "(two gate declarations would make 'why did it stop' unreadable)"
        )


@dataclass(frozen=True, slots=True)
class ProgramDecision:
    """一次推进的 canonical 事实（含被引事实的**原文**）。"""

    program_id: str
    after_index: int
    """本决策发生在第几轮之后（0 = 起第 1 轮之前）。"""

    kind: ProgramDecisionKind
    reason: str
    cited_run_id: str | None = None
    cited_facts: tuple[str, ...] = ()
    decided_at: Timestamp = field(default_factory=Timestamp.now)

    def __post_init__(self) -> None:
        if not self.program_id:
            raise ValueError("decision program_id must not be empty")
        if self.after_index < 0:
            raise ValueError("after_index must be >= 0")
        if not self.reason:
            raise ValueError("decision reason must not be empty")
