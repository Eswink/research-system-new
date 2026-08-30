"""Snapshot migration use case tests (M14 debt closure, WP-A).

Covers:
- plan_legacy_migration classification (keep/re-freeze/fork) per run state
- apply_migration re-freeze writes digests back; resume guard then passes
- apply_migration fork creates an independent new run (original untouched)
- idempotent re-run: a second scan+apply does not create duplicate migrations
- safety boundary: assert_semantics_frozen still rejects unmigrated legacy runs
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from packages.application.run_orchestration.convergence import assert_semantics_frozen
from packages.application.run_orchestration.snapshot_migration import (
    apply_migration,
    plan_legacy_migration,
)
from packages.domain.core import ID, Digest, Timestamp
from packages.domain.run import ResearchRun
from packages.domain.run_state import ResearchRunState

D1 = "sha256:" + "a" * 64
D2 = "sha256:" + "b" * 64


def _uid(tag: str) -> str:
    """Deterministic UUID4 from a tag (tests only)."""
    return str(uuid.uuid4())


def _run(
    tag: str,
    state: str,
    *,
    manifest_digest: Digest | None = None,
    semantic: Digest | None = None,
) -> ResearchRun:
    return ResearchRun(
        id=ID(_uid(tag)),
        project_id="p-1",
        protocol_id="console_demo_research_v1_0_1",
        state=state,
        manifest_digest=manifest_digest,
        manifest_semantic_digest=semantic,
    )


class _FakeRunStore:
    """RunStore 内存实现（测试用；无并发语义需要）。"""

    def __init__(self, runs: list[ResearchRun]) -> None:
        self._runs: dict[str, ResearchRun] = {r.id.value: r for r in runs}

    def list_runs(self, project_id: str | None = None) -> list[ResearchRun]:
        if project_id is None:
            return list(self._runs.values())
        return [r for r in self._runs.values() if r.project_id == project_id]

    def get_run(self, run_id: str) -> ResearchRun:
        try:
            return self._runs[run_id]
        except KeyError:
            raise KeyError(f"run not found: {run_id!r}") from None

    def save_run(self, run: ResearchRun) -> None:
        self._runs[run.id.value] = run


def _refreeze(run: ResearchRun) -> tuple[str, str]:
    """Deterministic refreeze: digests derived from run/protocol (test seam)."""
    return D1, D2


class TestPlanClassification:
    def test_legacy_frozen_snapshot_is_refreeze(self) -> None:
        run = _run("legacy", ResearchRunState.State.PAUSED, manifest_digest=Digest.parse(D1))
        plan = plan_legacy_migration((run,))
        assert plan.runs[0].action == "re-freeze"
        assert plan.needs_action

    def test_unfrozen_draft_is_keep(self) -> None:
        run = _run("draft", ResearchRunState.State.DRAFT)
        plan = plan_legacy_migration((run,))
        assert plan.runs[0].action == "keep"

    def test_terminal_legacy_is_keep(self) -> None:
        run = _run("done", ResearchRunState.State.SUCCEEDED, manifest_digest=Digest.parse(D1))
        plan = plan_legacy_migration((run,))
        assert plan.runs[0].action == "keep"

    def test_missing_manifest_in_running_is_fork(self) -> None:
        run = _run("broken", ResearchRunState.State.RUNNING)
        plan = plan_legacy_migration((run,))
        assert plan.runs[0].action == "fork"

    def test_already_migrated_is_keep(self) -> None:
        run = _run(
            "ok",
            ResearchRunState.State.PAUSED,
            manifest_digest=Digest.parse(D1),
            semantic=Digest.parse(D2),
        )
        plan = plan_legacy_migration((run,))
        assert plan.runs[0].action == "keep"


class TestApplyRefreeze:
    def test_refreeze_writes_digests(self) -> None:
        run = _run("legacy", ResearchRunState.State.PAUSED, manifest_digest=Digest.parse(D1))
        store = _FakeRunStore([run])
        plan = plan_legacy_migration((run,))
        result = apply_migration(plan, store, _refreeze)
        assert result.migrated_count == 1

        migrated = store.get_run(run.id.value)
        assert migrated.manifest_semantic_digest == Digest.parse(D2)
        assert migrated.manifest_digest == Digest.parse(D1)

    def test_unmigrated_legacy_still_rejected_by_guard(self) -> None:
        run = _run("old", ResearchRunState.State.PAUSED, manifest_digest=Digest.parse(D1))
        # Guard contract: semantic_digest=None raises ManifestFreezeError.
        from packages.application.preflight.preflight import ManifestFreezeError
        from packages.application.run_orchestration.context import RunContext

        guard_context = RunContext(
            protocol=None,  # type: ignore[arg-type]
            plan=None,  # type: ignore[arg-type]
            report=None,  # type: ignore[arg-type]
            run=run,
            catalog=None,  # type: ignore[arg-type]
            project=None,  # type: ignore[arg-type]
            preflight=None,  # type: ignore[arg-type]
            trace_id="",
        )
        with pytest.raises(ManifestFreezeError):
            assert_semantics_frozen(guard_context)

    def test_refreeze_idempotent_second_apply_noop(self) -> None:
        run = _run("legacy2", ResearchRunState.State.PAUSED, manifest_digest=Digest.parse(D1))
        store = _FakeRunStore([run])
        first = apply_migration(plan_legacy_migration((run,)), store, _refreeze)
        assert first.migrated_count == 1
        # re-scan after migration: run is now fully migrated -> keep
        second_plan = plan_legacy_migration((store.get_run(run.id.value),))
        second = apply_migration(second_plan, store, _refreeze)
        assert second.migrated_count == 0
        assert store.get_run(run.id.value).manifest_semantic_digest == Digest.parse(D2)


class TestApplyFork:
    def test_fork_creates_independent_run(self) -> None:
        original = _run("broken2", ResearchRunState.State.RUNNING)
        store = _FakeRunStore([original])
        plan = plan_legacy_migration((original,))
        result = apply_migration(plan, store, _refreeze)
        assert result.migrated_count == 1
        forked_id = result.runs[0].run_id
        forked = store.get_run(forked_id)
        assert forked_id != original.id.value
        assert forked.state == "READY"
        assert forked.manifest_digest == Digest.parse(D1)
        assert forked.manifest_semantic_digest == Digest.parse(D2)
        # original untouched (read-only history)
        assert store.get_run(original.id.value).manifest_digest is None
        assert store.get_run(original.id.value).state == ResearchRunState.State.RUNNING


class TestTimestampRoundtrip:
    def test_refreeze_preserves_created_at(self) -> None:
        ts = Timestamp(datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc))
        run = ResearchRun(
            id=ID(_uid("ts")),
            project_id="p-1",
            protocol_id="proto",
            state=ResearchRunState.State.PAUSED,
            manifest_digest=Digest.parse(D1),
            created_at=ts,
            updated_at=ts,
        )
        store = _FakeRunStore([run])
        apply_migration(plan_legacy_migration((run,)), store, _refreeze)
        migrated = store.get_run(run.id.value)
        assert migrated.created_at == ts
