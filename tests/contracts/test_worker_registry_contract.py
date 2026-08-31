"""WorkerRegistry contract suite (M16 WP1).

Shared semantics enforced against every registered implementation
(Fake + PostgreSQL): generation-monotonic registration, server-time
heartbeat with stale-generation rejection, state-machine transitions,
drain, lost detection, and deterministic read projections.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from packages.application.ports.errors import InvalidInputError
from packages.application.ports.worker_registry import WorkerRegistry
from packages.domain.state_base import InvalidTransitionError
from packages.domain.workers import WorkerRegistration, WorkerState
from tests.contracts.registry import PORT_IMPLEMENTATIONS

_FACTORIES: list[Callable[[], object]] = list(PORT_IMPLEMENTATIONS["worker_registry"])


def _registration(worker_id: str = "worker-a") -> WorkerRegistration:
    return WorkerRegistration(
        worker_id=worker_id,
        protocol_version="1",
        runtime_version="0.1.0",
        capabilities=frozenset({"docker", "cpu"}),
        backend_kinds=frozenset({"DOCKER"}),
        platform="linux/amd64",
        partition_slots=frozenset({0, 1}),
        max_concurrency=2,
    )


@pytest.mark.parametrize("factory", _FACTORIES)
def test_register_assigns_generation_one_and_registering(factory: Callable[[], object]) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    stored = registry.register(_registration())
    assert stored.registration_generation == 1
    assert stored.state == WorkerState.State.REGISTERING
    assert stored.last_heartbeat is not None


@pytest.mark.parametrize("factory", _FACTORIES)
def test_reregister_increments_generation_and_resets(factory: Callable[[], object]) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    registry.register(_registration())
    registry.transition("worker-a", WorkerState.Transition.HANDSHAKE_OK)
    second = registry.register(_registration())
    assert second.registration_generation == 2
    assert second.state == WorkerState.State.REGISTERING
    assert second.drain_requested is False


@pytest.mark.parametrize("factory", _FACTORIES)
def test_heartbeat_accepts_current_generation_rejects_stale(
    factory: Callable[[], object]
) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    stored = registry.register(_registration())
    assert registry.heartbeat("worker-a", stored.registration_generation) is True
    # stale generation (old session) fails closed
    assert registry.heartbeat("worker-a", stored.registration_generation - 1) is False
    # unknown worker fails closed
    assert registry.heartbeat("ghost", 1) is False


@pytest.mark.parametrize("factory", _FACTORIES)
def test_stale_generation_heartbeat_rejected_after_reregister(
    factory: Callable[[], object]
) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    first = registry.register(_registration())
    registry.register(_registration())  # bumps to generation 2
    # old session token's generation is now dead
    assert registry.heartbeat("worker-a", first.registration_generation) is False


@pytest.mark.parametrize("factory", _FACTORIES)
def test_transition_walks_lifecycle(factory: Callable[[], object]) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    registry.register(_registration())
    ready = registry.transition("worker-a", WorkerState.Transition.HANDSHAKE_OK)
    assert ready.state == WorkerState.State.READY
    busy = registry.transition("worker-a", WorkerState.Transition.CLAIM)
    assert busy.state == WorkerState.State.BUSY
    settled = registry.transition("worker-a", WorkerState.Transition.JOB_SETTLED)
    assert settled.state == WorkerState.State.READY


@pytest.mark.parametrize("factory", _FACTORIES)
def test_illegal_transition_raises(factory: Callable[[], object]) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    registry.register(_registration())
    with pytest.raises(InvalidTransitionError):
        registry.transition("worker-a", WorkerState.Transition.CLAIM)  # REGISTERING->BUSY illegal


@pytest.mark.parametrize("factory", _FACTORIES)
def test_transition_unknown_worker_raises(factory: Callable[[], object]) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    with pytest.raises(InvalidInputError):
        registry.transition("ghost", WorkerState.Transition.HANDSHAKE_OK)


@pytest.mark.parametrize("factory", _FACTORIES)
def test_drain_sets_flag_and_state(factory: Callable[[], object]) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    registry.register(_registration())
    registry.transition("worker-a", WorkerState.Transition.HANDSHAKE_OK)
    drained = registry.drain("worker-a")
    assert drained.state == WorkerState.State.DRAINING
    assert drained.drain_requested is True


@pytest.mark.parametrize("factory", _FACTORIES)
def test_mark_lost_from_ready(factory: Callable[[], object]) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    registry.register(_registration())
    registry.transition("worker-a", WorkerState.Transition.HANDSHAKE_OK)
    lost = registry.mark_lost("worker-a")
    assert lost.state == WorkerState.State.LOST


@pytest.mark.parametrize("factory", _FACTORIES)
def test_list_stale_fresh_worker_not_returned(factory: Callable[[], object]) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    registry.register(_registration())
    # a worker registered "now" is not stale under a one-hour threshold
    assert "worker-a" not in registry.list_stale(3600.0)


@pytest.mark.parametrize("factory", _FACTORIES)
def test_get_unknown_returns_none_and_list_is_sorted(factory: Callable[[], object]) -> None:
    registry: WorkerRegistry = factory()  # type: ignore[assignment]
    assert registry.get("ghost") is None
    registry.register(_registration("worker-b"))
    registry.register(_registration("worker-a"))
    ids = [w.worker_id for w in registry.list_workers()]
    assert ids == sorted(ids)
    assert {"worker-a", "worker-b"}.issubset(set(ids))
