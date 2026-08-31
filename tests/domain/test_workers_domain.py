"""M16 WP1 domain tests: WorkerState machine + bounded WorkerRegistration."""

from __future__ import annotations

import pytest

from packages.domain.core import ID
from packages.domain.enums import TaskKind
from packages.domain.state_base import InvalidTransitionError
from packages.domain.tasks import ResearchTask
from packages.domain.workers import (
    PARTITION_COUNT,
    WorkerRegistration,
    WorkerState,
)


def _reg(**overrides: object) -> WorkerRegistration:
    base: dict[str, object] = {
        "worker_id": "w1",
        "protocol_version": "1",
        "runtime_version": "0.1.0",
        "capabilities": frozenset({"docker"}),
        "backend_kinds": frozenset({"DOCKER"}),
        "platform": "linux/amd64",
        "partition_slots": frozenset({0}),
        "max_concurrency": 1,
    }
    base.update(overrides)
    return WorkerRegistration(**base)  # type: ignore[arg-type]


def test_worker_state_initial_and_terminal() -> None:
    assert WorkerState.initial() == WorkerState.State.REGISTERING
    assert WorkerState.terminal() == frozenset({WorkerState.State.OFFLINE})


def test_worker_state_full_happy_path() -> None:
    current = WorkerState.initial()
    for event, expected in [
        (WorkerState.Transition.HANDSHAKE_OK, WorkerState.State.READY),
        (WorkerState.Transition.CLAIM, WorkerState.State.BUSY),
        (WorkerState.Transition.JOB_SETTLED, WorkerState.State.READY),
        (WorkerState.Transition.DRAIN_REQUESTED, WorkerState.State.DRAINING),
        (WorkerState.Transition.OWNED_WORK_SETTLED, WorkerState.State.OFFLINE),
    ]:
        current = WorkerState.transition(current, event)
        assert current == expected


def test_worker_state_lost_then_reregister() -> None:
    current = WorkerState.transition(
        WorkerState.State.READY, WorkerState.Transition.HEARTBEAT_EXPIRED
    )
    assert current == WorkerState.State.LOST
    current = WorkerState.transition(current, WorkerState.Transition.RE_REGISTER)
    assert current == WorkerState.State.REGISTERING


def test_worker_state_terminal_offline_has_no_outgoing() -> None:
    for event in vars(WorkerState.Transition).values():
        if isinstance(event, str):
            with pytest.raises(InvalidTransitionError):
                WorkerState.transition(WorkerState.State.OFFLINE, event)


def test_worker_state_handshake_rejected_offlines_generation() -> None:
    nxt = WorkerState.transition(
        WorkerState.State.REGISTERING, WorkerState.Transition.HANDSHAKE_REJECTED
    )
    assert nxt == WorkerState.State.OFFLINE


def test_every_declared_state_is_reachable_or_initial() -> None:
    states = {
        getattr(WorkerState.State, name)
        for name in dir(WorkerState.State)
        if not name.startswith("_")
    }
    reachable = {WorkerState.initial()}
    for (_src, _evt), dst in WorkerState._TRANSITIONS.items():
        reachable.add(_src)
        reachable.add(dst)
    assert states == reachable


def test_registration_rejects_oversized_worker_id() -> None:
    with pytest.raises(ValueError):
        _reg(worker_id="x" * 200)


def test_registration_rejects_out_of_range_partition() -> None:
    with pytest.raises(ValueError):
        _reg(partition_slots=frozenset({PARTITION_COUNT}))


def test_registration_rejects_zero_concurrency() -> None:
    with pytest.raises(ValueError):
        _reg(max_concurrency=0)


def test_registration_rejects_too_many_capabilities() -> None:
    caps = frozenset(f"cap-{i}" for i in range(100))
    with pytest.raises(ValueError):
        _reg(capabilities=caps)


def test_registration_rejects_unknown_state() -> None:
    with pytest.raises(ValueError):
        _reg(state="NOT_A_STATE")


def test_with_state_preserves_identity_and_updates_state() -> None:
    reg = _reg()
    moved = reg.with_state(WorkerState.State.READY, drain_requested=True)
    assert moved.state == WorkerState.State.READY
    assert moved.drain_requested is True
    assert moved.worker_id == reg.worker_id


def test_research_task_defaults_to_agent_session() -> None:
    task = ResearchTask(id=ID.generate(), run_id=ID.generate())
    assert task.kind == TaskKind.AGENT_SESSION
    assert task.partition is None
    assert task.required_capability is None


def test_research_task_accepts_execution_kind_and_coerces_string() -> None:
    task = ResearchTask(
        id=ID.generate(),
        run_id=ID.generate(),
        kind="EXECUTION",
        partition=3,
        required_capability="docker",
    )
    assert task.kind is TaskKind.EXECUTION
    assert task.partition == 3


def test_research_task_rejects_negative_partition() -> None:
    with pytest.raises(ValueError):
        ResearchTask(id=ID.generate(), run_id=ID.generate(), partition=-1)


def test_research_task_rejects_blank_required_capability() -> None:
    with pytest.raises(ValueError):
        ResearchTask(
            id=ID.generate(), run_id=ID.generate(), required_capability="   "
        )
