"""一次尝试一套账：in-process 重试走 durable 尝试（GOAL-003 cycle 17 / PLAN-20260915-080）。

收口前实测（探针 `scratch/goal3-cycle17-probe1-two-ledgers.py`）：

```text
max_attempts=3 backoff=None: 第一次 execute_task 调 runtime 3 次；累计 9 次
                              [首轮 status=LEASED / 交付 3 代 / runtime 共调用 9 次]
```

三条同时成立的缺陷：① 局部计数与 durable 的交付代次各算各的 ⇒ 每次交付都能"再来一遍
预算"；② 退避声明对 in-process 循环无效（照样立刻跑满）；③ 失败后**不落账**，任务停在
LEASED，durable 的重排/死信判据永远够不着。

本文件把收口后的行为钉住：执行次数受 `max_attempts` 总量约束、每次失败都落账、
声明了退避就把下一次尝试交回派发方。
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.agent_runtime import (
    AgentSessionHandle,
    AgentSessionResult,
    AgentSessionSpec,
)
from packages.application.ports.errors import InvalidInputError, TransientPortError
from packages.application.run_orchestration.task_executor import (
    ExecutionDeps,
    SessionSpecContext,
    execute_task,
)
from packages.domain.core import ID
from packages.domain.enums import FailureCategory
from packages.domain.events import EventType
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import RetryPolicy
from tests.contracts.fixtures import agent_spec, research_task, role_definition, task_contract

_RUN_ID = "3f2a9c14-8d5b-4e77-9a10-6b4c2d8e1f03"


@dataclass(slots=True)
class _FailingRuntime:
    """每次都抛同一个瞬态错误，并记下被调用的次数。"""

    error: TransientPortError
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


def _spec_context() -> SessionSpecContext:
    return SessionSpecContext(
        role=role_definition(), agent=agent_spec(), frozen_manifest_digest="manifest-digest"
    )


def _deps() -> tuple[ExecutionDeps, _FailingRuntime, SqliteWorkflowEngine]:
    runtime = _FailingRuntime(
        error=TransientPortError("model timed out", failure_category=FailureCategory.MODEL_TIMEOUT)
    )
    engine = SqliteWorkflowEngine(":memory:")
    return ExecutionDeps(engine, runtime), runtime, engine  # type: ignore[arg-type]


def _contract(*, max_attempts: int, backoff: int | None = None) -> object:
    return replace(
        task_contract(),
        retry_policy=RetryPolicy(
            max_attempts=max_attempts,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=backoff,
        ),
    )


def _task() -> object:
    return replace(research_task(), run_id=ID(_RUN_ID), assigned_agent_id="agent-1")


def _status(engine: SqliteWorkflowEngine, task: object) -> tuple[str, int]:
    row = engine.list_tasks(task.run_id.value)[0].task  # type: ignore[attr-defined]
    return str(row.status), int(row.attempt)


def test_exhausted_transient_failure_is_recorded_and_dead_lettered() -> None:
    """预算耗尽 ⇒ 每次尝试都落账、任务落 DEAD_LETTER（收口前停在 LEASED）。"""
    deps, runtime, engine = _deps()
    task = _task()

    result = execute_task(deps, task, _contract(max_attempts=3), _spec_context(), "t")  # type: ignore[arg-type]

    assert runtime.runs == 3, "总执行次数 = max_attempts（收口前是每交付一遍预算）"
    assert result.message == "retry budget exhausted"
    status, attempt = _status(engine, task)
    assert (status, attempt) == (ResearchTaskState.State.DEAD_LETTER, 3)
    kinds = [envelope.event_type for envelope in engine.pending_outbox()]
    assert kinds.count(EventType.TASK_RETRY_SCHEDULED) == 2, "前两次失败排了重试"
    assert kinds.count(EventType.TASK_COMPLETED) == 1, "第三次用尽 ⇒ 死信"
    completed = [e for e in engine.pending_outbox() if e.event_type == EventType.TASK_COMPLETED]
    assert completed[-1].payload["action"] == "DEAD_LETTER"


def test_a_declared_backoff_hands_the_next_attempt_back_to_the_dispatcher() -> None:
    """声明了退避 ⇒ 一次调用只执行一次，任务留 RETRY_SCHEDULED 等派发方。"""
    deps, runtime, engine = _deps()
    task = _task()

    result = execute_task(deps, task, _contract(max_attempts=3, backoff=3600), _spec_context(), "t")  # type: ignore[arg-type]

    assert runtime.runs == 1, "进程内不自旋（收口前会立刻跑满 3 次）"
    assert result.message == "retry deferred to the dispatcher"
    status, attempt = _status(engine, task)
    assert (status, attempt) == (ResearchTaskState.State.RETRY_SCHEDULED, 1)
    scheduled = [
        e for e in engine.pending_outbox() if e.event_type == EventType.TASK_RETRY_SCHEDULED
    ]
    assert scheduled[-1].payload["retry_at"] is not None, "deadline 落进事件"
    # 同一个进程再执行一次也不行：deadline 没到，acquire 被拒（PLAN-20260915-080 的另一半）。
    import pytest

    with pytest.raises(InvalidInputError):
        engine.acquire_lease(task.id.value)  # type: ignore[attr-defined]


def test_each_attempt_number_is_its_own_ledger_scope() -> None:
    """attempt 号 = durable 交付代次 ⇒ 每次尝试的记账 id 互不重复（M15 BLOCKER-5 不回退）。"""
    deps, runtime, engine = _deps()
    task = _task()

    execute_task(deps, task, _contract(max_attempts=3), _spec_context(), "t")  # type: ignore[arg-type]

    assert runtime.runs == 3
    _, attempt = _status(engine, task)
    assert attempt == 3, "durable 的 attempt 与执行次数对齐（收口前 attempt 停在 1）"
