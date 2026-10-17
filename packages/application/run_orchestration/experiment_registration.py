"""实验路径的 `ResultRegistration` 构造（自 `task_phase_helpers.py` 拆出守规模门）。

**为什么单列**：`task_phase_helpers.py` 卡在 450 行硬上限上，而 GOAL-20261016-081 EC-04
给 `ChainCarry` / `register_or_fail` 各加了一条跨相输入通道 ⇒ 那里的函数长度与文件长度
同时越界。拆法与全仓既有手法一致（`report_facts` 自 `report_task` 拆出、`runner_deps`
自 `service` 拆出）：**一段职责自洽的构造**单独成模块，调用点逐字不变。

**逐字搬运，零语义变化**：`registration_from_experiment` 的函数体与拆出前**逐字相同**
（含那条 GOAL-010 EC-02 的「声明输入必须挂 claim relation」）。
"""

from __future__ import annotations

from typing import Any

from packages.application.run_orchestration.result_handler import (
    RegistrationDeps,
    ResultRegistration,
    register_declared_input_sources,
)
from packages.domain.evidence import EvidenceRelation, EvidenceRelationType


def registration_from_experiment(
    deps: Any,
    execution: Any,
    tctx: Any,
) -> ResultRegistration:
    """沙箱实验的执行结果 → `ResultRegistration`（自产件不计入覆盖）。"""
    outcome = execution.experiment_outcome
    assert outcome is not None
    artifact_ids = (
        set(outcome.run.result.artifact_refs) if outcome.run.result is not None else set()
    )
    artifacts = tuple(
        artifact for artifact in deps.artifacts.list_refs() if artifact.id in artifact_ids
    )
    admission = execution.experiment_admission
    claim_id = admission.claim.id if admission is not None else f"claim:{tctx.task.id.value}:result"
    inputs = register_declared_input_sources(
        RegistrationDeps(
            store=deps.artifacts,
            agent_id=tctx.spec_context.agent.id,
            ledger=deps.ledger,
            declared_inputs=tctx.spec_context.declared_input_artifacts,
        ),
        tctx.task,
        claim_id=claim_id,
    )
    # 声明输入的 evidence 必须挂到 claim 上，否则 `GET /runs/{id}/evidence` 的
    # claim-relation 投影看不到它（GOAL-010 EC-02：判据要求来源**可读**）。
    if admission is not None and deps.ledger is not None:
        for evidence in inputs:
            deps.ledger.attach_relation(
                EvidenceRelation(
                    claim_id=claim_id,
                    evidence_id=evidence.id,
                    relation=EvidenceRelationType.SUPPORTS,
                )
            )
    return ResultRegistration(
        artifacts=artifacts,
        evidence=(admission.evidence if admission is not None else ()) + inputs,
        claims=(admission.claim,) if admission is not None else (),
        # 同一判别性质（GOAL-010 EC-02）：本路径的「自身产物」是该 experiment run
        # 自己登记的 artifact_refs ⇒ 它们不构成覆盖来源。
        self_artifact_ids=frozenset(artifact_ids),
    )


__all__ = ["registration_from_experiment"]
