"""ScheduleRegistry 定向用例（GOAL-003 EC-03 / PLAN-066 WP-A）。

覆盖：内置定义补齐、创建/更新/删除的取值域、`due()` 的 reserve 语义、
`record()` 的运行事实、`trigger()` 与守护线程共用同一条 pass（含失败留痕），
以及"启停被读面消费"的可证伪证据（停用后 run_count 不再增长）。
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from adapters.fakes.schedule_store import FakeScheduleStore
from packages.application.ops.schedule_registry import ScheduleRegistry
from packages.application.ports.errors import InvalidInputError
from packages.domain.core import Timestamp
from packages.domain.schedules import BUILTIN_NAMES, ScheduleJob


class _Clock:
    """可控时钟：`advance()` 推进，`now()` 给 registry 用。"""

    def __init__(self) -> None:
        self.current = Timestamp.now()

    def advance(self, seconds: float) -> None:
        self.current = Timestamp(self.current.value + timedelta(seconds=seconds))

    def now(self) -> Timestamp:
        return self.current


def _registry() -> tuple[ScheduleRegistry, FakeScheduleStore, _Clock]:
    store = FakeScheduleStore()
    clock = _Clock()
    return ScheduleRegistry(store, now=clock.now), store, clock


def test_ensure_builtins_is_idempotent() -> None:
    registry, _, _ = _registry()
    assert registry.ensure_builtins() == sorted(BUILTIN_NAMES)
    assert registry.ensure_builtins() == []
    assert {item.name for item in registry.definitions()} == BUILTIN_NAMES


def test_create_validates_and_reserves_builtin_names() -> None:
    registry, _, _ = _registry()
    created = registry.create(
        name="outbox_relay_fast",
        job=ScheduleJob.OUTBOX_RELAY,
        interval_seconds=2.0,
    )
    assert created.builtin is False
    assert registry.get("outbox_relay_fast") is not None

    with pytest.raises(InvalidInputError, match="already exists"):
        registry.create(
            name="outbox_relay_fast", job=ScheduleJob.OUTBOX_RELAY, interval_seconds=3.0
        )
    with pytest.raises(InvalidInputError, match="already exists"):
        registry.create(name="outbox_relay", job=ScheduleJob.OUTBOX_RELAY, interval_seconds=3.0)
    with pytest.raises(InvalidInputError, match="interval_seconds"):
        registry.create(name="too_fast", job=ScheduleJob.RETENTION, interval_seconds=0.01)
    with pytest.raises(InvalidInputError, match="lowercase"):
        registry.create(name="Bad-Name", job=ScheduleJob.RETENTION, interval_seconds=60.0)


def test_update_changes_state_and_rejects_unknown() -> None:
    registry, _, _ = _registry()
    registry.ensure_builtins()

    updated = registry.update("retention", enabled=False, interval_seconds=120.0)
    assert updated.enabled is False
    assert updated.interval_seconds == 120.0
    assert registry.get("retention") == updated

    with pytest.raises(KeyError):
        registry.update("nope", enabled=True)
    with pytest.raises(InvalidInputError, match="interval_seconds"):
        registry.update("retention", interval_seconds=0.0)


def test_delete_refuses_builtins_and_removes_custom() -> None:
    registry, _, _ = _registry()
    registry.ensure_builtins()
    registry.create(name="extra_reap", job=ScheduleJob.WORKER_REAPER, interval_seconds=45.0)
    registry.delete("extra_reap")
    assert registry.get("extra_reap") is None

    with pytest.raises(InvalidInputError, match="builtin"):
        registry.delete("worker_reaper")
    with pytest.raises(KeyError):
        registry.delete("missing")


def test_due_reserves_and_skips_disabled() -> None:
    registry, _, clock = _registry()
    registry.ensure_builtins()
    registry.create(name="relay_fast", job=ScheduleJob.OUTBOX_RELAY, interval_seconds=5.0)
    registry.update("outbox_relay", enabled=False)

    due = registry.due(ScheduleJob.OUTBOX_RELAY)
    assert [item.name for item in due] == ["relay_fast"]
    # reserve：立即再问不会重复交付
    assert registry.due(ScheduleJob.OUTBOX_RELAY) == []
    clock.advance(5.1)
    assert [item.name for item in registry.due(ScheduleJob.OUTBOX_RELAY)] == ["relay_fast"]


def test_record_updates_facts_and_next_due() -> None:
    registry, _, clock = _registry()
    registry.ensure_builtins()
    registry.record("lease_recovery", outcome="OK")

    facts = registry.runtime("lease_recovery")
    assert facts.run_count == 1
    assert facts.last_run_at == clock.current
    assert facts.last_outcome == "OK"
    assert facts.next_due_at is not None
    assert facts.next_due_at.value > clock.current.value


def test_trigger_shares_pass_with_daemon_and_records_failure() -> None:
    registry, _, _ = _registry()
    registry.ensure_builtins()
    calls: list[str] = []
    registry.register_executor(ScheduleJob.LEASE_RECOVERY, lambda: calls.append("pass"))

    facts = registry.trigger("lease_recovery")
    assert calls == ["pass"]
    assert facts.run_count == 1
    assert facts.last_outcome == "OK"
    assert facts.executor_attached is True

    def boom() -> None:
        raise RuntimeError("pass exploded")

    registry.register_executor(ScheduleJob.LEASE_RECOVERY, boom)
    failed = registry.trigger("lease_recovery")
    assert failed.last_outcome == "FAILED"
    assert failed.last_error == "pass exploded"
    assert failed.run_count == 2


def test_trigger_rejects_unknown_disabled_and_unattached() -> None:
    registry, _, _ = _registry()
    registry.ensure_builtins()
    registry.register_executor(ScheduleJob.RETENTION, lambda: None)

    with pytest.raises(KeyError):
        registry.trigger("missing")

    registry.update("retention", enabled=False)
    with pytest.raises(InvalidInputError, match="disabled"):
        registry.trigger("retention")

    # 无执行体（本装配不跑 outbox relay）⇒ 如实拒绝，不假装跑过
    with pytest.raises(InvalidInputError, match="no executor attached"):
        registry.trigger("outbox_relay")
    assert registry.runtime("outbox_relay").executor_attached is False


def test_disable_is_consumed_by_read_surface() -> None:
    """写面被读面消费：守护线程按 `due()` 执行时，停用后 run_count 冻结。"""

    registry, _, clock = _registry()
    registry.ensure_builtins()
    registry.create(name="relay_fast", job=ScheduleJob.OUTBOX_RELAY, interval_seconds=5.0)
    registry.register_executor(ScheduleJob.OUTBOX_RELAY, lambda: None)

    def daemon_ticks(count: int) -> None:
        for _ in range(count):
            clock.advance(5.0)
            for definition in registry.due(ScheduleJob.OUTBOX_RELAY):
                registry.record(definition.name, outcome="OK")

    daemon_ticks(3)
    assert registry.runtime("relay_fast").run_count == 3

    registry.update("relay_fast", enabled=False)
    daemon_ticks(5)
    assert registry.runtime("relay_fast").run_count == 3

    registry.update("relay_fast", enabled=True)
    daemon_ticks(2)
    assert registry.runtime("relay_fast").run_count == 5


def test_wait_seconds_never_sprints_before_the_daemons_own_interval() -> None:
    """尚未预约的定义不缩短守护线程的等待：定义"下一轮生效"，不能让它启动瞬间抢跑。

    首版对"未预约"返回 0.1s，于是四个守护线程在 app 起来的 100ms 后同时开跑，
    与启动期其他初始化写并发（共享连接上互相打断事务）——本题是那条回归的钉子。
    """

    registry, _, clock = _registry()
    registry.ensure_builtins()  # 内置 lease_recovery interval = 30s

    # 没有任何预约：等待 = 守护线程自身 interval（这里给 5s），而不是 0.1s
    assert registry.next_wait_seconds(ScheduleJob.LEASE_RECOVERY, 5.0) == 5.0

    # 预约之后：等待 = min(自身 interval, 定义剩余时间)——定义更近就等定义
    registry.due(ScheduleJob.LEASE_RECOVERY)
    assert registry.next_wait_seconds(ScheduleJob.LEASE_RECOVERY, 60.0) == 30.0
    clock.advance(29.0)
    assert registry.next_wait_seconds(ScheduleJob.LEASE_RECOVERY, 60.0) == 1.0


def test_wait_seconds_ignores_disabled_definitions() -> None:
    registry, _, _ = _registry()
    registry.ensure_builtins()
    registry.update("lease_recovery", enabled=False)
    assert registry.next_wait_seconds(ScheduleJob.LEASE_RECOVERY, 7.0) == 7.0
