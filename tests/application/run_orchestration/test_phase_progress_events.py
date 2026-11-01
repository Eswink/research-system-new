"""相级事件：`phase.started` / `phase.completed` 的**两向语义**（GOAL-20261101-103 EC-01）。

**它封住的失败形态**（不是"少了个进度条"，是"读面在撒谎"）：

- 只发 `phase.started` 不发 `completed` ⇒ 读面永远显示"跑到最后一相、都还在跑"；
- **在失败组也发 `completed`** ⇒ 一次停在第 9 相的 run 在事件链上看起来像"9 相全走完"。
  这是本文件最重要的一条：**"相结束了"与"相成功了"必须是两件事**；
- 在 human gate / 暂停信号拦下的组发 `started` ⇒ "等审批"被读成"正在跑"。

三条判据各自钉一个方向，另有一条**反证臂**（摘掉发射点 ⇒ 判据判红）。

**射程边界（如实登记）**：本文件判的是**事件序与载荷**，不判前端会不会渲染——那由
`apps/web/tests/e2e/run-phase-progress.spec.ts` 判；两条合起来才是"用户看得见"。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from adapters.fakes import FakeArtifactStore, FakeWorkflowEngine
from packages.application.run_orchestration.outcomes import RunOutcome
from packages.application.run_orchestration.phase_progress import (
    PHASE_OUTCOME_DEGRADED,
    PHASE_OUTCOME_SUCCEEDED,
    PHASE_OUTCOMES,
    phase_outcome,
    phase_started_payload,
)
from packages.application.run_orchestration.phase_runner import (
    PhaseContext,
    PhaseRunnerDeps,
    execute_phases,
)
from packages.application.run_orchestration.task_phase_helpers import PhaseStep
from packages.domain.core import ID
from packages.domain.events import EventType
from packages.domain.run_state import ResearchRunState
from tests.contracts.fixtures import research_task, task_contract

_RUN_ID = "5b6c7d8e-9f0a-4b1c-8d2e-3f4a5b6c7d8e"


class _RecordingRuntime:
    """成功返回的空运行时（本文件不判会话行为）。"""

    def create_session(self, spec: Any) -> Any:
        return type("Handle", (), {"session_id": f"s-{spec.task_id.value}"})()

    def run(self, session_id: str) -> Any:
        raise AssertionError("本判据不该真的跑会话（执行器被替换）")

    def pause(self, session_id: str) -> None: ...
    def cancel(self, session_id: str) -> None: ...


def _context(phase_id: str, strategy: str = "single_agent") -> Any:
    from tests.contracts.fixtures import agent_spec, role_definition

    return _SpecContext(
        role=role_definition(),
        agent=agent_spec(),
        frozen_manifest_digest="manifest-digest",
        phase_id=phase_id,
        phase_strategy=strategy,
    )


def _spec(phase_id: str, agent: str, *, strategy: str = "single_agent") -> tuple[Any, Any, Any]:
    task = replace(
        research_task(),
        id=ID.generate(),
        run_id=ID(_RUN_ID),
        assigned_agent_id=agent,
        idempotency_key=f"{phase_id}:{agent}",
    )
    return (task, task_contract(), _context(phase_id, strategy))


def _deps(published: list[tuple[EventType, dict[str, object]]]) -> PhaseRunnerDeps:
    def publish(
        event_type: EventType,
        payload: dict[str, object],
        run_id: str,
        trace_id: str,
        task_id: str | None,
    ) -> None:
        _ = (run_id, trace_id, task_id)
        published.append((event_type, payload))

    return PhaseRunnerDeps(
        workflow=FakeWorkflowEngine(),
        runtime=_RecordingRuntime(),  # type: ignore[arg-type]
        artifacts=FakeArtifactStore(),
        publish=publish,
    )


def _ctx(specs: tuple[tuple[Any, Any, Any], ...]) -> PhaseContext:
    return PhaseContext(
        command=None,
        resolve_sessions=lambda: specs,
        frozen_manifest_digest="manifest-digest",
        trace_id="trace-1",
        run_id=_RUN_ID,
    )


def _succeeding_runner(seen: list[str] | None = None) -> Any:
    def run(deps: Any, tctx: Any) -> Any:
        if seen is not None:
            seen.append(tctx.task.id.value)
        return PhaseStep(handoff={"summary": "ok"}, verdict="PASS")

    return run


def _names(published: list[tuple[EventType, dict[str, object]]]) -> list[str]:
    return [event_type.value for event_type, _payload in published]


# --------------------------------------------------------------------------- 正向：时序


def test_phase_started_precedes_the_first_task_and_completed_follows_the_last(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**时序**：`phase.started` 在该组首个任务之前；`completed` 在末个任务之后。

    判法是**在任务执行时读一次已发事件**（不是事后看顺序）：只有"任务开始时已经能看到
    started"才能证明它排在前面。`completed` 同理反向看。
    """
    from packages.application.run_orchestration import phase_runner as pr

    published: list[tuple[EventType, dict[str, object]]] = []
    during: list[list[str]] = []

    def run(deps: Any, tctx: Any) -> Any:  # noqa: ARG001 - 只需要观测时机
        during.append(_names(published))
        return PhaseStep(handoff={"summary": "ok"}, verdict="PASS")

    monkeypatch.setattr(pr, "_execute_one_task", run)
    specs = (_spec("phase-a", "agent-1"), _spec("phase-b", "agent-2"))

    outcome = execute_phases(_deps(published), _ctx(specs))

    assert outcome.state == ResearchRunState.State.SUCCEEDED
    assert during == [
        # 第一相的第一个任务：本相 started 已在它之前（本相无 completed）
        ["phase.started"],
        # 第二相的第一个任务：第一相 completed 已发 ⇒ 它排在**末个任务之后**；
        # 本相的 started 也已在它之前。
        ["phase.started", "phase.completed", "phase.started"],
    ], (
        "第一相任务开始时只有 started；第二相任务开始时第一相 completed 已发 "
        "⇒ completed 排在末个任务之后；且本相 started 先于本相任务",
        during,
    )
    assert _names(published) == [
        "phase.started",
        "phase.completed",
        "phase.started",
        "phase.completed",
        "run.completed",
    ]


def test_each_payload_carries_its_declared_keys() -> None:
    """payload 键逐条在场（`strategy` 来自 `PhaseStrategy`，不填 vendor 名）。"""
    group = (_spec("phase-a", "agent-1", strategy="map_reduce"),)

    started = phase_started_payload(group)

    assert set(started) == {"phase_id", "strategy", "contract_ids"}
    assert started["phase_id"] == "phase-a"
    assert started["strategy"] == "map_reduce"
    assert started["contract_ids"] == [group[0][1].id]


def test_the_completed_payload_names_the_outcome_and_the_real_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`completed` 带 `outcome` 与**真实产出**的制品 id（取自 HandoffBundle）。"""
    from packages.application.run_orchestration import phase_runner as pr

    published: list[tuple[EventType, dict[str, object]]] = []

    class _Bundle:
        artifact_refs = ("task-x:research_question",)

    def run(deps: Any, tctx: Any) -> Any:  # noqa: ARG001
        return PhaseStep(handoff=_Bundle(), verdict="PASS")

    monkeypatch.setattr(pr, "_execute_one_task", run)
    specs = (_spec("phase-a", "agent-1"),)

    execute_phases(_deps(published), _ctx(specs))

    completed = [
        payload for event_type, payload in published if event_type is EventType.PHASE_COMPLETED
    ]
    assert len(completed) == 1
    assert completed[0]["outcome"] == PHASE_OUTCOME_SUCCEEDED
    assert completed[0]["artifact_ids"] == ["task-x:research_question"]
    assert completed[0]["outcome"] in PHASE_OUTCOMES


# --------------------------------------------------------------- 反向：失败/停车不发 completed


def test_a_failed_phase_does_not_report_completed(monkeypatch: pytest.MonkeyPatch) -> None:
    """**核心边界**：组内终局失败 ⇒ 发过 `started`，**绝不**发 `completed`。

    这是本判据存在的全部理由：若失败组也发 completed，一次停在第 9 相的 run 会在事件链上
    看起来像"9 相全走完"——读面由此对用户撒谎。
    """
    from packages.application.run_orchestration import phase_runner as pr

    published: list[tuple[EventType, dict[str, object]]] = []

    def failing(deps: Any, tctx: Any) -> Any:
        return PhaseStep(failure=deps.fail(tctx.ctx.run_id, "boom", True))

    monkeypatch.setattr(pr, "_execute_one_task", failing)

    outcome = execute_phases(_deps(published), _ctx((_spec("phase-a", "agent-1"),)))

    assert outcome.state == ResearchRunState.State.FAILED
    assert _names(published) == ["phase.started"], (
        "失败相必须发 started（它确实开始了）但**不得**发 completed（它没跑完）",
        _names(published),
    )


def test_a_parked_phase_does_not_report_completed(monkeypatch: pytest.MonkeyPatch) -> None:
    """重排停车（非终局失败）⇒ 同样只有 `started`，没有 `completed`。"""
    from packages.application.run_orchestration import phase_runner as pr

    published: list[tuple[EventType, dict[str, object]]] = []

    def defer(deps: Any, tctx: Any) -> Any:  # noqa: ARG001
        return PhaseStep(retry_deferred=True)

    monkeypatch.setattr(pr, "_execute_one_task", defer)

    outcome = execute_phases(_deps(published), _ctx((_spec("phase-a", "agent-1"),)))

    assert outcome.state == ResearchRunState.State.PAUSED
    assert _names(published) == ["phase.started"]


def test_a_phase_blocked_by_the_human_gate_never_starts(monkeypatch: pytest.MonkeyPatch) -> None:
    """被 human gate 拦下的组**没有开始执行** ⇒ 连 `started` 都不发。

    否则"等审批"会被读成"正在跑"，而二者的出路完全不同（一个要人、一个要时间）。
    """
    from packages.application.run_orchestration import phase_runner as pr

    published: list[tuple[EventType, dict[str, object]]] = []
    specs = (_spec("phase-a", "agent-1"),)
    deps = replace(
        _deps(published),
        human_gated=frozenset({"phase-a"}),
        # 没有 approvals store ⇒ `pause_for_human_gate` 会点名失败（不静默放行），
        # 所以这里直接给一个只做记账的替身：本判据只关心**事件**。
        approvals=None,
    )
    monkeypatch.setattr(pr, "_execute_one_task", _succeeding_runner())
    monkeypatch.setattr(pr, "pause_for_human_gate", lambda *_a, **_k: None)
    parked = RunOutcome(run_id=_RUN_ID, state=ResearchRunState.State.PAUSED)
    monkeypatch.setattr(pr, "pause_if_requested", lambda *_a, **_k: parked)

    outcome = execute_phases(deps, _ctx(specs))

    assert outcome is parked
    assert _names(published) == [], "被停车拦下的组不得发 phase.started"


# ------------------------------------------------------------------------ 结论词表与按压


def test_the_outcome_vocabulary_is_a_closed_set() -> None:
    """`PHASE_OUTCOMES` 是闭集：两值穷举"组跑完了"的两种真实形态。"""
    assert PHASE_OUTCOMES == {PHASE_OUTCOME_SUCCEEDED, PHASE_OUTCOME_DEGRADED}


def test_a_tolerated_failure_reports_degraded_not_succeeded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """被契约容忍的失败 ⇒ 本组 `DEGRADED`（与 `RunOutcome` 的 DEGRADED 口径同源）。"""
    from packages.application.run_orchestration import phase_runner as pr

    specs = (_spec("phase-a", "agent-1"),)

    def tolerated(deps: Any, tctx: Any) -> Any:  # noqa: ARG001
        return PhaseStep(tolerated_failure="model timeout (tolerated)")

    monkeypatch.setattr(pr, "_execute_one_task", tolerated)

    class _Outcome:
        failure_policy = "CONTINUE"
        task = specs[0][0]

    assert phase_outcome([_Outcome()], specs) == PHASE_OUTCOME_DEGRADED


class TestTheCriterionBites:
    """**反证臂**：摘掉发射点 ⇒ 判据真的判红（子进程按压、逐字节复原）。"""

    def test_removing_the_started_emission_turns_the_criterion_red(self) -> None:
        from tests.application.subprocess_press_support import press_run

        result = press_run(
            "packages/application/run_orchestration/phase_runner.py",
            "        phase_progress.emit_phase_started(deps, ctx, group)\n",
            "tests/application/run_orchestration/test_phase_progress_events.py"
            "::test_phase_started_precedes_the_first_task_and_completed_follows_the_last",
        )

        assert result.bit, (
            "摘掉 `emit_phase_started` 后时序判据必须判红（否则它没在判发射点）",
            result,
        )

    def test_removing_the_completed_emission_turns_the_criterion_red(self) -> None:
        """摘掉 `emit_phase_completed` ⇒ 时序判据必须判红（证明 completed 真是个发射点）。

        与上一条成对：一条钉 started 的发射点真的在跑，一条钉 completed 的。两条都证明
        「判据不是看着事件名自说自话」——删掉实现中对应的那一行，判据真的会红。
        """
        from tests.application.subprocess_press_support import press_run

        result = press_run(
            "packages/application/run_orchestration/phase_runner.py",
            "        phase_progress.emit_phase_completed(deps, ctx, group, run)\n",
            "tests/application/run_orchestration/test_phase_progress_events.py"
            "::test_phase_started_precedes_the_first_task_and_completed_follows_the_last",
        )

        assert result.bit, (
            "摘掉 `emit_phase_completed` 后时序判据必须判红（completed 真的不在事件里）",
            result,
        )


def _SpecContext(**kwargs: Any) -> Any:
    from packages.application.run_orchestration.task_executor import SessionSpecContext

    return SessionSpecContext(**kwargs)
