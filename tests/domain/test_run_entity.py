"""ResearchRun 实体不变量与状态迁移测试。"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.domain.core import ID, Digest, Timestamp
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState
from packages.domain.state_machines import InvalidTransitionError


def _utc(dt: datetime) -> Timestamp:
    return Timestamp(dt)


NOW = datetime(2026, 8, 13, 9, 0, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 8, 13, 9, 5, 0, tzinfo=timezone.utc)


def _run(**overrides: object) -> ResearchRun:
    base: dict[str, object] = {
        "id": ID.generate(),
        "project_id": "proj-1",
        "protocol_id": "sort_analysis_v1",
        "state": ResearchRunState.State.DRAFT,
        "created_at": _utc(NOW),
        "updated_at": _utc(NOW),
    }
    base.update(overrides)
    return ResearchRun(**base)  # type: ignore[arg-type]


class TestResearchRunInvariants:
    def test_requires_project_and_protocol(self) -> None:
        with pytest.raises(ValueError, match="project_id"):
            ResearchRun(id=ID.generate(), project_id="", protocol_id="p")
        with pytest.raises(ValueError, match="protocol_id"):
            ResearchRun(id=ID.generate(), project_id="proj", protocol_id="")

    def test_default_state_is_draft(self) -> None:
        run = _run()
        assert run.state == ResearchRunState.State.DRAFT
        assert not run.is_terminal

    def test_manifest_digest_defaults_none(self) -> None:
        assert _run().manifest_digest is None


class TestResearchRunTransitions:
    def test_happy_path_lifecycle(self) -> None:
        run = _run()
        run = run.transition(ResearchRunState.Transition.START_COMPILE)
        assert run.state == ResearchRunState.State.COMPILING
        run = run.transition(ResearchRunState.Transition.COMPILE_OK)
        assert run.state == ResearchRunState.State.PREFLIGHT
        run = run.transition(ResearchRunState.Transition.PREFLIGHT_OK)
        assert run.state == ResearchRunState.State.READY
        run = run.transition(ResearchRunState.Transition.START)
        assert run.state == ResearchRunState.State.RUNNING
        run = run.transition(ResearchRunState.Transition.SUCCEED)
        assert run.state == ResearchRunState.State.SUCCEEDED
        assert run.is_terminal

    def test_preflight_failure_path(self) -> None:
        run = _run()
        run = run.transition(ResearchRunState.Transition.START_COMPILE)
        run = run.transition(ResearchRunState.Transition.COMPILE_OK)
        run = run.transition(ResearchRunState.Transition.PREFLIGHT_FAILED)
        assert run.state == ResearchRunState.State.FAILED
        assert run.is_terminal

    def test_illegal_transition_raises(self) -> None:
        run = _run()
        with pytest.raises(InvalidTransitionError):
            run.transition(ResearchRunState.Transition.SUCCEED)

    def test_terminal_state_cannot_revert(self) -> None:
        run = _run()
        run = run.transition(ResearchRunState.Transition.CANCEL)
        assert run.state == ResearchRunState.State.CANCELLED
        with pytest.raises(InvalidTransitionError):
            run.transition(ResearchRunState.Transition.START)

    def test_transition_preserves_identity(self) -> None:
        run = _run()
        moved = run.transition(ResearchRunState.Transition.START_COMPILE)
        assert moved.id == run.id
        assert moved.project_id == run.project_id
        assert moved.protocol_id == run.protocol_id
        assert moved.manifest_digest is None

    def test_pause_resume_cycle(self) -> None:
        run = _run()
        run = run.transition(ResearchRunState.Transition.START_COMPILE)
        run = run.transition(ResearchRunState.Transition.COMPILE_OK)
        run = run.transition(ResearchRunState.Transition.PREFLIGHT_OK)
        run = run.transition(ResearchRunState.Transition.START)
        run = run.transition(ResearchRunState.Transition.PAUSE)
        assert run.state == ResearchRunState.State.PAUSED
        run = run.transition(ResearchRunState.Transition.RESUME)
        assert run.state == ResearchRunState.State.RUNNING


class TestResearchRunManifest:
    def test_with_manifest_records_digest_keeps_state(self) -> None:
        digest = Digest.of_bytes(b"manifest")
        run = _run(state=ResearchRunState.State.READY)
        frozen = run.with_manifest(digest)
        assert frozen.manifest_digest == digest
        assert frozen.state == ResearchRunState.State.READY
        assert run.manifest_digest is None
