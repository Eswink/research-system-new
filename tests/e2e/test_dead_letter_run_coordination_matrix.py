"""E2E（GOAL-20261008-033 EC-02）：**死信恢复 ↔ run 续跑的协同在哪、不在哪**。

GOAL-032 把「死信恢复与 run 续跑的自动协同不存在」登记为下一轮输入（代表而非穷尽）。
本文件把它**逐面量成判据**：三个面各给实测读数，并在每个面上分别回答「协同存在吗」。

| 面 | 情形 | 实测判定 |
| --- | --- | --- |
| **run 状态** | 默认契约：预算打满 ⇒ 死信 | run 收敛 **`FAILED`**（终态，①） |
| **run 状态** | 容忍契约（`on_task_failure: CONTINUE`） | run 收敛 **`DEGRADED`**（非终态，②） |
| **派发方** | `RetryDispatchScheduler` 一轮 pass | **连考虑都不考虑**它（只扫 `PAUSED`，③） |
| **任务面（worker）** | `kind=EXECUTION` 的死信，恢复后 | **自动可再交付** ⇒ 该面协同已存在（④） |
| **任务面（编排）** | 编排死信（`kind=AGENT_SESSION`） | worker 面够不着；会话面取得回来（⑤） |
| **机制边界** | run `FAILED --RESUME-->` | **非法** ⇒ run 级自动继续需新机制（⑥） |

**为什么 A/B 是**逐面**回答而不是整体二选一**：EC-02 (b) 的路径 A 有一个前置条件
——「实测表明**恢复后无任何自动交付方**」。实测把它**证伪了一半**：worker 面上自动交付方
**本来就在**（`claim_next` 按状态过滤，恢复后立刻可取），所以在那个面上**没有东西需要实现**；
而编排面上自动继续确实缺席，但实现它要么改 run 级状态机（`FAILED` 是终态）、要么新增一个
扫非 `PAUSED` run 的派发面 —— **两条都是新机制**。按 EC-02 (b) 的「B 路径」如实登记，
并把「为什么不是 A」写成判据而不是散文。

**射程边界（如实登记）**：本文件判**协同在哪、不在哪**；`requeue` 自身的语义（幂等 /
点名拒绝 / 三实现同判）由 `tests/contracts/test_dead_letter_manual_recovery_contract.py`
与 `tests/adapters/sqlite/test_workflow_dead_letter_manual_recovery.py` 判，
产品入口由 `tests/api/test_task_retry_api.py` 判 —— 本文件不重复。
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from adapters.fakes.budget_ledger import FakeBudgetLedger
from adapters.sqlite.artifact_store import SqliteArtifactStore
from adapters.sqlite.db import connect
from adapters.sqlite.event_publisher import SqliteOutboxEventPublisher
from adapters.sqlite.run_store import SqliteRunStore
from adapters.sqlite.workflow_engine import SqliteWorkflowEngine
from packages.application.ports.agent_runtime import AgentSessionResult
from packages.application.ports.errors import TransientPortError
from packages.application.ports.workflow_engine import ClaimRequest, TaskCompletion
from packages.application.run_orchestration import (
    OrchestrationDependencies,
    RunOrchestrationService,
)
from packages.domain.core import ID, Digest
from packages.domain.enums import (
    AcceptanceCriterionType,
    FailureCategory,
    TaskKind,
)
from packages.domain.failure_policy import OnTaskFailure
from packages.domain.protocol_source import ProtocolSource
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.state_base import InvalidTransitionError
from packages.domain.task_state import ResearchTaskState
from packages.domain.tasks import AcceptanceCriterion, ResearchTask, RetryPolicy, TaskContract
from services.api.run_resume import ResumeAttempt
from services.api.scheduler import RetryDispatchDeps, RetryDispatchScheduler
from tests.e2e.scenario import StructuredOutputAgentRuntime, seed_run_inputs
from tests.e2e.scenario_catalog import m7_catalog
from tests.e2e.test_restart_rebuild_resume import _frozen_digests
from tests.e2e.test_retry_park_and_resume import BACKOFF_SECONDS, OUTPUTS, _start

START = datetime(2026, 9, 18, 9, 0, 0, tzinfo=timezone.utc)

_EXECUTION_CONTRACT = "sort_analysis_execution"


class _Clock:
    def __init__(self) -> None:
        self.value = START

    def __call__(self) -> Any:
        return self.value


class _AlwaysFails(StructuredOutputAgentRuntime):
    """执行契约**每次都失败**（模拟"重试也救不回来"）。"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.execution_attempts = 0

    def run(self, session_id: str) -> AgentSessionResult:
        spec = self._specs.get(session_id)
        if spec is not None and spec.task_contract.id == _EXECUTION_CONTRACT:
            self.execution_attempts += 1
            raise TransientPortError(
                "model timed out", failure_category=FailureCategory.MODEL_TIMEOUT
            )
        return super().run(session_id)


class _Harness:
    """一次性装配（真 SQLite workflow + 真编排 + 注入时钟）。"""

    def __init__(self) -> None:
        self.clock = _Clock()
        self.connection = connect(":memory:")
        self.engine = SqliteWorkflowEngine(
            connection=self.connection, lease_ttl_seconds=60, now=self.clock
        )
        self.artifacts = SqliteArtifactStore(connection=self.connection)
        seed_run_inputs(self.artifacts)
        self.events = SqliteOutboxEventPublisher(connection=self.connection)
        self.runtime = _AlwaysFails(outputs_by_contract=OUTPUTS)
        self.service = RunOrchestrationService(
            OrchestrationDependencies(
                runtime=self.runtime,
                workflow=self.engine,
                artifacts=self.artifacts,
                events=self.events,
                budget=FakeBudgetLedger(),
            )
        )
        self.store = SqliteRunStore(connection=self.connection)

    def close(self) -> None:
        self.artifacts.close()
        self.engine.close()

    def statuses(self, run_id: str) -> list[str]:
        return [str(row.task.status) for row in self.engine.list_tasks(run_id)]

    def dead_letter_task_id(self, run_id: str) -> str:
        return next(
            row.task.id.value
            for row in self.engine.list_tasks(run_id)
            if row.task.status == ResearchTaskState.State.DEAD_LETTER
        )

    def scheduler(self) -> RetryDispatchScheduler:
        """与 `services/api/app.py` 同形接线（`rebuild` 留空：本文件只判它**扫不扫**）。"""
        return RetryDispatchScheduler(
            RetryDispatchDeps(runs=self.service, runs_store=self.store, workflow=self.engine),
            interval_seconds=15.0,
        )

    def claim(self) -> str | None:
        lease = self.engine.claim_next(
            ClaimRequest(
                worker_id="e2e-worker",
                capabilities=frozenset({"docker"}),
                partitions=frozenset({0}),
            )
        )
        return lease.task_id if lease else None


def _catalog(*, max_attempts: int, tolerate: bool) -> Any:
    """m7 目录 + 执行契约的失败处置（打满即死信；可声明容忍失败）。"""
    catalog = m7_catalog()
    execution = catalog.task_contracts[_EXECUTION_CONTRACT]
    policy: dict[str, str | bool | int | list[str]] = (
        {"on_task_failure": OnTaskFailure.CONTINUE} if tolerate else {}
    )
    dying = replace(
        execution,
        retry_policy=RetryPolicy(
            max_attempts=max_attempts,
            retryable_categories=[FailureCategory.MODEL_TIMEOUT],
            backoff_seconds=BACKOFF_SECONDS,
        ),
        failure_policy=policy,
    )
    return replace(catalog, task_contracts={**catalog.task_contracts, execution.id: dying})


# --- ①② run 状态面：死信与 run 状态的两条组合 -------------------------------------


def test_a_dead_letter_from_an_unretryable_run_lands_with_run_failed() -> None:
    """**①默认契约**：预算打满 ⇒ 任务死信，**run 同时收敛 `FAILED`**（终态）。

    这是 GOAL-032 观察到的组合；本用例把它固定在判据里，免得「死信 ⇒ run 终态」
    被读成普遍规律（下一条用例证明它不是）。
    """
    harness = _Harness()
    try:
        run_id = ID.generate()
        outcome = _start(harness.service, _catalog(max_attempts=1, tolerate=False), run_id)

        assert outcome.state == ResearchRunState.State.FAILED, outcome.state
        assert outcome.state in ResearchRunState.terminal(), "FAILED 是终态"
        assert harness.statuses(run_id.value) == [ResearchTaskState.State.DEAD_LETTER]
    finally:
        harness.close()


def test_a_dead_letter_can_coexist_with_a_non_terminal_run() -> None:
    """**②容忍契约**：`on_task_failure: CONTINUE` ⇒ 任务死信而 run 收敛 **`DEGRADED`**。

    `DEGRADED` **不是**终态（`DEGRADED --RESUME--> RUNNING` 在迁移表里）⇒
    「死信 ⇒ run 终态」**不是**普遍规律。这条是 EC-02 的关键读数：它把「run 级自动继续」
    的可能性面**打开**了 —— 存在一个非终态、且有出边的 run 与死信**同现**。
    """
    harness = _Harness()
    try:
        run_id = ID.generate()
        outcome = _start(harness.service, _catalog(max_attempts=1, tolerate=True), run_id)

        assert outcome.state == ResearchRunState.State.DEGRADED, outcome.state
        assert outcome.state not in ResearchRunState.terminal(), "DEGRADED 不是终态"
        assert ResearchTaskState.State.DEAD_LETTER in harness.statuses(run_id.value), (
            "容忍失败不改变任务面的失败处置：它仍按 decide_failure 打满预算落死信"
        )
    finally:
        harness.close()


# --- ③ 派发方：恢复前后都不派发 ---------------------------------------------------


class _WorkflowSpy:
    """转调真实引擎，但记录**派发方问过哪条 run 的到期重排**。

    「考虑过这条 run」的可观察面就是这次询问：派发方在问之前先过状态过滤与重建能力
    两道门 ⇒ 被问到的 run 就是**真的进了它的能力圈**。用询问记录而不是 `dispatched`
    计数是因为计数被第三道门（「没有到期重排就跳过」）盖住：只改状态过滤时计数仍是 0
    ⇒ 那条断言**无法被单变量证伪**（实测踩到，见 `scratch/goal033-cycle2/press-matrix.log`）。
    """

    def __init__(self, engine: SqliteWorkflowEngine) -> None:
        self._engine = engine
        self.due_calls: list[str] = []

    def due_retry_task_ids(self, run_id: str) -> tuple[str, ...]:
        self.due_calls.append(run_id)
        return self._engine.due_retry_task_ids(run_id)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._engine, name)


def _sealed_run(run_id: ID, catalog: Any, state: str) -> ResearchRun:
    """一条**可重建**（有冻结 digest + 装配来源）的 run 行：给定状态。"""
    digest, semantic = _frozen_digests(run_id, catalog)
    return ResearchRun(
        id=run_id,
        project_id="m7-project",
        protocol_id="sort_analysis_v1",
        state=state,
        manifest_digest=Digest.parse(digest),
        manifest_semantic_digest=Digest.parse(semantic),
        protocol_source=ProtocolSource(protocol_path="examples/protocols/sort_analysis_v1.yaml"),
    )


def test_the_retry_dispatcher_never_even_considers_a_dead_letter_run() -> None:
    """**③派发方读数**：`RetryDispatchScheduler` **根本不把死信 run 纳入考虑**。

    量的是「考虑没考虑」而不是 `dispatched`：后者被「没有到期重排就跳过」这道门盖住，
    会让断言无法被**单变量**证伪（按压实测：只改状态过滤时计数仍是 0 ⇒ 假绿）。
    这里用 spy 记录派发方对 `due_retry_task_ids` 的询问 —— 它在两道门（状态、重建能力）
    **之后**才发生，所以「被问到 ⟺ 真的进了能力圈」。

    **正向对照**（防空真）：同一条 run 改成 `PAUSED` ⇒ 它**必须**被问到。
    """
    harness = _Harness()
    try:
        run_id = ID.generate()
        catalog = _catalog(max_attempts=1, tolerate=False)
        outcome = _start(harness.service, catalog, run_id)
        assert outcome.state == ResearchRunState.State.FAILED, "默认契约下 run 落终态"

        # 把它放进 store 并装配来源 ⇒ 状态过滤是**唯一**还挡着它的那道门（其余两道是热的）
        harness.store.save_run(_sealed_run(run_id, catalog, ResearchRunState.State.FAILED))

        spy = _WorkflowSpy(harness.engine)
        rebuild_calls: list[str] = []

        def _rebuild(run: Any) -> Any:
            rebuild_calls.append(run.id.value)
            return ResumeAttempt(refusal="probe: this test only measures consideration")

        scheduler = RetryDispatchScheduler(
            RetryDispatchDeps(
                runs=harness.service, runs_store=harness.store, workflow=spy, rebuild=_rebuild
            ),
            interval_seconds=15.0,
        )
        assert scheduler.run_once() == 0
        assert spy.due_calls == [], (
            f"派发方把一条 {ResearchRunState.State.FAILED} run 纳入了考虑（实测 {spy.due_calls}）"
            " —— 它只扫 PAUSED"
        )
        assert rebuild_calls == [], "更不该走到重建那一步"

        # 正向对照：只改状态 ⇒ 它必须被考虑（否则上面的空集是空真）
        harness.store.save_run(_sealed_run(run_id, catalog, ResearchRunState.State.PAUSED))
        scheduler.run_once()
        assert spy.due_calls == [run_id.value], (
            f"PAUSED 时它必须被问一次（实测 {spy.due_calls}）—— 否则本用例的受判面是空的"
        )
    finally:
        harness.close()


# --- ④⑤⑥ 任务面与机制边界 -------------------------------------------------------


def _worker_face_dead_letter(harness: _Harness, run_id: ID) -> str:
    """造一条 `kind=EXECUTION` 的死信（**不经编排**）：claim → 失败完成 ⇒ 打满即死信。

    走的是 worker 面自己的路径（`claim_next` + `complete`）而不是编排 —— 这正是 ④
    要判的那条面。
    """
    task = ResearchTask(
        id=ID.generate(),
        run_id=run_id,
        status=ResearchTaskState.State.QUEUED,
        kind=TaskKind.EXECUTION,
        required_capability="docker",
        partition=0,
    )
    contract = TaskContract(
        id="worker-face",
        version="1.0",
        purpose="worker-face redelivery",
        acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
        retry_policy=RetryPolicy(
            max_attempts=1, retryable_categories=[FailureCategory.MODEL_TIMEOUT]
        ),
    )
    harness.engine.submit(task, contract)
    lease = harness.engine.claim_next(
        ClaimRequest(
            worker_id="e2e-worker",
            capabilities=frozenset({"docker"}),
            partitions=frozenset({0}),
        )
    )
    assert lease is not None, "提交后必须能被 claim（本助手的前置）"
    harness.engine.complete(
        lease,
        TaskCompletion(
            task_id=task.id.value,
            outcome="FAILED",
            failure_category=FailureCategory.MODEL_TIMEOUT,
        ),
    )
    assert harness.statuses(run_id.value) == [ResearchTaskState.State.DEAD_LETTER]
    return task.id.value


def test_on_the_worker_face_recovery_is_followed_by_automatic_redelivery() -> None:
    """**④worker 面的协同已经存在**：`kind=EXECUTION` 的死信恢复后 `claim_next` 直接取到。

    这条**证伪**了「恢复后无任何自动交付方」这个 A 路径前置条件的一半：
    worker 面按**状态过滤**取任务，`requeue` 把它写回 `QUEUED` ⇒ 下一次 claim
    就取到它。**没有东西需要实现**（判据只需钉住它不被改坏）。
    """
    harness = _Harness()
    try:
        run_id = ID.generate()
        task_id = _worker_face_dead_letter(harness, run_id)

        assert harness.engine.requeue(task_id) == "restored"
        assert harness.claim() == task_id, (
            "恢复后 worker 面必须自动取到它 —— 这条面上协同**已存在**"
        )
    finally:
        harness.close()


def test_on_the_orchestration_face_the_worker_claim_cannot_reach_the_dead_task() -> None:
    """**⑤编排面的两条结构事实**（合起来说明 ④ 的机制**够不着**这条面上的死信）。

    ① 编排产生的死信任务是 `AGENT_SESSION`（会话投递面），而 worker 的 claim 扫描
       **只取 `EXECUTION`** ⇒ 恢复后 `claim_next` 仍然取不到它；
    ② run 级续跑只能靠 `resume` / 重建（`rebuild_and_resume`），而那要求 run **可
       resume**（`FAILED` 不是）。
    """
    harness = _Harness()
    try:
        run_id = ID.generate()
        _start(harness.service, _catalog(max_attempts=1, tolerate=False), run_id)
        task_id = harness.dead_letter_task_id(run_id.value)

        kind = next(
            str(row.task.kind)
            for row in harness.engine.list_tasks(run_id.value)
            if row.task.id.value == task_id
        )
        assert kind == str(TaskKind.AGENT_SESSION), (
            f"编排死信的 kind 是会话面（实测 {kind}）⇒ worker claim 的结构面够不着它"
        )

        assert harness.engine.requeue(task_id) == "restored"
        assert harness.claim() is None, "① worker 面不得取到会话面任务（claim 只扫 EXECUTION）"
        assert harness.engine.acquire_lease(task_id).task_id == task_id, (
            "② 但**会话面**（编排续跑用的那条路径）取得回来 ⇒ 能力在，只缺「谁来驱动 run」"
        )
    finally:
        harness.close()


def test_the_run_state_machine_has_no_edge_from_failed_back_to_running() -> None:
    """**⑥机制边界**：`FAILED` 是真终态 ⇒ run 级自动继续**需要新机制**。

    这是「为什么不是路径 A」的机械依据：在默认契约下死信与 `FAILED` 同现，而
    `FAILED` 没有任何出边 ⇒ 「恢复后自动把 run 带回去跑完」不可能只靠组合既有部件实现；
    它要么改 run 级状态机（改语义，须 ADR），要么新增一个扫非 `PAUSED` run 的派发面
    （新机制）。两者都在本 GOAL 的射程外 ⇒ 按 EC-02 (b) 的 **B 路径**如实登记。
    """
    try:
        ResearchRunState.transition(
            ResearchRunState.State.FAILED, ResearchRunState.Transition.RESUME
        )
    except InvalidTransitionError:
        pass
    else:  # pragma: no cover - 状态机若放开这条边，本判据必须红
        raise AssertionError("run 级出现了 FAILED → RUNNING 的边 ⇒ EC-02 的 B 判定要重做")

    assert ResearchRunState.State.FAILED in ResearchRunState.terminal()
    # 对照：`DEGRADED` 有出边（②里那条非终态 run）—— 两条读数的差别正是 B 判定的依据。
    assert (
        ResearchRunState.transition(
            ResearchRunState.State.DEGRADED, ResearchRunState.Transition.RESUME
        )
        == ResearchRunState.State.RUNNING
    )
