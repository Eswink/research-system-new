"""G14 ExperimentQueueEntry 域实体：状态机、来源值对象与迁移事实。

与 ExperimentPlan/Run 同模式：terminal 状态无出边、非法迁移抛
InvalidTransitionError；来源二选一在构造期即拒绝（不建"半个来源"的条目）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from packages.domain.core import ID, Timestamp
from packages.domain.experiment_queue import ExperimentQueueEntry, QueueProtocolSource
from packages.domain.experiment_state import ExperimentQueueState
from packages.domain.state_base import InvalidTransitionError

NOW = Timestamp(datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc))


def _at(offset_seconds: float = 0.0) -> Timestamp:
    return Timestamp(NOW.value + timedelta(seconds=offset_seconds))


def _events() -> list[str]:
    """ExperimentQueueState.Transition 的事件常量（按定义顺序，显式列举）。"""
    transitions = ExperimentQueueState.Transition
    return [
        transitions.CLAIM,
        transitions.COMPLETE_DISPATCH,
        transitions.COMPLETE_FAILURE,
        transitions.CLAIM_EXPIRED,
        transitions.CANCEL,
    ]


def _entry(**overrides: object) -> ExperimentQueueEntry:
    base: dict[str, object] = {
        "id": ID.generate(),
        "project_id": "proj-1",
        "plan_id": ID.generate(),
        "source": QueueProtocolSource(protocol_path="examples/protocols/m12.yaml"),
        "created_at": NOW,
        "updated_at": NOW,
    }
    base.update(overrides)
    return ExperimentQueueEntry(**base)  # type: ignore[arg-type]


# --- QueueProtocolSource ---


def test_source_accepts_exactly_one_form() -> None:
    assert QueueProtocolSource(protocol_path="p.yaml").draft_ref is None
    assert QueueProtocolSource(draft_id="d1", draft_revision=3).draft_ref == ("d1", 3)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"protocol_path": "p.yaml", "draft_id": "d1", "draft_revision": 1},
        {"draft_id": "d1"},
        {"draft_revision": 2},
        {"draft_id": "d1", "draft_revision": 0},
        {"protocol_path": ""},
    ],
)
def test_source_rejects_ambiguous_or_incomplete(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        QueueProtocolSource(**kwargs)  # type: ignore[arg-type]


# --- 状态机 ---


def test_state_machine_rejects_illegal_edges() -> None:
    with pytest.raises(InvalidTransitionError):
        ExperimentQueueState.transition(
            ExperimentQueueState.State.DISPATCHED, ExperimentQueueState.Transition.CANCEL
        )
    with pytest.raises(InvalidTransitionError):
        ExperimentQueueState.transition(
            ExperimentQueueState.State.QUEUED, ExperimentQueueState.Transition.COMPLETE_DISPATCH
        )
    with pytest.raises(InvalidTransitionError):
        ExperimentQueueState.transition(
            ExperimentQueueState.State.DISPATCHING,
            ExperimentQueueState.Transition.CANCEL,
        )


def test_terminal_states_have_no_outgoing_edges() -> None:
    for state in ExperimentQueueState.terminal():
        for event in _events():
            with pytest.raises(InvalidTransitionError):
                ExperimentQueueState.transition(state, event)


# --- 迁移事实 ---


def test_claim_then_dispatch_records_run_id() -> None:
    claimed = _entry().claim(NOW)
    assert claimed.state == ExperimentQueueState.State.DISPATCHING
    assert claimed.claimed_at == NOW
    dispatched = claimed.mark_dispatched("run-7")
    assert dispatched.state == ExperimentQueueState.State.DISPATCHED
    assert dispatched.run_id == "run-7"
    assert dispatched.is_terminal


def test_claim_expiry_returns_entry_to_queue() -> None:
    requeued = _entry().claim(NOW).requeue(_at(600))
    assert requeued.state == ExperimentQueueState.State.QUEUED
    assert requeued.claimed_at is None
    assert requeued.updated_at == _at(600)


def test_requeue_clears_previous_failure_note() -> None:
    """FAILED 是终态，故这里构造带旧失败注记的条目验证重认领会清空它。"""
    stale = _entry(failure_reason="earlier attempt failed")
    requeued = stale.claim(NOW).requeue(_at(600))
    assert requeued.failure_reason is None


def test_failure_requires_reason_and_dispatch_requires_run_id() -> None:
    claimed = _entry().claim(NOW)
    with pytest.raises(ValueError):
        claimed.mark_failed("")
    with pytest.raises(ValueError):
        claimed.mark_dispatched("")


def test_reschedule_only_queued_and_keeps_state() -> None:
    entry = _entry(not_before=NOW)
    later = _at(3 * 3600)
    moved = entry.reschedule(later, NOW)
    assert moved.state == ExperimentQueueState.State.QUEUED
    assert moved.not_before == later
    cleared = moved.reschedule(None, NOW)
    assert cleared.not_before is None
    with pytest.raises(InvalidTransitionError):
        entry.claim(NOW).reschedule(later, NOW)


def test_due_only_when_queued_and_schedule_passed() -> None:
    assert _entry().is_due(NOW)
    assert _entry(not_before=NOW).is_due(NOW)
    assert not _entry(not_before=_at(1)).is_due(NOW)
    assert not _entry().claim(NOW).is_due(NOW)


def test_entry_requires_project_id() -> None:
    with pytest.raises(ValueError):
        _entry(project_id="")
