"""NudgeSink Port：**等待超期**（「等太久了」）信号的**出口**（GOAL-20261011-057）。

**为什么需要**：序 24 让等待面**能判超期**（`gate_nudge_after_seconds` ⇒ 判词里点名
「等太久了」）—— 但那条信号**只能在被拉取时读**：**实测** `NudgeSink`、`notify(`、
`dispatch_notification`、`escalate` 在三个产品根**零命中** ⇒ 人不去问就永远不知道。
本端口把那条信号接一个**可注入的出口**。

**边界（与观测面同形，但有一处关键差别）**：

- **只送结构化摘要**（run / 程序 / 序号 / 已等待秒数 / 声明的界）—— **不**含内容原文、
  **不**含 Prompt / 模型输入输出 / **不**含凭据（AGENTS.md §10 的口径）。
- **缺省是静默的**（`NullNudgeSink`）：未注入 ⇒ 既有行为**逐字不变**（不报错、不静默当成失败）。
- **与 `TelemetrySink` 的一处关键差别（本模块的设计要点）**：观测面是 **fail-open**
  （「实现必须吞掉自身错误…telemetry 可 sampled/delayed/dropped」）。**本端口不照抄那一句** ——
  本 GOAL 的纪律是**点名而非静默降级**：**业务路径不因送失败而断**（连续性），
  **但失败要被点名**（由调用方把异常**转成判词**，见 `program_runner` 那一侧）。两条口径
  **必须分辨**：观测面丢失可接受，而「该让人知道的事没送出去」**要能被读出来**。

**非职责**：**不做真实外发**（邮件 / webhook / IM —— 都不做，本 Port 只是**进程内的缝**）；
**不做重试 / 去重 / 投递保证**（本 Port 只保证「信号**被交给**实现」——
**不**保证送达；投递语义仍只能是 at-least-once + idempotency + deduplication）；
**不做升级链**；**不做业务决策回读**。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class NudgeNotice:
    """一条**超期通知**的载荷（**结构化摘要** —— 不是内容搬运）。

    字段**逐个说明**（为什么是这些、为什么没有别的）：

    - `program_id` / `run_id`：**谁**等太久了（定位用）；
    - `index`：**哪一轮**（与三种闸门声明里的序号同一口径）；
    - `waited_seconds`：**等了多久**（序 24 算出来的读数，原样带出 —— 不重算）；
    - `declared_bound_seconds`：**声明的界**（读者据此判断「超了多少」）。

    **刻意没有的**：内容原文、Prompt / 模型输入输出、凭据、审批上下文全文 ——
    这些**都不进**本载荷（§10 的口径：只送**标识 / 计数 / 判词片段**级别的信息）。
    """

    program_id: str
    run_id: str
    index: int
    waited_seconds: int
    declared_bound_seconds: int


@runtime_checkable
class NudgeSink(Protocol):
    """超期信号的出口；**实现可以抛**（调用方负责把它**点名**，不静默吞）。"""

    def nudge(self, notice: NudgeNotice) -> None: ...


class NullNudgeSink:
    """**缺省实现**（未注入 ⇒ 静默；**零副作用**）。

    与 `NullTelemetrySink` 同形（同名方法的静默实现 + 空 `calls`），差别是**只有一条方法**
    —— 本端口只承载**一件事**（超期通知），不为将来预留空方法（预留会让「实现了但没接上」
    与「没实现」看起来一样）。
    """

    def nudge(self, notice: NudgeNotice) -> None:
        return None

    @property
    def calls(self) -> tuple[object, ...]:
        """契约套件的约定：调用日志；**Null 永远为空**（静默的可复核证据）。"""
        return ()


__all__ = ["NudgeNotice", "NudgeSink", "NullNudgeSink"]
