"""Reference admission, interruption replay, and immutable truth regressions."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import packages.application.m12_reference.clean_run as workflow
from adapters.execution.remote_backend import RemoteExecutionBackend
from adapters.fakes.artifact_store import FakeArtifactStore
from adapters.fakes.execution_job_queue import FakeExecutionJobQueue
from packages.application.m12_reference.clean_run_stages import experiment_run_id_of
from packages.domain.workspace import ExecutionSpec
from tests.application.m12_clean_run_fixtures import COMMAND, PLAN_ID, RUN_ID
from tests.tooling.test_个人生产续审v2 import _durable_deps


def _run(deps: Any) -> Any:
    return workflow.run_clean_workflow(deps, experiment_plan_id=PLAN_ID, experiment_command=COMMAND)


def test_run_and_frozen_manifest_exist_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    deps = _durable_deps(tmp_path)
    execute = deps.execution.execute

    def observed(*args: Any, **kwargs: Any) -> Any:
        run = deps.persistence.run_store.get_run(RUN_ID)
        assert run.state == "RUNNING"
        meta = deps.artifacts.meta(f"{RUN_ID}:run_manifest.json")
        assert meta is not None and meta.digest == run.manifest_digest
        return execute(*args, **kwargs)

    monkeypatch.setattr(deps.execution, "execute", observed)
    _run(deps)


@pytest.mark.parametrize("cut", ["_complete_run", "commit_memory", "close_budget"])
def test_interrupted_process_resumes_without_reexecuting_completed_experiment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cut: str
) -> None:
    deps = _durable_deps(tmp_path)
    original = getattr(workflow, cut)

    def interrupt(*args: Any, **kwargs: Any) -> Any:
        if cut != "_complete_run":
            original(*args, **kwargs)
        raise KeyboardInterrupt("simulated process loss")

    with monkeypatch.context() as context:
        context.setattr(workflow, cut, interrupt)
        with pytest.raises(KeyboardInterrupt):
            _run(deps)
    before = deps.persistence.run_store.get_run(RUN_ID)
    assert before.state == "RUNNING"
    result = _run(deps)
    after = deps.persistence.run_store.get_run(RUN_ID)
    assert after.state == "SUCCEEDED"
    assert after.created_at == before.created_at
    assert after.manifest_digest == before.manifest_digest
    assert deps.execution._counter == 1
    assert result.budget_entries == 2  # this CPU-only fixture has CPU + evaluation usage


def test_resume_refuses_configuration_drift_before_any_new_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    deps = _durable_deps(tmp_path)

    def interrupt(*_: Any, **__: Any) -> Any:
        raise KeyboardInterrupt

    with monkeypatch.context() as context:
        context.setattr(workflow, "_complete_run", interrupt)
        with pytest.raises(KeyboardInterrupt):
            _run(deps)
    with pytest.raises(RuntimeError, match="drift"):
        _run(replace(deps, objective="different scientific objective"))
    assert deps.execution._counter == 1
    assert deps.persistence.run_store.get_run(RUN_ID).state == "RUNNING"


def test_worker_image_mismatch_cannot_publish_success_or_deliverable(tmp_path: Path) -> None:
    deps = replace(_durable_deps(tmp_path), expected_image_digest="sha256:other-image")
    with pytest.raises(RuntimeError, match="worker image drift"):
        _run(deps)
    assert deps.persistence.run_store.get_run(RUN_ID).state == "FAILED"
    assert deps.artifacts.meta(f"{RUN_ID}:deliverable.json") is None


def test_terminal_run_is_not_silently_reexecuted_or_overwritten(tmp_path: Path) -> None:
    deps = _durable_deps(tmp_path)
    _run(deps)
    before = deps.persistence.run_store.get_run(RUN_ID)
    with pytest.raises(RuntimeError, match="not resumable"):
        _run(deps)
    assert deps.persistence.run_store.get_run(RUN_ID) == before
    assert deps.execution._counter == 1


def test_bound_job_replay_does_not_depend_on_host_workspace_path(tmp_path: Path) -> None:
    first, second = tmp_path / "old-host", tmp_path / "restored-host"
    first.mkdir()
    second.mkdir()
    for root in (first, second):
        (root / "experiment.py").write_text("print('same immutable input')", encoding="utf-8")
    queue = FakeExecutionJobQueue()
    backend = RemoteExecutionBackend.for_run(RUN_ID, job_queue=queue, artifacts=FakeArtifactStore())
    spec = ExecutionSpec(
        backend_kind="DOCKER", command="python experiment.py", workspace_path=str(first)
    )
    original = backend._submit(spec, first)
    replay = backend._submit(replace(spec, workspace_path=str(second)), second)
    assert replay == original
    assert queue.state.jobs[original].spec.workspace_path is None


def test_run_ids_with_same_prefix_do_not_share_experiment_identity() -> None:
    first = "12121212-2222-4333-8444-555555555555"
    second = "12121212-2222-4333-8444-666666666666"
    assert experiment_run_id_of(first) != experiment_run_id_of(second)
