"""`execute_task` / `ExecutionDeps` 回归(M15 复审 BLOCKER-5)。

复审发现两件事,而全仓当时**没有任何**测试构造 `ExecutionDeps` 或调用
`execute_task`——这正是 CI 看不见它们的根因:

1. 重复记账崩溃:`_attempt_once` 已按 `task.attempt` 记账,`execute_task`
   在重试预算耗尽时又以**同一 attempt** 记一次 → 同 `entry_id` →
   `InvalidInputError` 穿出 use case,把一次干净的 task FAILED 变成未处理异常。
   transient(可重试,预算耗尽)与 timeout(max_attempts=1)两条路径必现。
2. 生产未接 budget:`phase_runner._execute_one_task` 构造
   `ExecutionDeps(workflow, runtime)` 时漏传 `budget`,而
   `record_attempt_usage` 在 `budget is None` 时提前返回 → 失败/重试尝试
   在真实 run 中**从不落账**。

本套件用真实 `SqliteWorkflowEngine` + 真实 `SqliteBudgetLedger` 驱动,
不用 mock ledger:重复 entry_id 只有真实 ledger 才会拒绝。
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from adapters.sqlite.budget_ledger import SqliteBudgetLedger
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.agent_runtime import (
    AgentSessionHandle,
    AgentSessionResult,
    AgentSessionSpec,
)
from packages.application.ports.errors import (
    InvalidInputError,
    PermanentPortError,
    PortError,
    PortTimeoutError,
    TransientPortError,
)
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
    TaskContext,
    _execute_one_task,
)
from packages.application.run_orchestration.task_executor import (
    ExecutionDeps,
    SessionSpecContext,
    _failure_reason,
    execute_task,
)
from packages.application.run_orchestration.usage_recording import (
    record_attempt_usage,
    record_task_usage,
)
from packages.domain.core import ID
from packages.domain.enums import FailureCategory
from packages.domain.tasks import RetryPolicy
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract

_RUN_ID = "3f2a9c14-8d5b-4e77-9a10-6b4c2d8e1f03"


@dataclass(slots=True)
class _FailingRuntime:
    """每次 run 都抛指定 PortError 的最小 AgentRuntime。"""

    error: PortError
    runs: int = 0

    def create_session(self, spec: AgentSessionSpec) -> AgentSessionHandle:
        return AgentSessionHandle(session_id=f"session-{spec.task_id.value}")

    def run(self, session_id: str) -> AgentSessionResult:
        self.runs += 1
        raise self.error

    def pause(self, session_id: str) -> None:  # pragma: no cover - 未走到
        raise NotImplementedError

    def cancel(self, session_id: str) -> None:  # pragma: no cover - 未走到
        raise NotImplementedError

    def stream_events(self, session_id: str) -> tuple[object, ...]:  # pragma: no cover
        return ()

    def fork(self, session_id: str, spec: object) -> AgentSessionHandle:  # pragma: no cover
        raise NotImplementedError


def _spec_context() -> SessionSpecContext:
    return SessionSpecContext(
        role=role_definition(),
        agent=agent_spec(),
        frozen_manifest_digest="manifest-digest",
    )


class _NullArtifacts:
    """_execute_one_task 只在成功路径用到 artifacts;失败路径不触达。"""

    def put(self, *args: object, **kwargs: object) -> object:  # pragma: no cover
        raise NotImplementedError

    def get(self, *args: object, **kwargs: object) -> object:  # pragma: no cover
        raise NotImplementedError


def _task() -> object:
    return replace(research_task(), run_id=ID(_RUN_ID), assigned_agent_id="agent-1")


def _deps(error: PortError) -> tuple[ExecutionDeps, SqliteBudgetLedger, _FailingRuntime]:
    engine = SqliteWorkflowEngine(":memory:")
    ledger = SqliteBudgetLedger(":memory:")
    runtime = _FailingRuntime(error=error)
    return ExecutionDeps(engine, runtime, budget=ledger), ledger, runtime  # type: ignore[arg-type]


def _run(error: PortError, max_attempts: int) -> tuple[object, SqliteBudgetLedger, _FailingRuntime]:
    deps, ledger, runtime = _deps(error)
    task = _task()
    contract = replace(
        task_contract(),
        retry_policy=RetryPolicy(
            max_attempts=max_attempts,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT, FailureCategory.WORKER_LOST],
        ),
    )
    result = execute_task(deps, task, contract, _spec_context(), "trace-1")  # type: ignore[arg-type]
    return result, ledger, runtime


@pytest.mark.parametrize(
    ("error", "max_attempts", "expected_attempts"),
    [
        (
            TransientPortError("model timed out", failure_category=FailureCategory.MODEL_TIMEOUT),
            2,
            2,
        ),
        (
            PortTimeoutError("model timed out", failure_category=FailureCategory.MODEL_TIMEOUT),
            1,
            1,
        ),
        (
            PermanentPortError("config broken", failure_category=FailureCategory.CONFIGURATION),
            2,
            1,
        ),
    ],
)
def test_retry_exhaustion_converges_to_failed_without_duplicate_entry(
    error: PortError,
    max_attempts: int,
    expected_attempts: int,
) -> None:
    """失败路径必须收敛为 outcome=FAILED,不得抛 duplicate usage entry。"""
    result, _ledger, runtime = _run(error, max_attempts)
    assert result.outcome == "FAILED"  # type: ignore[attr-defined]
    assert result.attempts == expected_attempts  # type: ignore[attr-defined]
    assert runtime.runs == expected_attempts


def test_each_attempt_is_recorded_exactly_once() -> None:
    """每次 attempt 恰好一条 ledger entry,entry_id 按 attempt 作用域不碰撞。"""
    _result, ledger, _runtime = _run(
        TransientPortError("model timed out", failure_category=FailureCategory.MODEL_TIMEOUT),
        max_attempts=3,
    )
    entries = ledger.snapshot().entries
    turn_entries = [entry for entry in entries if entry.unit == "turns"]
    assert len(turn_entries) == 3, f"expected one entry per attempt, got {turn_entries}"
    assert len({entry.entry_id for entry in turn_entries}) == 3, "attempt entry ids must be unique"
    assert sorted(entry.attempt for entry in turn_entries) == [1, 2, 3]


def test_failed_attempts_are_unmeasurable_not_zero() -> None:
    """失败尝试记为 quantity_status=UNKNOWN,绝不伪造成"已测量的 0"。"""
    _result, ledger, _runtime = _run(
        TransientPortError("model timed out", failure_category=FailureCategory.MODEL_TIMEOUT),
        max_attempts=2,
    )
    for entry in ledger.snapshot().entries:
        assert entry.quantity_status.value == "UNKNOWN"
        assert entry.unavailable_reason, "unmeasurable entry must carry a reason"
        assert entry.unavailable_reason != "None", (
            "missing failure category must not serialize as the literal 'None'"
        )


def test_missing_failure_category_is_total_over_the_optional_field() -> None:
    """`_failure_reason` 对 Optional 字段是全函数(不产生字面量 'None')。

    诚实边界:`TransientPortError` / `PermanentPortError` 的构造签名要求
    非空 `FailureCategory`,所以这两条路径上 None 实际不可达——复审提出的
    "写入字面量 None" 是理论隐患而非已发生缺陷。基类字段仍是
    `FailureCategory | None`,因此保留显式转换并在此固定其契约。
    """
    assert _failure_reason(None) is None
    assert _failure_reason(FailureCategory.MODEL_TIMEOUT) == "MODEL_TIMEOUT"


def test_duplicate_attempt_entry_id_is_rejected_by_the_real_ledger() -> None:
    """机制说明:同 attempt 记两次必被真实 ledger 拒绝。

    这就是被移除的那行重复记账为什么会把 task FAILED 变成未处理异常。
    保留本测试,使"只记一次"不是巧合而是被约束的行为。
    """
    ledger = SqliteBudgetLedger(":memory:")
    task = _task()
    record_attempt_usage(ledger, task, 1, "first")  # type: ignore[arg-type]
    with pytest.raises(InvalidInputError, match="duplicate usage entry"):
        record_attempt_usage(ledger, task, 1, "second")  # type: ignore[arg-type]


def test_attempt_and_completion_records_do_not_share_entry_id_namespace() -> None:
    """失败尝试记录与完成记录必须使用不同 entry_id 基名。

    两者是不同事实(某次尝试消耗不可计量 / 任务完成消耗 1 turn)。共用基名会在
    "重试后成功"路径上碰撞——把 budget 接进生产路径后该碰撞立即在 F-01
    用例中暴露(复审只指出失败记账未接线,没看到这一层)。
    """
    ledger = SqliteBudgetLedger(":memory:")
    task = _task()
    record_attempt_usage(ledger, task, 1, "attempt 1 failed")  # type: ignore[arg-type]
    record_task_usage(ledger, task)  # type: ignore[arg-type]
    entries = ledger.snapshot().entries
    assert len({entry.entry_id for entry in entries}) == 2, [e.entry_id for e in entries]
    quantities = sorted(entry.quantity for entry in entries)
    assert quantities == [0, 1], "unmeasurable attempt must stay 0; completion must stay 1"


def test_phase_runner_wires_budget_into_execution_deps() -> None:
    """生产接线回归:经 `_execute_one_task` 的失败尝试必须真的落账。

    原先 `_execute_one_task` 构造 `ExecutionDeps(workflow, runtime)` 漏传
    budget,`record_attempt_usage` 因 `budget is None` 提前返回,失败尝试在
    真实 run 中从不落账。断言 ledger 拿到条目,而不是断言源码文本。
    """
    engine = SqliteWorkflowEngine(":memory:")
    ledger = SqliteBudgetLedger(":memory:")
    runtime = _FailingRuntime(
        error=TransientPortError("model timed out", failure_category=FailureCategory.MODEL_TIMEOUT)
    )
    deps = PhaseRunnerDeps(
        workflow=engine,
        runtime=runtime,  # type: ignore[arg-type]
        artifacts=_NullArtifacts(),  # type: ignore[arg-type]
        budget=ledger,
    )
    task = _task()
    contract = replace(task_contract(), retry_policy=RetryPolicy(max_attempts=1))
    ctx = PhaseContext(
        command=None,
        resolve_sessions=lambda: (),
        frozen_manifest_digest="manifest-digest",
        trace_id="trace-1",
        run_id=_RUN_ID,
    )
    step = _execute_one_task(
        deps,
        TaskContext(task=task, contract=contract, spec_context=_spec_context(), ctx=ctx),  # type: ignore[arg-type]
    )
    assert step.failure is not None, "failing runtime must converge to a run failure"
    entries = ledger.snapshot().entries
    assert entries, "phase runner must pass budget through so failed attempts are recorded"
    assert all(entry.quantity_status.value == "UNKNOWN" for entry in entries)


def test_execution_deps_without_budget_records_nothing() -> None:
    """对照面(证明上一个测试非空):budget 缺失时确实一条都不落账。

    这正是修复前 `_execute_one_task` 的状态——`record_attempt_usage` 在
    `budget is None` 时提前返回,失败尝试静默消失。
    """
    engine = SqliteWorkflowEngine(":memory:")
    ledger = SqliteBudgetLedger(":memory:")
    runtime = _FailingRuntime(
        error=TransientPortError("model timed out", failure_category=FailureCategory.MODEL_TIMEOUT)
    )
    deps = ExecutionDeps(engine, runtime)  # type: ignore[arg-type]
    contract = replace(task_contract(), retry_policy=RetryPolicy(max_attempts=1))
    result = execute_task(deps, _task(), contract, _spec_context(), "trace-1")  # type: ignore[arg-type]
    assert result.outcome == "FAILED"
    assert ledger.snapshot().entries == (), "an unwired ledger must stay empty by construction"
