"""会话结果的 `ChainCarry` 构造（自 `phase_runner.py` 拆出守 450 行规模门）。

**为什么单列**：`phase_runner.py` 卡在 450 行硬上限上，而 GOAL-20261016-081 EC-04 的
跨相输入通道让那里的 `_session_carry` 越过规模与函数长度两条门。拆法与全仓既有手法一致
（`task_dispatch` / `report_facts` / `runner_deps` 同一手法）：**一段职责自洽的构造**
单独成模块，调用点逐字不变。

**三件事同源**（都是「这一步产出了什么证据」）：

- `retrieved`：运行链自己取得的证据（GOAL-011 EC-01）—— 随会话结果进同一个 claim；
- `cross_phase`：跨相输入登记出的证据（GOAL-20261016-081 EC-04）—— 解析失败返回
  **点名的消息串**，由调用方转成 task 失败（不静默跳过：那会让覆盖门在来源不在时通过）；
- `skipped` / `chain_outputs` / `annotations`：声明式跳过的理由与各步返回内容（既有）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from packages.application.ports.artifact_store import ArtifactStore
from packages.application.ports.evidence_ledger import EvidenceLedger
from packages.application.ports.workflow_engine import WorkflowEngine
from packages.application.run_orchestration.cross_phase_inputs import cross_phase_evidence
from packages.application.run_orchestration.task_phase_helpers import ChainCarry
from packages.domain.enums import TrustLabel
from packages.domain.tasks import ResearchTask


@dataclass(frozen=True, slots=True)
class SessionCarryInputs:
    """`build_session_carry` 的输入面（参数对象：守住 5 参数上限）。"""

    workflow: WorkflowEngine
    artifacts: ArtifactStore
    ledger: EvidenceLedger | None
    task: ResearchTask
    declared: tuple[tuple[str, str, TrustLabel], ...]
    capability: Any


def build_session_carry(inputs: SessionCarryInputs) -> ChainCarry | str:
    """本任务会话结果的 `ChainCarry`（跨相输入解析失败 ⇒ 点名的消息串）。"""
    cross_phase = cross_phase_evidence(
        inputs.workflow, inputs.artifacts, inputs.ledger, inputs.task, inputs.declared
    )
    if isinstance(cross_phase, str):
        return cross_phase
    return ChainCarry(
        retrieved=inputs.capability.evidences,
        skipped=inputs.capability.skipped,
        chain_outputs=inputs.capability.outputs,
        annotations=inputs.capability.annotations,
        cross_phase=cross_phase,
    )


__all__ = ["SessionCarryInputs", "build_session_carry"]
