"""PeriodicDaemon 与调度定义读面的接线证据（GOAL-003 EC-03 / PLAN-066 WP-B）。

这里断言的不是"响应体里写了 enabled"，而是**既有守护线程真的按定义读面行事**：

- 定义 `interval_seconds` 决定 pass 节奏（守护线程自身的 interval 不决定）；
- `enabled=False` 后 `run_count` 冻结（守护线程仍在轮询，`due()` 不再授予）；
- 失败的 pass 被记为 FAILED + 错误原文，且守护线程不会因此消失；
- `trigger(name)` 跑的是守护线程注册的**同一条** pass 函数（计数器证明）。

时间由注入 registry 的可控时钟推进（域内 interval 下限 1s，真等会拖慢套件）；
真实线程的轮询用有界等待 `_wait_for` 观察，不用固定 sleep 判定。
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import timedelta

from adapters.fakes.schedule_store import FakeScheduleStore
from packages.application.ops.schedule_registry import (
    OUTCOME_FAILED,
    OUTCOME_OK,
    ScheduleRegistry,
)
from packages.domain.core import Timestamp
from packages.domain.schedules import ScheduleJob
from services.api.scheduler import PeriodicDaemon


class _Clock:
    def __init__(self) -> None:
        self.current = Timestamp.now()

    def advance(self, seconds: float) -> None:
        self.current = Timestamp(self.current.value + timedelta(seconds=seconds))

    def now(self) -> Timestamp:
        return self.current


def _wait_for(predicate: Callable[[], bool], timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def _registry() -> tuple[ScheduleRegistry, _Clock]:
    clock = _Clock()
    registry = ScheduleRegistry(FakeScheduleStore(), now=clock.now)
    registry.ensure_builtins()
    return registry, clock


class _CountingDaemon(PeriodicDaemon):
    """每个 pass 只计数；用于观察"谁在跑、跑了几次"。"""

    job = ScheduleJob.LEASE_RECOVERY
    thread_name = "test-counting"

    def __init__(self, *, control: object = None, interval_seconds: float = 0.02) -> None:
        super().__init__(interval_seconds=interval_seconds, control=control)
        self.passes = 0

    def _execute_pass(self) -> int:
        self.passes += 1
        return self.passes


class _FailingDaemon(PeriodicDaemon):
    """pass 永远失败：用来证明失败被记录、且守护线程活了下来。"""

    job = ScheduleJob.WORKER_REAPER
    thread_name = "test-failing"

    def __init__(self, *, control: object = None) -> None:
        super().__init__(interval_seconds=0.02, control=control)
        self.calls = 0

    def _execute_pass(self) -> None:
        self.calls += 1
        raise RuntimeError("pass exploded")


def _lease_facts(registry: ScheduleRegistry) -> int:
    return registry.runtime("lease_recovery").run_count


def test_daemon_cadence_follows_definition_not_own_interval() -> None:
    """定义 interval=30s、守护线程 interval=0.02s：29s 内不得再跑，31s 后必须跑。"""

    registry, clock = _registry()
    daemon = _CountingDaemon(control=registry, interval_seconds=0.02)
    daemon.start()
    try:
        assert _wait_for(lambda: _lease_facts(registry) >= 1)
        clock.advance(29.0)
        time.sleep(0.2)  # 守护线程在这段时间里已轮询 ~10 次
        assert _lease_facts(registry) == 1
        clock.advance(2.0)
        assert _wait_for(lambda: _lease_facts(registry) >= 2)
    finally:
        daemon.stop()


def test_disable_is_consumed_by_the_daemon_loop() -> None:
    registry, clock = _registry()
    registry.update("lease_recovery", interval_seconds=1.0)
    daemon = _CountingDaemon(control=registry)
    daemon.start()
    try:
        assert _wait_for(lambda: _lease_facts(registry) >= 1)
        clock.advance(2.0)
        assert _wait_for(lambda: _lease_facts(registry) >= 2)

        registry.update("lease_recovery", enabled=False)
        time.sleep(0.15)  # 让在途 pass 收尾
        frozen = _lease_facts(registry)
        clock.advance(600.0)
        time.sleep(0.3)
        assert _lease_facts(registry) == frozen
        assert registry.runtime("lease_recovery").next_due_at is None

        registry.update("lease_recovery", enabled=True)
        clock.advance(2.0)
        assert _wait_for(lambda: _lease_facts(registry) > frozen)
    finally:
        daemon.stop()


def test_failed_pass_is_recorded_and_loop_survives() -> None:
    registry, clock = _registry()
    registry.update("worker_reaper", interval_seconds=1.0)
    daemon = _FailingDaemon(control=registry)
    daemon.start()
    try:
        assert _wait_for(lambda: registry.runtime("worker_reaper").run_count >= 1)
        clock.advance(2.0)
        assert _wait_for(lambda: registry.runtime("worker_reaper").run_count >= 2)
        facts = registry.runtime("worker_reaper")
        assert facts.last_outcome == OUTCOME_FAILED
        assert facts.last_error == "pass exploded"
        assert daemon.calls >= 2
    finally:
        daemon.stop()


def test_trigger_runs_the_registered_daemon_pass() -> None:
    """`trigger` 复用守护线程注册的同一个函数对象（计数器是唯一证据）。"""

    registry, _ = _registry()
    daemon = _CountingDaemon(control=registry, interval_seconds=60.0)
    daemon.start()
    daemon.stop()
    assert registry.has_executor(ScheduleJob.LEASE_RECOVERY) is True

    before = daemon.passes
    facts = registry.trigger("lease_recovery")
    assert daemon.passes == before + 1
    assert facts.last_outcome == OUTCOME_OK


def test_daemon_without_control_runs_on_its_own_interval() -> None:
    """未装配调度写面时退化为原行为：每轮都跑，不注册执行体、不写事实。"""

    registry, _ = _registry()
    daemon = _CountingDaemon(control=None, interval_seconds=0.02)
    daemon.start()
    try:
        assert _wait_for(lambda: daemon.passes >= 3)
        assert registry.has_executor(ScheduleJob.LEASE_RECOVERY) is False
        assert _lease_facts(registry) == 0
    finally:
        daemon.stop()


def test_daemon_does_not_sprint_at_startup() -> None:
    """启动后必须**先等自己的 interval**，不能在 0.1s 处抢跑。

    首版 `next_wait_seconds` 对"尚未预约的定义"返回 0.1s ⇒ 四个守护线程在 app 起来的
    100ms 后同时开跑，和启动期其他初始化写并发（共享连接上互相打断事务）：
    真实爆炸是 `tests/postgres/test_m13_pg_run_e2e.py`（HEAD 6/6 绿、带该行为 6/6 红）。
    这里把时序钉死在守护线程自己身上：0.2s 时一次都不许跑，0.5s 之后必须跑过。
    """

    registry, _ = _registry()  # 内置 lease_recovery interval = 30s
    daemon = _CountingDaemon(control=registry, interval_seconds=0.5)
    daemon.start()
    try:
        time.sleep(0.2)
        assert daemon.passes == 0  # 0.1s 抢跑的话这里已经是 1
        assert _wait_for(lambda: daemon.passes >= 1, timeout=2.0)
    finally:
        daemon.stop()


class _Definition:
    """读面给的到点定义（只需要 name）。"""

    def __init__(self, name: str) -> None:
        self.name = name


class _FlakyControl:
    """可控故障的调度读面：单独验证"记账/读面抖动不能让守护线程消失"。"""

    def __init__(self, *, fail_due: bool = False, fail_record: bool = False) -> None:
        self.fail_due = fail_due
        self.fail_record = fail_record
        self.records: list[tuple[str, str]] = []

    def register_executor(self, job: ScheduleJob, run_pass: Callable[[], object]) -> None:
        return None

    def due(self, job: ScheduleJob) -> list[_Definition]:
        if self.fail_due:
            raise RuntimeError("schedule store unavailable")
        return [_Definition("flaky_name")]

    def next_wait_seconds(self, job: ScheduleJob, fallback: float) -> float:
        return 0.02

    def record(self, name: str, *, outcome: str, error: str | None = None) -> None:
        if self.fail_record:
            raise KeyError(name)
        self.records.append((name, outcome))


def test_daemon_records_facts_when_bookkeeping_works() -> None:
    control = _FlakyControl()
    daemon = _CountingDaemon(control=control)
    daemon.start()
    try:
        assert _wait_for(lambda: len(control.records) >= 2)
    finally:
        daemon.stop()
    assert set(control.records) == {("flaky_name", OUTCOME_OK)}


def test_daemon_survives_bookkeeping_failure() -> None:
    """`record` 抛错（定义被删/存储抖动）⇒ 不写事实，但 pass 继续跑。"""

    control = _FlakyControl(fail_record=True)
    daemon = _CountingDaemon(control=control)
    daemon.start()
    try:
        assert _wait_for(lambda: daemon.passes >= 3)
    finally:
        daemon.stop()
    assert control.records == []


def test_daemon_recovers_after_read_failure() -> None:
    """`due` 抛错 ⇒ 本轮不跑（不是线程死掉）；读面恢复后重新开跑。"""

    control = _FlakyControl(fail_due=True)
    daemon = _CountingDaemon(control=control)
    daemon.start()
    try:
        time.sleep(0.2)
        assert daemon.passes == 0
        control.fail_due = False
        assert _wait_for(lambda: daemon.passes >= 1)
    finally:
        daemon.stop()
