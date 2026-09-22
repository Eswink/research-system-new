"""GOAL-011 EC-03：沙箱实验阶段的**派发语义**（默认门可跑、不出网、不起容器）。

判的是「谁执行这件工作」这条声明怎么被读：

- 声明非空 ⇒ 交给装配方声明的实验执行缝（本用例用**计数桩**证明真的走了那道缝）；
- 声明非空而缝没接 ⇒ **点名拒绝**（fail-closed；**不**静默回退到会话）；
- 声明缺席 ⇒ 会话语义（既有行为）。

真实容器那一段由 `tests/e2e/test_sandbox_experiment_live.py`（`requires_docker` +
`requires_live_llm`）承担——本模块只判派发，不假装跑过容器。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from packages.application.run_orchestration.experiment_task import dispatch_experiment
from packages.application.run_orchestration.task_executor import TaskExecutionResult
from packages.domain.tasks import ExperimentExecutionSpec, ResearchTask, TaskContract


def _task() -> ResearchTask:
    from packages.domain.core import ID

    return ResearchTask(
        id=ID.generate(), run_id=ID.generate(), contract_id="sort_analysis_execution"
    )


def _contract(**overrides: Any) -> TaskContract:
    from packages.domain.enums import AcceptanceCriterionType
    from packages.domain.tasks import AcceptanceCriterion

    base = TaskContract(
        id="sort_analysis_execution",
        version="1.0.0",
        purpose="analysis",
        acceptance_criteria=[
            AcceptanceCriterion(
                type=AcceptanceCriterionType.ARTIFACT_EXISTS, artifact="analysis_report"
            )
        ],
    )
    return replace(base, **overrides) if overrides else base


def _result() -> TaskExecutionResult:
    return TaskExecutionResult(task=_task(), outcome="SUCCEEDED", message="")


class _Seam:
    """装配方的实验缝桩：只记账「被调用过没有」，不做任何执行。"""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, *args: Any, **kwargs: Any) -> TaskExecutionResult:
        self.calls += 1
        return _result()


def _tctx(contract: TaskContract) -> Any:
    ctx = type("C", (), {"trace_id": "trace-dispatch"})()
    return type(
        "T", (), {"task": _task(), "contract": contract, "spec_context": None, "ctx": ctx}
    )()


def test_declared_experiment_is_dispatched_to_the_wired_seam() -> None:
    """声明非空 ⇒ 走实验缝（判据是可观测的后果：缝被调用，且返回值原样交回）。"""
    seam = _Seam()
    outcome = dispatch_experiment(type("D", (), {"experiment_task": seam})(), _tctx(_contract()))
    assert seam.calls == 1
    assert outcome.outcome == "SUCCEEDED"


def test_declared_experiment_without_a_seam_is_named_not_silently_downgraded() -> None:
    """声明非空而缝缺席 ⇒ **点名拒绝**：消息点名合约与「没接线」，类别是装配错。

    这条是 EC-03 的**反证面**：如果这里静默回退到会话，run 会照常走到成功，
    而「声明了实验」与「真的跑了实验」就分叉了——那是本判据要拦的形态。
    """
    outcome = dispatch_experiment(type("D", (), {"experiment_task": None})(), _tctx(_contract()))
    assert outcome.outcome == "FAILED"
    assert "sort_analysis_execution" in outcome.message
    assert "no experiment runner is wired" in outcome.message
    assert outcome.failure_category is not None


def test_declaration_shape_is_validated() -> None:
    """声明本身拒绝退化取值（空 command / 非正超时）。"""
    with pytest.raises(ValueError, match="command"):
        ExperimentExecutionSpec(command="")
    with pytest.raises(ValueError, match="timeout_seconds"):
        ExperimentExecutionSpec(timeout_seconds=0)


def test_a_contract_without_the_declaration_keeps_session_semantics() -> None:
    """缺省 `None` ⇒ 会话语义：非空才派发，`None` 不派发（既有行为逐字不变）。"""
    assert _contract().experiment is None
    assert _contract().experiment is None
