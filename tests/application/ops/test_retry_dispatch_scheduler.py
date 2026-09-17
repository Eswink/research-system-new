"""重排派发守护线程（GOAL-003 cycle 19 / PLAN-20260915-082）。

覆盖"派发方真的会来取"这件事的可证伪断言：

1. 到期的停车 run ⇒ 续跑并把结果写回 canonical run（store 被 save）；
2. 没到期 ⇒ 一次都不动（判定由 adapter 的权威时钟做，本类不自己拿墙钟比）；
3. 用户手动暂停（没有到期的重排）⇒ 不碰（区分"重排停车"与"用户暂停"）；
4. 本进程没有续跑上下文（重启后）⇒ 跳过，不假装能续跑；
5. 单个 run 抛错不影响整轮（下一个 pass 重新评估）。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from packages.domain.core import ID
from packages.domain.protocol_source import ProtocolSource
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from services.api.scheduler import RetryDispatchDeps, RetryDispatchScheduler

_RUN_ID = "3a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"


@dataclass
class _RunStore:
    runs: list[ResearchRun] = field(default_factory=list)
    saved: list[tuple[str, str]] = field(default_factory=list)

    def list_runs(self) -> list[ResearchRun]:
        return list(self.runs)

    def save_run(self, run: ResearchRun) -> None:
        self.saved.append((run.id.value, run.state))


@dataclass
class _Workflow:
    due: dict[str, tuple[str, ...]] = field(default_factory=dict)
    asked: list[str] = field(default_factory=list)
    boom: bool = False

    def due_retry_task_ids(self, run_id: str) -> tuple[str, ...]:
        self.asked.append(run_id)
        if self.boom:
            raise RuntimeError("read face down")
        return self.due.get(run_id, ())


@dataclass
class _Runs:
    contexts: set[str] = field(default_factory=set)
    resumed: list[str] = field(default_factory=list)
    outcome_state: str = ResearchRunState.State.SUCCEEDED
    boom: bool = False
    compensations: list[tuple[str, str]] = field(default_factory=list)

    def has_paused_context(self, run_id: str) -> bool:
        return run_id in self.contexts

    def resume_paused(self, run_id: str, run: Any) -> Any:
        if self.boom:
            raise RuntimeError("resume exploded")
        self.resumed.append(run_id)
        return replace(run, state=self.outcome_state)

    def compensate_failed_resume(self, run: Any, failure: BaseException) -> Any:
        """与真实现同形：放回 PAUSED（迁移 + 记原因在真实现里发事件）。"""
        self.compensations.append((run.id.value, type(failure).__name__))
        return run.transition(ResearchRunState.Transition.PAUSE)


def _run(
    state: str = ResearchRunState.State.PAUSED,
    *,
    protocol_source: ProtocolSource | None = None,
) -> ResearchRun:
    return ResearchRun(
        id=ID(_RUN_ID),
        project_id="project-1",
        protocol_id="protocol-1",
        state=state,
        protocol_source=protocol_source,
    )


def _scheduler(
    *,
    run: ResearchRun | None = None,
    due: tuple[str, ...] = ("task-1",),
    context: bool = True,
) -> tuple[RetryDispatchScheduler, _Workflow, _Runs, _RunStore]:
    workflow = _Workflow(due={_RUN_ID: due} if due else {})
    runs = _Runs(contexts={_RUN_ID} if context else set())
    store = _RunStore(runs=[run or _run()])
    scheduler = RetryDispatchScheduler(
        RetryDispatchDeps(runs=runs, runs_store=store, workflow=workflow)
    )
    return scheduler, workflow, runs, store


def test_a_due_retry_is_dispatched_and_the_run_state_is_saved() -> None:
    scheduler, _, runs, store = _scheduler()

    dispatched = scheduler._execute_pass()

    assert dispatched == 1
    assert runs.resumed == [_RUN_ID]
    assert store.saved == [
        (_RUN_ID, ResearchRunState.State.RUNNING),
        (_RUN_ID, ResearchRunState.State.SUCCEEDED),
    ], "先迁到 RUNNING（暂停谓词读的就是它），再把续跑结果写回"


def test_nothing_due_means_no_dispatch() -> None:
    """没到期（`due_retry_task_ids` 为空）⇒ 一次都不动。"""
    scheduler, workflow, runs, store = _scheduler(due=())

    assert scheduler._execute_pass() == 0
    assert runs.resumed == []
    assert store.saved == []
    assert workflow.asked == [_RUN_ID], "到期判定必须真的问过 workflow 读面"


def test_a_user_paused_run_is_left_alone() -> None:
    """用户手动暂停没有到期的重排 ⇒ 不碰它（本进程有上下文也不行）。"""
    scheduler, _, runs, store = _scheduler(due=(), context=True)

    assert scheduler._execute_pass() == 0
    assert runs.resumed == []
    assert store.saved == []


def test_a_run_without_local_context_is_skipped() -> None:
    """本进程没有续跑上下文（重启后）⇒ 跳过；并如实问过读面之前先看上下文。"""
    scheduler, workflow, runs, store = _scheduler(context=False)

    assert scheduler._execute_pass() == 0
    assert runs.resumed == []
    assert store.saved == []
    assert workflow.asked == [], "没有上下文就不该去问有没有到期的重排"


def test_a_run_in_another_state_is_not_touched() -> None:
    scheduler, workflow, runs, _ = _scheduler(run=_run(ResearchRunState.State.RUNNING))

    assert scheduler._execute_pass() == 0
    assert runs.resumed == []
    assert workflow.asked == []


def test_one_bad_run_does_not_break_the_pass() -> None:
    """单个 run 的读面失败 ⇒ 本轮跳过它（返回 0），不把异常抛出守护线程。"""
    scheduler, workflow, runs, store = _scheduler()
    workflow.boom = True

    assert scheduler._execute_pass() == 0
    assert runs.resumed == []
    assert store.saved == [], "读面失败连状态都不该动"


def test_a_failed_resume_is_compensated_back_to_paused() -> None:
    """续跑失败不留悬空 RUNNING（GOAL-004 cycle 7 = EC-06）：放回 PAUSED 并记原因。"""
    scheduler, workflow, runs, store = _scheduler()
    workflow.boom = False
    runs.boom = True

    assert scheduler._execute_pass() == 0, "失败的那条不算派发成功"

    assert runs.compensations == [(_RUN_ID, "RuntimeError")], "补偿必须真的发生（带原因类型）"
    assert store.saved == [
        (_RUN_ID, ResearchRunState.State.RUNNING),
        (_RUN_ID, ResearchRunState.State.PAUSED),
    ], "先迁 RUNNING（续跑需要），失败后补偿回 PAUSED——不留悬空 RUNNING"


def test_a_compensated_run_can_be_resumed_on_the_next_pass() -> None:
    """补偿后可重入：同一入口下一轮 pass 真的能把它续起来（不是把它钉死在停车态）。"""
    scheduler, _, runs, store = _scheduler()
    runs.boom = True
    assert scheduler._execute_pass() == 0
    assert store.saved[-1] == (_RUN_ID, ResearchRunState.State.PAUSED)

    runs.boom = False
    assert scheduler._execute_pass() == 1, "补偿只是回到可重试的状态，不是终局"

    assert store.saved[-1] == (_RUN_ID, ResearchRunState.State.SUCCEEDED)
    assert runs.resumed == [_RUN_ID]


# --- GOAL-003 cycle 20：本进程没有上下文时按 durable 来源重建续跑 ---

_SOURCE = ProtocolSource(protocol_path="examples/protocols/sort_analysis_v1.yaml")


@dataclass
class _Outcome:
    state: str


@dataclass
class _Attempt:
    outcome: _Outcome | None = None
    refusal: str | None = None


@dataclass
class _Rebuilder:
    attempts: list[str] = field(default_factory=list)
    refusal: str | None = None

    def __call__(self, run: Any) -> _Attempt:
        self.attempts.append(run.id.value)
        if self.refusal is not None:
            return _Attempt(refusal=self.refusal)
        return _Attempt(outcome=_Outcome(state=ResearchRunState.State.SUCCEEDED))


def _scheduled_for_rebuild(
    *, source: ProtocolSource | None = _SOURCE
) -> tuple[RetryDispatchScheduler, _RunStore, _Rebuilder, _Runs]:
    workflow = _Workflow(due={_RUN_ID: ("task-1",)})
    runs = _Runs(contexts=set())  # 重启后：本进程没有续跑上下文
    store = _RunStore(runs=[_run(protocol_source=source)])
    rebuilder = _Rebuilder()
    scheduler = RetryDispatchScheduler(
        RetryDispatchDeps(runs=runs, runs_store=store, workflow=workflow, rebuild=rebuilder)
    )
    return scheduler, store, rebuilder, runs


def test_without_a_local_context_a_recorded_source_is_rebuilt_and_resumed() -> None:
    """重启后没有上下文 ⇒ 按 run 记下的来源重建续跑（cycle 20 的新入口）。"""
    scheduler, store, rebuilder, _ = _scheduled_for_rebuild()

    dispatched = scheduler._execute_pass()

    assert dispatched == 1
    assert rebuilder.attempts == [_RUN_ID], "重建入口必须被真的调用"
    assert store.saved == [
        (_RUN_ID, ResearchRunState.State.RUNNING),
        (_RUN_ID, ResearchRunState.State.SUCCEEDED),
    ]


def test_a_refused_rebuild_puts_the_run_back_to_parked() -> None:
    """重建被诚实拒绝 ⇒ 放回停车状态（本进程一个任务都没执行，不假装 RUNNING）。"""
    scheduler, store, rebuilder, _ = _scheduled_for_rebuild()
    rebuilder.refusal = "run has no recorded protocol source"

    assert scheduler._execute_pass() == 0
    assert store.saved == [
        (_RUN_ID, ResearchRunState.State.RUNNING),
        (_RUN_ID, ResearchRunState.State.PAUSED),
    ], "拒绝之后 canonical 必须回到 PAUSED"


def test_a_run_without_a_recorded_source_is_not_even_considered() -> None:
    """没有来源可重建 ⇒ 连 canonical 都不碰（不把"没有入口"伪装成"派发过一次"）。"""
    scheduler, store, rebuilder, runs = _scheduled_for_rebuild(source=None)

    assert scheduler._execute_pass() == 0
    assert store.saved == []
    assert rebuilder.attempts == []
    assert runs.resumed == []
