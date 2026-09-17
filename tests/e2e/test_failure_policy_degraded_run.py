"""E2E：契约声明 `on_task_failure: CONTINUE` ⇒ 失败被容忍、剩余工作照跑、run 收敛 DEGRADED。

GOAL-004 cycle 3 = EC-03。这里走真装配（SQLite 任务面 + canonical 事件链 + 真 phase
runner），只注入两件事：runtime 的失败脚本、契约里的策略声明。

可观测差异（与基线对照）：
- 声明 CONTINUE：首个任务**终局失败**后仍发起后续会话（第二会话被尝试）⇒ 收敛 DEGRADED，
  事件链有 `run.degraded`（payload 点名策略与被容忍的失败），**没有** `run.completed`；
- 不声明（缺省 fail-fast）：同一场景 ⇒ 收敛 FAILED，只发起一次会话，无 `run.degraded`。
"""

from __future__ import annotations

from dataclasses import replace

from packages.application.ports.errors import PermanentPortError
from packages.application.ports.resource_catalog import CatalogSnapshot
from packages.application.run_orchestration import RunOutcome, StartRunCommand
from packages.domain.core import ID
from packages.domain.enums import FailureCategory
from packages.domain.events import EventType
from packages.domain.run_state import ResearchRunState
from tests.e2e.scenario import M7Harness, StructuredOutputAgentRuntime, m7_protocol
from tests.e2e.scenario_catalog import m7_catalog, m7_preflight_context, m7_project


class _CountingRuntime(StructuredOutputAgentRuntime):
    """ "后续工作有没有跑"的可观测证据：run 调用次数（同实例脚本语义不变）。"""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self.run_calls = 0

    def run(self, session_id: str):  # type: ignore[no-untyped-def]
        self.run_calls += 1
        return super().run(session_id)


def _catalog_with(policy: dict[str, str | bool | int | list[str]]) -> CatalogSnapshot:
    catalog = m7_catalog()
    return replace(
        catalog,
        task_contracts={
            ref: replace(contract, failure_policy=policy)
            for ref, contract in catalog.task_contracts.items()
        },
    )


def _runtime() -> _CountingRuntime:
    runtime = _CountingRuntime(
        structured_output={
            "analysis_report": {"baseline": "O(n^2)"},
            "review_decision": {"verdict": "PASS"},
        }
    )
    runtime.set_script(
        "run", [PermanentPortError("model refused", failure_category=FailureCategory.MODEL_AUTH)]
    )
    return runtime


def _start(harness: M7Harness, catalog: CatalogSnapshot) -> RunOutcome:
    return harness.service.start_run(
        m7_protocol(),
        catalog,
        m7_project(),
        m7_preflight_context(catalog, m7_project()),
        StartRunCommand(
            project_id="m7-project",
            protocol_id="sort_analysis_v1",
            run_id=ID.generate(),
            trace_id="trace-failure-policy",
        ),
    )


def test_a_declared_continue_tolerates_the_failure_and_finishes_the_work() -> None:
    runtime = _runtime()
    harness = M7Harness(runtime=runtime)
    try:
        outcome = _start(harness, _catalog_with({"on_task_failure": "CONTINUE"}))
        kinds = [envelope.event_type for envelope in harness.events.published]
    finally:
        harness.close()

    assert runtime.run_calls >= 2, "被容忍的失败之后必须还有后续会话被发起"
    assert outcome.state == ResearchRunState.State.DEGRADED
    assert outcome.system_failure is False
    tolerated = [task for task in outcome.tasks if task.failure_policy == "CONTINUE"]
    assert tolerated, "被容忍的失败必须出现在 task outcomes 里并标明策略"
    assert EventType.RUN_DEGRADED in kinds
    assert EventType.RUN_COMPLETED not in kinds, "有被容忍的失败就不发 run.completed"


def test_the_undeclared_baseline_still_fails_fast() -> None:
    runtime = _runtime()
    harness = M7Harness(runtime=runtime)
    try:
        outcome = _start(harness, _catalog_with({}))
        kinds = [envelope.event_type for envelope in harness.events.published]
    finally:
        harness.close()

    assert runtime.run_calls == 1, "缺省 fail-fast：第一个失败之后不再发起会话"
    assert outcome.state == ResearchRunState.State.FAILED
    assert EventType.RUN_DEGRADED not in kinds
    assert EventType.RUN_FAILED in kinds
